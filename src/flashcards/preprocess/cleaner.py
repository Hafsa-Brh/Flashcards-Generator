"""
Text cleaning and normalization utilities.

This module handles cleaning raw text extracted from documents:
- Normalize whitespace and line breaks
- Remove URLs, emails, and other noise
- Fix common OCR errors and formatting issues
- Prepare text for chunking and AI processing
"""

import re
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from ..config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class CleaningStats:
    """Statistics from the cleaning process."""
    original_length: int
    cleaned_length: int
    lines_removed: int = 0
    urls_removed: int = 0
    emails_removed: int = 0
    special_chars_removed: int = 0
    
    @property
    def reduction_percentage(self) -> float:
        """Calculate the percentage reduction in text length."""
        if self.original_length == 0:
            return 0.0
        return ((self.original_length - self.cleaned_length) / self.original_length) * 100


class TextCleaner:
    """Handles text cleaning and normalization."""
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        
        # Compile regex patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile commonly used regex patterns."""
        
        # URL pattern
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Email pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Multiple whitespace pattern
        self.whitespace_pattern = re.compile(r'\s+')
        
        # Common page artifacts (headers/footers)
        self.page_artifact_patterns = [
            re.compile(r'Page \d+ of \d+', re.IGNORECASE),
            re.compile(r'Page \d+', re.IGNORECASE),
            re.compile(r'^\d+$'),  # Standalone page numbers
            re.compile(r'Chapter \d+', re.IGNORECASE),
        ]
        
        # Hyphenation fix patterns
        self.hyphenation_patterns = [
            (re.compile(r'(\w+)-\s*\n\s*(\w+)'), r'\1\2'),  # word-\nword -> wordword
            (re.compile(r'(\w+)-\s+(\w+)'), r'\1\2'),       # word- word -> wordword
        ]
        
        # Special characters to normalize
        self.special_char_replacements = {
            '"': '"',  # Smart quotes
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',  # En dash
            '—': '-',  # Em dash
            '…': '...',  # Ellipsis
        }
    
    def remove_urls(self, text: str) -> tuple[str, int]:
        """Remove URLs from text."""
        urls_found = len(self.url_pattern.findall(text))
        cleaned_text = self.url_pattern.sub(' [URL] ', text)
        return cleaned_text, urls_found
    
    def remove_emails(self, text: str) -> tuple[str, int]:
        """Remove email addresses from text."""
        emails_found = len(self.email_pattern.findall(text))
        cleaned_text = self.email_pattern.sub(' [EMAIL] ', text)
        return cleaned_text, emails_found
    
    def fix_hyphenation(self, text: str) -> str:
        """Fix broken hyphenation from PDF extraction."""
        for pattern, replacement in self.hyphenation_patterns:
            text = pattern.sub(replacement, text)
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and line breaks."""
        # Replace multiple spaces/tabs with single space
        text = self.whitespace_pattern.sub(' ', text)
        
        # Fix excessive line breaks (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing/leading whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines but preserve paragraph breaks
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')  # Preserve single empty line for paragraph break
                prev_empty = True
        
        return '\n'.join(cleaned_lines)
    
    def remove_page_artifacts(self, text: str) -> tuple[str, int]:
        """Remove common page headers, footers, and artifacts."""
        lines = text.split('\n')
        original_count = len(lines)
        cleaned_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                cleaned_lines.append(line)
                continue
            
            # Check if line matches any page artifact pattern
            is_artifact = any(pattern.match(stripped_line) for pattern in self.page_artifact_patterns)
            
            if not is_artifact:
                cleaned_lines.append(line)
        
        removed_count = original_count - len(cleaned_lines)
        return '\n'.join(cleaned_lines), removed_count
    
    def normalize_special_characters(self, text: str) -> tuple[str, int]:
        """Replace special characters with standard equivalents."""
        original_text = text
        replacements_made = 0
        
        for special_char, replacement in self.special_char_replacements.items():
            count_before = text.count(special_char)
            text = text.replace(special_char, replacement)
            replacements_made += count_before
        
        return text, replacements_made
    
    def remove_excessive_punctuation(self, text: str) -> str:
        """Clean up excessive punctuation."""
        # Multiple consecutive punctuation marks
        text = re.sub(r'[.]{3,}', '...', text)  # Multiple dots to ellipsis
        text = re.sub(r'[!]{2,}', '!', text)    # Multiple exclamations
        text = re.sub(r'[?]{2,}', '?', text)    # Multiple questions
        
        return text
    
    def clean_text(self, text: str, aggressive: bool = False) -> tuple[str, CleaningStats]:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            aggressive: If True, apply more aggressive cleaning
            
        Returns:
            Tuple of (cleaned_text, cleaning_stats)
        """
        if not text or not text.strip():
            return text, CleaningStats(0, 0)
        
        original_length = len(text)
        cleaned_text = text
        stats = CleaningStats(original_length=original_length, cleaned_length=0)
        
        logger.debug(f"Starting text cleaning (original length: {original_length})")
        
        # Step 1: Fix hyphenation issues (common in PDFs)
        cleaned_text = self.fix_hyphenation(cleaned_text)
        
        # Step 2: Remove URLs if configured
        if self.settings.text_processing.remove_urls:
            cleaned_text, urls_removed = self.remove_urls(cleaned_text)
            stats.urls_removed = urls_removed
            logger.debug(f"Removed {urls_removed} URLs")
        
        # Step 3: Remove emails if configured
        if self.settings.text_processing.remove_email:
            cleaned_text, emails_removed = self.remove_emails(cleaned_text)
            stats.emails_removed = emails_removed
            logger.debug(f"Removed {emails_removed} email addresses")
        
        # Step 4: Remove page artifacts
        cleaned_text, lines_removed = self.remove_page_artifacts(cleaned_text)
        stats.lines_removed = lines_removed
        logger.debug(f"Removed {lines_removed} page artifact lines")
        
        # Step 5: Normalize special characters
        cleaned_text, special_chars_removed = self.normalize_special_characters(cleaned_text)
        stats.special_chars_removed = special_chars_removed
        
        # Step 6: Clean up punctuation
        cleaned_text = self.remove_excessive_punctuation(cleaned_text)
        
        # Step 7: Normalize whitespace (should be last)
        if self.settings.text_processing.normalize_whitespace:
            cleaned_text = self.normalize_whitespace(cleaned_text)
        
        # Aggressive cleaning if requested
        if aggressive:
            cleaned_text = self._aggressive_cleaning(cleaned_text)
        
        # Final cleanup
        cleaned_text = cleaned_text.strip()
        stats.cleaned_length = len(cleaned_text)
        
        logger.info(f"Text cleaning complete: {original_length} -> {stats.cleaned_length} chars "
                   f"({stats.reduction_percentage:.1f}% reduction)")
        
        return cleaned_text, stats
    
    def _aggressive_cleaning(self, text: str) -> str:
        """Apply more aggressive cleaning rules."""
        
        # Remove very short lines (likely artifacts)
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip very short lines unless they're punctuation or numbers
            if len(stripped) < 3 and not re.match(r'^[.!?0-9]+$', stripped):
                continue
                
            # Skip lines that are mostly non-alphabetic (likely noise)
            if stripped and len(re.findall(r'[a-zA-Z]', stripped)) / len(stripped) < 0.5:
                continue
                
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def clean_for_chunking(self, text: str) -> str:
        """Clean text specifically for optimal chunking."""
        cleaned_text, _ = self.clean_text(text, aggressive=False)
        
        # Ensure proper sentence endings
        cleaned_text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', cleaned_text)
        
        # Ensure paragraph breaks are preserved
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        
        return cleaned_text


# Convenience functions
def clean_text(text: str, aggressive: bool = False) -> tuple[str, CleaningStats]:
    """Clean text using default settings."""
    cleaner = TextCleaner()
    return cleaner.clean_text(text, aggressive)


def clean_for_chunking(text: str) -> str:
    """Clean text for optimal chunking."""
    cleaner = TextCleaner()
    return cleaner.clean_for_chunking(text)
