#!/usr/bin/env python3
"""
Test with localhost LM Studio configuration.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from flashcards.llm.client import LMStudioClient
from flashcards.llm.client import ChatMessage


async def test_localhost_connection():
    """Test connection to localhost LM Studio."""
    print("🔗 Testing Local LM Studio Connection")
    print("=" * 50)
    
    # Override the base URL for local testing
    print("🏠 Using localhost configuration for testing")
    
    try:
        # Create client with localhost URL
        client = LMStudioClient()
        # Override the base_url for this test
        client.base_url = "http://localhost:1234"
        
        print(f"📡 Testing connection to: {client.base_url}")
        
        # Test models
        models = await client.list_models()
        if not models:
            print("❌ No models available")
            print("💡 Make sure:")
            print("   1. LM Studio is running locally")
            print("   2. A model is loaded")
            print("   3. Server is started")
            return False
        
        print(f"✅ Connection successful!")
        print(f"📚 Available models:")
        for model in models[:3]:
            print(f"   - {model.id}")
        
        # Test chat completion
        print(f"\n🤖 Testing chat completion...")
        test_message = ChatMessage(
            role="user", 
            content="Say exactly 'Hello from LM Studio!' and nothing else."
        )
        
        response = await client.chat_completion([test_message], max_tokens=20)
        
        if response and response.content:
            print(f"✅ Chat completion successful!")
            print(f"🤖 Response: {response.content}")
            return True
        else:
            print("❌ Chat completion failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 To fix this:")
        print("   1. Open LM Studio")
        print("   2. Load a model")
        print("   3. Start the local server")
        print("   4. Make sure it's running on port 1234")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_localhost_connection())
    
    if success:
        print(f"\n🎉 LOCAL CONNECTION WORKING!")
        print(f"You can now run the full pipeline with local LM Studio")
        print(f"Command: python test_e2e.py")
    else:
        print(f"\n❌ Please set up LM Studio first, then try again")
