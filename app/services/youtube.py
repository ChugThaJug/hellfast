import os
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from youtube_transcript_api import YouTubeTranscriptApi
from fastapi import HTTPException
import yt_dlp
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import DetachedInstanceError
from app.db.database import SessionLocal
import re

from app.core.settings import settings
from app.services.openai import OpenAIService
from app.services.transcription import TranscriptionService
from app.models.database import Video, ProcessingJob, User, ProcessingMode, OutputFormat

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.transcription_service = TranscriptionService()
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        dirs = [
            settings.CACHE_DIR,
            settings.DOWNLOAD_DIR,
            settings.OUTPUT_DIR,
        ]
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)

    async def get_transcript(self, video_id: str, languages: List[str] = ["en"]) -> List[Dict[str, Any]]:
        """Fetch transcript from YouTube video."""
        try:
            # Try YouTube API first
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            return [{'start': s['start'], 'text': s['text']} for s in transcript]
        except Exception as e:
            logger.warning(f"Failed to get YouTube transcript, falling back to Replicate: {str(e)}")
            try:
                # Fallback to Replicate transcription
                transcript = await self.transcription_service.transcribe_video(video_id)
                return transcript
            except Exception as e2:
                logger.error(f"Both transcript methods failed: {str(e2)}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get transcript from both YouTube and Replicate"
                )

    async def process_simple(self, video_id: str, output_format: OutputFormat) -> Tuple[Dict, int, int, float]:
        """Process transcript in simple mode (without chunking)."""
        transcript = await self.get_transcript(video_id)
        
        # Combine all text into one string
        full_text = " ".join([t["text"] for t in transcript])
        
        # Get prompt for the selected output format
        system_prompt = settings.SYSTEM_PROMPTS.get(
            output_format.value, 
            settings.SYSTEM_PROMPTS["step_by_step"]
        )
        
        # Process with OpenAI in one go
        response = await self.openai_service.process_text(full_text, system_prompt)
        
        # Create structured content based on format
        if output_format == OutputFormat.BULLET_POINTS:
            # Split into bullet points
            content = response.choices[0].message.content
            bullets = [p.strip().replace("• ", "").replace("- ", "") for p in content.split("\n") if p.strip()]
            processed_content = {
                "type": "bullet_points",
                "content": bullets,
                "text": content
            }
        elif output_format == OutputFormat.SUMMARY:
            # Simple summary
            content = response.choices[0].message.content
            processed_content = {
                "type": "summary",
                "content": content,
                "text": content
            }
        elif output_format == OutputFormat.STEP_BY_STEP:
            # Step by step guide, try to detect steps
            content = response.choices[0].message.content
            sections = content.split("\n\n")
            steps = []
            
            for section in sections:
                if section.strip():
                    # Check if it starts with a step number
                    steps.append(section.strip())
            
            processed_content = {
                "type": "step_by_step",
                "steps": steps,
                "text": content
            }
        else:  # OutputFormat.PODCAST_ARTICLE
            # Article format
            content = response.choices[0].message.content
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            
            processed_content = {
                "type": "podcast_article",
                "paragraphs": paragraphs,
                "text": content
            }
        
        # Get token usage from response
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        price = self.openai_service.calculate_price(input_tokens, output_tokens)
        
        return processed_content, input_tokens, output_tokens, price

    # In app/services/youtube.py


    async def process_detailed(self, video_id: str, output_format: OutputFormat) -> Tuple[Dict, int, int, float]:
        """Process transcript in detailed mode (with chunking)."""
        transcript = await self.get_transcript(video_id)
        
        # Process transcript into paragraphs
        paragraphs, p_input_tokens, p_output_tokens, p_price = await self.openai_service.transcript_to_paragraphs(
            transcript,
            settings.SYSTEM_PROMPTS["podcast_article"]  # Always use article format for paragraphs
        )
        
        # Generate TOC
        toc, t_input_tokens, t_output_tokens, t_price = await self.openai_service.generate_toc(paragraphs)
        
        # Clean up TOC data
        sections = []
        for chapter in toc:
            start = chapter.get('start_paragraph_number', 0)
            # Find paragraphs in this section
            section_paragraphs = []
            for i in range(start, len(paragraphs)):
                if i == start or (i > start and not any(c.get('start_paragraph_number', -1) == i for c in toc)):
                    if i < len(paragraphs):
                        section_paragraphs.append(paragraphs[i]['paragraph_text'])
            
            sections.append({
                "title": chapter['title'],
                "content": section_paragraphs
            })
        
        # Process into the requested output format
        processed_content, f_input_tokens, f_output_tokens, f_price = await self._convert_to_output_format(
            sections, output_format
        )
        
        # ENHANCEMENT 5: Post-process for coherence
        processed_content = await self._post_process_for_coherence(processed_content, output_format)
        
        # Calculate total tokens and price
        total_input = p_input_tokens + t_input_tokens + f_input_tokens
        total_output = p_output_tokens + t_output_tokens + f_output_tokens
        total_price = p_price + t_price + f_price
        
        return processed_content, total_input, total_output, total_price

    # Add this new method for post-processing
    async def _post_process_for_coherence(self, content: Dict, output_format: OutputFormat) -> Dict:
        """Post-process content for better coherence between sections."""
        if not content or "sections" not in content:
            return content
        
        try:
            # Different post-processing based on output format
            if content["type"] == "step_by_step":
                # Fix step numbering and duplicated content
                step_pattern = re.compile(r'^(Step\s*\d+:|#\s*Step\s*\d+:|\d+\.\s*|\*\s*Step\s*\d+:)')
                introduction_patterns = [
                    re.compile(r'^#+\s*introduction', re.IGNORECASE),
                    re.compile(r'^introduction', re.IGNORECASE),
                    re.compile(r'welcome to', re.IGNORECASE),
                    re.compile(r'^getting started', re.IGNORECASE),
                ]
                
                # Track steps across sections
                step_counter = 1
                processed_sections = []
                
                for i, section in enumerate(content["sections"]):
                    steps = section.get("steps", [])
                    processed_steps = []
                    
                    for step in steps:
                        # Skip duplicate introductions in non-first sections
                        if i > 0 and any(pattern.search(step) for pattern in introduction_patterns):
                            continue
                        
                        # Fix step numbering
                        processed_step = step
                        if step_pattern.search(step):
                            processed_step = step_pattern.sub(f"Step {step_counter}:", step)
                            step_counter += 1
                        
                        processed_steps.append(processed_step)
                    
                    if processed_steps:  # Only add section if it has steps
                        processed_sections.append({
                            "title": section["title"],
                            "steps": processed_steps
                        })
                
                content["sections"] = processed_sections
                
            elif content["type"] == "bullet_points":
                # Similar processing for bullet points
                processed_sections = []
                seen_bullets = set()
                
                for section in content["sections"]:
                    bullets = section.get("bullets", [])
                    processed_bullets = []
                    
                    for bullet in bullets:
                        # Normalize bullet to compare for duplicates
                        normalized = re.sub(r'\s+', ' ', bullet.lower().strip())
                        
                        # Skip if we've seen similar content before
                        if normalized in seen_bullets:
                            continue
                        
                        seen_bullets.add(normalized)
                        processed_bullets.append(bullet)
                    
                    if processed_bullets:  # Only add section if it has bullets
                        processed_sections.append({
                            "title": section["title"],
                            "bullets": processed_bullets
                        })
                
                content["sections"] = processed_sections
                
            elif content["type"] == "summary":
                # Process summaries for coherence
                # (This is simpler as summaries are already consolidated)
                pass
                
        except Exception as e:
            logger.warning(f"Error in post-processing for coherence: {str(e)}")
        
        return content

    # In app/services/youtube.py

    async def _convert_to_output_format(
        self, 
        sections: List[Dict], 
        output_format: OutputFormat
    ) -> Tuple[Dict, int, int, float]:
        """Convert structured content to the requested output format."""
        total_input_tokens = 0
        total_output_tokens = 0
        total_price = 0
        
        if output_format == OutputFormat.BULLET_POINTS:
            # Process each section into bullet points
            formatted_sections = []
            for i, section in enumerate(sections):
                section_text = "\n\n".join(section['content'])
                
                # ENHANCEMENT 6: Context-aware prompts
                section_prompt = settings.SYSTEM_PROMPTS["bullet_points"] + f"""

    This is section {i+1} of {len(sections)}, titled "{section['title']}".
    {"This is the first section." if i == 0 else "Continue from the previous section."}
    {"This is the last section." if i == len(sections) - 1 else "This will be followed by another section."}

    Do NOT repeat information already covered in previous sections.
    Do NOT include introductory text if this is not the first section.
    Focus on clear, concise bullet points specific to this section's content.
    """
                
                response = await self.openai_service.process_text(
                    section_text, 
                    section_prompt
                )
                
                # Extract bullets
                content = response.choices[0].message.content
                bullets = [p.strip().replace("• ", "").replace("- ", "") for p in content.split("\n") if p.strip()]
                
                formatted_sections.append({
                    "title": section['title'],
                    "bullets": bullets
                })
                
                # Track token usage
                total_input_tokens += response.usage.prompt_tokens
                total_output_tokens += response.usage.completion_tokens
                total_price += self.openai_service.calculate_price(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens
                )
            
            return {
                "type": "bullet_points",
                "sections": formatted_sections
            }, total_input_tokens, total_output_tokens, total_price
        
        elif output_format == OutputFormat.STEP_BY_STEP:
            # Process each section into step-by-step instructions
            formatted_sections = []
            step_count = 1  # ENHANCEMENT 7: Track steps across sections
            
            for i, section in enumerate(sections):
                section_text = "\n\n".join(section['content'])
                
                # ENHANCEMENT 8: Context-aware step-by-step prompts
                step_prompt = settings.SYSTEM_PROMPTS["step_by_step"] + f"""

    This is section {i+1} of {len(sections)}, titled "{section['title']}".
    {"This is the first section." if i == 0 else f"Continue from the previous section, which ended at Step {step_count-1}."}
    {"This is the last section." if i == len(sections) - 1 else "This will be followed by another section."}

    Start step numbering at Step {step_count}.
    Do NOT repeat information already covered in previous sections.
    Do NOT include introductory text if this is not the first section.
    Focus on clear, actionable steps specific to this section's content.
    """
                
                response = await self.openai_service.process_text(
                    section_text, 
                    step_prompt
                )
                
                content = response.choices[0].message.content
                steps = [p.strip() for p in content.split("\n\n") if p.strip()]
                
                # Update step count for next section
                step_matches = re.findall(r'Step\s*(\d+)', content)
                if step_matches:
                    try:
                        highest_step = max(int(s) for s in step_matches)
                        step_count = highest_step + 1
                    except ValueError:
                        step_count += len(steps)
                else:
                    step_count += len(steps)
                
                formatted_sections.append({
                    "title": section['title'],
                    "steps": steps
                })
                
                # Track token usage
                total_input_tokens += response.usage.prompt_tokens
                total_output_tokens += response.usage.completion_tokens
                total_price += self.openai_service.calculate_price(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens
                )
            
            return {
                "type": "step_by_step",
                "sections": formatted_sections
            }, total_input_tokens, total_output_tokens, total_price
        
        # Other formats remain the same...
        
        else:  # OutputFormat.PODCAST_ARTICLE
            # Keep the content as paragraphs
            formatted_sections = []
            for section in sections:
                formatted_sections.append({
                    "title": section['title'],
                    "paragraphs": section['content']
                })
            
            return {
                "type": "podcast_article",
                "sections": formatted_sections
            }, 0, 0, 0  # No additional processing needed

    @staticmethod
    async def get_video_info(video_id: str) -> Dict:
        """Get video information using yt-dlp."""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'skip_download': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            # Extract relevant info
            return {
                "title": info.get("title", ""),
                "channel": info.get("uploader", ""),
                "duration": info.get("duration", 0),
                "upload_date": info.get("upload_date", ""),
                "view_count": info.get("view_count", 0),
                "thumbnail": info.get("thumbnail", "")
            }
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return {"title": "", "channel": "", "duration": 0}

    @staticmethod
    async def create_video_db_entry(
        db: Session, 
        user_id: int, 
        video_id: str,
        mode: ProcessingMode, 
        output_format: OutputFormat
    ) -> Video:
        """Create a new video entry in the database."""
        # Get video info
        video_info = await YouTubeService.get_video_info(video_id)
        
        # Check if video already exists for this user
        existing = db.query(Video).filter(
            Video.user_id == user_id,
            Video.video_id == video_id
        ).first()
        
        if existing:
            # Update existing video
            existing.processing_mode = mode
            existing.output_format = output_format
            existing.status = "pending"
            existing.updated_at = datetime.utcnow()
            existing.title = video_info.get("title", "")
            
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new video
            db_video = Video(
                user_id=user_id,
                video_id=video_id,
                title=video_info.get("title", ""),
                status="pending",
                processing_mode=mode,
                output_format=output_format
            )
            
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            return db_video

    @staticmethod
    async def create_processing_job(
        db: Session, 
        video_db_id: int,
        mode: ProcessingMode, 
        output_format: OutputFormat
    ) -> ProcessingJob:
        """Create a new processing job in the database."""
        # Generate job ID
        job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{video_db_id}"
        
        # Create job
        job = ProcessingJob(
            job_id=job_id,
            video_id=video_db_id,
            status="pending",
            progress=0.0,
            mode=mode,
            output_format=output_format
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        return job


class YouTubeProcessingJob:
    def __init__(
        self,
        db: Session,
        job_id: str,
    ):
        self.db = db
        self.job_id = job_id
        self.youtube_service = YouTubeService()
        
        # Load job from database
        self.job = self._load_job()
        self.video = self._load_video()
    
    def _load_job(self) -> ProcessingJob:
        """Load job from database."""
        job = self.db.query(ProcessingJob).filter(ProcessingJob.job_id == self.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {self.job_id} not found")
        return job
    
    def _load_video(self) -> Video:
        """Load video from database."""
        video = self.db.query(Video).filter(Video.id == self.job.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video not found for job {self.job_id}")
        return video
    
    async def update_progress(self, progress: float, description: str = ""):
        """Update job progress."""
        self.job.progress = progress
        logger.info(f"Job {self.job_id}: {description} - {progress:.2%}")
        self.db.commit()
    
    async def process(self):
        """Process YouTube video based on selected mode."""
        # Create a new database session for this background task
        db = SessionLocal()
        
        try:
            # Get fresh copies of the job and video from the database
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == self.job_id).first()
            if not job:
                logger.error(f"Job {self.job_id} not found in the database")
                return
                
            video = db.query(Video).filter(Video.id == job.video_id).first()
            if not video:
                logger.error(f"Video for job {self.job_id} not found in the database")
                job.status = "failed"
                job.error = "Video not found"
                db.commit()
                return
            
            # Update status
            job.status = "processing"
            db.commit()
            
            # Use video_id from the video object directly
            video_id = video.video_id
            
            try:
                await self._update_progress_in_session(db, job.job_id, 0.1, "Starting processing")
                
                # Process based on mode
                if job.mode == ProcessingMode.SIMPLE:
                    processed_content, input_tokens, output_tokens, price = await self.youtube_service.process_simple(
                        video_id,
                        job.output_format
                    )
                    await self._update_progress_in_session(db, job.job_id, 0.8, "Processing completed")
                else:  # ProcessingMode.DETAILED
                    processed_content, input_tokens, output_tokens, price = await self.youtube_service.process_detailed(
                        video_id,
                        job.output_format
                    )
                    await self._update_progress_in_session(db, job.job_id, 0.8, "Processing completed")
                
                # Get fresh copies of job and video again to avoid any detached issues
                job = db.query(ProcessingJob).filter(ProcessingJob.job_id == self.job_id).first()
                video = db.query(Video).filter(Video.id == job.video_id).first()
                
                # Update job with results
                job.result = processed_content
                job.input_tokens = input_tokens
                job.output_tokens = output_tokens
                job.cost = price
                job.completed_at = datetime.utcnow()
                job.status = "completed"
                job.progress = 1.0
                
                # Update video status
                video.status = "completed"
                video.stats = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": price
                }
                video.chapters = processed_content
                
                # Save to database
                db.commit()
                logger.info(f"Job {self.job_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Job {self.job_id} failed: {str(e)}")
                
                # Get fresh copies of job and video again
                job = db.query(ProcessingJob).filter(ProcessingJob.job_id == self.job_id).first()
                video = db.query(Video).filter(Video.id == job.video_id).first()
                
                if job:
                    # Update job status
                    job.status = "failed"
                    job.error = str(e)
                
                if video:
                    # Update video status
                    video.status = "failed"
                    video.error = str(e)
                
                # Save to database
                db.commit()
        
        except Exception as e:
            logger.error(f"Error in background processing for job {self.job_id}: {str(e)}")
        finally:
            # Close the database session
            db.close()
    
    @staticmethod
    async def _update_progress_in_session(db: Session, job_id: str, progress: float, description: str = ""):
        """Update job progress within a specific session."""
        job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
        if job:
            job.progress = progress
            db.commit()
            logger.info(f"Job {job_id}: {description} - {progress:.2%}")
    
    @staticmethod
    async def get_job(db: Session, job_id: str) -> "YouTubeProcessingJob":
        """Get job by ID."""
        return YouTubeProcessingJob(db, job_id)
    
    @staticmethod
    async def get_latest_for_video(db: Session, video_db_id: int) -> Optional[ProcessingJob]:
        """Get latest job for a video."""
        return db.query(ProcessingJob).filter(
            ProcessingJob.video_id == video_db_id
        ).order_by(ProcessingJob.created_at.desc()).first()