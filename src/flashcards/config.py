"""
Configuration management for the flashcards application.

This module handles all configuration settings including:
- LM Studio connection settings
- Text processing parameters
- Export preferences  
- Environment variables
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl
from pydantic_settings import BaseSettings


class LMStudioConfig(BaseModel):
    """Configuration for LM Studio connection."""
    
    base_url: str = Field(
        default="http://192.168.1.2:1234", 
        description="LM Studio server URL"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key if required (usually not needed for LM Studio)"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Specific model to use (auto-selected if None)"
    )
    timeout: int = Field(
        default=120,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for generation"
    )
    max_tokens: int = Field(
        default=2500,
        ge=1,
        le=4096,
        description="Maximum tokens to generate"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p sampling parameter"
    )


class TextProcessingConfig(BaseModel):
    """Configuration for text processing."""
    
    max_chunk_size: int = Field(
        default=200,
        ge=50,
        le=1000,
        description="Maximum words per chunk"
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=200,
        description="Word overlap between chunks"
    )
    min_chunk_size: int = Field(
        default=20,
        ge=10,
        le=100,
        description="Minimum words per chunk"
    )
    remove_urls: bool = Field(
        default=True,
        description="Remove URLs from text"
    )
    remove_email: bool = Field(
        default=True,
        description="Remove email addresses from text"
    )
    normalize_whitespace: bool = Field(
        default=True,
        description="Normalize whitespace and line breaks"
    )
    
    @validator('chunk_overlap')
    def overlap_must_be_less_than_max_size(cls, v, values):
        if 'max_chunk_size' in values and v >= values['max_chunk_size']:
            raise ValueError('chunk_overlap must be less than max_chunk_size')
        return v


class CardGenerationConfig(BaseModel):
    """Configuration for flashcard generation."""
    
    max_cards_per_chunk: int = Field(
        default=8,
        ge=1,
        le=20,
        description="Maximum cards to generate per text chunk"
    )
    min_cards_per_chunk: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Minimum cards to generate per text chunk"
    )
    prefer_questions: bool = Field(
        default=True,
        description="Prefer question format for card fronts"
    )
    include_definitions: bool = Field(
        default=True,
        description="Include definition-type cards"
    )
    include_comparisons: bool = Field(
        default=True,
        description="Include comparison-type cards"
    )
    auto_tag: bool = Field(
        default=True,
        description="Automatically generate tags from content"
    )
    rate_limit_delay: float = Field(
        default=0.5,
        ge=0.0,
        le=10.0,
        description="Delay between API requests in seconds"
    )
    
    @validator('min_cards_per_chunk')
    def min_must_be_less_than_max(cls, v, values):
        if 'max_cards_per_chunk' in values and v > values['max_cards_per_chunk']:
            raise ValueError('min_cards_per_chunk must be <= max_cards_per_chunk')
        return v


class ExportConfig(BaseModel):
    """Configuration for export settings."""
    
    output_dir: Path = Field(
        default=Path("data/output"),
        description="Directory for output files"
    )
    filename_template: str = Field(
        default="{deck_name}_{timestamp}",
        description="Template for output filenames"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include metadata in exported files"
    )
    pretty_json: bool = Field(
        default=True,
        description="Format JSON output with indentation"
    )
    backup_existing: bool = Field(
        default=True,
        description="Backup existing files before overwriting"
    )


class Settings(BaseSettings):
    """Main application settings."""
    
    # LM Studio configuration
    lm_studio: LMStudioConfig = Field(default_factory=LMStudioConfig)
    
    # Processing configuration
    text_processing: TextProcessingConfig = Field(default_factory=TextProcessingConfig)
    card_generation: CardGenerationConfig = Field(default_factory=CardGenerationConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    
    # Application settings
    app_name: str = Field(default="AI Flashcards Generator")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    verbose: bool = Field(default=False)
    
    # Data directories
    input_dir: Path = Field(default=Path("data/input"))
    samples_dir: Path = Field(default=Path("data/samples"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False
        
        # Allow loading from environment variables with prefix
        env_prefix = "FLASHCARDS_"
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.input_dir,
            self.samples_dir,
            self.export.output_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_lm_studio_url(self) -> str:
        """Get the complete LM Studio API URL."""
        base = self.lm_studio.base_url.rstrip('/')
        if not base.endswith('/v1'):
            base += '/v1'
        return base
    
    def model_dump_for_display(self) -> Dict[str, Any]:
        """Get configuration as dictionary suitable for display."""
        config = self.model_dump()
        
        # Mask sensitive information
        if config.get('lm_studio', {}).get('api_key'):
            config['lm_studio']['api_key'] = "***MASKED***"
        
        return config


# Global settings instance
settings = Settings()


def load_settings(config_file: Optional[Path] = None) -> Settings:
    """Load settings from file or environment variables."""
    if config_file and config_file.exists():
        # Load from YAML/JSON file if needed
        pass
    
    # Ensure directories exist
    settings.ensure_directories()
    
    return settings


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
