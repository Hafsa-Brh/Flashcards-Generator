#!/usr/bin/env python3
"""
Test connectivity to remote LM Studio server.
"""

import asyncio
import httpx
from src.flashcards.llm.client import LMStudioClient
from src.flashcards.config import get_settings

async def test_remote_connection():
    """Test connection to remote LM Studio."""
    print("🔌 Testing Remote LM Studio Connection")
    print("=" * 50)
    
    config = get_settings()
    print(f"📡 Server URL: {config.lm_studio.base_url}")
    print(f"⏱️  Timeout: {config.lm_studio.timeout}s")
    print()
    
    try:
        # Test basic HTTP connectivity
        print("1️⃣ Testing HTTP connectivity...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config.lm_studio.base_url}/v1/models")
            print(f"   ✅ HTTP Response: {response.status_code}")
            
        # Test LM Studio client
        print("\n2️⃣ Testing LM Studio client...")
        client = LMStudioClient()
        
        # Get available models
        print("   🔍 Fetching available models...")
        models = await client.list_models()
        print(f"   ✅ Found {len(models)} models:")
        for i, model in enumerate(models, 1):
            print(f"      {i}. {model.id}")  # ModelInfo has an id attribute
        
        # Test chat completion
        print("\n3️⃣ Testing chat completion...")
        if models:
            test_message = "Hello! Please respond with just 'Connection successful!'"
            response = await client.chat_completion(
                messages=[{"role": "user", "content": test_message}],
                max_tokens=50
            )
            # Extract content from response object
            if hasattr(response, 'content'):
                print(f"   ✅ Chat response: {response.content[:100]}...")
            elif hasattr(response, 'choices') and response.choices:
                print(f"   ✅ Chat response: {response.choices[0].message.content[:100]}...")
            else:
                print(f"   ✅ Chat response received: {str(response)[:100]}...")
            
        print("\n🎉 All tests passed! Remote LM Studio is ready!")
        return True
        
    except httpx.ConnectError as e:
        print(f"   ❌ Connection failed: Cannot reach {config.lm_studio.base_url}")
        print(f"   💡 Make sure LM Studio is running on the remote computer")
        return False
        
    except httpx.TimeoutException as e:
        print(f"   ❌ Timeout: Server took too long to respond")
        return False
        
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_remote_connection())
