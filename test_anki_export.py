"""
Test the Anki export functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.flashcards.schemas import Card
from src.flashcards.export.anki import create_anki_export

async def test_anki_export():
    """Test creating an Anki deck from sample cards."""
    
    # Create sample cards
    cards = [
        Card(
            front="What is the capital of France?",
            back="Paris is the capital city of France.",
            tags=["geography", "europe", "capitals"]
        ),
        Card(
            front="Qu'est-ce qu'une fonction en mathématiques?",
            back="Une fonction est une relation qui associe à chaque élément d'un ensemble de départ un unique élément d'un ensemble d'arrivée.",
            tags=["mathematics", "functions", "french"]
        ),
        Card(
            front="What is the formula for the area of a circle?",
            back="The area of a circle is π × r², where r is the radius.",
            tags=["mathematics", "geometry", "formulas"]
        )
    ]
    
    try:
        # Export to Anki format
        output_path = create_anki_export(
            cards=cards,
            deck_name="Test Flashcards",
            source_name="Test Document"
        )
        
        print(f"✅ Anki export successful!")
        print(f"📁 File created: {output_path}")
        print(f"📊 Exported {len(cards)} cards")
        
        # Check if file exists and has content
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"📦 File size: {file_size} bytes")
            
            if file_size > 0:
                print("🎉 Export test completed successfully!")
                return True
            else:
                print("❌ File is empty")
                return False
        else:
            print("❌ File was not created")
            return False
            
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_anki_export())
    exit(0 if success else 1)
