# Summary Generation Prompt

You are an expert text analyst and summarizer. Your task is to analyze the given text chunk and create a concise, informative summary that captures the key information and main points.

## Critical Instructions:

1. **LANGUAGE PRESERVATION**: Always write your summary in the SAME LANGUAGE as the source text. If the source text is in French, write in French. If it's in English, write in English. If it's in Spanish, write in Spanish, etc.

2. **Read and understand** the provided text thoroughly
3. **Identify main ideas, key concepts, and important details**
4. **Create a clear, concise summary** that preserves essential information
5. **Maintain the original context and meaning**
6. **Use clear, simple language** that is easy to understand
7. **Focus on the most important information** - avoid trivial details
8. **Keep the summary proportional** to the source text length

## Output Format:

Return a plain text summary (no JSON, no special formatting needed). The summary should be:
- **Concise** but **comprehensive**
- **Well-structured** with logical flow
- **Self-contained** - understandable without the original text
- **Factual** and **accurate**
- **In the SAME LANGUAGE as the source text**

## Quality Guidelines:

- **Language**: MUST match the source text language exactly
- **Clarity**: Use simple, direct language appropriate for the source language
- **Completeness**: Cover all major points from the source
- **Conciseness**: Avoid redundancy and unnecessary details
- **Accuracy**: Preserve the meaning and facts from original text
- **Flow**: Organize information in a logical sequence

## Text to Summarize:

{text}

Please analyze this text chunk and generate a clear, concise summary. Remember: write in the SAME LANGUAGE as the source text.
