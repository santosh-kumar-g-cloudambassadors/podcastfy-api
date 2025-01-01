# from fastapi import FastAPI, Request, Form, HTTPException
# from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse, JSONResponse
# from pathlib import Path
# import os
# import tempfile
# import logging
# from typing import Optional
# from podcastfy.client import generate_podcast

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Podcast Generator API")

# # Setup templates and static files
# templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # Create necessary directories
# Path("data/transcripts").mkdir(parents=True, exist_ok=True)
# Path("data/audio").mkdir(parents=True, exist_ok=True)
# Path("templates").mkdir(exist_ok=True)

# class TranscriptGenerator:
#     @staticmethod
#     async def generate(text: str) -> str:
#         try:
#             logger.info(f"Generating transcript for text: {text}")
#             # Generate transcript using podcastfy
#             transcript_file = generate_podcast(
#                 text=text,
#                 transcript_only=True
#             )
#             logger.info(f"Transcript generated successfully: {transcript_file}")
#             return transcript_file
#         except Exception as e:
#             logger.error(f"Error generating transcript: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"Failed to generate transcript: {str(e)}")

# class AudioGenerator:
#     @staticmethod
#     async def generate(transcript_file: str) -> str:
#         try:
#             logger.info(f"Generating audio for transcript file: {transcript_file}")
            
#             # Create temporary directory structure
#             temp_dir = os.path.join(os.getcwd(), "data", "audio", "tmp")
#             os.makedirs(temp_dir, exist_ok=True)
            
#             # Set environment variable for temporary directory
#             os.environ['TMPDIR'] = temp_dir
            
#             # Generate audio using podcastfy
#             audio_file = generate_podcast(
#                 transcript_file=transcript_file,
#                 tts_model="gemini"
#             )
#             logger.info(f"Audio generated successfully: {audio_file}")
#             return audio_file
#         except Exception as e:
#             logger.error(f"Error generating audio: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

# @app.get("/")
# async def home(request: Request):
#     return templates.TemplateResponse(
#         "index.html",
#         {"request": request}
#     )

# @app.post("/generate-transcript")
# async def generate_transcript(text: str = Form(...)):
#     try:
#         logger.info("Received request to generate transcript")
#         transcript_file = await TranscriptGenerator.generate(text)
        
#         # Read the transcript content
#         try:
#             with open(transcript_file, 'r', encoding='utf-8', errors='replace') as f:
#                 transcript_content = f.read()
#         except Exception as e:
#             logger.error(f"Error reading transcript file: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"Error reading transcript file: {str(e)}")
        
#         return JSONResponse({
#             "status": "success",
#             "transcript_file": transcript_file,
#             "transcript_content": transcript_content
#         })
#     except Exception as e:
#         logger.error(f"Error in generate_transcript endpoint: {str(e)}")
#         if isinstance(e, HTTPException):
#             raise e
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/generate-audio")
# async def generate_audio(transcript_file: str = Form(...)):
#     try:
#         logger.info("Received request to generate audio")
#         if not Path(transcript_file).exists():
#             raise HTTPException(status_code=400, detail=f"Transcript file not found: {transcript_file}")
            
#         audio_file = await AudioGenerator.generate(transcript_file)
        
#         if not Path(audio_file).exists():
#             raise HTTPException(status_code=500, detail="Generated audio file not found")
            
#         return FileResponse(
#             path=audio_file,
#             media_type="audio/mpeg",
#             filename=Path(audio_file).name,
#             headers={"Content-Disposition": f"attachment; filename={Path(audio_file).name}"}
#         )
#     except Exception as e:
#         logger.error(f"Error in generate_audio endpoint: {str(e)}")
#         if isinstance(e, HTTPException):
#             raise e
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Request, Form, HTTPException, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import logging
from typing import Optional
from podcastfy.client import generate_podcast
import os
import tempfile
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Podcast Generator API")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create necessary directories
Path("data/transcripts").mkdir(parents=True, exist_ok=True)
Path("data/audio").mkdir(parents=True, exist_ok=True)

# Pydantic models for request validation
class TranscriptRequest(BaseModel):
    text: str

class AudioRequest(BaseModel):
    transcript_file: str

class TranscriptGenerator:
    @staticmethod
    async def generate(text: str) -> str:
        try:
            logger.info(f"Generating transcript for text: {text}")
            transcript_file = generate_podcast(
                text=text,
                transcript_only=True
            )
            logger.info(f"Transcript generated successfully: {transcript_file}")
            return transcript_file
        except Exception as e:
            logger.error(f"Error generating transcript: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

class AudioGenerator:
    @staticmethod
    async def generate(transcript_file: str) -> str:
        try:
            logger.info(f"Generating audio for transcript file: {transcript_file}")
            
            # Create temporary directory structure
            temp_dir = os.path.join(os.getcwd(), "data", "audio", "tmp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Set environment variable for temporary directory
            os.environ['TMPDIR'] = temp_dir
            
            audio_file = generate_podcast(
                transcript_file=transcript_file,
                tts_model="gemini"
            )
            logger.info(f"Audio generated successfully: {audio_file}")
            return audio_file
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/generate-transcript")
async def generate_transcript(text: str = Form(None), request: TranscriptRequest = Body(None)):
    try:
        # Handle both form data and JSON requests
        input_text = text if text else request.text if request else None
        if not input_text:
            raise HTTPException(status_code=400, detail="Text is required")
            
        transcript_file = await TranscriptGenerator.generate(input_text)
        
        # Read the transcript content
        try:
            with open(transcript_file, 'r', encoding='utf-8', errors='replace') as f:
                transcript_content = f.read()
        except Exception as e:
            logger.error(f"Error reading transcript file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error reading transcript file: {str(e)}")
        
        return JSONResponse({
            "status": "success",
            "transcript_file": transcript_file,
            "transcript_content": transcript_content
        })
    except Exception as e:
        logger.error(f"Error in generate_transcript endpoint: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-audio")
async def generate_audio(transcript_file: str = Form(None), request: AudioRequest = Body(None)):
    try:
        # Handle both form data and JSON requests
        input_file = transcript_file if transcript_file else request.transcript_file if request else None
        if not input_file:
            raise HTTPException(status_code=400, detail="Transcript file path is required")
            
        if not Path(input_file).exists():
            raise HTTPException(status_code=400, detail=f"Transcript file not found: {input_file}")
            
        audio_file = await AudioGenerator.generate(input_file)
        
        if not Path(audio_file).exists():
            raise HTTPException(status_code=500, detail="Generated audio file not found")
            
        return FileResponse(
            path=audio_file,
            media_type="audio/mpeg",
            filename=Path(audio_file).name,
            headers={"Content-Disposition": f"attachment; filename={Path(audio_file).name}"}
        )
    except Exception as e:
        logger.error(f"Error in generate_audio endpoint: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)