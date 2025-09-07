"""
Data schemas for the flashcards application.

This module defines the core data models using Pydantic for validation:
- Source: Represents input documents (PDF, DOCX, TXT, etc.)
- Chunk: Text segments extracted from sources for processing
- Card: Individual flashcards with front/back content
- Deck: Collections of cards for export
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    """Supported input file types."""
    TXT = "txt"
    MARKDOWN = "md"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"


class CardType(str, Enum):
    """Types of flashcards that can be generated."""
    BASIC = "basic"          # Simple Q&A
    CLOZE = "cloze"         # Fill-in-the-blank (future)
    REVERSED = "reversed"    # Bidirectional (future)


class DifficultyLevel(str, Enum):
    """Difficulty levels for cards."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Source(BaseModel):
    """Represents an input document/source file."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    title: str = Field(..., description="Human-readable title")
    file_path: Optional[str] = Field(None, description="Path to source file")
    source_type: SourceType = Field(..., description="Type of source document")
    content: Optional[str] = Field(None, description="Raw text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Path: str
        }


class Chunk(BaseModel):
    """Represents a text chunk extracted from a source for processing."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    source_id: UUID = Field(..., description="ID of the source document")
    text: str = Field(..., description="Text content of the chunk")
    token_count: int = Field(..., ge=0, description="Number of tokens in chunk")
    word_count: int = Field(..., ge=0, description="Number of words in chunk")
    index: int = Field(..., ge=0, description="Position in source document")
    start_char: int = Field(..., ge=0, description="Starting character position")
    end_char: int = Field(..., ge=0, description="Ending character position")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Chunk text cannot be empty')
        return v.strip()
    
    @field_validator('end_char')
    @classmethod
    def end_char_must_be_after_start(cls, v, info):
        if 'start_char' in info.data and v <= info.data['start_char']:
            raise ValueError('end_char must be greater than start_char')
        return v
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Card(BaseModel):
    """Represents a single flashcard."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    front: str = Field(..., description="Question or front side content")
    back: str = Field(..., description="Answer or back side content")
    card_type: CardType = Field(default=CardType.BASIC, description="Type of card")
    tags: List[str] = Field(default_factory=list, description="Category tags")
    source_id: Optional[UUID] = Field(None, description="ID of source document")
    chunk_id: Optional[UUID] = Field(None, description="ID of source chunk")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Estimated difficulty")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence in card quality")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('front')
    @classmethod
    def front_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Card front cannot be empty')
        return v.strip()
    
    @field_validator('back')
    @classmethod
    def back_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Card back cannot be empty')
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def tags_must_be_unique(cls, v):
        # Remove duplicates and empty strings
        unique_tags = list(set(tag.strip().lower() for tag in v if tag.strip()))
        return unique_tags
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the card if it doesn't already exist."""
        clean_tag = tag.strip().lower()
        if clean_tag and clean_tag not in self.tags:
            self.tags.append(clean_tag)
    
    def has_question_format(self) -> bool:
        """Check if the front side looks like a question."""
        return self.front.strip().endswith('?')
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Deck(BaseModel):
    """Represents a collection of flashcards."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., description="Deck name")
    description: Optional[str] = Field(None, description="Deck description")
    cards: List[Card] = Field(default_factory=list, description="List of cards")
    source_ids: List[UUID] = Field(default_factory=list, description="IDs of source documents")
    tags: List[str] = Field(default_factory=list, description="Deck-level tags")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip()
    
    def add_card(self, card: Card) -> None:
        """Add a card to the deck."""
        self.cards.append(card)
        self.updated_at = datetime.now()
        
        # Add source_id to deck if not already present
        if card.source_id and card.source_id not in self.source_ids:
            self.source_ids.append(card.source_id)
    
    def add_cards(self, cards: List[Card]) -> None:
        """Add multiple cards to the deck."""
        for card in cards:
            self.add_card(card)
    
    def get_cards_by_tag(self, tag: str) -> List[Card]:
        """Get all cards that have a specific tag."""
        return [card for card in self.cards if tag.lower() in card.tags]
    
    def get_cards_by_difficulty(self, difficulty: DifficultyLevel) -> List[Card]:
        """Get all cards of a specific difficulty level."""
        return [card for card in self.cards if card.difficulty == difficulty]
    
    def remove_duplicates(self) -> int:
        """Remove duplicate cards based on front and back content."""
        seen = set()
        unique_cards = []
        
        for card in self.cards:
            card_key = (card.front.lower().strip(), card.back.lower().strip())
            if card_key not in seen:
                seen.add(card_key)
                unique_cards.append(card)
        
        removed_count = len(self.cards) - len(unique_cards)
        self.cards = unique_cards
        
        if removed_count > 0:
            self.updated_at = datetime.now()
            
        return removed_count
    
    @property
    def card_count(self) -> int:
        """Get the number of cards in the deck."""
        return len(self.cards)
    
    @property
    def all_tags(self) -> List[str]:
        """Get all unique tags from all cards in the deck."""
        all_tags = set(self.tags)  # Start with deck-level tags
        for card in self.cards:
            all_tags.update(card.tags)
        return sorted(list(all_tags))
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ProcessingStats(BaseModel):
    """Statistics for a processing session."""
    
    sources_processed: int = 0
    chunks_created: int = 0
    cards_generated: int = 0
    cards_filtered: int = 0
    duplicates_removed: int = 0
    processing_time: float = 0.0
    errors: List[str] = Field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message to the stats."""
        self.errors.append(error)
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of card generation."""
        if self.chunks_created == 0:
            return 0.0
        return self.cards_generated / self.chunks_created
