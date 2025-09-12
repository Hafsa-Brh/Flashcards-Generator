"""
LLM-based summary generation module.

This module handles the generation of summaries from text chunks using
the configured LLM (LM Studio).
"""

import logging
import asyncio
import re
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..schemas import Chunk, ProcessingStats
from ..llm.client import LMStudioClient, ChatMessage
from ..config import get_settings

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generates summaries from text chunks using LLM."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = LMStudioClient()
        
        # Load generation prompt template
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """Load the summary generation prompt template."""
        try:
            from pathlib import Path
            prompt_file = Path(__file__).parent.parent / "prompts" / "summary_generation.md"
            
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"Prompt file not found: {prompt_file}, using default template")
                return self._get_default_prompt_template()
                
        except Exception as e:
            logger.warning(f"Error loading prompt template: {e}, using default")
            return self._get_default_prompt_template()
    
    def _get_default_prompt_template(self) -> str:
        """Get the default prompt template."""
        return """You are an expert text summarizer. Analyze the following text and create a concise, informative summary that captures the key information and main points.

Text to summarize:
{text}

Please provide a clear, concise summary of this text chunk."""
    
    async def generate_summary_from_chunk(self, chunk: Chunk) -> Optional[str]:
        """
        Generate a summary from a single text chunk.
        
        Args:
            chunk: Text chunk to summarize
            
        Returns:
            Optional[str]: Generated summary or None if generation failed
        """
        try:
            # Prepare the prompt
            prompt = self.prompt_template.format(
                text=chunk.text,
                chunk_id=str(chunk.id)
            )
            
            # Create chat message
            messages = [ChatMessage(role="user", content=prompt)]
            
            # Generate summary
            logger.info(f"Generating summary for chunk {chunk.id}")
            response = await self.client.chat_completion(
                messages=messages,
                max_tokens=self.settings.lm_studio.max_tokens,
                temperature=self.settings.lm_studio.temperature
            )
            
            # Extract content from response object
            if response:
                summary_content = response.content if hasattr(response, 'content') else str(response)
                if summary_content and summary_content.strip():
                    summary = summary_content.strip()
                    logger.info(f"Generated summary for chunk {chunk.id}: {len(summary)} characters")
                    return summary
            
            logger.warning(f"Empty response for chunk {chunk.id}")
            return None
                
        except Exception as e:
            logger.error(f"Error generating summary for chunk {chunk.id}: {e}")
            return None
    
    async def generate_summaries_from_chunks(self, chunks: List[Chunk]) -> List[str]:
        """
        Generate summaries from multiple chunks.
        
        Args:
            chunks: List of text chunks to summarize
            
        Returns:
            List[str]: List of generated summaries (may contain empty strings for failed generations)
        """
        if not chunks:
            logger.warning("No chunks provided for summary generation")
            return []
        
        logger.info(f"Starting summary generation for {len(chunks)} chunks")
        
        # Process chunks in batches to avoid overwhelming the LLM
        batch_size = min(5, len(chunks))  # Process max 5 chunks at once
        summaries = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            logger.info(f"Processing summary batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            
            # Generate summaries for this batch
            batch_tasks = [self.generate_summary_from_chunk(chunk) for chunk in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process batch results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Exception in batch processing: {result}")
                    summaries.append("")  # Add empty summary for failed generation
                elif result is None:
                    summaries.append("")  # Add empty summary for failed generation
                else:
                    summaries.append(result)
            
            # Small delay between batches to be respectful to the LLM service
            if i + batch_size < len(chunks):
                await asyncio.sleep(1)
        
        successful_summaries = sum(1 for s in summaries if s.strip())
        logger.info(f"Summary generation complete: {successful_summaries}/{len(chunks)} successful")
        
        return summaries


class SummaryCombiner:
    """
    Combines multiple partial summaries into a final comprehensive summary.
    Adapted from the original doc-summarizer project.
    """
    
    def __init__(self, llm_client: Optional[LMStudioClient] = None):
        """
        Initialize the combiner.
        
        Args:
            llm_client: Optional LLM client for AI-powered combination
        """
        self.llm_client = llm_client or LMStudioClient()
    
    def simple_combine(self, summaries: List[str]) -> str:
        """
        Simple combination by concatenating summaries.
        
        Args:
            summaries: List of individual chunk summaries
            
        Returns:
            str: Combined summary
        """
        if not summaries:
            return "No summaries to combine."
        
        # Filter out empty summaries
        valid_summaries = [s.strip() for s in summaries if s and s.strip()]
        
        if not valid_summaries:
            return "No valid summaries found."
        
        # Simple concatenation with separators
        combined = "\n\n".join(f"• {summary}" for summary in valid_summaries)
        
        return f"Document Summary:\n\n{combined}"
    
    def structured_combine(self, summaries: List[str]) -> str:
        """
        Create a structured combination with sections.
        
        Args:
            summaries: List of individual chunk summaries
            
        Returns:
            str: Structured combined summary
        """
        if not summaries:
            return "No summaries to combine."
        
        valid_summaries = [s.strip() for s in summaries if s and s.strip()]
        
        if not valid_summaries:
            return "No valid summaries found."
        
        # Create structured output
        result = "# Document Summary\n\n"
        result += f"This document has been analyzed in {len(valid_summaries)} sections:\n\n"
        
        for i, summary in enumerate(valid_summaries, 1):
            result += f"## Section {i}\n{summary}\n\n"
        
        return result
    
    async def ai_combine(self, summaries: List[str], target_length: int = 300) -> Optional[str]:
        """
        Use AI to combine summaries into a coherent final summary.
        Handles large documents by combining in hierarchical stages.
        
        Args:
            summaries: List of individual chunk summaries
            target_length: Target word count for final summary
            
        Returns:
            str: AI-generated combined summary, or None if failed
        """
        if not summaries:
            return "No summaries to combine."
        
        valid_summaries = [s.strip() for s in summaries if s and s.strip()]
        
        if not valid_summaries:
            return "No valid summaries found."
        
        # If only one summary, return it
        if len(valid_summaries) == 1:
            return valid_summaries[0]
        
        # Clean up any raw chunk references or formatting issues
        cleaned_summaries = []
        for summary in valid_summaries:
            # Remove chunk ID references and unwanted formatting
            cleaned = summary.replace("### Summary", "").replace("**Chunk ID:**", "")
            cleaned = cleaned.replace("Chunk ID:", "").strip()
            # Remove UUID patterns
            import re
            cleaned = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '', cleaned)
            cleaned = cleaned.strip()
            if cleaned and len(cleaned) > 10:  # Only keep meaningful content
                cleaned_summaries.append(cleaned)
        
        # For large documents (>20 summaries), use hierarchical combination
        if len(cleaned_summaries) > 20:
            logger.info(f"Large document detected ({len(cleaned_summaries)} summaries), using hierarchical combination")
            return await self._hierarchical_combine(cleaned_summaries, target_length)
        
        # For smaller documents, direct combination
        return await self._direct_combine(cleaned_summaries, target_length)
    
    async def _direct_combine(self, summaries: List[str], target_length: int) -> Optional[str]:
        """Direct AI combination for smaller documents."""
        # Detect the language from the summaries to preserve it
        sample_text = " ".join(summaries[:2])  # Use first 2 summaries as language sample
        
        # Prepare prompt for AI combination
        summaries_text = "\n\n".join(f"Section {i+1}: {summary}" 
                                    for i, summary in enumerate(summaries))
        
        prompt = f"""I have {len(summaries)} partial summaries from different sections of a document. Please combine them into ONE coherent, comprehensive final summary of approximately {target_length} words.

CRITICAL: Write the final summary in the SAME LANGUAGE as the partial summaries. Do not translate or change the language.

Your task:
1. Remove redundancy and repetition between sections
2. Maintain all key information and important details
3. Create a flowing, cohesive narrative (not numbered sections)
4. Write in the same language as the source summaries
5. Aim for about {target_length} words

Partial summaries to combine:
{summaries_text}

Combined Final Summary:"""
        
        try:
            messages = [ChatMessage(role="user", content=prompt)]
            combined = await self.llm_client.chat_completion(
                messages=messages,
                max_tokens=target_length * 3,  # Allow more buffer for better combination
                temperature=0.3  # Lower temperature for more focused combination
            )
            # Extract content from response object
            if combined:
                content = combined.content if hasattr(combined, 'content') else str(combined)
                if content and content.strip():
                    # Clean up any unwanted formatting or section headers
                    result = content.strip()
                    # Remove common section markers that might appear
                    result = result.replace("Combined Final Summary:", "").strip()
                    result = result.replace("Final Summary:", "").strip()
                    return result
            return None
        except Exception as e:
            logger.error(f"Error in AI combination: {e}")
            return None
    
    async def _hierarchical_combine(self, summaries: List[str], target_length: int) -> Optional[str]:
        """Hierarchical combination for large documents to avoid context length limits."""
        # Stage 1: Combine in groups of 10 to create intermediate summaries
        intermediate_summaries = []
        group_size = 8  # Smaller groups to stay within context limits
        
        logger.info(f"Stage 1: Creating {(len(summaries) + group_size - 1) // group_size} intermediate summaries")
        
        for i in range(0, len(summaries), group_size):
            group = summaries[i:i + group_size]
            group_text = "\n\n".join(f"Part {j+1}: {summary}" for j, summary in enumerate(group))
            
            intermediate_prompt = f"""Combine these {len(group)} summaries into one cohesive summary. Maintain key information and write in the same language as the source text:

{group_text}

Cohesive Summary:"""
            
            try:
                messages = [ChatMessage(role="user", content=intermediate_prompt)]
                response = await self.llm_client.chat_completion(
                    messages=messages,
                    max_tokens=400,  # Moderate length for intermediate summaries
                    temperature=0.3
                )
                
                if response:
                    content = response.content if hasattr(response, 'content') else str(response)
                    if content and content.strip():
                        intermediate_summaries.append(content.strip())
                
                # Small delay to be respectful to the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error in intermediate combination: {e}")
                # Fallback: just concatenate the group
                intermediate_summaries.append(". ".join(group))
        
        # Stage 2: Combine intermediate summaries into final summary
        if len(intermediate_summaries) == 1:
            return intermediate_summaries[0]
        elif len(intermediate_summaries) <= 5:
            logger.info(f"Stage 2: Combining {len(intermediate_summaries)} intermediate summaries")
            return await self._direct_combine(intermediate_summaries, target_length)
        else:
            # If still too many, do another round
            logger.info(f"Stage 2: Still too many intermediates ({len(intermediate_summaries)}), doing another round")
            return await self._hierarchical_combine(intermediate_summaries, target_length)
    
    async def hybrid_combine(self, summaries: List[str], use_ai: bool = True, target_length: int = 300) -> str:
        """
        Hybrid approach: try AI first, fallback to structured combination.
        
        Args:
            summaries: List of individual chunk summaries
            use_ai: Whether to attempt AI combination first
            target_length: Target length for AI summary
            
        Returns:
            str: Best available combined summary
        """
        if not summaries:
            return "No summaries to combine."
        
        valid_summaries = [s.strip() for s in summaries if s and s.strip()]
        
        if not valid_summaries:
            return "No valid summaries found."
        
        # Try AI combination first if requested and we have multiple summaries
        if use_ai and len(valid_summaries) > 1:
            logger.info(f"Attempting AI combination of {len(valid_summaries)} summaries")
            ai_result = await self.ai_combine(summaries, target_length)
            if ai_result and len(ai_result.strip()) > 30:  # Valid AI result
                logger.info("AI combination successful")
                return ai_result
            else:
                logger.warning("AI combination failed or produced insufficient content")
        
        # If only one summary, return it directly
        if len(valid_summaries) == 1:
            return valid_summaries[0]
        
        # Fallback: simple concatenation without section headers (better than structured)
        logger.info("Using simple combination fallback")
        combined = " ".join(valid_summaries)
        
        # Basic cleanup - remove redundant sentences if any
        sentences = [s.strip() for s in combined.split('.') if s.strip()]
        unique_sentences = []
        for sentence in sentences:
            if sentence and not any(sentence.lower() in existing.lower() for existing in unique_sentences):
                unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences) + ('.' if unique_sentences else '')
    
    def get_combination_stats(self, original_summaries: List[str], combined_summary: str) -> dict:
        """
        Get statistics about the combination process.
        
        Args:
            original_summaries: List of original summaries
            combined_summary: Final combined summary
            
        Returns:
            dict: Combination statistics
        """
        valid_summaries = [s.strip() for s in original_summaries if s and s.strip()]
        
        original_word_count = sum(len(s.split()) for s in valid_summaries)
        combined_word_count = len(combined_summary.split())
        
        compression_ratio = round(combined_word_count / max(original_word_count, 1), 2)
        
        return {
            "original_summaries_count": len(valid_summaries),
            "original_total_words": original_word_count,
            "combined_words": combined_word_count,
            "compression_ratio": compression_ratio,
            "average_original_length": round(original_word_count / max(len(valid_summaries), 1), 2)
        }


def create_summary_generator() -> SummaryGenerator:
    """Create a SummaryGenerator instance."""
    return SummaryGenerator()


def create_summary_combiner(llm_client: Optional[LMStudioClient] = None) -> SummaryCombiner:
    """
    Create a SummaryCombiner instance.
    
    Args:
        llm_client: Optional LLM client for AI-powered combination
        
    Returns:
        SummaryCombiner: Configured combiner instance
    """
    return SummaryCombiner(llm_client=llm_client)
