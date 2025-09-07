# AI Flashcards Generator

A beginner-friendly Python application that converts text documents (PDFs, Word docs, plain text) into interactive flashcards using local AI models.

## Features

- **📄 Multi-format Input**: Support for `.txt`, `.md`, `.pdf`, and `.docx` files
- **🤖 Local AI Generation**: Uses LM Studio for local AI-powered Q&A generation
- **🔧 Smart Processing**: Automatic text cleaning and intelligent chunking
- **✅ Quality Control**: Built-in validation and duplicate detection
- **📊 Multiple Export Formats**: JSON output (Anki support coming soon)
- **🎯 Beginner Friendly**: Simple CLI interface with clear instructions

## Quick Start

### Prerequisites

- Python 3.11+
- LM Studio with a compatible model 

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd flashcards
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your LM Studio:
   - Start LM Studio
   - Load your preferred model
   - Start the local server (usually runs on `http://localhost:1234`)

### Usage

```bash
# Basic usage
python -m flashcards.cli generate input.pdf

# With custom settings
python -m flashcards.cli generate input.pdf --output-dir ./my_cards --max-cards 10
```

## Project Structure

```
flashcards/
├── src/flashcards/
│   ├── cli.py              # Command line interface
│   ├── config.py           # Configuration settings
│   ├── schemas.py          # Data models (Card, Deck, Source)
│   ├── pipeline.py         # Main processing pipeline
│   ├── ingest/             # File loading and parsing
│   ├── preprocess/         # Text cleaning and chunking
│   ├── llm/               # AI model interaction
│   ├── postprocess/       # Validation and quality control
│   ├── export/            # Output format handlers
│   └── prompts/           # AI prompt templates
├── data/
│   ├── input/             # Input documents
│   ├── output/            # Generated flashcards
│   └── samples/           # Example documents
└── tests/                 # Unit and integration tests
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# LM Studio settings
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL_NAME=your-model-name

# Processing settings
MAX_CHUNK_SIZE=200
CHUNK_OVERLAP=50
MAX_CARDS_PER_CHUNK=8
```

## Development

Run tests:
```bash
pytest
```

Code formatting:
```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

## Roadmap

- [x] Basic text processing and AI generation
- [x] PDF and Word document support
- [x] JSON export format
- [ ] Anki integration (AnkiConnect)
- [ ] Streamlit web interface
- [ ] Cloze deletion cards
- [ ] Difficulty scoring
- [ ] Batch processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with LM Studio for local AI processing
- Inspired by spaced repetition learning principles
- Thanks to the open-source AI community