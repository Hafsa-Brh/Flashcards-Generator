"""
Complete flashcard generation pipeline.

This module orchestrates the entire process from document loading
to flashcard generation, integrating all components.
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from .schemas import Source, SourceType, Deck, Card, ProcessingStats
from .ingest.loader import DocumentLoader
from .preprocess.cleaner import TextCleaner
from .preprocess.chunker import TextChunker
from .llm.generate import FlashcardGenerator

logger = logging.getLogger(__name__)


class FlashcardPipeline:
    """Complete pipeline for generating flashcards from documents."""
    
    def __init__(self):
        """Initialize the pipeline with all components."""
        self.loader = DocumentLoader()
        self.cleaner = TextCleaner()
        self.chunker = TextChunker()
        self.generator = FlashcardGenerator()
        
    def load_source(self, file_path: str, source_type: SourceType) -> Source:
        """Load a document and return a Source object."""
        # Convert string path to Path object
        path = Path(file_path)
        
        # Load the document
        source = self.loader.load_document(path, source_type)
        
        logger.info(f"Successfully loaded source: {source.title} ({len(source.content)} chars)")
        return source
        
    def process_text(self, source: Source) -> List:
        """Process text through cleaning and chunking pipeline."""
        # Clean the text
        cleaned_content, cleaning_stats = self.cleaner.clean_text(source.content)
        
        # Update source with cleaned content
        source.content = cleaned_content
        
        # Chunk the text
        chunks = self.chunker.chunk_text(source.content, source_id=source.id)
        
        logger.info(f"Text processing complete: {len(chunks)} chunks created")
        return chunks
        
    def generate_flashcards(self, source: Source) -> Deck:
        """Generate flashcards from a source document."""
        try:
            # Process the text
            chunks = self.process_text(source)
            
            # Generate flashcards from chunks
            all_cards = []
            stats = ProcessingStats()
            stats.chunks_created = len(chunks)
            
            for chunk in chunks:
                try:
                    # Use asyncio.run for better event loop management
                    cards = asyncio.run(self.generator.generate_cards_from_chunk(chunk))
                    
                    all_cards.extend(cards)
                    stats.cards_generated += len(cards)
                    
                except Exception as e:
                    logger.error(f"Failed to generate cards from chunk {chunk.id}: {e}")
                    stats.add_error(f"Chunk {chunk.id}: {str(e)}")
                    continue
            
            # Create deck
            deck = Deck(
                id=uuid4(),
                name=f"Flashcards from {source.title}",
                description=f"Generated from {source.source_type.value} document: {source.title}",
                source_ids=[source.id],
                cards=all_cards
            )
            
            logger.info(f"Pipeline complete: Generated {len(all_cards)} flashcards from {source.title}")
            return deck
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
            
    async def generate_flashcards_async(self, source: Source) -> Deck:
        """Async version of flashcard generation."""
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.generate_flashcards, 
            source
        )
