"""
Professional FastAPI Web Application for AI Flashcards Generator
Modern, responsive design with white and purple theme
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
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

@app.get("/api/status/{generation_id}")
async def get_status(generation_id: str):
    """Get the current status of flashcard generation"""
    if generation_id not in generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    return generations[generation_id]

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
            "processing_time": round(processing_time, 2)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
