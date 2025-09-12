"""
Professional FastAPI Web Application for AI Flashcards Generator
Modern, responsive design with white and purple theme
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Optional
import tempfile
import os
import logging

# Import our flashcard generation components
from ..pipeline import FlashcardPipeline
from ..schemas import Source, SourceType
from ..llm.summarize import SummaryGenerator, SummaryCombiner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with professional metadata
app = FastAPI(
    title="Smart Learning Platform",
    description="AI-powered e-learning platform with flashcards, summaries, quizzes, and study plans",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Setup static files and templates
web_dir = Path(__file__).parent
static_dir = web_dir / "static"
templates_dir = web_dir / "templates"

# Create directories if they don't exist
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# In-memory storage for demo (in production, use a database)
generations = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the beautiful main interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/summary", response_class=HTMLResponse)
async def summary_home(request: Request):
    """Render the AI document summarizer interface"""
    return templates.TemplateResponse("summary.html", {"request": request})

@app.get("/results/{generation_id}", response_class=HTMLResponse)
async def results_page(request: Request, generation_id: str):
    """Render the results page with generated flashcards"""
    if generation_id not in generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation = generations[generation_id]
    return templates.TemplateResponse("results.html", {
        "request": request, 
        "generation": generation,
        "generation_id": generation_id
    })

@app.get("/summary-results/{generation_id}", response_class=HTMLResponse)
async def summary_results_page(request: Request, generation_id: str):
    """Render the results page with generated summary"""
    if generation_id not in generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation = generations[generation_id]
    if generation.get("type") != "summary":
        raise HTTPException(status_code=404, detail="Summary generation not found")
    
    # Format summary content with proper line breaks for HTML
    summary_content = generation.get("summary", "").replace('\n', '<br>')
    
    return templates.TemplateResponse("summary_results.html", {
        "request": request,
        "summary": summary_content,
        "filename": generation.get("filename", "Unknown"),
        "stats": {
            "chunks_count": generation.get("chunks_count", 0),
            "compression_ratio": generation.get("compression_ratio", 0),
            "processing_time": generation.get("processing_time", 0),
            "word_count": generation.get("word_count", 0),
            "original_word_count": generation.get("original_word_count", 0)
        }
    })

@app.post("/api/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Handle file upload and start flashcard generation"""
    
    # Validate file type
    allowed_extensions = {'.md', '.txt', '.pdf', '.docx', '.html'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique ID for this generation
    generation_id = str(uuid.uuid4())
    
    # Initialize generation status
    generations[generation_id] = {
        "id": generation_id,
        "filename": file.filename,
        "status": "processing",
        "type": "flashcards",
        "created_at": datetime.now().isoformat(),
        "flashcards": [],
        "error": None,
        "progress": 0
    }
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    # Start background processing
    background_tasks.add_task(process_flashcards, generation_id, tmp_file_path, file.filename)
    
    return {"generation_id": generation_id, "status": "processing"}

@app.post("/api/generate-summary")
async def generate_summary(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    config: str = Form(None)
):
    """Handle file upload and start summary generation with configuration"""
    
    # Parse configuration
    summary_config = {}
    if config:
        try:
            import json
            summary_config = json.loads(config)
            logger.info(f"📋 Received config: {summary_config}")
        except json.JSONDecodeError:
            logger.warning("Failed to parse config JSON, using defaults")
    
    # Set defaults for missing config values
    summary_config = {
        "model": summary_config.get("model", "qwen/qwen3-30b-a3b-2507"),
        "chunkSize": summary_config.get("chunkSize", 200),
        "overlapWords": summary_config.get("overlapWords", 10),
        "summaryLength": summary_config.get("summaryLength", 120),
        "finalSummaryLength": summary_config.get("finalSummaryLength", 350),
        "processingQuality": summary_config.get("processingQuality", "balanced")
    }
    
    # Validate file type
    allowed_extensions = {'.md', '.txt', '.pdf', '.docx', '.html'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique ID for this generation
    generation_id = str(uuid.uuid4())
    
    # Initialize generation status with config
    generations[generation_id] = {
        "id": generation_id,
        "filename": file.filename,
        "status": "processing",
        "type": "summary",
        "created_at": datetime.now().isoformat(),
        "config": summary_config,
        "summary": "",
        "error": None,
        "progress": 0
    }
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    # Start background processing with config
    background_tasks.add_task(process_summary, generation_id, tmp_file_path, file.filename, summary_config)
    
    return {"generation_id": generation_id, "status": "processing", "config": summary_config}

@app.get("/api/status/{generation_id}")
async def get_status(generation_id: str):
    """Get the current status of generation (flashcards or summary)"""
    if generation_id not in generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation = generations[generation_id]
    
    # Add result_url based on type and status
    if generation["status"] == "completed":
        generation_type = generation.get("type", "flashcards")
        if generation_type == "summary":
            generation["result_url"] = f"/summary-results/{generation_id}"
        else:
            generation["result_url"] = f"/results/{generation_id}"
    
    return generation

@app.get("/api/download/{generation_id}")
async def download_flashcards(generation_id: str):
    """Download generated flashcards as JSON"""
    if generation_id not in generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation = generations[generation_id]
    if generation["status"] != "completed":
        raise HTTPException(status_code=400, detail="Generation not completed")
    
    # Format for download
    download_data = {
        "title": f"Flashcards from {generation['filename']}",
        "created_at": generation["created_at"],
        "flashcards": generation["flashcards"]
    }
    
    return JSONResponse(
        content=download_data,
        headers={
            "Content-Disposition": f"attachment; filename=flashcards_{generation_id[:8]}.json"
        }
    )

async def process_flashcards(generation_id: str, file_path: str, filename: str):
    """Background task to process flashcards"""
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Starting flashcard generation for {filename}")
        
        # Update progress
        generations[generation_id]["progress"] = 10
        logger.info(f"Progress: 10% - Initializing")
        
        # Determine source type
        extension = Path(filename).suffix.lower()
        source_type_map = {
            '.md': SourceType.MARKDOWN,
            '.txt': SourceType.TXT,
            '.pdf': SourceType.PDF,
            '.docx': SourceType.DOCX,
            '.html': SourceType.HTML
        }
        
        source_type = source_type_map.get(extension, SourceType.TXT)
        logger.info(f"Detected source type: {source_type} for extension {extension}")
        
        # Initialize pipeline
        pipeline = FlashcardPipeline()
        generations[generation_id]["progress"] = 30
        logger.info(f"Progress: 30% - Pipeline initialized")
        
        # Load document
        logger.info(f"Loading document from: {file_path}")
        source = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: pipeline.load_source(file_path, source_type)
        )
        generations[generation_id]["progress"] = 50
        logger.info(f"Progress: 50% - Document loaded: {source.title}")
        
        # Generate flashcards
        logger.info(f"Starting flashcard generation...")
        deck = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: pipeline.generate_flashcards(source)
        )
        generations[generation_id]["progress"] = 90
        logger.info(f"Progress: 90% - Generated {len(deck.cards)} flashcards")
        
        # Format flashcards for display
        flashcards = []
        for card in deck.cards:
            flashcards.append({
                "id": str(card.id),
                "front": card.front,
                "back": card.back,
                "chunk_id": str(card.chunk_id)
            })
        
        # Update final status
        end_time = time.time()
        processing_time = end_time - start_time
        
        generations[generation_id].update({
            "status": "completed",
            "flashcards": flashcards,
            "progress": 100,
            "total_cards": len(flashcards),
            "processing_time": round(processing_time, 2),
            "type": "flashcards"
        })
        
        logger.info(f"Successfully completed flashcard generation: {len(flashcards)} cards created")
        
    except Exception as e:
        logger.error(f"Flashcard generation failed: {str(e)}", exc_info=True)
        generations[generation_id].update({
            "status": "error",
            "error": str(e),
            "progress": 0
        })
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp file {file_path}: {e}")

async def process_summary(generation_id: str, file_path: str, filename: str, config: dict = None):
    """Background task to process document summary with configuration"""
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Starting summary generation for {filename} with config: {config}")
        
        # Use config values or defaults
        if config is None:
            config = {}
        
        model_name = config.get("model", "qwen3-40b")
        chunk_size = config.get("chunkSize", 200)
        overlap_words = config.get("overlapWords", 10)
        summary_length = config.get("summaryLength", 120)
        final_summary_length = config.get("finalSummaryLength", 350)
        processing_quality = config.get("processingQuality", "balanced")
        
        logger.info(f"🔧 Using model: {model_name}, chunk_size: {chunk_size}, overlap: {overlap_words}")
        
        # Update progress
        generations[generation_id]["progress"] = 10
        logger.info(f"Progress: 10% - Initializing summary generation")
        
        # Determine source type
        extension = Path(filename).suffix.lower()
        source_type_map = {
            '.md': SourceType.MARKDOWN,
            '.txt': SourceType.TXT,
            '.pdf': SourceType.PDF,
            '.docx': SourceType.DOCX,
            '.html': SourceType.HTML
        }
        
        source_type = source_type_map.get(extension, SourceType.TXT)
        logger.info(f"Detected source type: {source_type} for extension {extension}")
        
        # Initialize pipeline for document processing with custom chunk size
        pipeline = FlashcardPipeline()
        
        # Update chunker settings if available
        if hasattr(pipeline, 'chunker'):
            pipeline.chunker.chunk_size = chunk_size
            pipeline.chunker.overlap = overlap_words
            logger.info(f"Updated chunker: size={chunk_size}, overlap={overlap_words}")
        
        generations[generation_id]["progress"] = 25
        logger.info(f"Progress: 25% - Pipeline initialized")
        
        # Load document
        logger.info(f"Loading document from: {file_path}")
        source = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: pipeline.load_source(file_path, source_type)
        )
        generations[generation_id]["progress"] = 40
        logger.info(f"Progress: 40% - Document loaded: {source.title}")
        
        # Process document (extract, clean, chunk) with custom settings
        logger.info(f"Processing document chunks with size={chunk_size}, overlap={overlap_words}...")
        chunks = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: pipeline.process_text(source)
        )
        generations[generation_id]["progress"] = 60
        logger.info(f"Progress: 60% - Generated {len(chunks)} chunks for summarization")
        
        # Generate summaries from chunks using configured model
        logger.info(f"Starting AI summarization with model: {model_name}")
        
        # For large documents (>20 chunks), use advanced summarization strategy
        chunk_summaries = []  # Initialize for statistics calculation
        
        if len(chunks) > 20:
            logger.info(f"Large document detected ({len(chunks)} chunks), using advanced summarization strategy")
            from ..llm.advanced_summarizer import AdvancedSummarizer
            advanced_summarizer = AdvancedSummarizer()
            final_summary = await advanced_summarizer.extract_and_summarize(chunks, final_summary_length)
            generations[generation_id]["progress"] = 95
            logger.info(f"Progress: 95% - Advanced summarization complete: {len(final_summary)} characters")
            # For advanced summarization, we don't have individual chunk summaries, keep empty list
        else:
            # For smaller documents, use the traditional approach with improved combination
            summary_generator = SummaryGenerator()
            chunk_summaries = await summary_generator.generate_summaries_from_chunks(chunks)
            generations[generation_id]["progress"] = 80
            logger.info(f"Progress: 80% - Generated {len([s for s in chunk_summaries if s])} chunk summaries")
            
            # Combine summaries into final summary with configured length
            logger.info(f"Combining summaries with target length: {final_summary_length}")
            summary_combiner = SummaryCombiner()
            final_summary = await summary_combiner.hybrid_combine(
                chunk_summaries, 
                use_ai=True, 
                target_length=final_summary_length
            )
            generations[generation_id]["progress"] = 95
            logger.info(f"Progress: 95% - Final summary created: {len(final_summary)} characters")
        
        # Calculate statistics
        valid_summaries = [s.strip() for s in chunk_summaries if s and s.strip()]
        # Get original word count from the source document content
        original_word_count = len(source.content.split()) if hasattr(source, 'content') else 0
        final_word_count = len(final_summary.split())
        compression_ratio = round((final_word_count / max(original_word_count, 1)) * 100, 1)
        
        # Update final status
        end_time = time.time()
        processing_time = end_time - start_time
        
        generations[generation_id].update({
            "status": "completed",
            "summary": final_summary,
            "progress": 100,
            "chunks_count": len(chunks),
            "word_count": final_word_count,
            "original_word_count": original_word_count,
            "compression_ratio": compression_ratio,
            "processing_time": round(processing_time, 2),
            "type": "summary"
        })
        
        logger.info(f"Successfully completed summary generation: {final_word_count} words, {compression_ratio}% compression")
        
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}", exc_info=True)
        generations[generation_id].update({
            "status": "failed",
            "error": str(e),
            "progress": 0,
            "type": "summary"
        })
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp file {file_path}: {e}")


@app.get("/api/export/anki/{generation_id}")
async def export_anki(generation_id: str):
    """Export flashcards to Anki format (.apkg file)."""
    from fastapi.responses import FileResponse
    from ..export.anki import create_anki_export
    
    if generation_id not in generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation = generations[generation_id]
    
    if generation["status"] != "completed":
        raise HTTPException(status_code=400, detail="Generation not completed yet")
    
    if generation.get("type") != "flashcards":
        raise HTTPException(status_code=400, detail="Generation is not flashcards")
    
    try:
        # Get the cards from the generation
        cards_data = generation.get("flashcards", [])
        if not cards_data:
            raise HTTPException(status_code=400, detail="No cards found")
        
        # Convert dict cards back to Card objects
        from ..schemas import Card
        cards = []
        for card_data in cards_data:
            # Handle the card data format from the generation
            if isinstance(card_data, dict):
                card = Card(
                    front=card_data.get("front", ""),
                    back=card_data.get("back", ""),
                    tags=[]  # Tags are not stored in the current format
                )
            else:
                # If it's already a Card object
                card = card_data
            cards.append(card)
        
        # Generate deck name from source
        source_name = generation.get("source_name", "Unknown Source")
        deck_name = f"Flashcards - {source_name}"
        
        # Create temporary file for export
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        output_file = temp_dir / f"flashcards_{generation_id}.apkg"
        
        # Export to Anki format
        anki_file = create_anki_export(
            cards=cards,
            deck_name=deck_name,
            output_path=output_file,
            source_name=source_name
        )
        
        # Return the file as download
        return FileResponse(
            path=str(anki_file),
            filename=f"{deck_name.replace(' ', '_')}.apkg",
            media_type='application/octet-stream',
            headers={"Content-Disposition": f"attachment; filename={deck_name.replace(' ', '_')}.apkg"}
        )
        
    except Exception as e:
        logger.error(f"Anki export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
