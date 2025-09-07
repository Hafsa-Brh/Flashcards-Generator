#!/usr/bin/env python3
"""
End-to-end test for the complete flashcard generation pipeline.

This script tests:
1. Document loading
2. Text cleaning and chunking  
3. LLM-based flashcard generation
4. Card validation
5. JSON export
"""

import sys
import asyncio
from pathlib import Path
import logging
import json

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flashcards.ingest.loader import DocumentLoader
from flashcards.preprocess.cleaner import TextCleaner
from flashcards.preprocess.chunker import TextChunker
from flashcards.llm.generate import FlashcardGenerator
from flashcards.llm.client import LMStudioClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_llm_connection():
    """Test the LM Studio connection."""
    print("🔗 Testing LM Studio Connection")
    print("=" * 50)
    
    try:
        client = LMStudioClient()
        
        # Test connection
        models = await client.list_models()
        if not models:
            print("❌ No models available")
            return False
        
        print(f"✅ Connection successful! Available models:")
        for model in models[:3]:  # Show first 3 models
            print(f"   - {model.id}")
        
        # Test a simple chat completion
        from flashcards.llm.client import ChatMessage
        test_message = ChatMessage(role="user", content="Say 'Hello, I'm working!' in exactly those words.")
        
        print(f"\n🧪 Testing chat completion...")
        response = await client.chat_completion([test_message], max_tokens=50)
        
        if response and response.content:
            print(f"✅ Chat completion successful!")
            print(f"   Response: {response.content}")
            return True
        else:
            print("❌ Empty response from chat completion")
            return False
            
    except Exception as e:
        print(f"❌ LM Studio connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_flashcard_generation():
    """Test flashcard generation from a simple text."""
    print("\n🎯 Testing Flashcard Generation")
    print("=" * 50)
    
    # Simple test text
    test_text = """
    Python is a high-level programming language. It was created by Guido van Rossum and first released in 1991. 
    Python emphasizes code readability and uses significant whitespace. It supports multiple programming paradigms 
    including procedural, object-oriented, and functional programming.
    
    Variables in Python are created when you assign a value to them. Python has several built-in data types 
    including integers, floats, strings, and booleans. Lists are ordered collections that can contain different 
    data types and are mutable, meaning they can be changed after creation.
    """
    
    try:
        # Initialize components
        cleaner = TextCleaner()
        chunker = TextChunker()
        generator = FlashcardGenerator()
        
        # Process text
        print("📝 Processing test text...")
        cleaned_text, stats = cleaner.clean_text(test_text)
        print(f"   - Cleaned text: {len(cleaned_text)} chars")
        
        # Create a mock chunk (since we don't have a full Source object)
        from flashcards.schemas import Chunk
        from uuid import uuid4
        
        chunk = Chunk(
            source_id=uuid4(),
            text=cleaned_text,
            token_count=int(len(cleaned_text.split()) * 1.3),  # Convert to int
            word_count=len(cleaned_text.split()),
            index=0,
            start_char=0,
            end_char=len(cleaned_text)
        )
        
        print(f"📦 Created test chunk: {chunk.word_count} words, ~{int(chunk.token_count)} tokens")
        
        # Generate flashcards
        print("🤖 Generating flashcards with LLM...")
        cards = await generator.generate_cards_from_chunk(chunk)
        
        if not cards:
            print("❌ No flashcards generated")
            return False
        
        print(f"✅ Generated {len(cards)} flashcards!")
        print("\n📚 Generated Flashcards:")
        
        for i, card in enumerate(cards, 1):
            print(f"\n   Card {i}:")
            print(f"   Q: {card.front}")
            print(f"   A: {card.back}")
            print(f"   Difficulty: {card.difficulty}")
        
        # Validate cards
        print(f"\n🔍 Validating flashcards...")
        valid_cards = generator.validate_cards(cards)
        print(f"✅ Validation complete: {len(valid_cards)}/{len(cards)} cards passed")
        
        return len(valid_cards) > 0
        
    except Exception as e:
        print(f"❌ Flashcard generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_pipeline():
    """Test the complete pipeline with a real document."""
    print("\n🚀 Testing Complete Pipeline")
    print("=" * 50)
    
    try:
        # Initialize all components
        loader = DocumentLoader()
        cleaner = TextCleaner()
        chunker = TextChunker()
        generator = FlashcardGenerator()
        
        # Load test document
        test_file = Path("test_document.md")
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"📖 Loading document: {test_file}")
        source = loader.load_document(test_file)
        print(f"✅ Document loaded: {source.title} ({len(source.content)} chars)")
        
        # Clean text
        print("🧹 Cleaning text...")
        cleaned_text, cleaning_stats = cleaner.clean_text(source.content)
        print(f"✅ Text cleaned: {cleaning_stats.cleaned_length} chars")
        
        # Chunk text
        print("✂️ Chunking text...")
        chunks = chunker.chunk_text(cleaned_text, source.id)
        print(f"✅ Text chunked: {len(chunks)} chunks created")
        
        # Generate flashcards (limit to first 2 chunks for testing)
        test_chunks = chunks[:2] if len(chunks) > 2 else chunks
        print(f"🤖 Generating flashcards from {len(test_chunks)} chunks...")
        
        all_cards = []
        for i, chunk in enumerate(test_chunks):
            print(f"   Processing chunk {i+1}/{len(test_chunks)}...")
            cards = await generator.generate_cards_from_chunk(chunk)
            all_cards.extend(cards)
            
            # Show progress
            if cards:
                print(f"   ✅ Generated {len(cards)} cards from chunk {i+1}")
            else:
                print(f"   ⚠️ No cards generated from chunk {i+1}")
        
        if not all_cards:
            print("❌ No flashcards generated from any chunks")
            return False
        
        print(f"\n✅ Total flashcards generated: {len(all_cards)}")
        
        # Validate all cards
        print("🔍 Validating all flashcards...")
        valid_cards = generator.validate_cards(all_cards)
        print(f"✅ Final validation: {len(valid_cards)} valid flashcards")
        
        # Show sample results
        print(f"\n📚 Sample Flashcards (showing first 3):")
        for i, card in enumerate(valid_cards[:3], 1):
            print(f"\n   Card {i}:")
            print(f"   Q: {card.front}")
            print(f"   A: {card.back}")
            print(f"   Difficulty: {card.difficulty}")
            print(f"   Source chunk: {card.chunk_id}")
        
        if len(valid_cards) > 3:
            print(f"   ... and {len(valid_cards) - 3} more cards")
        
        # Export to JSON
        print(f"\n💾 Exporting to JSON...")
        output_file = Path("data/output/output_flashcards.json")
        
        # Convert cards to JSON-serializable format
        cards_data = {
            "source_document": source.title,
            "total_cards": len(valid_cards),
            "generation_stats": {
                "chunks_processed": len(test_chunks),
                "cards_generated": len(all_cards),
                "cards_valid": len(valid_cards),
                "validation_pass_rate": f"{len(valid_cards)/len(all_cards)*100:.1f}%" if all_cards else "0%"
            },
            "flashcards": []
        }
        
        for card in valid_cards:
            cards_data["flashcards"].append({
                "id": str(card.id),
                "question": card.front,
                "answer": card.back,
                "difficulty": card.difficulty,
                "card_type": card.card_type.value,
                "tags": card.tags,
                "metadata": card.metadata
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cards_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Flashcards exported to: {output_file}")
        
        return len(valid_cards) > 0
        
    except Exception as e:
        print(f"❌ Complete pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🧪 Flashcard Generation Pipeline - End-to-End Test")
    print("=" * 70)
    
    # Test LM Studio connection first
    llm_ok = await test_llm_connection()
    
    if not llm_ok:
        print("\n❌ LM Studio connection failed - cannot proceed with generation tests")
        print("Please ensure LM Studio is running and accessible at the configured URL")
        sys.exit(1)
    
    # Test simple flashcard generation
    generation_ok = await test_flashcard_generation()
    
    if not generation_ok:
        print("\n❌ Basic flashcard generation failed")
        sys.exit(1)
    
    # Test complete pipeline
    pipeline_ok = await test_complete_pipeline()
    
    # Final results
    print("\n" + "=" * 70)
    if pipeline_ok:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("\nThe complete flashcard generation pipeline is working!")
        print("✅ Document loading")
        print("✅ Text processing") 
        print("✅ LLM integration")
        print("✅ Flashcard generation")
        print("✅ Validation and export")
        print(f"\nCheck 'data/output/output_flashcards.json' for the generated flashcards.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
