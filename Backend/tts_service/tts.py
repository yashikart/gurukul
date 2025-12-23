# TTS Service for Gurukul AI
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyttsx3
import uuid
import os
import sys
from pathlib import Path
from datetime import datetime

# Load environment variables from centralized configuration
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared_config import load_shared_config

# Load centralized configuration
load_shared_config("tts_service")

# Logging
from utils.logging_config import configure_logging
logger = configure_logging("tts_service")

# Import centralized CORS helper
from common.cors import configure_cors

app = FastAPI(title="Gurukul TTS Service", description="Text-to-Speech service for lesson content")

# Configure CORS using centralized helper
configure_cors(app)

# Generic OPTIONS handler for preflight requests
from fastapi import Response

@app.options("/{path:path}")
async def preflight(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": os.getenv("NGROK_URL", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

# Global exception handler for consistent errors
from uuid import uuid4

@app.exception_handler(Exception)
async def _on_error(request, exc):
    trace = str(uuid4())
    logger.exception(f"[{trace}] Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Unexpected error"}, "trace_id": trace})



OUTPUT_DIR = "tts_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Gurukul TTS Service is running",
        "service": "Text-to-Speech",
        "version": "1.0.0",
        "endpoints": {
            "generate": "POST /api/generate - Generate TTS audio from text",
            "get_audio": "GET /api/audio/{filename} - Retrieve audio file",
            "list_files": "GET /api/list-audio-files - List all audio files"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy",
        "service": "TTS Service",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/audio/{filename}")
async def get_audio_file(filename: str):
    """Get audio file by filename"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='audio/mpeg',
        headers={"Cache-Control": "public, max-age=3600"}
    )

@app.get("/api/list-audio-files")
async def list_audio_files():
    """List all available audio files"""
    try:
        files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp3')]
        return {"audio_files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.post("/api/generate")
async def text_to_speech(text: str = Form(...)):
    """Generate TTS audio from text"""
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    if len(text) > 10000:  # Limit text length
        raise HTTPException(status_code=400, detail="Text too long (max 10000 characters)")

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        print(f"Generating TTS for text: {text[:100]}...")

        # Initialize TTS engine
        engine = pyttsx3.init()

        # Configure TTS settings for better quality
        voices = engine.getProperty('voices')
        if voices:
            # Try to use a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break

        # Set speech rate (words per minute)
        engine.setProperty('rate', 180)  # Slightly slower for clarity

        # Set volume (0.0 to 1.0)
        engine.setProperty('volume', 0.9)

        # Generate audio file
        engine.save_to_file(text, filepath)
        engine.runAndWait()

        # Verify file was created
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Audio generation failed - file not created")

        # Check file size
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            os.remove(filepath)  # Remove empty file
            raise HTTPException(status_code=500, detail="Audio generation failed - empty file")

        print(f"TTS generated successfully: {filename} ({file_size} bytes)")

        return JSONResponse({
            "status": "success",
            "message": "Audio generated successfully",
            "audio_url": f"/api/audio/{filename}",
            "filename": filename,
            "file_size": file_size,
            "text_length": len(text)
        })

    except Exception as e:
        # Clean up failed file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

        logger.exception(f"TTS generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")


@app.post("/api/generate/stream")
async def text_to_speech_stream(text: str = Form(...)):
    """Generate TTS audio and stream directly without saving to disk"""
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    if len(text) > 10000:  # Limit text length
        raise HTTPException(status_code=400, detail="Text too long (max 10000 characters)")

    try:
        import io
        import tempfile
        import wave

        print(f"Generating streaming TTS for text: {text[:100]}...")

        # Initialize TTS engine
        engine = pyttsx3.init()

        # Configure TTS settings for better quality
        voices = engine.getProperty('voices')
        if voices:
            # Try to use a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break

        # Set speech rate (words per minute)
        engine.setProperty('rate', 180)  # Slightly slower for clarity

        # Set volume (0.0 to 1.0)
        engine.setProperty('volume', 0.9)

        # Create temporary file for audio generation
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filepath = temp_file.name

        try:
            # Generate audio to temporary file
            engine.save_to_file(text, temp_filepath)
            engine.runAndWait()

            # Read the generated audio file into memory
            with open(temp_filepath, 'rb') as audio_file:
                audio_data = audio_file.read()

            # Clean up temporary file
            os.unlink(temp_filepath)

            if not audio_data:
                raise HTTPException(status_code=500, detail="Audio generation failed - no data")

            # Create streaming response
            def generate_audio():
                yield audio_data

            return StreamingResponse(
                generate_audio(),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "inline; filename=tts_audio.wav",
                    "Cache-Control": "no-cache",
                    "X-Text-Length": str(len(text))
                }
            )

        except Exception as cleanup_error:
            # Ensure temp file is cleaned up even on error
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
            raise cleanup_error

    except Exception as e:
        logger.exception(f"TTS streaming error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS streaming failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test TTS engine
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        return {
            "status": "healthy",
            "service": "TTS",
            "tts_engine": "pyttsx3",
            "voices_available": len(voices) if voices else 0,
            "output_directory": OUTPUT_DIR,
            "audio_files_count": len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp3')])
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn

    print("Starting Gurukul TTS Service...")
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")

    # Run on all interfaces so it can be accessed from other machines
    uvicorn.run(
        app,
        host="0.0.0.0",  # Listen on all interfaces
        port=8007,       # Use port 8007 for TTS service
        log_level="info"
    )
