#!/usr/bin/env python3
"""
Focused test to identify the exact JSON parsing issue.
"""

import asyncio
import json
import re
from src.flashcards.llm.generate import FlashcardGenerator
from src.flashcards.schemas import Chunk, Source
from uuid import uuid4

async def debug_json_parsing_issue():
    """Debug the exact JSON parsing problem."""
    print("🐛 Debugging JSON Parsing Issue")
    print("=" * 50)
    
    # Create test data exactly like the working example
    source = Source(
        id=uuid4(),
        filename="test.txt",
        title="Test Document",
        content_type="text/plain",
        source_type="txt",
        content="Python is a high-level programming language known for its simplicity."
    )
    
    # Create a chunk similar to what failed in the pipeline
    chunk = Chunk(
        id=uuid4(),
        source_id=source.id,
        index=0,
        text="Test Document for Flashcard Generation This is a sample document to test our flashcard generation pipeline. It contains various concepts and information that should be turned into educational flashcards. The content covers multiple topics including programming concepts, definitions, and practical examples that students might need to learn and remember.",
        word_count=73,
        token_count=105,
        start_char=0,
        end_char=439
    )
    
    print(f"📦 Test chunk ({len(chunk.text)} chars):")
    print(f"   {chunk.text[:100]}...")
    print()
    
    # Initialize generator
    generator = FlashcardGenerator()
    
    try:
        print("🤖 Making LLM call...")
        from src.flashcards.llm.client import ChatMessage
        
        # Create prompt
        prompt = generator._create_generation_prompt(chunk.text, str(chunk.id))
        
        # Call LLM
        response = await generator.client.chat_completion(
            messages=[ChatMessage(role="user", content=prompt)],
            temperature=0.1,
            max_tokens=500
        )
        
        print("✅ LLM responded successfully")
        print(f"📥 Raw response content:")
        print("=" * 30)
        print(response.content)
        print("=" * 30)
        print()
        
        # Try to parse JSON manually
        print("🔍 Analyzing JSON structure...")
        
        # Extract JSON using regex
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            json_text = json_match.group()
            print(f"📄 Extracted JSON ({len(json_text)} chars):")
            print(json_text)
            print()
            
            # Try to parse
            try:
                data = json.loads(json_text)
                print("✅ JSON is valid!")
                print(f"Keys: {list(data.keys())}")
                
                if 'cards' in data:
                    print(f"Found {len(data['cards'])} cards")
                    for i, card in enumerate(data['cards']):
                        print(f"  Card {i+1}: {list(card.keys())}")
                else:
                    print("❌ No 'cards' key found")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"   Error at line {e.lineno}, column {e.colno}")
                print(f"   Error position: {e.pos}")
                
                # Show the problematic area
                lines = json_text.split('\n')
                if e.lineno <= len(lines):
                    problem_line = lines[e.lineno - 1]
                    print(f"   Problem line: '{problem_line}'")
                    if e.colno <= len(problem_line):
                        print(f"   Problem char: '{problem_line[e.colno-1] if e.colno > 0 else 'START'}'")
        else:
            print("❌ No JSON pattern found in response")
        
        # Test the actual parsing method
        print("\n🔧 Testing FlashcardGenerator._parse_llm_response...")
        try:
            cards = generator._parse_llm_response(response.content, chunk)
            print(f"✅ Generator parsed {len(cards)} cards successfully!")
        except Exception as e:
            print(f"❌ Generator parsing failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_json_parsing_issue())
