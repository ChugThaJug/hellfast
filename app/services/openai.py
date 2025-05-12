import logging
from typing import Dict, List, Optional, Tuple, Callable
import asyncio
from openai import AsyncOpenAI
from app.core.settings import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Price rates for different models
        self.price_rates = settings.TOKEN_PRICES
        self.default_rates = settings.DEFAULT_TOKEN_PRICE

    def calculate_price(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate price based on token usage."""
        model = settings.MODEL
        rates = self.price_rates.get(model, self.default_rates)
        total_price = (
            input_tokens * rates['input'] +
            output_tokens * rates['output']
        )
        return round(total_price, 6)

    async def process_text(self, text: str, system_prompt: str, temperature: float = 0.7) -> Dict:
        """Process a chunk of text with a specific system prompt."""
        try:
            response = await self.client.chat.completions.create(
                model=settings.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=temperature,
                max_tokens=settings.MAX_TOKENS
            )
            return response
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise

    # In app/services/openai.py

    async def transcript_to_paragraphs(
        self,
        transcript: List[Dict],
        system_prompt: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Tuple[List[Dict], int, int, float]:
        """Process transcript into paragraphs with progress tracking."""
        if system_prompt is None:
            system_prompt = settings.SYSTEM_PROMPTS["podcast_article"]
            
        total_input_tokens = 0
        total_output_tokens = 0
        total_price = 0
        paragraphs = []
        successful_chunks = 0
        
        # Combine transcript text while keeping track of start times
        text_chunks = []
        current_chunk = {"text": "", "start_time": None}
        current_length = 0
        
        for segment in transcript:
            text = segment["text"].strip()
            if not text:
                continue
                
            # Start new chunk if needed
            if current_length + len(text) > settings.CHUNK_SIZE or not current_chunk["text"]:
                if current_chunk["text"]:
                    text_chunks.append(current_chunk)
                current_chunk = {"text": text, "start_time": float(segment["start"])}
                current_length = len(text)
            else:
                current_chunk["text"] += " " + text
                current_length += len(text) + 1
                
        # Add final chunk if not empty
        if current_chunk["text"]:
            text_chunks.append(current_chunk)
        
        total_chunks = len(text_chunks)
        
        # Create enhanced prompts for each chunk
        for i, chunk in enumerate(text_chunks):
            if progress_callback:
                progress = (i + 1) / total_chunks * 0.5
                await progress_callback(progress, "Processing transcript chunks")
            
            # ENHANCEMENT 1: Create context-aware prompt
            enhanced_prompt = system_prompt + f"""

    This is part {i+1} of {total_chunks} of the transcript. Your task is to:
    1. Convert this section into coherent paragraphs
    2. Maintain the flow of information
    3. {"This is the beginning of the transcript." if i == 0 else "Continue the flow from the previous part."}
    4. {"This is the end of the transcript." if i == total_chunks - 1 else "The content continues in the next part."}
    5. Do not repeat introductions or restart numbering
    """

            # ENHANCEMENT 2: Add context from adjacent chunks
            chunk_text = chunk["text"]
            if i > 0:
                # Add the last 100 characters from previous chunk for context
                prev_chunk_end = text_chunks[i-1]["text"][-100:] if len(text_chunks[i-1]["text"]) > 100 else text_chunks[i-1]["text"]
                chunk_text = f"[CONTEXT FROM PREVIOUS PART: {prev_chunk_end}]\n\n{chunk_text}"
                
            if i < total_chunks - 1:
                # Add the first 100 characters from next chunk for context
                next_chunk_start = text_chunks[i+1]["text"][:100] if len(text_chunks[i+1]["text"]) > 100 else text_chunks[i+1]["text"]
                chunk_text = f"{chunk_text}\n\n[CONTEXT FOR NEXT PART: {next_chunk_start}]"

            for attempt in range(settings.MAX_RETRIES):
                try:
                    response = await self.client.chat.completions.create(
                        model=settings.MODEL,
                        messages=[
                            {"role": "system", "content": enhanced_prompt},
                            {"role": "user", "content": chunk_text}
                        ],
                        temperature=0.7,
                        max_tokens=int(len(chunk["text"]) * 1.5)
                    )
                    
                    # Update tokens and price
                    total_input_tokens += response.usage.prompt_tokens
                    total_output_tokens += response.usage.completion_tokens
                    total_price += self.calculate_price(
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens
                    )
                    
                    # Process the response into paragraphs
                    chunk_paragraphs = [p.strip() for p in response.choices[0].message.content.strip().split("\n\n") if p.strip()]
                    
                    if chunk_paragraphs:
                        for j, p in enumerate(chunk_paragraphs):
                            # ENHANCEMENT 3: Filter out context markers
                            if not p.startswith("[CONTEXT") and not "CONTEXT]" in p:
                                paragraphs.append({
                                    "paragraph_number": len(paragraphs),
                                    "paragraph_text": p,
                                    "start_time": chunk["start_time"],
                                    "chunk_index": i  # Add chunk index for reference
                                })
                        successful_chunks += 1
                    break  # Break retry loop if successful
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {i} (attempt {attempt + 1}): {str(e)}")
                    if attempt == settings.MAX_RETRIES - 1:
                        logger.warning(f"Failed to process chunk {i} after {settings.MAX_RETRIES} attempts")
                    await asyncio.sleep(settings.RETRY_DELAY)
        
        # Check if we have enough successful chunks
        if successful_chunks < total_chunks * 0.5:  # At least 50% success rate
            logger.error(f"Too many failed chunks: {successful_chunks}/{total_chunks}")
            raise ValueError(f"Failed to process too many chunks ({successful_chunks}/{total_chunks})")
        
        if not paragraphs:
            raise ValueError("No paragraphs were generated")
            
        logger.info(f"Successfully processed {successful_chunks}/{total_chunks} chunks")
        return paragraphs, total_input_tokens, total_output_tokens, total_price

    async def generate_toc(
        self,
        paragraphs: List[Dict]
    ) -> Tuple[List[Dict], int, int, float]:
        """Generate table of contents from paragraphs."""
        try:
            # Prepare the text
            text = "\n\n".join([p["paragraph_text"] for p in paragraphs])
            total_paragraphs = len(paragraphs)
            
            # ENHANCEMENT 4: Improved TOC prompt for better section division
            system_prompt = f"""Create a detailed table of contents for this content.
            
            Instructions:
            1. Identify 3-7 major topics or natural break points
            2. Each chapter should represent a coherent section of content
            3. Make chapter titles clear and descriptive
            4. Ensure chapters are evenly distributed
            5. Look for natural topic transitions, not arbitrary divisions
            6. Avoid creating sections that would break the flow of a step-by-step guide
            
            Format your response as JSON with this structure:
            {{
                "chapters": [
                    {{"start_paragraph_number": 0, "title": "Introduction"}},
                    {{"start_paragraph_number": N, "title": "Chapter Title"}},
                    ...
                ]
            }}

            Rules:
            - start_paragraph_number must be between 0 and {total_paragraphs-1}
            - Chapters must be in chronological order
            - Chapter titles should be descriptive and relevant
            - Each chapter should cover a distinct topic or theme
            - The first chapter should always start at paragraph 0
            - Do not create too many small sections - aim for 3-5 substantive sections
            """

            # Rest of the method remains the same...

            response = await self.client.chat.completions.create(
                model=settings.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Extract and process the response
            toc_content = response.choices[0].message.content
            try:
                import json
                toc_data = json.loads(toc_content)
            except json.JSONDecodeError:
                logger.error("Failed to parse TOC JSON response")
                return (
                    [{"start_paragraph_number": 0, "title": "Complete Content"}],
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    self.calculate_price(
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens
                    )
                )
            
            # Validate chapter data
            valid_chapters = []
            last_valid_point = -1
            
            for chapter in toc_data.get("chapters", []):
                start_point = chapter.get("start_paragraph_number")
                title = chapter.get("title", "").strip()
                
                if not title:
                    continue
                    
                if (start_point is None or 
                    start_point >= total_paragraphs or 
                    start_point <= last_valid_point):
                    logger.warning(f"Skipping invalid TOC entry: {chapter}")
                    continue
                
                valid_chapters.append({
                    "start_paragraph_number": start_point,
                    "title": title
                })
                last_valid_point = start_point

            # Ensure we have at least one chapter
            if not valid_chapters:
                valid_chapters = [{
                    "start_paragraph_number": 0,
                    "title": "Complete Content"
                }]

            return (
                valid_chapters,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                self.calculate_price(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens
                )
            )
            
        except Exception as e:
            logger.error(f"Error generating TOC: {str(e)}")
            return (
                [{"start_paragraph_number": 0, "title": "Complete Content"}],
                0, 0, 0
            )