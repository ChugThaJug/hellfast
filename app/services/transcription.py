from io import BytesIO
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from pytube import YouTube
import os
from typing import Dict, List
from fastapi import HTTPException

from app.core.settings import settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self._ensure_replicate_token()

    def _ensure_replicate_token(self):
        """Ensure REPLICATE_API_TOKEN is set"""
        if not settings.REPLICATE_API_TOKEN:
            logger.warning("REPLICATE_API_TOKEN not set, transcription fallback will be unavailable")
            return
            
        # Set for replicate package
        os.environ["REPLICATE_API_TOKEN"] = settings.REPLICATE_API_TOKEN

    async def transcribe_video(self, video_id: str) -> List[Dict]:
        """Main method to transcribe a YouTube video."""
        if not settings.REPLICATE_API_TOKEN:
            raise ValueError("Replicate API token not configured")
        
        try:
            start_time = time.time()
            
            # Get video audio
            buffer = await self._get_audio_buffer(video_id)
            
            # Get transcription
            transcription = await self._get_transcription(buffer)
            
            # Format transcription
            formatted_transcription = self._format_transcription(transcription)
            
            end_time = time.time()
            logger.info(f"Transcription completed in {end_time - start_time:.2f} seconds")
            
            return formatted_transcription
            
        except Exception as e:
            logger.error(f"Error transcribing video {video_id}: {str(e)}")
            raise

    async def _get_audio_buffer(self, video_id: str) -> BytesIO:
        """Download YouTube video audio into memory buffer."""
        try:
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            
            # Get best audio stream
            audio_streams = yt.streams.filter(only_audio=True)
            
            # Prefer webm format but fallback to others
            stream = None
            for mime_type in ["audio/webm", "audio/mp4"]:
                for s in audio_streams:
                    if s.mime_type == mime_type:
                        stream = s
                        break
                if stream:
                    break
            
            if not stream:
                # Fall back to any audio stream
                if audio_streams:
                    stream = audio_streams[0]
                else:
                    raise ValueError("No suitable audio stream found")
            
            # Download to buffer
            buffer = BytesIO()
            stream.stream_to_buffer(buffer)
            buffer.name = f"audio.{stream.subtype}"
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error downloading audio for video {video_id}: {str(e)}")
            raise

    async def _get_transcription(self, buffer: BytesIO) -> Dict:
        """Get transcription using Replicate's Whisper model."""
        try:
            import replicate
            
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                transcription = await loop.run_in_executor(
                    executor,
                    self._run_replicate,
                    buffer
                )
            return transcription
            
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            raise

    def _run_replicate(self, buffer: BytesIO) -> Dict:
        """Run Replicate's Whisper model."""
        try:
            import replicate
            return replicate.run(
                "vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c",
                input={
                    "audio": buffer,
                    "batch_size": 64
                }
            )
        except ImportError:
            raise ValueError("Replicate package not installed. Install with 'pip install replicate'")
        except Exception as e:
            raise ValueError(f"Replicate transcription failed: {str(e)}")

    def _format_transcription(self, transcription: Dict) -> List[Dict]:
        """Format Replicate transcription to match required format."""
        formatted = []
        for segment in transcription.get('segments', []):
            formatted.append({
                'start': float(segment.get('start', 0)),
                'text': segment.get('text', '').strip()
            })
        return formatted