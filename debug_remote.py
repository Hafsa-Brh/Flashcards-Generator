#!/usr/bin/env python3
"""
Debug raw LLM responses from remote server.
"""

import asyncio
from src.flashcards.llm.client import LMStudioClient

async def debug_remote_response():
    """Test raw response from remote LM Studio."""
    print("🔍 Debugging Remote LLM Response")
    print("=" * 40)
    
    client = LMStudioClient()
    
    # Simple test with direct prompt
    test_text = """Python is a high-level programming language. It's known for its simplicity and readability."""
    
    prompt = f"""Create flashcards from this text in JSON format:

Text: {test_text}

Respond with only JSON:
{{
  "cards": [
    {{
      "front": "Question here?",
      "back": "Answer here",
      "chunk_id": "test"
    }}
  ]
}}"""
    
    print("📤 Sending prompt...")
    print(f"Text: {test_text}")
    print()
    
    try:
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        print("📥 Raw Response:")
        print("-" * 20)
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            print(repr(content))  # Show exact string with escape chars
            print("\nFormatted:")
            print(content)
        else:
            print(f"Response object: {type(response)}")
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_remote_response())
