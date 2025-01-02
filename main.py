from fastapi import FastAPI, Request, Form, HTTPException, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any
from podcastfy.client import generate_podcast
import os
import tempfile
import json
from pydantic import BaseModel, Field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load available voices from JSON file
try:
    with open("./VOICE_DATA_STRUCTURED.json", "r") as f:
        AVAILABLE_VOICES = json.load(f)
    logger.info("Voice data loaded successfully")
except Exception as e:
    logger.error(f"Error loading voice data: {str(e)}")
    AVAILABLE_VOICES = {
        "English (US)": {
            "languageCode": "en-US",
            "types": {
                "Standard": [
                    {"name": "en-US-Standard-A", "gender": "MALE"},
                    {"name": "en-US-Standard-B", "gender": "MALE"},
                    {"name": "en-US-Standard-C", "gender": "FEMALE"}
                ],
                "Premium": [
                    {"name": "en-US-Journey-D", "gender": "MALE"},
                    {"name": "en-US-Journey-O", "gender": "FEMALE"}
                ],
                "Studio": [
                    {"name": "en-US-Studio-O", "gender": "FEMALE"},
                    {"name": "en-US-Studio-Q", "gender": "MALE"}
                ]
            }
        }
    }

app = FastAPI(title="Podcast Generator API")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create necessary directories
Path("data/transcripts").mkdir(parents=True, exist_ok=True)
Path("data/audio").mkdir(parents=True, exist_ok=True)

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class VoiceDetails(BaseModel):
    name: str
    gender: Gender

class VoiceTypes(BaseModel):
    Standard: List[VoiceDetails] = []
    Premium: List[VoiceDetails] = []
    Studio: List[VoiceDetails] = []

class LanguageVoices(BaseModel):
    languageCode: str
    types: VoiceTypes

def validate_voice(voice_name: str) -> bool:
    """Validate if a voice name exists in the available voices."""
    for language in AVAILABLE_VOICES.values():
        for type_voices in language["types"].values():
            if any(voice["name"] == voice_name for voice in type_voices):
                return True
    return False

class VoiceConfiguration(BaseModel):
    question: str
    answer: str

class TTSModelConfig(BaseModel):
    default_voices: VoiceConfiguration
    model: Optional[str] = None

class TextToSpeechConfig(BaseModel):
    default_tts_model: str = "openai"
    output_directories: dict = {
        "transcripts": "./data/transcripts",
        "audio": "./data/audio"
    }
    elevenlabs: TTSModelConfig = Field(
        default_factory=lambda: TTSModelConfig(
            default_voices=VoiceConfiguration(question="Chris", answer="Jessica"),
            model="eleven_multilingual_v2"
        )
    )
    openai: TTSModelConfig = Field(
        default_factory=lambda: TTSModelConfig(
            default_voices=VoiceConfiguration(question="echo", answer="shimmer"),
            model="tts-1-hd"
        )
    )
    edge: TTSModelConfig = Field(
        default_factory=lambda: TTSModelConfig(
            default_voices=VoiceConfiguration(question="en-US-JennyNeural", answer="en-US-EricNeural")
        )
    )
    gemini: TTSModelConfig = Field(
        default_factory=lambda: TTSModelConfig(
            default_voices=VoiceConfiguration(question="en-US-Journey-D", answer="en-US-Journey-O")
        )
    )
    geminimulti: TTSModelConfig = Field(
        default_factory=lambda: TTSModelConfig(
            default_voices=VoiceConfiguration(question="en-US-Studio-Q", answer="en-US-Studio-O"),
            model="en-US-Studio-MultiSpeaker"
        )
    )
    audio_format: str = "mp3"
    temp_audio_dir: str = "data/audio/tmp/"
    ending_message: str = "Thanks for listening!"

class ConversationConfig(BaseModel):
    conversation_style: List[str] = ["engaging", "fast-paced", "enthusiastic"]
    roles_person1: str = "main summarizer"
    roles_person2: str = "questioner/clarifier"
    dialogue_structure: List[str] = ["Introduction", "Main Content Summary", "Conclusion"]
    podcast_name: str = "PODCASTIFY"
    podcast_tagline: str = "Your Personal Generative AI Podcast"
    output_language: str = "English"
    engagement_techniques: List[str] = ["rhetorical questions", "anecdotes", "analogies", "humor"]
    creativity: int = Field(default=1, ge=0, le=1)
    user_instructions: str = ""
    max_num_chunks: int = Field(default=8, ge=1)
    min_chunk_size: int = Field(default=600, ge=100)

class TranscriptRequest(BaseModel):
    urls: Optional[List[str]] = None
    url_file: Optional[str] = None
    text: Optional[str] = None
    topic: Optional[str] = None
    image_paths: Optional[List[str]] = None
    llm_model_name: Optional[str] = None
    api_key_label: Optional[str] = None
    is_local: bool = False
    longform: bool = False
    conversation_config: ConversationConfig = Field(default_factory=ConversationConfig)
    text_to_speech: TextToSpeechConfig = Field(default_factory=TextToSpeechConfig)

class AudioRequest(BaseModel):
    transcript_file: str
    text_to_speech: TextToSpeechConfig
    llm_model_name: Optional[str] = None
    api_key_label: Optional[str] = None
    is_local: bool = False
    longform: bool = False

class TranscriptGenerator:
    @staticmethod
    async def generate(params: TranscriptRequest) -> str:
        try:
            logger.info(f"Generating transcript with parameters: {params}")
            
            # Convert conversation_config to dict for the generate_podcast function
            conversation_config = params.conversation_config.dict()
            
            transcript_file = generate_podcast(
                urls=params.urls,
                url_file=params.url_file,
                text=params.text,
                topic=params.topic,
                image_paths=params.image_paths,
                transcript_only=True,
                conversation_config=conversation_config,
                is_local=params.is_local,
                llm_model_name=params.llm_model_name,
                api_key_label=params.api_key_label,
                longform=params.longform
            )
            
            logger.info(f"Transcript generated successfully: {transcript_file}")
            return transcript_file
        except Exception as e:
            logger.error(f"Error generating transcript: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

class AudioGenerator:
    @staticmethod
    async def generate(transcript_file: str, params: AudioRequest) -> str:
        try:
            logger.info(f"Generating audio for transcript file: {transcript_file}")
            
            # Validate voices before generation
            tts_model = params.text_to_speech.default_tts_model
            model_config = getattr(params.text_to_speech, tts_model)
            
            if not model_config:
                raise HTTPException(status_code=400, detail=f"Invalid TTS model: {tts_model}")
                
            question_voice = model_config.default_voices.question
            answer_voice = model_config.default_voices.answer
            
            if not validate_voice(question_voice):
                raise HTTPException(status_code=400, detail=f"Invalid question voice: {question_voice}")
            if not validate_voice(answer_voice):
                raise HTTPException(status_code=400, detail=f"Invalid answer voice: {answer_voice}")
            
            # Create temporary directory structure
            temp_dir = os.path.join(os.getcwd(), "data", "audio", "tmp")
            os.makedirs(temp_dir, exist_ok=True)
            os.environ['TMPDIR'] = temp_dir
            
            audio_file = generate_podcast(
                transcript_file=transcript_file,
                tts_model=tts_model,
                conversation_config=params.text_to_speech.dict(),
                is_local=params.is_local,
                llm_model_name=params.llm_model_name,
                api_key_label=params.api_key_label,
                longform=params.longform
            )
            logger.info(f"Audio generated successfully: {audio_file}")
            return audio_file
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-transcript")
async def generate_transcript(request: TranscriptRequest = Body(...)):
    try:
        transcript_file = await TranscriptGenerator.generate(request)
        
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
async def generate_audio(request: AudioRequest = Body(...)):
    try:
        if not Path(request.transcript_file).exists():
            raise HTTPException(status_code=400, detail=f"Transcript file not found: {request.transcript_file}")
            
        audio_file = await AudioGenerator.generate(request.transcript_file, request)
        
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