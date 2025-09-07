#!/usr/bin/env python3
"""
Test script for the text processing pipeline.

This script tests the complete flow:
1. Document loading (various formats)
2. Text cleaning 
3. Text chunking
"""

import sys
from pathlib import Path
import logging

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flashcards.ingest.loader import DocumentLoader
from flashcards.preprocess.cleaner import TextCleaner
from flashcards.preprocess.chunker import TextChunker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_pipeline():
    """Test the complete text processing pipeline."""
    
    print("🧪 Testing Text Processing Pipeline")
    print("=" * 50)
    
    # Initialize components
    loader = DocumentLoader()
    cleaner = TextCleaner()
    chunker = TextChunker()
    
    # Test document path
    test_file = Path("test_document.md")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Step 1: Load document
        print(f"📖 Loading document: {test_file}")
        source = loader.load_document(test_file)
        print(f"✅ Document loaded successfully")
        print(f"   - Title: {source.title}")
        print(f"   - Type: {source.source_type}")
        print(f"   - Character count: {len(source.content)}")
        print(f"   - Word count: {source.metadata.get('word_count', 'N/A')}")
        print()
        
        # Step 2: Clean text
        print("🧹 Cleaning text...")
        cleaned_text, cleaning_stats = cleaner.clean_text(source.content)
        print(f"✅ Text cleaned successfully")
        print(f"   - Original length: {len(source.content)} chars")
        print(f"   - Cleaned length: {len(cleaned_text)} chars")
        print(f"   - Reduction: {len(source.content) - len(cleaned_text)} chars")
        print(f"   - URLs removed: {cleaning_stats.urls_removed}")
        print(f"   - Emails removed: {cleaning_stats.emails_removed}")
        print(f"   - Lines removed: {cleaning_stats.lines_removed}")
        print()
        
        # Step 3: Chunk text
        print("✂️ Chunking text...")
        chunks = chunker.chunk_text(cleaned_text, source.id)
        print(f"✅ Text chunked successfully")
        print(f"   - Number of chunks: {len(chunks)}")
        print(f"   - Average chunk size: {sum(len(chunk.text) for chunk in chunks) / len(chunks):.0f} chars")
        print()
        
        # Display chunk details
        print("📋 Chunk Details:")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"   Chunk {i+1}:")
            print(f"   - Length: {len(chunk.text)} chars")
            print(f"   - Token estimate: {chunk.token_count}")
            print(f"   - Preview: {chunk.text[:100]}...")
            print()
        
        if len(chunks) > 3:
            print(f"   ... and {len(chunks) - 3} more chunks")
            print()
        
        print("🎉 Pipeline test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_formats():
    """Test loading different file formats."""
    
    print("\n📂 Testing File Format Support")
    print("=" * 50)
    
    loader = DocumentLoader()
    
    # Test markdown file
    test_file = Path("test_document.md")
    if test_file.exists():
        try:
            source = loader.load_document(test_file)
            print(f"✅ Markdown: {test_file} loaded successfully ({len(source.content)} chars)")
        except Exception as e:
            print(f"❌ Markdown: Failed to load {test_file}: {e}")
    
    # Test sample files in data/samples if they exist
    samples_dir = Path("data/samples")
    if samples_dir.exists():
        for sample_file in samples_dir.iterdir():
            if sample_file.is_file():
                try:
                    source = loader.load_document(sample_file)
                    print(f"✅ {sample_file.suffix.upper()}: {sample_file.name} loaded successfully ({len(source.content)} chars)")
                except Exception as e:
                    print(f"❌ {sample_file.suffix.upper()}: Failed to load {sample_file.name}: {e}")


if __name__ == "__main__":
    print("🚀 Flashcards Text Processing Pipeline Test")
    print("=" * 60)
    
    success = test_pipeline()
    test_file_formats()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("The text processing pipeline is ready for integration.")
    else:
        print("\n❌ Some tests failed!")
        print("Please check the errors above.")
        sys.exit(1)
