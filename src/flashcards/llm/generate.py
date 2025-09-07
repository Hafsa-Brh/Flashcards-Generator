"""
LLM-based flashcard generation module.

This module handles the generation of flashcards from text chunks using
the configured LLM (LM Studio).
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import json
import re

from ..schemas import Chunk, Card, CardType, ProcessingStats
from ..llm.client import LMStudioClient, ChatMessage
from ..config import get_settings

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """Generates flashcards from text chunks using LLM."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = LMStudioClient()
        
        # Load generation prompt template
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """Load the flashcard generation prompt template."""
        try:
            from pathlib import Path
            prompt_file = Path(__file__).parent.parent / "prompts" / "qa_generation.md"
            
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"Prompt file not found: {prompt_file}, using default template")
                return self._get_default_prompt_template()
                
        except Exception as e:
            logger.warning(f"Error loading prompt template: {e}, using default")
            return self._get_default_prompt_template()
    
    def _get_default_prompt_template(self) -> str:
        """Get the default prompt template."""
        return """You are an expert educational content creator. Your task is to generate high-quality flashcards from the provided text content.

Guidelines:
1. Create clear, concise question-answer pairs
2. Focus on key concepts, definitions, and important facts
3. Ensure questions are specific and answerable from the content
4. Make answers complete but concise
5. Generate {max_cards} flashcards maximum per chunk
6. Output valid JSON format only

Input Text:
{text_content}

Output Format (JSON only, no other text):
{{
  "flashcards": [
    {{
      "question": "What is...?",
      "answer": "Clear, concise answer...",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}"""

    def _create_generation_prompt(self, chunk_text: str, chunk_id: str = "unknown") -> str:
        """Create the generation prompt for a text chunk."""
        return self.prompt_template.format(
            text=chunk_text,
            chunk_id=chunk_id
        )
    
    async def generate_cards_from_chunk(self, chunk: Chunk) -> List[Card]:
        """Generate flashcards from a single text chunk."""
        try:
            logger.info(f"Generating flashcards from chunk {chunk.index} ({len(chunk.text)} chars)")
            
            # Create the prompt
            prompt = self._create_generation_prompt(chunk.text, str(chunk.id))
            
            # Prepare the chat message
            messages = [
                ChatMessage(role="user", content=prompt)
            ]
            
            # Generate response from LLM
            response = await self.client.chat_completion(
                messages=messages,
                temperature=self.settings.lm_studio.temperature,
                max_tokens=self.settings.lm_studio.max_tokens
            )
            
            if not response or not response.content:
                logger.error("Empty response from LLM")
                return []
            
            # Parse the JSON response
            cards = self._parse_llm_response(response.content, chunk)
            
            logger.info(f"Successfully generated {len(cards)} flashcards from chunk {chunk.index}")
            return cards
            
        except Exception as e:
            logger.error(f"Error generating cards from chunk {chunk.index}: {e}")
            return []
    
    def _parse_llm_response(self, response_text: str, chunk: Chunk) -> List[Card]:
        """Parse the LLM response and create Card objects."""
        try:
            # Clean up the response - sometimes LLMs add extra text
            response_text = response_text.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
            else:
                json_text = response_text
            
            # Parse JSON with fallback for truncated responses
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError:
                # Try to fix truncated JSON by parsing valid cards
                data = self._parse_truncated_json(json_text)
                if not data:
                    # Try to fix common JSON issues
                    json_text = self._fix_json_format(json_text)
                    data = json.loads(json_text)
            
            # Extract flashcards - try both 'cards' and 'flashcards' keys
            cards_data = None
            if 'cards' in data:
                cards_data = data['cards']
            elif 'flashcards' in data:
                cards_data = data['flashcards']
            else:
                logger.error("Invalid JSON structure - missing 'cards' or 'flashcards' key")
                return []
            
            if not isinstance(cards_data, list):
                logger.error("Cards data is not a list")
                return []
            
            cards = []
            for i, card_data in enumerate(cards_data):
                try:
                    # Support both old and new field names
                    front_text = card_data.get('front') or card_data.get('question', '')
                    back_text = card_data.get('back') or card_data.get('answer', '')
                    
                    if not front_text or not back_text:
                        logger.warning(f"Skipping card {i}: missing front/back text")
                        continue
                    
                    # Create Card object
                    card = Card(
                        front=front_text.strip(),
                        back=back_text.strip(),
                        card_type=CardType.BASIC,  # Default to basic type
                        chunk_id=chunk.id,
                        source_id=chunk.source_id,
                        difficulty=card_data.get('difficulty', 'medium'),
                        tags=[],  # Can be enhanced later
                        metadata={
                            'chunk_index': chunk.index,
                            'generated_at': str(chunk.created_at) if hasattr(chunk, 'created_at') else None
                        }
                    )
                    
                    cards.append(card)
                    
                except Exception as e:
                    logger.warning(f"Error creating card {i}: {e}")
                    continue
            
            return cards
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            return []
    
    def _parse_truncated_json(self, json_text: str) -> dict:
        """Try to parse truncated JSON by extracting valid cards."""
        try:
            # Look for complete card objects in the truncated JSON
            cards = []
            
            # Use regex to find complete card objects
            card_pattern = r'\{\s*"front":\s*"[^"]*",\s*"back":\s*"[^"]*",\s*"chunk_id":\s*"[^"]*"\s*\}'
            card_matches = re.findall(card_pattern, json_text, re.DOTALL)
            
            for match in card_matches:
                try:
                    card_data = json.loads(match)
                    cards.append(card_data)
                except json.JSONDecodeError:
                    continue
            
            if cards:
                logger.info(f"Recovered {len(cards)} cards from truncated JSON")
                return {"cards": cards}
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse truncated JSON: {e}")
            return None
    
    def _fix_json_format(self, json_text: str) -> str:
        """Try to fix common JSON formatting issues."""
        # Remove leading/trailing whitespace
        json_text = json_text.strip()
        
        # Remove any text before the first {
        first_brace = json_text.find('{')
        if first_brace > 0:
            json_text = json_text[first_brace:]
        
        # Remove any text after the last }
        last_brace = json_text.rfind('}')
        if last_brace > 0:
            json_text = json_text[:last_brace + 1]
        
        # Fix common issues with quotes
        json_text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text)
        
        return json_text
    
    async def generate_cards_from_chunks(self, chunks: List[Chunk]) -> List[Card]:
        """Generate flashcards from multiple chunks."""
        if not chunks:
            return []
        
        logger.info(f"Generating flashcards from {len(chunks)} chunks")
        
        all_cards = []
        
        for chunk in chunks:
            # Rate limiting - add delay between requests if configured
            if self.settings.card_generation.rate_limit_delay > 0:
                await asyncio.sleep(self.settings.card_generation.rate_limit_delay)
            
            cards = await self.generate_cards_from_chunk(chunk)
            all_cards.extend(cards)
            
            # Log progress
            if len(all_cards) > 0:
                logger.info(f"Progress: {len(all_cards)} cards generated from {chunks.index(chunk) + 1}/{len(chunks)} chunks")
        
        logger.info(f"Successfully generated {len(all_cards)} total flashcards")
        return all_cards
    
    async def generate_cards_batch(self, chunks: List[Chunk], max_concurrent: int = 3) -> List[Card]:
        """Generate flashcards from chunks with concurrent processing."""
        if not chunks:
            return []
        
        logger.info(f"Generating flashcards from {len(chunks)} chunks (max concurrent: {max_concurrent})")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(chunk: Chunk) -> List[Card]:
            async with semaphore:
                # Add rate limiting delay
                if self.settings.card_generation.rate_limit_delay > 0:
                    await asyncio.sleep(self.settings.card_generation.rate_limit_delay)
                
                return await self.generate_cards_from_chunk(chunk)
        
        # Process chunks concurrently
        tasks = [generate_with_semaphore(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results
        all_cards = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing chunk {i}: {result}")
            elif isinstance(result, list):
                all_cards.extend(result)
        
        logger.info(f"Batch processing complete: {len(all_cards)} total flashcards generated")
        return all_cards
    
    def validate_cards(self, cards: List[Card]) -> List[Card]:
        """Validate and filter generated cards."""
        valid_cards = []
        
        for card in cards:
            try:
                # Basic validation
                if not card.front or not card.back:
                    logger.warning("Skipping card with empty question or answer")
                    continue
                
                # Length validation
                if len(card.front) < 10:
                    logger.warning(f"Skipping card with very short question: {card.front[:50]}...")
                    continue
                
                if len(card.back) < 5:
                    logger.warning(f"Skipping card with very short answer: {card.back[:50]}...")
                    continue
                
                # Quality validation (can be enhanced)
                if self._is_low_quality_card(card):
                    logger.warning(f"Skipping low-quality card: {card.front[:50]}...")
                    continue
                
                valid_cards.append(card)
                
            except Exception as e:
                logger.warning(f"Error validating card: {e}")
                continue
        
        logger.info(f"Validation complete: {len(valid_cards)}/{len(cards)} cards passed validation")
        return valid_cards
    
    def _is_low_quality_card(self, card: Card) -> bool:
        """Check if a card is low quality."""
        # Simple heuristics - can be enhanced
        question = card.front.lower()
        answer = card.back.lower()
        
        # Check for overly generic questions
        generic_starters = [
            "what is this", "what are these", "explain this", 
            "describe this", "what does this mean"
        ]
        if any(question.startswith(starter) for starter in generic_starters):
            return True
        
        # Check if answer is just a repetition of the question
        if question in answer or answer in question:
            return True
        
        return False


# Convenience functions
async def generate_cards_from_chunks(chunks: List[Chunk]) -> List[Card]:
    """Generate flashcards from chunks using default settings."""
    generator = FlashcardGenerator()
    return await generator.generate_cards_from_chunks(chunks)


async def generate_cards_batch(chunks: List[Chunk], max_concurrent: int = 3) -> List[Card]:
    """Generate flashcards with concurrent processing."""
    generator = FlashcardGenerator()
    return await generator.generate_cards_batch(chunks, max_concurrent)
