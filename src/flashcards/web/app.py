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

# Import our flashcard generation components
from ..pipeline import FlashcardPipeline
from ..schemas import Source, SourceType

# Initialize FastAPI app with professional metadata
app = FastAPI(
    title="AI Flashcards Generator",
    description="Professional AI-powered flashcard generation from documents",
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
    try:
        # Update progress
        generations[generation_id]["progress"] = 10
        
        # Determine source type
        extension = Path(filename).suffix.lower()
        source_type_map = {
            '.md': SourceType.MARKDOWN,
            '.txt': SourceType.TEXT,
            '.pdf': SourceType.PDF,
            '.docx': SourceType.DOCX,
            '.html': SourceType.HTML
        }
        
        source_type = source_type_map.get(extension, SourceType.TEXT)
        
        # Initialize pipeline
        pipeline = FlashcardPipeline()
        generations[generation_id]["progress"] = 30
        
        # Load document
        source = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: pipeline.load_source(file_path, source_type)
        )
        generations[generation_id]["progress"] = 50
        
        # Generate flashcards
        deck = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: pipeline.generate_flashcards(source)
        )
        generations[generation_id]["progress"] = 90
        
        # Format flashcards for display
        flashcards = []
        for card in deck.cards:
            flashcards.append({
                "id": card.id,
                "front": card.front,
                "back": card.back,
                "chunk_id": card.chunk_id
            })
        
        # Update final status
        generations[generation_id].update({
            "status": "completed",
            "flashcards": flashcards,
            "progress": 100,
            "total_cards": len(flashcards)
        })
        
    except Exception as e:
        generations[generation_id].update({
            "status": "error",
            "error": str(e),
            "progress": 0
        })
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(file_path)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
