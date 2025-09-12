"""
Alternative summarization strategies for better handling of large documents.
"""

import logging
import asyncio
from typing import List, Optional
from ..llm.client import LMStudioClient, ChatMessage
from ..schemas import Chunk

logger = logging.getLogger(__name__)


class AdvancedSummarizer:
    """Advanced summarization strategies that avoid the chunk-then-combine problem."""
    
    def __init__(self):
        self.client = LMStudioClient()
    
    async def extract_and_summarize(self, chunks: List[Chunk], target_length: int = 300) -> str:
        """
        Instead of summarizing each chunk then combining, extract key themes 
        first, then create a unified summary around those themes.
        """
        # Step 1: Extract key themes and concepts
        themes = await self._extract_themes(chunks[:10])  # Use first 10 chunks for themes
        
        # Step 2: Create summary around themes using content from all chunks
        summary = await self._create_thematic_summary(chunks, themes, target_length)
        
        return summary or "Unable to generate summary."
    
    async def _extract_themes(self, chunks: List[Chunk]) -> List[str]:
        """Extract main themes and concepts from the document."""
        # Combine first few chunks to get document overview
        combined_text = "\n\n".join([chunk.text for chunk in chunks[:5]])
        
        # Detect language from text
        language_hint = "français" if any(word in combined_text.lower() 
                                        for word in ["le", "la", "les", "de", "des", "et", "à", "un", "une"]) else "English"
        
        prompt = f"""Analyze this document excerpt and identify the main themes, topics, and key concepts. List them as bullet points in {language_hint}.

Document excerpt:
{combined_text[:2000]}  

Main themes and concepts:"""
        
        try:
            messages = [ChatMessage(role="user", content=prompt)]
            response = await self.client.chat_completion(
                messages=messages,
                max_tokens=200,
                temperature=0.2
            )
            
            if response:
                content = response.content if hasattr(response, 'content') else str(response)
                if content:
                    # Extract themes from bullet points
                    themes = [line.strip().lstrip('•-*').strip() 
                             for line in content.split('\n') 
                             if line.strip() and not line.strip().startswith('Main themes')]
                    return themes[:8]  # Limit to 8 main themes
            
        except Exception as e:
            logger.warning(f"Theme extraction failed: {e}")
        
        return ["Main concepts", "Key information", "Important details"]  # Fallback themes
    
    async def _create_thematic_summary(self, chunks: List[Chunk], themes: List[str], target_length: int) -> Optional[str]:
        """Create a summary organized around the identified themes."""
        
        # Sample content from chunks more strategically
        sample_chunks = self._sample_chunks_strategically(chunks, max_chunks=15)
        
        # Combine sampled content
        content_text = "\n\n".join([f"Section: {chunk.text}" for chunk in sample_chunks])
        
        # Detect language
        language_hint = "français" if any(word in content_text.lower() 
                                        for word in ["sécurité", "données", "blockchain", "cryptographie"]) else "English"
        
        themes_text = "\n".join([f"- {theme}" for theme in themes])
        
        prompt = f"""Create a comprehensive summary of approximately {target_length} words based on the following document content. Organize the summary around these main themes:

{themes_text}

CRITICAL: Write the summary in {language_hint} (the same language as the source document).

Document content:
{content_text[:6000]}  

Create a flowing, coherent summary that covers all the main themes without using numbered sections or bullet points. Write naturally in {language_hint}:"""
        
        try:
            messages = [ChatMessage(role="user", content=prompt)]
            response = await self.client.chat_completion(
                messages=messages,
                max_tokens=target_length * 3,
                temperature=0.3
            )
            
            if response:
                content = response.content if hasattr(response, 'content') else str(response)
                if content and content.strip():
                    return content.strip()
                    
        except Exception as e:
            logger.error(f"Thematic summary creation failed: {e}")
        
        return None
    
    def _sample_chunks_strategically(self, chunks: List[Chunk], max_chunks: int = 15) -> List[Chunk]:
        """Sample chunks strategically to get good coverage of the document."""
        if len(chunks) <= max_chunks:
            return chunks
        
        # Take chunks from beginning, middle, and end
        step = len(chunks) // max_chunks
        sampled = []
        
        # Always include first and last chunks
        sampled.append(chunks[0])
        if len(chunks) > 1:
            sampled.append(chunks[-1])
        
        # Sample from the middle
        for i in range(1, len(chunks) - 1, step):
            if len(sampled) < max_chunks:
                sampled.append(chunks[i])
        
        return sampled[:max_chunks]
