#!/usr/bin/env python3
"""
Debug script to test the summary generation pipeline
"""
import asyncio
import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flashcards.llm.client import LMStudioClient
from flashcards.llm.summarize import SummaryGenerator
from flashcards.pipeline import FlashcardPipeline
from flashcards.schemas import SourceType

async def test_summary_generation():
    print("🔍 Testing Summary Generation Pipeline")
    print("=" * 50)
    
    # Test 1: LM Studio Connection
    print("\n1️⃣ Testing LM Studio Connection...")
    try:
        client = LMStudioClient()
        models_info = await client.list_models()
        models = [model.id for model in models_info]
        print(f"✅ Found {len(models)} available models:")
        for model in models[:5]:  # Show first 5
            print(f"   - {model}")
        
        if 'qwen/qwen3-30b-a3b-2507' in models:
            print("✅ Target model 'qwen/qwen3-30b-a3b-2507' is available!")
        else:
            print("❌ Target model 'qwen/qwen3-30b-a3b-2507' NOT found!")
            print("Available models containing 'qwen':")
            qwen_models = [m for m in models if 'qwen' in m.lower()]
            for model in qwen_models:
                print(f"   - {model}")
    except Exception as e:
        print(f"❌ LM Studio connection failed: {e}")
        traceback.print_exc()
        return
    
    # Test 2: Document Loading
    print("\n2️⃣ Testing Document Loading...")
    try:
        pipeline = FlashcardPipeline()
        # Use the sample document if it exists
        sample_path = Path("data/samples/python_basics.md")
        if sample_path.exists():
            print(f"📄 Loading sample document: {sample_path}")
            source = pipeline.load_source(str(sample_path), SourceType.MARKDOWN)
            print(f"✅ Document loaded: {len(source.content)} characters")
            print(f"   Title: {source.title}")
            print(f"   Content preview: {source.content[:200]}...")
        else:
            print("❌ Sample document not found")
            return
    except Exception as e:
        print(f"❌ Document loading failed: {e}")
        traceback.print_exc()
        return
    
    # Test 3: Text Processing (Chunking)
    print("\n3️⃣ Testing Text Processing...")
    try:
        chunks = pipeline.process_text(source)
        print(f"✅ Created {len(chunks)} chunks")
        if chunks:
            print(f"   First chunk preview: {chunks[0].content[:200]}...")
            print(f"   Chunk word count: {len(chunks[0].content.split())} words")
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
        traceback.print_exc()
        return
    
    # Test 4: Summary Generation
    print("\n4️⃣ Testing Summary Generation...")
    try:
        summary_generator = SummaryGenerator()
        
        # Test with just the first chunk
        test_chunk = chunks[0] if chunks else None
        if test_chunk:
            print(f"🧪 Testing with first chunk ({len(test_chunk.content.split())} words)")
            
            # Generate summary for single chunk
            chunk_summaries = await summary_generator.generate_summaries_from_chunks([test_chunk])
            
            if chunk_summaries and chunk_summaries[0]:
                summary = chunk_summaries[0]
                print(f"✅ Summary generated!")
                print(f"   Length: {len(summary)} characters")
                print(f"   Word count: {len(summary.split())} words")
                print(f"   Preview: {summary[:300]}...")
            else:
                print("❌ No summary generated from chunk")
                print(f"   Chunk summaries result: {chunk_summaries}")
        else:
            print("❌ No chunks available for testing")
    except Exception as e:
        print(f"❌ Summary generation failed: {e}")
        traceback.print_exc()
        return
    
    # Test 5: Direct LM Studio API Test
    print("\n5️⃣ Testing Direct LM Studio API...")
    try:
        client = LMStudioClient(model_name='qwen/qwen3-30b-a3b-2507')
        
        test_prompt = """Summarize this text in about 50 words:
        
Python is a high-level, interpreted programming language with dynamic semantics. Its high-level built-in data structures, combined with dynamic typing and dynamic binding, make it very attractive for Rapid Application Development, as well as for use as a scripting or glue language to connect existing components together."""
        
        print("🧪 Sending test prompt to LM Studio...")
        response = await client.generate_completion(test_prompt)
        
        if response and response.strip():
            print(f"✅ Direct API test successful!")
            print(f"   Response length: {len(response)} characters")
            print(f"   Response: {response}")
        else:
            print(f"❌ Direct API test failed - empty response")
            print(f"   Raw response: {repr(response)}")
            
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_summary_generation())
