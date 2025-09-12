#!/usr/bin/env python3
"""
Debug the flashcard generation step by step.
"""

import asyncio
import json
from src.flashcards.llm.generate import FlashcardGenerator
from src.flashcards.schemas import Chunk, Source
from uuid import uuid4

async def debug_generation_step_by_step():
    """Debug each step of flashcard generation."""
    print("🐛 Step-by-Step Flashcard Generation Debug")
    print("=" * 50)
    
    # Create test chunk
    source = Source(
        id=uuid4(),
        filename="test.txt",
        title="Test Document",
        content_type="text/plain",
        source_type="txt",
        content="Python is a high-level programming language known for its simplicity."
    )
    
    chunk = Chunk(
        id=uuid4(),
        source_id=source.id,
        index=0,
        text="Python is a high-level programming language known for its simplicity and readability.",
        word_count=13,
        token_count=20,
        start_char=0,
        end_char=87
    )
    
    print(f"📦 Test chunk: {chunk.text}")
    print()
    
    # Initialize generator
    generator = FlashcardGenerator()
    
    # Step 1: Check prompt template
    print("1️⃣ Checking prompt template...")
    try:
        prompt = generator._create_generation_prompt(chunk.text, str(chunk.id))
        print("✅ Prompt created successfully")
        print("📝 Prompt (first 500 chars):")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print()
    except Exception as e:
        print(f"❌ Error creating prompt: {e}")
        return
    
    # Step 2: Test LLM call
    print("2️⃣ Testing LLM call...")
    try:
        from src.flashcards.llm.client import ChatMessage
        
        messages = [ChatMessage(role="user", content=prompt)]
        response = await generator.client.chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=500
        )
        
        print("✅ LLM response received")
        print(f"📥 Response type: {type(response)}")
        print(f"📥 Response content: {response.content}")
        print()
        
        # Step 3: Test JSON parsing
        print("3️⃣ Testing JSON parsing...")
        try:
            cards = generator._parse_llm_response(response.content, chunk)
            print(f"✅ Successfully parsed {len(cards)} cards")
            for i, card in enumerate(cards):
                print(f"   Card {i+1}: {card.front[:50]}...")
        except Exception as e:
            print(f"❌ JSON parsing error: {e}")
            print("🔍 Attempting manual JSON extraction...")
            
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                print(f"📄 Extracted JSON: {json_text}")
                try:
                    data = json.loads(json_text)
                    print(f"✅ JSON is valid: {data}")
                except json.JSONDecodeError as je:
                    print(f"❌ JSON decode error: {je}")
            else:
                print("❌ No JSON pattern found in response")
        
    except Exception as e:
        print(f"❌ LLM call error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_generation_step_by_step())
