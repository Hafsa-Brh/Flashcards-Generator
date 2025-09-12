#!/usr/bin/env python3
"""Test which model is actually loaded and working in LM Studio"""

import asyncio
from src.flashcards.llm.client import LMStudioClient

async def test_loaded_model():
    print("🔍 Testing which model is actually loaded in LM Studio...")
    
    try:
        client = LMStudioClient()
        
        # Get all available models
        models = await client.list_models()
        print(f"📋 Available models: {len(models)}")
        
        # Test each model with a simple request
        for model_info in models[:5]:  # Test first 5 models only
            model_name = model_info.name
            print(f"\n🧪 Testing: {model_name}")
            
            try:
                # Create a new client instance for this specific model
                test_client = LMStudioClient()
                test_client.model_name = model_name
                
                # Try a simple chat completion
                from src.flashcards.llm.client import ChatMessage
                messages = [ChatMessage(role="user", content="Say 'Hello' in one word.")]
                
                response = await test_client.chat_completion(
                    messages=messages,
                    max_tokens=10,
                    temperature=0.1
                )
                
                if response and hasattr(response, 'content'):
                    print(f"  ✅ WORKING: {model_name} -> {response.content.strip()[:50]}")
                    return model_name  # Return the first working model
                else:
                    print(f"  ❌ No response: {model_name}")
                    
            except Exception as e:
                print(f"  ❌ Error: {model_name} -> {str(e)[:100]}")
                
        print("\n❌ No working models found!")
        return None
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

if __name__ == "__main__":
    working_model = asyncio.run(test_loaded_model())
    if working_model:
        print(f"\n🎯 USE THIS MODEL: {working_model}")
    else:
        print("\n💡 Please load a model in LM Studio first!")
