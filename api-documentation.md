# Podcast Generator API Documentation

## Overview

This FastAPI application provides a service for generating podcasts from various input sources, including URLs, text, and images. The application supports multiple text-to-speech (TTS) providers and offers customizable voice configurations.

## Core Components

### 1. Configuration and Setup

The application initializes with several key components:

- FastAPI application instance with title "Podcast Generator API"
- Jinja2 templates for web interface
- Static file serving
- Directory structure for storing transcripts and audio files
- Voice data loaded from JSON file (with fallback configuration)

### 2. Data Models

#### Voice Configuration

- `Gender`: Enumeration for voice gender (MALE/FEMALE)
- `VoiceSelection`: Configuration for individual voice selection
  - language: e.g., "English (US)"
  - type: Voice type (Standard/Premium/Studio)
  - name: Specific voice identifier
  - gender: Voice gender

#### Text-to-Speech Configuration

- `TTSModelConfig`: Configuration for specific TTS providers
- `TextToSpeechConfig`: Global TTS settings including:
  - Default TTS model
  - Output directories
  - Provider-specific configurations (Elevenlabs, OpenAI, Edge, Gemini)
  - Audio format settings
  - Temporary directory configuration

#### Conversation Configuration

- `ConversationConfig`: Settings for podcast conversation style
  - Conversation style attributes
  - Role definitions
  - Dialogue structure
  - Engagement techniques
  - Creativity level
  - Output constraints

#### Request Models

- `TranscriptRequest`: Input parameters for transcript generation
- `AudioRequest`: Parameters for audio generation

### 3. Core Functions

#### Transcript Generation

`TranscriptGenerator` class handles:

- Processing input sources (URLs, text, images)
- Generating conversation transcripts
- Error handling and logging

#### Audio Generation

`AudioGenerator` class manages:

- Voice validation
- TTS model configuration
- Audio file generation
- Temporary file management

### 4. API Endpoints

#### Main Endpoints

1. `GET /`: Home page
2. `GET /available-voices`: List all available voices
3. `GET /available-voices/{language}`: Get voices for specific language
4. `POST /generate-transcript`: Generate podcast transcript
5. `POST /generate-audio`: Generate audio from transcript

### 5. Error Handling and Validation

The application implements comprehensive error handling:

- Voice validation before generation
- File existence checks
- Proper HTTP error responses
- Detailed error logging

### 6. Security and File Management

- Secure file handling with proper directory structure
- Temporary file management
- Content-type validation
- Proper file response headers

## Usage Examples

### Generating a Transcript

```python
POST /generate-transcript
{
  "text": "Discuss on the new season 2 of Netflix's Squid Game",
  "conversation_config": {
    "conversation_style": ["engaging", "fast-paced", "enthusiastic"],
    "roles_person1": "main summarizer",
    "roles_person2": "questioner/clarifier",
    "dialogue_structure": [
      "Introduction",
      "Main Content Summary",
      "Conclusion"
    ],
    "podcast_name": "PODCASTER",
    "podcast_tagline": "Your Cloud Ambassadors Personal Generative AI Podcast",
    "output_language": "English",
    "engagement_techniques": [
      "rhetorical questions",
      "anecdotes",
      "analogies",
      "humor"
    ],
    "creativity": 1,
    "user_instructions": "Focus on making the content accessible to a general audience",
    "max_num_chunks": 8,
    "min_chunk_size": 600
  },
  "text_to_speech": {
    "default_tts_model": "gemini",
    "gemini": {
      "default_voices": {
        "question": {
          "language": "English (US)",
          "type": "Studio",
          "name": "en-US-Studio-Q",
          "gender": "MALE"
        },
        "answer": {
          "language": "English (US)",
          "type": "Studio",
          "name": "en-US-Studio-O",
          "gender": "FEMALE"
        }
      }
    }
  }
}
```

### Generating Audio

```python
POST /generate-audio
{
  "transcript_file": "./data/transcripts\\transcript_2f7a215beb844161a97e762544d53cb3.txt",
  "text_to_speech": {
    "default_tts_model": "gemini",
    "gemini": {
      "default_voices": {
        "question": {
          "language": "English (US)",
          "type": "Studio",
          "name": "en-US-Studio-Q",
          "gender": "MALE"
        },
        "answer": {
          "language": "English (US)",
          "type": "Studio",
          "name": "en-US-Studio-O",
          "gender": "FEMALE"
        }
      }
    }
  }
}
```

## Technical Details

### Dependencies

- FastAPI
- Jinja2Templates
- Pydantic
- logging
- pathlib
- uvicorn (for running the server)

### Directory Structure

```
project/
├── main.py
├── data/
│   ├── transcripts/
│   └── audio/
│       └── tmp/
├── templates/
├── static/
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── VOICE_DATA_STRUCTURED.json
```

### Environment Setup

The application requires:

- Python 3.7+
- FastAPI and its dependencies
- Proper file permissions for data directories
- Access to TTS services (Gemini, Elevenlabs, OpenAI, Edge)
