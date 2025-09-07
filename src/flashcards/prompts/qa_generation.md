# Flashcard Generation Prompt

You are an expert educator and flashcard creator. Your task is to analyze the given text and create high-quality flashcards that will help students learn and retain the key information.

## Instructions:

1. **Read and understand** the provided text thoroughly
2. **Identify key concepts, facts, definitions, and important details** that would be valuable for learning
3. **Create flashcards** that test understanding, not just memorization
4. **Make questions clear and specific** - avoid ambiguous wording
5. **Provide complete, accurate answers** that fully address the question
6. **Vary question types** - include definitions, explanations, examples, comparisons, and applications
7. **Ensure educational value** - focus on concepts that enhance understanding

## Output Format:

Return your response as a valid JSON object with this exact structure:

```json
{{
  "cards": [
    {{
      "front": "What is the main purpose of Python's built-in `len()` function?",
      "back": "The `len()` function returns the number of items in an object, such as the length of a string, list, tuple, or other collection.",
      "chunk_id": "provided_chunk_id"
    }},
    {{
      "front": "How do you create a list in Python?",
      "back": "You create a list by placing comma-separated values inside square brackets. For example: `my_list = [1, 2, 3, 'hello']`",
      "chunk_id": "provided_chunk_id"
    }}
  ]
}}
```

## Quality Guidelines:

- **Front (Question)**: Should be clear, specific, and test important concepts
- **Back (Answer)**: Should be comprehensive but concise, providing complete understanding
- **Relevance**: Only create cards for genuinely important information
- **Clarity**: Use simple, direct language that students can easily understand
- **Educational Value**: Focus on concepts that build understanding, not trivial details

## Text to Process:

{text}

**Chunk ID: {chunk_id}**

Please analyze this text and generate appropriate flashcards in the JSON format specified above.
