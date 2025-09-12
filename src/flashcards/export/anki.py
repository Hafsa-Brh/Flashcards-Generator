"""
Anki export functionality using genanki.

This module creates Anki-compatible .apkg files from flashcard data.
"""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional
import random

try:
    import genanki
except ImportError:
    raise ImportError("genanki is required for Anki export. Install with: pip install genanki")

from ..schemas import Card

logger = logging.getLogger(__name__)


class AnkiExporter:
    """Handles export of flashcards to Anki format."""
    
    # Anki note type for basic front/back cards
    BASIC_MODEL = genanki.Model(
        model_id=1607392319,  # Random unique ID
        name="Basic (Flashcards Generator)",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
            {"name": "Tags"},
            {"name": "Source"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": """
                <div class="card">
                    <div class="front">{{Front}}</div>
                    {{#Source}}<div class="source">Source: {{Source}}</div>{{/Source}}
                </div>
                """,
                "afmt": """
                <div class="card">
                    <div class="front">{{Front}}</div>
                    <hr id="answer">
                    <div class="back">{{Back}}</div>
                    {{#Source}}<div class="source">Source: {{Source}}</div>{{/Source}}
                    {{#Tags}}<div class="tags">Tags: {{Tags}}</div>{{/Tags}}
                </div>
                """,
            }
        ],
        css="""
        .card {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 18px;
            text-align: center;
            color: #333;
            background-color: #fff;
            padding: 20px;
            line-height: 1.5;
        }
        
        .front {
            font-weight: 600;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        
        .back {
            margin-top: 15px;
            color: #34495e;
        }
        
        .source {
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 15px;
            font-style: italic;
        }
        
        .tags {
            font-size: 12px;
            color: #95a5a6;
            margin-top: 10px;
        }
        
        hr {
            border: none;
            border-top: 1px solid #ecf0f1;
            margin: 20px 0;
        }
        
        /* Dark mode support */
        .night_mode .card {
            background-color: #2c3e50;
            color: #ecf0f1;
        }
        
        .night_mode .front {
            color: #3498db;
        }
        
        .night_mode .back {
            color: #ecf0f1;
        }
        
        .night_mode hr {
            border-top-color: #34495e;
        }
        """,
    )
    
    def __init__(self, deck_name: str = "Generated Flashcards"):
        """Initialize the Anki exporter.
        
        Args:
            deck_name: Name for the Anki deck
        """
        self.deck_name = deck_name
        # Generate a random deck ID
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        
    def export_cards(self, cards: List[Card], output_path: Optional[Path] = None, 
                    source_name: Optional[str] = None) -> Path:
        """Export flashcards to Anki format.
        
        Args:
            cards: List of Card objects to export
            output_path: Optional path for the output file
            source_name: Optional source document name to include in cards
            
        Returns:
            Path to the generated .apkg file
        """
        if not cards:
            raise ValueError("No cards provided for export")
            
        # Create the deck
        deck = genanki.Deck(self.deck_id, self.deck_name)
        
        # Convert cards to Anki notes
        for card in cards:
            note = self._card_to_note(card, source_name)
            deck.add_note(note)
        
        # Generate output path if not provided
        if output_path is None:
            output_path = Path(tempfile.gettempdir()) / f"{self.deck_name.replace(' ', '_')}.apkg"
        else:
            output_path = Path(output_path)
            
        # Ensure .apkg extension
        if output_path.suffix != '.apkg':
            output_path = output_path.with_suffix('.apkg')
            
        # Create the package
        package = genanki.Package(deck)
        package.write_to_file(str(output_path))
        
        logger.info(f"Exported {len(cards)} cards to {output_path}")
        return output_path
    
    def _card_to_note(self, card: Card, source_name: Optional[str] = None) -> genanki.Note:
        """Convert a Card object to an Anki Note.
        
        Args:
            card: Card object to convert
            source_name: Optional source document name
            
        Returns:
            Anki Note object
        """
        # Prepare tags
        tags = card.tags.copy() if card.tags else []
        if card.difficulty:
            tags.append(f"difficulty:{card.difficulty.value}")
            
        # Prepare fields
        fields = [
            card.front,
            card.back,
            " ".join(tags) if tags else "",
            source_name or "",
        ]
        
        # Create note
        note = genanki.Note(
            model=self.BASIC_MODEL,
            fields=fields,
            tags=tags,
        )
        
        return note
    
    def export_with_media(self, cards: List[Card], media_files: List[Path], 
                         output_path: Optional[Path] = None, 
                         source_name: Optional[str] = None) -> Path:
        """Export flashcards with media files to Anki format.
        
        Args:
            cards: List of Card objects to export
            media_files: List of media file paths to include
            output_path: Optional path for the output file
            source_name: Optional source document name
            
        Returns:
            Path to the generated .apkg file
        """
        if not cards:
            raise ValueError("No cards provided for export")
            
        # Create the deck
        deck = genanki.Deck(self.deck_id, self.deck_name)
        
        # Convert cards to Anki notes
        for card in cards:
            note = self._card_to_note(card, source_name)
            deck.add_note(note)
        
        # Generate output path if not provided
        if output_path is None:
            output_path = Path(tempfile.gettempdir()) / f"{self.deck_name.replace(' ', '_')}.apkg"
        else:
            output_path = Path(output_path)
            
        # Ensure .apkg extension
        if output_path.suffix != '.apkg':
            output_path = output_path.with_suffix('.apkg')
            
        # Create the package with media
        package = genanki.Package(deck)
        package.media_files = [str(f) for f in media_files if f.exists()]
        package.write_to_file(str(output_path))
        
        logger.info(f"Exported {len(cards)} cards with {len(package.media_files)} media files to {output_path}")
        return output_path


def create_anki_export(cards: List[Card], deck_name: str = "Generated Flashcards", 
                      output_path: Optional[Path] = None, 
                      source_name: Optional[str] = None) -> Path:
    """Convenience function to export cards to Anki format.
    
    Args:
        cards: List of Card objects to export
        deck_name: Name for the Anki deck
        output_path: Optional path for the output file
        source_name: Optional source document name
        
    Returns:
        Path to the generated .apkg file
    """
    exporter = AnkiExporter(deck_name)
    return exporter.export_cards(cards, output_path, source_name)
