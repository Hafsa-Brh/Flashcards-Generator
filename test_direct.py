#!/usr/bin/env python3
"""
Direct test of LM Studio API to see what's actually happening.
"""

import asyncio
import httpx
import json


async def direct_test():
    """Test LM Studio directly."""
    
    print("🔍 Direct LM Studio test...")
    
    client = httpx.AsyncClient(timeout=30)
    
    # The same prompt our app uses
    prompt = """Create flashcards from the given text. Return only valid JSON with no additional text.

Text to analyze:
Python is a programming language. Variables in Python can store different types of data like numbers, strings, and lists.

Required JSON format:
{
  "cards": [
    {
      "front": "Question here",
      "back": "Answer here", 
      "chunk_id": "test_chunk"
    }
  ]
}"""
    
    request_data = {
        "model": "qwen3-4b-instruct-2507@q4_k_m",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2500,
        "temperature": 0.2
    }
    
    try:
        print("📤 Sending request to LM Studio...")
        response = await client.post(
            "http://192.168.1.2:1234/v1/chat/completions",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error response: {response.text}")
            return
        
        # Parse the response
        data = response.json()
        print(f"📋 Full response structure: {json.dumps(data, indent=2)}")
        
        # Extract content
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
                print(f"📝 Content: {content}")
                print(f"📏 Content length: {len(content)}")
                
                # Try to parse as JSON
                try:
                    json_data = json.loads(content)
                    print(f"✅ Valid JSON: {json_data}")
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {e}")
                    print(f"Raw content: '{content}'")
            else:
                print(f"❌ Missing message/content in choice: {choice}")
        else:
            print(f"❌ No choices in response: {data}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(direct_test())
