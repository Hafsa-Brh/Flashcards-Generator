#!/usr/bin/env python3
"""Quick script to get available models from LM Studio"""

import asyncio
from src.flashcards.llm.client import LMStudioClient

async def main():
    print("🔍 Getting your LM Studio models...")
    
    try:
        client = LMStudioClient()
        models = await client.list_models()
        
        print(f"\n✅ Found {len(models)} models:")
        model_names = [m.name for m in models]
        for i, name in enumerate(model_names, 1):
            print(f"{i:2d}. {name}")
        
        # Find best matches for our presets
        print("\n🎯 Best matches for presets:")
        
        # Fast models (smaller, faster)
        fast_models = [m for m in model_names if any(x in m.lower() for x in ['0.5b', '1b', '3b', '4b', '7b'])]
        if fast_models:
            print(f"⚡ Fast & Quick: {fast_models[0]}")
        
        # Balanced models (medium size)
        balanced_models = [m for m in model_names if any(x in m.lower() for x in ['14b', '30b', '32b', 'qwen3', 'a3b'])]
        if balanced_models:
            print(f"⚖️  Balanced: {balanced_models[0]}")
        
        # Detailed models (largest, best quality)
        detailed_models = [m for m in model_names if any(x in m.lower() for x in ['40b', '70b', '72b', '8x'])]
        if detailed_models:
            print(f"🔬 Detailed: {detailed_models[0]}")
            
        return model_names
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(main())
