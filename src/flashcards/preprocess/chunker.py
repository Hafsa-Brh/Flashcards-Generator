"""
Text chunking utilities for optimal AI processing.

This module handles splitting text into chunks suitable for LLM processing:
- Word-based chunking with sentence boundary awareness
- Configurable chunk sizes and overlap
- Token counting for precise chunk sizing
- Context preservation between chunks
"""

import re
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from uuid import UUID

import tiktoken

from ..schemas import Chunk, Source
from ..config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class ChunkingStats:
    """Statistics from the chunking process."""
    total_chunks: int
    avg_chunk_size: float
    min_chunk_size: int
    max_chunk_size: int
    total_tokens: int
    avg_tokens_per_chunk: float
    overlap_efficiency: float  # Percentage of text that's not duplicated


class TextChunker:
    """Handles intelligent text chunking for AI processing."""
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        
        # Initialize tokenizer for accurate token counting
        try:
            # Use cl100k_base encoding (GPT-3.5/4 tokenizer) as it's widely compatible
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Could not load tiktoken tokenizer: {e}")
            self.tokenizer = None
        
        # Compile sentence boundary patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for sentence detection."""
        
        # Sentence ending pattern (handles common cases)
        self.sentence_end_pattern = re.compile(
            r'[.!?]+\s+(?=[A-Z]|"[A-Z]|\'[A-Z])',  # Sentence endings followed by capital
            re.MULTILINE
        )
        
        # Paragraph boundary pattern
        self.paragraph_pattern = re.compile(r'\n\s*\n')
        
        # List item pattern
        self.list_pattern = re.compile(r'^\s*[•\-\*\d+\.]\s+', re.MULTILINE)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.debug(f"Tokenizer error, falling back to word count: {e}")
        
        # Fallback: estimate tokens as roughly 0.75 * word count
        word_count = len(text.split())
        return int(word_count * 0.75)
    
    def count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def find_sentence_boundaries(self, text: str) -> List[int]:
        """Find positions of sentence boundaries in text."""
        boundaries = [0]  # Start of text
        
        # Find sentence endings
        for match in self.sentence_end_pattern.finditer(text):
            end_pos = match.end()
            if end_pos < len(text):  # Don't add if it's the very end
                boundaries.append(end_pos)
        
        # Add end of text
        if boundaries[-1] != len(text):
            boundaries.append(len(text))
        
        return boundaries
    
    def find_paragraph_boundaries(self, text: str) -> List[int]:
        """Find positions of paragraph boundaries in text."""
        boundaries = [0]
        
        for match in self.paragraph_pattern.finditer(text):
            end_pos = match.end()
            if end_pos < len(text):
                boundaries.append(end_pos)
        
        if boundaries[-1] != len(text):
            boundaries.append(len(text))
            
        return boundaries
    
    def split_by_sentences(self, text: str, max_words: int) -> List[str]:
        """Split text by sentences, respecting word limits."""
        sentences = self.sentence_end_pattern.split(text)
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_words = len(sentence.split())
            
            # If adding this sentence would exceed the limit, save current chunk
            if current_chunk and current_word_count + sentence_words > max_words:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_word_count = sentence_words
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def split_by_paragraphs(self, text: str, max_words: int) -> List[str]:
        """Split text by paragraphs, respecting word limits."""
        paragraphs = self.paragraph_pattern.split(text)
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            paragraph_words = len(paragraph.split())
            
            # If paragraph is too long, split it further
            if paragraph_words > max_words:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_word_count = 0
                
                # Split long paragraph by sentences
                sub_chunks = self.split_by_sentences(paragraph, max_words)
                chunks.extend(sub_chunks)
                
            elif current_word_count + paragraph_words > max_words:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_word_count = paragraph_words
            else:
                current_chunk.append(paragraph)
                current_word_count += paragraph_words
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def add_overlap(self, chunks: List[str], overlap_words: int) -> List[str]:
        """Add overlap between consecutive chunks."""
        if overlap_words <= 0 or len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]  # First chunk unchanged
        
        for i in range(1, len(chunks)):
            previous_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Get last N words from previous chunk
            prev_words = previous_chunk.split()
            if len(prev_words) > overlap_words:
                overlap_text = ' '.join(prev_words[-overlap_words:])
                overlapped_chunk = overlap_text + ' ' + current_chunk
            else:
                # If previous chunk is shorter than overlap, use it all
                overlapped_chunk = previous_chunk + ' ' + current_chunk
            
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def chunk_text(
        self,
        text: str,
        source_id: Optional[UUID] = None,
        method: str = "paragraph"  # "paragraph", "sentence", or "word"
    ) -> List[Chunk]:
        """
        Chunk text into optimal pieces for AI processing.
        
        Args:
            text: Text to chunk
            source_id: UUID of the source document
            method: Chunking method ("paragraph", "sentence", or "word")
            
        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        max_words = self.settings.text_processing.max_chunk_size
        min_words = self.settings.text_processing.min_chunk_size
        overlap_words = self.settings.text_processing.chunk_overlap
        
        logger.info(f"Chunking text with method='{method}', max_words={max_words}, "
                   f"overlap={overlap_words}")
        
        # Choose chunking method
        if method == "paragraph":
            raw_chunks = self.split_by_paragraphs(text, max_words)
        elif method == "sentence":
            raw_chunks = self.split_by_sentences(text, max_words)
        else:  # word-based chunking
            raw_chunks = self._split_by_words(text, max_words)
        
        # Add overlap between chunks
        if overlap_words > 0:
            raw_chunks = self.add_overlap(raw_chunks, overlap_words)
        
        # Filter out chunks that are too small
        filtered_chunks = [
            chunk for chunk in raw_chunks 
            if len(chunk.split()) >= min_words
        ]
        
        # Create Chunk objects
        chunks = []
        char_position = 0
        
        for i, chunk_text in enumerate(filtered_chunks):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue
            
            # Find the position of this chunk in the original text
            start_pos = text.find(chunk_text[:50], char_position)  # Use first 50 chars for search
            if start_pos == -1:
                start_pos = char_position
            
            end_pos = start_pos + len(chunk_text)
            char_position = end_pos
            
            chunk = Chunk(
                source_id=source_id,
                text=chunk_text,
                token_count=self.count_tokens(chunk_text),
                word_count=self.count_words(chunk_text),
                index=i,
                start_char=start_pos,
                end_char=end_pos,
                metadata={
                    "chunking_method": method,
                    "overlap_words": overlap_words,
                }
            )
            
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def _split_by_words(self, text: str, max_words: int) -> List[str]:
        """Simple word-based splitting (fallback method)."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_words):
            chunk_words = words[i:i + max_words]
            chunks.append(' '.join(chunk_words))
        
        return chunks
    
    def chunk_source(self, source: Source, method: str = "paragraph") -> List[Chunk]:
        """Chunk a Source document."""
        if not source.content:
            logger.warning(f"Source {source.title} has no content to chunk")
            return []
        
        return self.chunk_text(source.content, source.id, method)
    
    def get_chunking_stats(self, chunks: List[Chunk]) -> ChunkingStats:
        """Calculate statistics for a list of chunks."""
        if not chunks:
            return ChunkingStats(0, 0, 0, 0, 0, 0, 0)
        
        word_counts = [chunk.word_count for chunk in chunks]
        token_counts = [chunk.token_count for chunk in chunks]
        
        # Calculate overlap efficiency (rough estimate)
        total_words = sum(word_counts)
        unique_text_estimate = total_words * 0.85  # Assume ~15% overlap
        overlap_efficiency = (unique_text_estimate / total_words) * 100 if total_words > 0 else 0
        
        return ChunkingStats(
            total_chunks=len(chunks),
            avg_chunk_size=sum(word_counts) / len(word_counts),
            min_chunk_size=min(word_counts),
            max_chunk_size=max(word_counts),
            total_tokens=sum(token_counts),
            avg_tokens_per_chunk=sum(token_counts) / len(token_counts),
            overlap_efficiency=overlap_efficiency
        )
    
    def optimize_chunks_for_model(self, chunks: List[Chunk], target_tokens: int = 400) -> List[Chunk]:
        """Optimize chunks for a specific token target."""
        optimized_chunks = []
        
        for chunk in chunks:
            if chunk.token_count <= target_tokens:
                optimized_chunks.append(chunk)
            else:
                # Split large chunks
                sub_chunks = self._split_large_chunk(chunk, target_tokens)
                optimized_chunks.extend(sub_chunks)
        
        return optimized_chunks
    
    def _split_large_chunk(self, chunk: Chunk, target_tokens: int) -> List[Chunk]:
        """Split a large chunk into smaller pieces."""
        # Simple splitting - could be made more sophisticated
        words = chunk.text.split()
        estimated_words_per_target = int(target_tokens * 1.3)  # Rough estimate
        
        sub_chunks = []
        for i in range(0, len(words), estimated_words_per_target):
            sub_words = words[i:i + estimated_words_per_target]
            sub_text = ' '.join(sub_words)
            
            sub_chunk = Chunk(
                source_id=chunk.source_id,
                text=sub_text,
                token_count=self.count_tokens(sub_text),
                word_count=len(sub_words),
                index=len(sub_chunks),  # Sub-chunk index
                start_char=chunk.start_char + len(' '.join(words[:i])),
                end_char=chunk.start_char + len(' '.join(words[:i + len(sub_words)])),
                metadata={
                    **chunk.metadata,
                    "parent_chunk_id": str(chunk.id),
                    "is_split_chunk": True,
                }
            )
            sub_chunks.append(sub_chunk)
        
        return sub_chunks


# Convenience functions
def chunk_text(text: str, source_id: Optional[UUID] = None, method: str = "paragraph") -> List[Chunk]:
    """Chunk text using default settings."""
    chunker = TextChunker()
    return chunker.chunk_text(text, source_id, method)


def chunk_source(source: Source, method: str = "paragraph") -> List[Chunk]:
    """Chunk a source document."""
    chunker = TextChunker()
    return chunker.chunk_source(source, method)
