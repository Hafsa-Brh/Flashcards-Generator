"""
LM Studio client for connecting to local AI models.

This module handles communication with LM Studio server including:
- Model listing and selection
- Chat completions
- Connection testing and error handling
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import httpx
from pydantic import BaseModel

from ..config import Settings, get_settings


logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    name: str
    size_gb: Optional[float] = None
    description: Optional[str] = None
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: str  # "system", "user", or "assistant"
    content: str


class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.2
    max_tokens: int = 512
    top_p: float = 0.9
    stream: bool = False


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""
    id: str
    model: str
    content: str
    usage: Dict[str, int]
    finish_reason: str


class LMStudioClient:
    """Client for communicating with LM Studio server."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.get_lm_studio_url()
        self.timeout = self.settings.lm_studio.timeout
        self.max_retries = self.settings.lm_studio.max_retries
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={"Content-Type": "application/json"}
        )
        
        self._available_models: Optional[List[ModelInfo]] = None
        self._selected_model: Optional[str] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection to LM Studio server."""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            if response.status_code == 200:
                return True, None
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        
        except httpx.ConnectError as e:
            return False, f"Connection failed: {str(e)}"
        except httpx.TimeoutException:
            return False, f"Connection timeout after {self.timeout}s"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    async def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """Get list of available models from LM Studio."""
        if self._available_models is not None and not force_refresh:
            return self._available_models
        
        try:
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get("data", []):
                model = ModelInfo(
                    id=model_data["id"],
                    name=model_data.get("id", "Unknown"),  # LM Studio usually uses id as name
                    description=model_data.get("description"),
                )
                models.append(model)
            
            self._available_models = models
            logger.info(f"Found {len(models)} available models")
            
            return models
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing models: {e}")
            raise
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise
    
    def select_best_model(self, models: List[ModelInfo]) -> Optional[str]:
        """Select the best model for flashcard generation."""
        if not models:
            return None
        
        # Priority order for flashcard generation (adjust based on your models)
        preferred_models = [
            # Qwen models - excellent for Q&A generation
            "qwen2.5",
            "qwen2",
            "qwen",
            "qwen-instruct",
            
            # Llama models - good general performance
            "llama-3.1",
            "llama-3",
            "llama-2",
            "llama",
            
            # Gemma models - good for educational content
            "gemma-2",
            "gemma",
            
            # Mistral models - balanced performance
            "mistral",
            "mixtral",
            
            # OpenAI-compatible models
            "gpt",
            
            # Catch-all for instruction-tuned models
            "instruct",
            "chat",
        ]
        
        # Find the best match
        model_ids = [m.id.lower() for m in models]
        
        for preferred in preferred_models:
            for i, model_id in enumerate(model_ids):
                if preferred in model_id:
                    selected_model = models[i].id
                    logger.info(f"Selected model: {selected_model}")
                    return selected_model
        
        # If no preferred model found, use the first one
        selected_model = models[0].id
        logger.info(f"No preferred model found, using: {selected_model}")
        return selected_model
    
    async def initialize_model(self) -> str:
        """Initialize and select the best available model."""
        # Test connection first
        connected, error = await self.test_connection()
        if not connected:
            raise ConnectionError(f"Cannot connect to LM Studio: {error}")
        
        # Get available models
        models = await self.list_models()
        if not models:
            raise ValueError("No models available in LM Studio")
        
        # Select model
        if self.settings.lm_studio.model_name:
            # Use specified model
            model_ids = [m.id for m in models]
            if self.settings.lm_studio.model_name in model_ids:
                self._selected_model = self.settings.lm_studio.model_name
            else:
                logger.warning(f"Specified model {self.settings.lm_studio.model_name} not found")
                self._selected_model = self.select_best_model(models)
        else:
            # Auto-select best model
            self._selected_model = self.select_best_model(models)
        
        if not self._selected_model:
            raise ValueError("Could not select a suitable model")
        
        logger.info(f"Initialized with model: {self._selected_model}")
        return self._selected_model
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> ChatCompletionResponse:
        """Send a chat completion request."""
        
        # Ensure model is initialized
        if not self._selected_model:
            await self.initialize_model()
        
        # Use provided model or default selected model
        model = model or self._selected_model
        
        # Use provided parameters or defaults from settings
        request_data = ChatCompletionRequest(
            model=model,
            messages=messages,
            temperature=temperature or self.settings.lm_studio.temperature,
            max_tokens=max_tokens or self.settings.lm_studio.max_tokens,
            top_p=top_p or self.settings.lm_studio.top_p
        )
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=request_data.model_dump()
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract response content
            choice = data["choices"][0]
            content = choice["message"]["content"]
            
            return ChatCompletionResponse(
                id=data.get("id", ""),
                model=data.get("model", model),
                content=content,
                usage=data.get("usage", {}),
                finish_reason=choice.get("finish_reason", "stop")
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in chat completion: {e}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def generate_flashcards_prompt(
        self,
        text_chunk: str,
        max_cards: int = 8
    ) -> Optional[str]:
        """Generate flashcards from a text chunk using the LM Studio model."""
        
        system_message = ChatMessage(
            role="system",
            content="""You are a precise study assistant that creates high-quality flashcards.

RULES:
- Create factual, verifiable questions from the given text
- Use clear, simple language suitable for learning
- Avoid opinion-based or ambiguous questions
- Questions should end with '?'
- Answers should be concise (1-3 sentences max)
- Return ONLY valid JSON, no extra text
- If the text is too trivial, return an empty array []

Generate flashcards in this exact JSON format:
[
  {
    "front": "Question here?",
    "back": "Clear, concise answer.",
    "tags": ["relevant", "tags"]
  }
]"""
        )
        
        user_message = ChatMessage(
            role="user",
            content=f"""Create {max_cards} flashcards maximum from this text:

{text_chunk}

Return only the JSON array of flashcards."""
        )
        
        try:
            response = await self.chat_completion([system_message, user_message])
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            return None


# Convenience function for quick testing
async def test_lm_studio_connection(base_url: str = "http://192.168.1.2:1234") -> None:
    """Test connection to LM Studio and list models."""
    
    # Temporarily override settings for testing
    settings = get_settings()
    settings.lm_studio.base_url = base_url
    
    async with LMStudioClient(settings) as client:
        print(f"Testing connection to {base_url}...")
        
        connected, error = await client.test_connection()
        if not connected:
            print(f"❌ Connection failed: {error}")
            return
        
        print("✅ Connection successful!")
        
        print("\nListing available models...")
        try:
            models = await client.list_models()
            print(f"\n📋 Found {len(models)} models:")
            
            for i, model in enumerate(models, 1):
                print(f"  {i}. {model.id}")
                if model.description:
                    print(f"     Description: {model.description}")
            
            # Select best model
            best_model = client.select_best_model(models)
            print(f"\n🎯 Recommended model: {best_model}")
            
        except Exception as e:
            print(f"❌ Error listing models: {e}")


if __name__ == "__main__":
    # Run connection test
    asyncio.run(test_lm_studio_connection())
