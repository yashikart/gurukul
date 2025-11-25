"""
app.py - FastAPI application for serving the Gurukul Lesson Generator
"""

import os
import logging
from typing import Dict, Any, Optional, List
import sys

# Print Python version for debugging
print(f"Python version: {sys.version}")

# Try importing the necessary packages
try:
    from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks
    from fastapi.responses import FileResponse
    print("FastAPI imported successfully")
except ImportError as e:
    print(f"Error importing FastAPI: {e}")
    sys.exit(1)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
from dotenv import load_dotenv
import uvicorn
import uuid
from datetime import datetime, timedelta
from enum import Enum
import requests
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# In-memory storage for agent data (in production, use a proper database)
agent_outputs = []
agent_logs = []
agent_simulations = {}  # Track active simulations by user_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Simple function to check compute device
def get_compute_device():
    """Get the available compute device (CPU or GPU)"""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            device = f"GPU ({torch.cuda.get_device_name(0)})"
            logger.info(f"GPU available: {device}")
        else:
            device = "CPU"
            logger.info("Using CPU for compute")
        return device, gpu_available
    except Exception as e:
        logger.warning(f"Error checking compute device: {e}")
        return "CPU", False

# Get compute device
device, gpu_available = get_compute_device()

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Gurukul AI-Lesson Generator",
    description="Generate structured lessons based on ancient Indian wisdom texts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add middleware to log HTTP requests and status codes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log the request with a distinctive prefix
    request_message = f">>> HTTP REQUEST: {request.method} {request.url.path} - Query params: {request.query_params}"
    logger.info(request_message)
    print(request_message)  # Print directly to console

    # Process the request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log the response status code and processing time with a distinctive prefix
    response_message = f"<<< HTTP RESPONSE: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s"
    logger.info(response_message)
    print(response_message)  # Print directly to console

    return response

class CreateLessonRequest(BaseModel):
    subject: str
    topic: str
    user_id: str
    include_wikipedia: bool = True
    force_regenerate: bool = True  # Changed default to True for dynamic generation

class WikipediaInfo(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    related_articles: List[str] = []

class LessonResponse(BaseModel):
    title: str
    shloka: str
    translation: str
    explanation: str
    activity: str
    question: str
    wikipedia_info: Optional[WikipediaInfo] = None

# New models for async lesson generation
class GenerationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class LessonGenerationTask(BaseModel):
    task_id: str
    subject: str
    topic: str
    user_id: str
    status: GenerationStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    include_wikipedia: bool = True

class LessonGenerationResponse(BaseModel):
    task_id: str
    status: GenerationStatus
    message: str
    estimated_completion_time: Optional[str] = None
    poll_url: str

class LessonStatusResponse(BaseModel):
    task_id: str
    status: GenerationStatus
    progress_message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    lesson_data: Optional[LessonResponse] = None

# Pydantic model for data forwarding to 192.168.0.119
class DataForwardRequest(BaseModel):
    data: Dict[str, Any]
    endpoint: Optional[str] = "/"
    method: Optional[str] = "POST"
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = 30
    user_id: Optional[str] = "guest-user"
    description: Optional[str] = None

# Pydantic model for TTS generation request
class TTSGenerationRequest(BaseModel):
    text: str
    user_id: Optional[str] = "guest-user"
    description: Optional[str] = None
    timeout: Optional[int] = 60  # TTS might take longer

# Pydantic model for lesson TTS generation
class LessonTTSRequest(BaseModel):
    task_id: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    user_id: Optional[str] = "guest-user"
    include_sections: Optional[List[str]] = ["title", "shloka", "translation", "explanation", "activity", "question"]
    format_style: Optional[str] = "complete"  # "complete", "sections", "summary"
    auto_generate: Optional[bool] = True  # Whether to auto-generate TTS during lesson creation

# Global storage for generation tasks (in production, use Redis or database)
generation_tasks: Dict[str, LessonGenerationTask] = {}
generation_results: Dict[str, Dict[str, Any]] = {}

# TTS formatting and generation functions
def format_lesson_for_tts(lesson_data: Dict[str, Any], format_style: str = "complete", include_sections: List[str] = None) -> str:
    """
    Format lesson data for TTS conversion

    Args:
        lesson_data: The lesson data dictionary
        format_style: How to format the text ("complete", "sections", "summary")
        include_sections: Which sections to include in TTS

    Returns:
        str: Formatted text ready for TTS conversion
    """
    if include_sections is None:
        include_sections = ["title", "shloka", "translation", "explanation", "activity", "question"]

    formatted_text = ""

    if format_style == "complete":
        # Complete lesson format with natural speech flow
        if "title" in include_sections and lesson_data.get("title"):
            formatted_text += f"Welcome to today's lesson: {lesson_data['title']}.\n\n"

        if "shloka" in include_sections and lesson_data.get("shloka"):
            formatted_text += f"Let us begin with a sacred verse: {lesson_data['shloka']}.\n\n"

        if "translation" in include_sections and lesson_data.get("translation"):
            formatted_text += f"The meaning of this verse is: {lesson_data['translation']}.\n\n"

        if "explanation" in include_sections and lesson_data.get("explanation"):
            formatted_text += f"Now, let me explain this concept in detail. {lesson_data['explanation']}\n\n"

        if "activity" in include_sections and lesson_data.get("activity"):
            formatted_text += f"Here is an activity for you to practice: {lesson_data['activity']}\n\n"

        if "question" in include_sections and lesson_data.get("question"):
            formatted_text += f"Finally, please reflect on this question: {lesson_data['question']}\n\n"

        formatted_text += "Thank you for your attention. May this knowledge serve you well."

    elif format_style == "sections":
        # Section-by-section format
        for section in include_sections:
            if lesson_data.get(section):
                section_name = section.replace("_", " ").title()
                formatted_text += f"{section_name}: {lesson_data[section]}\n\n"

    elif format_style == "summary":
        # Brief summary format
        if lesson_data.get("title"):
            formatted_text += f"Lesson Summary: {lesson_data['title']}. "
        if lesson_data.get("translation"):
            formatted_text += f"Key teaching: {lesson_data['translation']}. "
        if lesson_data.get("explanation"):
            # Take first 200 characters of explanation
            explanation_summary = lesson_data['explanation'][:200] + "..." if len(lesson_data['explanation']) > 200 else lesson_data['explanation']
            formatted_text += f"Overview: {explanation_summary}"

    # Clean up the text for better TTS
    formatted_text = formatted_text.replace("\n\n", ". ")
    formatted_text = formatted_text.replace("\n", " ")
    formatted_text = formatted_text.strip()

    return formatted_text

async def send_to_tts_service(text: str, user_id: str = "guest-user", description: str = None) -> Dict[str, Any]:
    """
    Send text to the external TTS service at 192.168.0.119:8001

    Args:
        text: Text to convert to speech
        user_id: ID of the user requesting TTS
        description: Description of the TTS request

    Returns:
        Dict: Response from TTS service including audio file information
    """
    try:
        target_server = "192.168.0.119"
        target_port = 8001
        tts_url = f"http://{target_server}:{target_port}/api/generate"

        logger.info(f"Sending text to TTS service: {tts_url}")
        logger.info(f"Text length: {len(text)} characters, User: {user_id}")
        if description:
            logger.info(f"TTS Description: {description}")

        # Prepare form data as expected by the TTS service
        form_data = {
            'text': text
        }

        # Add metadata headers
        headers = {
            "User-Agent": "Gurukul-AI-TTS/1.0",
            "X-Source-System": "gurukul-ai",
            "X-User-ID": user_id,
            "X-Request-Type": "lesson-tts"
        }

        # Make the request to TTS service
        start_time = time.time()

        response = requests.post(
            tts_url,
            data=form_data,  # Use data parameter for form data
            headers=headers,
            timeout=60  # TTS generation might take longer
        )

        end_time = time.time()
        response_time = end_time - start_time

        logger.info(f"TTS service response - Status: {response.status_code}, Time: {response_time:.3f}s")

        if response.status_code == 200:
            try:
                tts_result = response.json()

                # Enhance the response with additional metadata
                enhanced_result = {
                    "status": "success",
                    "message": "TTS generation completed successfully",
                    "tts_service": {
                        "server": f"{target_server}:{target_port}",
                        "response_time_seconds": round(response_time, 3),
                        "text_length": len(text),
                        "text_preview": text[:100] + "..." if len(text) > 100 else text
                    },
                    "audio_info": tts_result,
                    "access_info": {
                        "audio_url": f"http://192.168.0.83:8000/api/audio/{tts_result.get('filename', '')}" if tts_result.get('filename') else None,
                        "direct_url": f"http://{target_server}:{target_port}/api/audio/{tts_result.get('filename', '')}" if tts_result.get('filename') else None
                    },
                    "request_info": {
                        "user_id": user_id,
                        "description": description,
                        "timestamp": datetime.now().isoformat()
                    }
                }

                logger.info(f"TTS generation successful - Audio file: {tts_result.get('filename', 'Unknown')}")
                return enhanced_result

            except ValueError as e:
                logger.error(f"Failed to parse TTS service JSON response: {e}")
                return {
                    "status": "error",
                    "message": "TTS service returned invalid JSON",
                    "error_details": str(e),
                    "raw_response": response.text[:500]
                }
        else:
            logger.error(f"TTS service returned error: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"TTS service returned error: {response.status_code}",
                "tts_service": {
                    "server": f"{target_server}:{target_port}",
                    "response_time_seconds": round(response_time, 3),
                    "status_code": response.status_code
                },
                "error_details": response.text[:500] if response.text else "No error details"
            }

    except requests.Timeout:
        logger.error(f"Timeout sending text to TTS service")
        return {
            "status": "timeout",
            "message": "TTS service request timed out",
            "tts_service": {
                "server": f"{target_server}:{target_port}",
                "timeout_seconds": 60
            },
            "suggestion": "The text might be too long or the TTS service is overloaded"
        }

    except requests.ConnectionError:
        logger.error(f"Connection error sending text to TTS service")
        return {
            "status": "connection_error",
            "message": "Could not connect to TTS service",
            "tts_service": {
                "server": f"{target_server}:{target_port}"
            },
            "suggestion": "Check if the TTS service is running and accessible"
        }

    except Exception as e:
        logger.error(f"Unexpected error sending text to TTS service: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "error_details": str(e)
        }

# Background task function for lesson generation
async def generate_lesson_background(task_id: str, subject: str, topic: str, user_id: str, include_wikipedia: bool = True):
    """
    Background task to generate a lesson asynchronously
    """
    try:
        # Update task status to in_progress
        if task_id in generation_tasks:
            generation_tasks[task_id].status = GenerationStatus.IN_PROGRESS
            logger.info(f"Starting background generation for task {task_id}: {subject}/{topic}")

        # Generate the lesson using enhanced lesson generator with force_fresh=True for dynamic generation
        try:
            from generate_lesson_enhanced import create_enhanced_lesson
            generated_lesson = create_enhanced_lesson(subject, topic)
        except ImportError:
            # Enhanced module is not available
            logger.error("Enhanced lesson generator module not available")
            raise Exception("Enhanced lesson generator module not available")
        except ValueError as e:
            # No content sources available (Ollama not working, no Wikipedia content)
            logger.error(f"Unable to generate lesson content: {str(e)}")
            raise Exception(f"Unable to generate lesson content: {str(e)}")
        except Exception as e:
            # Other generation errors
            logger.error(f"Error in lesson generation: {str(e)}")
            raise Exception(f"Error in lesson generation: {str(e)}")

        # Add user information to the generated lesson
        if isinstance(generated_lesson, dict):
            generated_lesson["created_by"] = user_id
            generated_lesson["generation_method"] = "async_background"
            generated_lesson["task_id"] = task_id

        # Store the result
        generation_results[task_id] = generated_lesson

        # Automatically generate TTS for the lesson
        try:
            logger.info(f"Starting automatic TTS generation for task {task_id}")

            # Format the lesson text for TTS
            tts_text = format_lesson_for_tts(
                generated_lesson,
                format_style="complete",
                include_sections=["title", "shloka", "translation", "explanation", "activity", "question"]
            )

            # Send to TTS service
            tts_result = await send_to_tts_service(
                text=tts_text,
                user_id=user_id,
                description=f"Auto-generated TTS for lesson: {subject}/{topic}"
            )

            # Add TTS information to the lesson data
            generated_lesson["tts_info"] = tts_result

            if tts_result.get("status") == "success":
                logger.info(f"TTS generation successful for task {task_id}: {tts_result.get('audio_info', {}).get('filename', 'Unknown')}")
                generated_lesson["audio_available"] = True
                generated_lesson["audio_filename"] = tts_result.get('audio_info', {}).get('filename')
                generated_lesson["audio_url"] = tts_result.get('access_info', {}).get('audio_url')
            else:
                logger.warning(f"TTS generation failed for task {task_id}: {tts_result.get('message', 'Unknown error')}")
                generated_lesson["audio_available"] = False
                generated_lesson["tts_error"] = tts_result.get('message', 'TTS generation failed')

        except Exception as e:
            logger.error(f"Error during automatic TTS generation for task {task_id}: {str(e)}")
            generated_lesson["audio_available"] = False
            generated_lesson["tts_error"] = f"TTS generation error: {str(e)}"

        # Update the stored result with TTS information
        generation_results[task_id] = generated_lesson

        # Update task status to completed
        if task_id in generation_tasks:
            generation_tasks[task_id].status = GenerationStatus.COMPLETED
            generation_tasks[task_id].completed_at = datetime.now()
            logger.info(f"Completed background generation for task {task_id}: {generated_lesson.get('title', 'Untitled')}")

    except Exception as e:
        logger.error(f"Error in background generation for task {task_id}: {str(e)}")

        # Update task status to failed
        if task_id in generation_tasks:
            generation_tasks[task_id].status = GenerationStatus.FAILED
            generation_tasks[task_id].error_message = str(e)
            generation_tasks[task_id].completed_at = datetime.now()

# Cleanup function to remove old completed tasks
def cleanup_old_tasks():
    """Remove tasks older than 1 hour to prevent memory leaks"""
    cutoff_time = datetime.now() - timedelta(hours=1)
    tasks_to_remove = []

    for task_id, task in generation_tasks.items():
        if task.completed_at and task.completed_at < cutoff_time:
            tasks_to_remove.append(task_id)

    for task_id in tasks_to_remove:
        generation_tasks.pop(task_id, None)
        generation_results.pop(task_id, None)
        logger.info(f"Cleaned up old task: {task_id}")

@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running
    """
    # Check GPU status
    try:
        import torch
        gpu_status = "available" if torch.cuda.is_available() else "unavailable"
        device = f"GPU ({torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else "CPU"
    except Exception:
        gpu_status = "error"
        device = "CPU (GPU check failed)"

    return {
        "message": "Welcome to the Gurukul AI-Lesson Generator API",
        "status": "Service is running - check /llm_status for details",
        "compute": {
            "device": device,
            "gpu_status": gpu_status
        },
        "endpoints": {
            "get_lesson": "/lessons/{subject}/{topic} - Retrieve existing lesson",
            "create_lesson_async": "/lessons - Create new lesson (POST, async) - Now includes automatic TTS!",
            "check_generation_status": "/lessons/status/{task_id} - Check lesson generation status",
            "list_active_tasks": "/lessons/tasks - List active generation tasks",
            "search_lessons": "/search_lessons?query=sound",
            "llm_status": "/llm_status",
            "generate_lesson_tts": "/lessons/generate-tts - Generate TTS for existing lesson (POST)",
            "generate_text_tts": "/tts/generate - Generate TTS from arbitrary text (POST)",
            "forward_data": "/forward_data - Send data to external server 192.168.0.119:8001 (POST)",
            "send_lesson_external": "/send_lesson_to_external - Send lesson to external server (POST)",
            "check_external_server": "/check_external_server - Check external server connectivity",
            "get_audio_file": "/api/audio/{filename} - Get audio file from 192.168.0.119:8001",
            "list_audio_files": "/api/audio-files - List available audio files from external server",
            "get_agent_output": "/get_agent_output - Get agent outputs",
            "agent_logs": "/agent_logs - Get agent logs",
            "agent_message": "/agent_message - Send message to agent (POST)",
            "start_agent_simulation": "/start_agent_simulation - Start agent simulation (POST)",
            "stop_agent_simulation": "/stop_agent_simulation - Stop agent simulation (POST)",
            "reset_agent_simulation": "/reset_agent_simulation - Reset agent simulation (POST)",
            "documentation": "/docs"
        },
        "tts_integration": {
            "automatic_tts": "Lessons now automatically generate TTS audio during creation",
            "tts_server": "192.168.0.119:8001",
            "audio_access": "Audio files accessible via /api/audio/{filename}",
            "supported_formats": ["complete lesson", "section-by-section", "summary"]
        }
    }

@app.get("/llm_status")
async def llm_status():
    """
    Endpoint to check the status of the LLM service
    """
    try:
        # Check if vector store exists
        vector_store_path = os.getenv("CHROMA_PERSIST_DIRECTORY", "knowledge_store")
        vector_store_status = "connected" if os.path.exists(vector_store_path) else "not found"

        # Check for available LLMs
        llm_status = "unavailable"
        llm_type = "none"
        llm_details = {}

        # Check OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key and openai_api_key != "your_openai_api_key_here":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_api_key)

                # Just check if the API key is valid without making an API call
                llm_status = "limited"
                llm_type = "openai"
                llm_details = {
                    "model": "gpt-3.5-turbo",
                    "provider": "OpenAI",
                    "status": "API key present but quota exceeded",
                    "note": "The OpenAI API key is valid but has exceeded its quota. Using mock lessons instead."
                }
            except Exception as e:
                llm_details = {"error": str(e), "provider": "OpenAI"}

        # Check Ollama if OpenAI is not available
        if llm_status != "operational":
            try:
                import subprocess
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                if result.returncode == 0:
                    llm_status = "operational"
                    llm_type = "ollama"
                    llm_details = {
                        "provider": "Ollama",
                        "models": result.stdout.strip()
                    }
                else:
                    llm_details = {"error": "Ollama is installed but not running properly", "provider": "Ollama"}
            except Exception as e:
                if not llm_details:  # Only update if OpenAI didn't already set an error
                    llm_details = {"error": str(e), "provider": "Ollama"}

        # If no real LLM is available, use the mock LLM
        if llm_status != "operational":
            if llm_status != "limited":  # Don't overwrite the limited status
                llm_status = "mock"
                llm_type = "mock"
                llm_details = {"provider": "Mock LLM", "response": "Using pre-defined lessons"}

        # Get GPU information from the global variable
        try:
            import torch
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                device_info = {
                    "status": "available",
                    "device_name": torch.cuda.get_device_name(0),
                    "device_count": torch.cuda.device_count(),
                    "cuda_version": torch.version.cuda,
                    "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**2:.2f} MB",
                    "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**2:.2f} MB",
                    "max_memory": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
                }
            else:
                device_info = {
                    "status": "unavailable",
                    "device_name": "cpu",
                    "reason": "CUDA not available on this system"
                }
        except Exception as e:
            device_info = {
                "status": "error",
                "device_name": "cpu",
                "error": f"Error checking GPU: {str(e)}"
            }

        return {
            "status": "operational" if llm_status == "operational" else "limited",
            "message": f"LLM service is {llm_status}",
            "vector_store": vector_store_status,
            "llm": {
                "status": llm_status,
                "type": llm_type,
                "details": llm_details
            },
            "device": device_info
        }
    except Exception as e:
        logger.error(f"Error checking LLM status: {str(e)}")
        return {
            "status": "error",
            "message": f"LLM service encountered an error: {str(e)}",
            "error_details": str(e)
        }

# Define specific routes BEFORE general routes to avoid conflicts
@app.get("/lessons/status/{task_id}", response_model=LessonStatusResponse)
async def get_lesson_generation_status(task_id: str):
    """
    Get the status of a lesson generation task

    Args:
        task_id: The unique task identifier returned from POST /lessons

    Returns:
        LessonStatusResponse: Current status and lesson data if completed
    """
    try:
        # Check if task exists
        if task_id not in generation_tasks:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Task {task_id} not found",
                    "suggestion": "The task may have expired or the task_id is invalid"
                }
            )

        task = generation_tasks[task_id]

        # Prepare response based on status
        if task.status == GenerationStatus.COMPLETED:
            # Get the generated lesson data
            lesson_data = generation_results.get(task_id)
            lesson_response = None

            if lesson_data:
                # Convert to LessonResponse format
                lesson_response = LessonResponse(
                    title=lesson_data.get("title", ""),
                    shloka=lesson_data.get("shloka", ""),
                    translation=lesson_data.get("translation", ""),
                    explanation=lesson_data.get("explanation", ""),
                    activity=lesson_data.get("activity", ""),
                    question=lesson_data.get("question", ""),
                    wikipedia_info=lesson_data.get("wikipedia_info")
                )

            return LessonStatusResponse(
                task_id=task_id,
                status=task.status,
                progress_message="Lesson generation completed successfully",
                created_at=task.created_at,
                completed_at=task.completed_at,
                lesson_data=lesson_response
            )

        elif task.status == GenerationStatus.FAILED:
            return LessonStatusResponse(
                task_id=task_id,
                status=task.status,
                progress_message="Lesson generation failed",
                created_at=task.created_at,
                completed_at=task.completed_at,
                error_message=task.error_message
            )

        elif task.status == GenerationStatus.IN_PROGRESS:
            return LessonStatusResponse(
                task_id=task_id,
                status=task.status,
                progress_message="Lesson generation is in progress...",
                created_at=task.created_at
            )

        else:  # PENDING
            return LessonStatusResponse(
                task_id=task_id,
                status=task.status,
                progress_message="Lesson generation is queued and will start shortly",
                created_at=task.created_at
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving task status: {str(e)}"
        )


@app.get("/lessons/tasks")
async def list_active_generation_tasks():
    """
    List all active lesson generation tasks

    Returns:
        Dict: Information about all active generation tasks
    """
    try:
        # Clean up old tasks first
        cleanup_old_tasks()

        active_tasks = []
        for task_id, task in generation_tasks.items():
            active_tasks.append({
                "task_id": task_id,
                "subject": task.subject,
                "topic": task.topic,
                "user_id": task.user_id,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error_message": task.error_message
            })

        return {
            "status": "success",
            "total_tasks": len(active_tasks),
            "tasks": active_tasks,
            "status_counts": {
                "pending": len([t for t in active_tasks if t["status"] == "pending"]),
                "in_progress": len([t for t in active_tasks if t["status"] == "in_progress"]),
                "completed": len([t for t in active_tasks if t["status"] == "completed"]),
                "failed": len([t for t in active_tasks if t["status"] == "failed"])
            }
        }

    except Exception as e:
        logger.error(f"Error listing active tasks: {str(e)}")
        return {
            "status": "error",
            "message": f"Error listing active tasks: {str(e)}",
            "total_tasks": 0,
            "tasks": []
        }


@app.get("/lessons/{subject}/{topic}", response_model=LessonResponse)
async def get_lesson_endpoint(
    subject: str,
    topic: str
):
    """
    Retrieve an existing lesson from the knowledge store

    This endpoint only retrieves existing lessons and does not generate new content.
    Use POST /lessons to create new lessons.

    Args:
        subject: Subject of the lesson (e.g., ved, ganita, yoga)
        topic: Topic of the lesson (e.g., sound, algebra, asana)

    Returns:
        LessonResponse: The existing lesson data

    Raises:
        404: If lesson is not found in knowledge store
        500: If there's an error retrieving the lesson

    Example usage:
        GET /lessons/ved/sound
    """
    try:
        logger.info(f"Retrieving lesson for subject: {subject}, topic: {topic}")

        # Try to get lesson from knowledge store
        try:
            from knowledge_store import get_lesson
            stored_lesson = get_lesson(subject, topic)

            if not stored_lesson:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": f"Lesson not found for subject '{subject}' and topic '{topic}'",
                        "suggestion": "Use POST /lessons to create a new lesson",
                        "available_endpoints": {
                            "create_lesson": "POST /lessons",
                            "search_lessons": "GET /search_lessons?query=your_search"
                        }
                    }
                )

            logger.info(f"Successfully retrieved lesson: {stored_lesson.get('title', 'Untitled')}")

            return stored_lesson

        except ImportError:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Knowledge store module not available",
                    "error": "Cannot retrieve lessons - knowledge store is not configured"
                }
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error retrieving lesson: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Error retrieving lesson: {str(e)}",
                "subject": subject,
                "topic": topic
            }
        )







@app.post("/lessons", response_model=LessonGenerationResponse)
async def create_lesson_endpoint(request: CreateLessonRequest, background_tasks: BackgroundTasks):
    """
    Create a new lesson by generating content using AI models (Async)

    This endpoint starts lesson generation in the background and returns immediately.
    The lesson generation happens asynchronously to prevent timeout issues.
    Use the returned task_id to poll for completion status.

    Args:
        request: CreateLessonRequest containing:
            - subject: Subject of the lesson (e.g., ved, ganita, yoga)
            - topic: Topic of the lesson (e.g., sound, algebra, asana)
            - user_id: ID of the user creating the lesson
            - include_wikipedia: Whether to include Wikipedia information
            - force_regenerate: Always True for dynamic generation

    Returns:
        LessonGenerationResponse: Task information for polling status

    Example usage:
        POST /lessons
        {
            "subject": "english",
            "topic": "verbs",
            "user_id": "user123",
            "include_wikipedia": true
        }
    """
    try:
        # Validate required parameters
        if not request.subject or not request.topic or not request.user_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Subject, topic, and user_id are required",
                    "example": {
                        "subject": "english",
                        "topic": "verbs",
                        "user_id": "user123"
                    },
                    "available_subjects": ["ved", "ganita", "yoga", "ayurveda", "english", "maths"],
                    "example_topics": ["sound", "algebra", "asana", "doshas", "verbs", "geometry"]
                }
            )

        # Clean up old tasks periodically
        cleanup_old_tasks()

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Create task record
        task = LessonGenerationTask(
            task_id=task_id,
            subject=request.subject,
            topic=request.topic,
            user_id=request.user_id,
            status=GenerationStatus.PENDING,
            created_at=datetime.now(),
            include_wikipedia=request.include_wikipedia
        )

        # Store task
        generation_tasks[task_id] = task

        # Start background generation
        background_tasks.add_task(
            generate_lesson_background,
            task_id=task_id,
            subject=request.subject,
            topic=request.topic,
            user_id=request.user_id,
            include_wikipedia=request.include_wikipedia
        )

        logger.info(f"Started async lesson generation - Task ID: {task_id}, Subject: {request.subject}, Topic: {request.topic}")

        # Return task information
        return LessonGenerationResponse(
            task_id=task_id,
            status=GenerationStatus.PENDING,
            message=f"Lesson generation started for {request.subject}/{request.topic}",
            estimated_completion_time="30-60 seconds",
            poll_url=f"/lessons/status/{task_id}"
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error starting lesson generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Error starting lesson generation: {str(e)}",
                "subject": request.subject if hasattr(request, 'subject') else 'unknown',
                "topic": request.topic if hasattr(request, 'topic') else 'unknown'
            }
        )

# Duplicate endpoints removed - moved above to fix routing conflicts



@app.get("/search_lessons")
async def search_lessons(query: str = Query(..., description="Search query")):
    """
    Search for lessons in the knowledge store
    """
    try:
        from knowledge_store import search_lessons as search_lessons_func
        results = search_lessons_func(query)
        return {
            "status": "success",
            "count": len(results),
            "results": results
        }
    except ImportError:
        return {
            "status": "error",
            "message": "Knowledge store module not available",
            "count": 0,
            "results": []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching lessons: {str(e)}",
            "count": 0,
            "results": []
        }

# Add middleware to forward requests to another server
class ForwardingMiddleware:
    def __init__(self, app, target_url, timeout=5):
        self.app = app
        self.target_url = target_url
        self.timeout = timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Process with the normal app
            await self.app(scope, receive, send)

            # After processing, forward the response to the target server
            if scope["method"] in ["GET", "POST", "PUT", "DELETE"]:
                try:
                    # Extract path and query string
                    path = scope["path"]
                    query_string = scope["query_string"].decode("utf-8")
                    full_path = f"{path}?{query_string}" if query_string else path

                    # Forward the request in a non-blocking way
                    requests.request(
                        method=scope["method"],
                        url=f"{self.target_url}{full_path}",
                        timeout=self.timeout,  # Use configurable timeout
                        headers={"X-Forwarded-By": "Gurukul-API"},
                    )
                    logger.info(f"Forwarded {scope['method']} {full_path} to {self.target_url}")
                except requests.Timeout:
                    logger.warning(f"Timeout forwarding {scope['method']} {full_path} to {self.target_url}")
                except Exception as e:
                    logger.error(f"Error forwarding request: {str(e)}")
        else:
            await self.app(scope, receive, send)

# Add the forwarding middleware
app.add_middleware(
    ForwardingMiddleware,
    target_url="http://192.168.0.83:8001",
    timeout=3  # Shorter timeout to avoid blocking
)

# Server startup moved to end of file

# Add this function to fetch audio files from the remote server (192.168.0.72:8000)
@app.get("/tts/tts_outputs/{filename}")
async def fetch_remote_audio(filename: str):
    """
    Fetch an audio file from the remote server (192.168.0.72:8000)
    """
    remote_url = f"http://192.168.0.72:8000/api/audio/{filename}"

    try:
        # Make request to the remote server
        response = requests.get(remote_url, stream=True)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Remote server returned error: {response.text}"
            )

        # Create a temporary file to store the audio
        local_path = os.path.join("temp_audio", f"remote_{filename}")
        os.makedirs("temp_audio", exist_ok=True)

        # Save the streamed content to the file
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Return the file as a response
        return FileResponse(
            path=local_path,
            media_type="audio/mpeg",
            filename=filename
        )

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch audio from remote server: {str(e)}"
        )

# Add this function to get a list of available audio files from the remote server
@app.get("/remote-audio-files")
async def list_remote_audio_files():
    """
    Get a list of available audio files from the remote server (192.168.0.72:8000)
    """
    remote_url = "http://192.168.0.72:8000/api/list-audio-files"

    try:
        response = requests.get(remote_url)

        if response.status_code == 200:
            return response.json()
        else:
            # If the remote server doesn't have a list endpoint,
            # we can try to get a list of recent audio files
            try:
                # Try to get recent PDF or image summaries which might have audio files
                pdf_response = requests.get("http://192.168.0.72:8000/summarize-pdf")
                img_response = requests.get("http://192.168.0.72:8000/summarize-img")

                audio_files = []

                if pdf_response.status_code == 200:
                    pdf_data = pdf_response.json()
                    if "audio_file" in pdf_data and pdf_data["audio_file"]:
                        audio_files.append(pdf_data["audio_file"].split("/")[-1])

                if img_response.status_code == 200:
                    img_data = img_response.json()
                    if "audio_file" in img_data and img_data["audio_file"]:
                        audio_files.append(img_data["audio_file"].split("/")[-1])

                return {
                    "audio_files": audio_files,
                    "count": len(audio_files),
                    "note": "Retrieved from recent summaries"
                }
            except:
                return {
                    "message": "Remote server doesn't support listing audio files",
                    "suggestion": "Try accessing specific files using /tts/tts_outputs/{filename}"
                }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to remote server: {str(e)}"
        )

# Add a new endpoint for exporting lessons
@app.post("/lessons/export")
async def export_lessons(request: Request):
    """
    Export lessons to various formats (PDF, Word, etc.)

    This endpoint allows exporting lessons to different file formats.
    """
    try:
        # Parse the request body
        body = await request.json()

        # Extract parameters
        subject = body.get("subject")
        topic = body.get("topic")
        format = body.get("format", "pdf")  # Default to PDF

        if not subject or not topic:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Subject and topic are required",
                    "example": {"subject": "maths", "topic": "algebra", "format": "pdf"}
                }
            )

        # Try to get the lesson
        try:
            from knowledge_store import get_lesson
            lesson = get_lesson(subject, topic)

            if not lesson:
                raise HTTPException(
                    status_code=404,
                    detail=f"Lesson not found for {subject}/{topic}"
                )

            # For now, just return the lesson data
            # In a real implementation, you would convert to the requested format
            return {
                "status": "success",
                "message": f"Lesson exported to {format} format",
                "lesson": lesson,
                "format": format
            }

        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Knowledge store module not available"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting lesson: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting lesson: {str(e)}"
        )


# TTS Generation Endpoints

@app.post("/lessons/generate-tts")
async def generate_lesson_tts(request: LessonTTSRequest):
    """
    Generate TTS audio for a lesson

    This endpoint can generate TTS for an existing lesson (by task_id) or
    for a lesson identified by subject/topic. It formats the lesson content
    appropriately and sends it to the external TTS service.

    Args:
        request: LessonTTSRequest containing:
            - task_id: ID of a generated lesson task (optional)
            - subject: Subject of the lesson (optional, used if no task_id)
            - topic: Topic of the lesson (optional, used if no task_id)
            - user_id: ID of the user requesting TTS
            - include_sections: Which sections to include in TTS
            - format_style: How to format the text for TTS

    Returns:
        Dict: TTS generation result with audio file information

    Example usage:
        POST /lessons/generate-tts
        {
            "task_id": "abc123-def456",
            "user_id": "user123",
            "include_sections": ["title", "explanation", "question"],
            "format_style": "complete"
        }
    """
    try:
        lesson_data = None
        lesson_identifier = ""

        # Get lesson data either by task_id or subject/topic
        if request.task_id:
            # Get lesson from generation results
            if request.task_id in generation_results:
                lesson_data = generation_results[request.task_id]
                lesson_identifier = f"Task {request.task_id}"
            else:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": f"Lesson task not found: {request.task_id}",
                        "suggestion": "Check if the task_id is correct or if the lesson generation is complete"
                    }
                )

        elif request.subject and request.topic:
            # Get lesson from knowledge store
            try:
                from knowledge_store import get_lesson
                lesson_data = get_lesson(request.subject, request.topic)
                lesson_identifier = f"{request.subject}/{request.topic}"

                if not lesson_data:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "message": f"Lesson not found: {request.subject}/{request.topic}",
                            "suggestion": "Generate the lesson first using POST /lessons"
                        }
                    )
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="Knowledge store module not available"
                )

        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Either task_id or both subject and topic must be provided",
                    "required_fields": "task_id OR (subject AND topic)"
                }
            )

        # Format the lesson for TTS
        tts_text = format_lesson_for_tts(
            lesson_data,
            format_style=request.format_style or "complete",
            include_sections=request.include_sections or ["title", "shloka", "translation", "explanation", "activity", "question"]
        )

        if not tts_text.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "No content available for TTS generation",
                    "lesson_data": lesson_data,
                    "suggestion": "Check if the lesson has content in the requested sections"
                }
            )

        # Generate TTS
        tts_result = await send_to_tts_service(
            text=tts_text,
            user_id=request.user_id or "guest-user",
            description=f"Manual TTS generation for lesson: {lesson_identifier}"
        )

        # Prepare response
        response = {
            "status": "success" if tts_result.get("status") == "success" else "error",
            "message": f"TTS generation completed for lesson: {lesson_identifier}",
            "lesson_info": {
                "identifier": lesson_identifier,
                "title": lesson_data.get("title", "Untitled"),
                "task_id": request.task_id,
                "subject": request.subject,
                "topic": request.topic
            },
            "tts_request": {
                "format_style": request.format_style or "complete",
                "include_sections": request.include_sections or ["title", "shloka", "translation", "explanation", "activity", "question"],
                "text_length": len(tts_text),
                "text_preview": tts_text[:200] + "..." if len(tts_text) > 200 else tts_text
            },
            "tts_result": tts_result,
            "generated_at": datetime.now().isoformat()
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating lesson TTS: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Error generating lesson TTS: {str(e)}",
                "error_details": str(e)
            }
        )


@app.post("/tts/generate")
async def generate_tts_from_text(request: TTSGenerationRequest):
    """
    Generate TTS audio from arbitrary text

    This endpoint allows direct TTS generation from any text content.
    It sends the text to the external TTS service and returns the audio file information.

    Args:
        request: TTSGenerationRequest containing:
            - text: Text to convert to speech
            - user_id: ID of the user requesting TTS
            - description: Description of the TTS request
            - timeout: Request timeout in seconds

    Returns:
        Dict: TTS generation result with audio file information

    Example usage:
        POST /tts/generate
        {
            "text": "Welcome to our lesson on ancient Indian mathematics.",
            "user_id": "user123",
            "description": "Introduction audio for mathematics lesson"
        }
    """
    try:
        # Validate text length
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Text is required and cannot be empty",
                    "field": "text"
                }
            )

        if len(request.text) > 10000:  # Reasonable limit for TTS
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Text is too long for TTS generation",
                    "max_length": 10000,
                    "current_length": len(request.text),
                    "suggestion": "Break the text into smaller chunks"
                }
            )

        # Generate TTS
        tts_result = await send_to_tts_service(
            text=request.text,
            user_id=request.user_id or "guest-user",
            description=request.description or "Direct TTS generation"
        )

        # Prepare response
        response = {
            "status": "success" if tts_result.get("status") == "success" else "error",
            "message": "TTS generation completed",
            "request_info": {
                "text_length": len(request.text),
                "text_preview": request.text[:200] + "..." if len(request.text) > 200 else request.text,
                "user_id": request.user_id,
                "description": request.description
            },
            "tts_result": tts_result,
            "generated_at": datetime.now().isoformat()
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating TTS from text: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Error generating TTS: {str(e)}",
                "error_details": str(e)
            }
        )


# Data forwarding endpoint to 192.168.0.119
@app.post("/forward_data")
async def forward_data_to_external_server(request: DataForwardRequest):
    """
    Forward data to external server at 192.168.0.119

    This endpoint allows sending various types of data to the external server.
    It supports different HTTP methods, custom headers, and flexible data formats.

    Args:
        request: DataForwardRequest containing:
            - data: The data to send (can be any JSON-serializable object)
            - endpoint: Target endpoint on the external server (default: "/")
            - method: HTTP method to use (default: "POST")
            - headers: Custom headers to include
            - timeout: Request timeout in seconds (default: 30)
            - user_id: ID of the user making the request
            - description: Optional description of the data being sent

    Returns:
        Dict: Response from the external server along with metadata

    Example usage:
        POST /forward_data
        {
            "data": {
                "lesson": {
                    "title": "Mathematics Lesson",
                    "content": "Algebra basics..."
                },
                "user_info": {
                    "user_id": "user123",
                    "timestamp": "2025-01-01T12:00:00"
                }
            },
            "endpoint": "/api/receive_lesson",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer token123"
            },
            "timeout": 30,
            "user_id": "user123",
            "description": "Sending generated lesson to external system"
        }
    """
    try:
        # Target server configuration
        target_server = "192.168.0.119"
        target_port = 8001  # Default port, can be made configurable

        # Build the full URL
        base_url = f"http://{target_server}:{target_port}"
        full_url = f"{base_url}{request.endpoint}"

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Gurukul-AI-System/1.0",
            "X-Forwarded-By": "Gurukul-API",
            "X-Source-IP": "192.168.0.83",
            "X-User-ID": request.user_id or "unknown"
        }

        # Add custom headers if provided
        if request.headers:
            headers.update(request.headers)

        # Add metadata to the data being sent
        enhanced_data = {
            "source": "gurukul-ai-system",
            "timestamp": datetime.now().isoformat(),
            "user_id": request.user_id,
            "description": request.description,
            "original_data": request.data
        }

        logger.info(f"Forwarding data to {full_url} - Method: {request.method}, User: {request.user_id}")
        logger.info(f"Data description: {request.description or 'No description provided'}")

        # Make the request to the external server
        start_time = time.time()

        response = requests.request(
            method=request.method.upper(),
            url=full_url,
            json=enhanced_data,
            headers=headers,
            timeout=request.timeout or 30
        )

        end_time = time.time()
        response_time = end_time - start_time

        # Log the response
        logger.info(f"External server response - Status: {response.status_code}, Time: {response_time:.3f}s")

        # Parse response
        try:
            response_data = response.json()
        except ValueError:
            # If response is not JSON, return as text
            response_data = {"text_response": response.text}

        # Prepare the return response
        result = {
            "status": "success" if response.status_code < 400 else "error",
            "message": f"Data forwarded to {target_server}",
            "external_server": {
                "url": full_url,
                "method": request.method.upper(),
                "status_code": response.status_code,
                "response_time_seconds": round(response_time, 3)
            },
            "request_info": {
                "user_id": request.user_id,
                "description": request.description,
                "data_size_bytes": len(str(request.data)),
                "timestamp": datetime.now().isoformat()
            },
            "external_response": response_data
        }

        # Return appropriate HTTP status
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=result
            )

        return result

    except requests.Timeout:
        logger.error(f"Timeout forwarding data to {target_server}")
        raise HTTPException(
            status_code=408,
            detail={
                "status": "timeout",
                "message": f"Request to {target_server} timed out after {request.timeout or 30} seconds",
                "external_server": {
                    "url": full_url,
                    "method": request.method.upper(),
                    "timeout": request.timeout or 30
                },
                "suggestion": "Try increasing the timeout value or check if the external server is responding"
            }
        )

    except requests.ConnectionError:
        logger.error(f"Connection error forwarding data to {target_server}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "connection_error",
                "message": f"Could not connect to {target_server}",
                "external_server": {
                    "url": full_url,
                    "method": request.method.upper()
                },
                "suggestion": "Check if the external server is running and accessible"
            }
        )

    except requests.RequestException as e:
        logger.error(f"Request error forwarding data to {target_server}: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "status": "request_error",
                "message": f"Error making request to {target_server}: {str(e)}",
                "external_server": {
                    "url": full_url,
                    "method": request.method.upper()
                },
                "error_details": str(e)
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error forwarding data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "internal_error",
                "message": f"Unexpected error: {str(e)}",
                "error_details": str(e)
            }
        )


# Convenience endpoint for sending lesson data specifically
@app.post("/send_lesson_to_external")
async def send_lesson_to_external_server(
    subject: str,
    topic: str,
    user_id: str = "guest-user",
    endpoint: str = "/api/receive_lesson",
    include_metadata: bool = True
):
    """
    Convenience endpoint to send a generated lesson to the external server at 192.168.0.119

    This endpoint retrieves a lesson and sends it to the external server in a standardized format.

    Args:
        subject: Subject of the lesson to send
        topic: Topic of the lesson to send
        user_id: ID of the user sending the lesson
        endpoint: Target endpoint on the external server
        include_metadata: Whether to include generation metadata

    Returns:
        Dict: Response from the external server

    Example usage:
        POST /send_lesson_to_external?subject=mathematics&topic=algebra&user_id=user123
    """
    try:
        # Try to get the lesson from knowledge store
        try:
            from knowledge_store import get_lesson
            lesson_data = get_lesson(subject, topic)

            if not lesson_data:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": f"Lesson not found for {subject}/{topic}",
                        "suggestion": "Generate the lesson first using POST /lessons"
                    }
                )
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Knowledge store module not available"
            )

        # Prepare the data to send
        data_to_send = {
            "lesson": lesson_data,
            "subject": subject,
            "topic": topic
        }

        if include_metadata:
            data_to_send["metadata"] = {
                "sent_at": datetime.now().isoformat(),
                "sent_by": user_id,
                "source_system": "gurukul-ai",
                "lesson_id": f"{subject}_{topic}",
                "format_version": "1.0"
            }

        # Create the forward request
        forward_request = DataForwardRequest(
            data=data_to_send,
            endpoint=endpoint,
            method="POST",
            user_id=user_id,
            description=f"Sending lesson: {subject}/{topic}"
        )

        # Forward the data
        result = await forward_data_to_external_server(forward_request)

        return {
            "status": "success",
            "message": f"Lesson {subject}/{topic} sent to external server",
            "lesson_info": {
                "subject": subject,
                "topic": topic,
                "title": lesson_data.get("title", "Untitled"),
                "user_id": user_id
            },
            "external_response": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending lesson to external server: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending lesson: {str(e)}"
        )


# GET endpoint to retrieve audio files from 192.168.0.119:8001
@app.get("/api/audio/{filename}")
async def get_audio_from_external_server(filename: str):
    """
    Retrieve an audio file from the external server at 192.168.0.119:8001

    This endpoint fetches audio files from the external TTS service and streams them
    to the client. It supports various audio formats and provides proper error handling.

    Args:
        filename: Name of the audio file to retrieve (e.g., "lesson_audio.mp3")

    Returns:
        FileResponse: The audio file streamed from the external server

    Example usage:
        GET /api/audio/0525b138-b104-477c-8c3b-3280c0abdd23.mp3
    """
    try:
        target_server = "192.168.0.119"
        target_port = 8001

        # Build the URL to the external server's audio endpoint
        external_audio_url = f"http://{target_server}:{target_port}/api/audio/{filename}"

        logger.info(f"Fetching audio file from external server: {external_audio_url}")

        # Make request to the external server
        response = requests.get(external_audio_url, stream=True, timeout=30)

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Audio file '{filename}' not found on external server",
                    "external_server": f"{target_server}:{target_port}",
                    "suggestion": "Check if the filename is correct or if the file exists on the external server"
                }
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    "message": f"External server returned error: {response.status_code}",
                    "external_server": f"{target_server}:{target_port}",
                    "external_response": response.text[:200] if response.text else "No response body"
                }
            )

        # Create the temp_audio_cache directory in the project root
        # Get the directory where app.py is located (project root)
        project_root = os.path.dirname(os.path.abspath(__file__))
        temp_audio_dir = os.path.join(project_root, "temp_audio_cache")
        os.makedirs(temp_audio_dir, exist_ok=True)

        # Create local path for the audio file (use original filename, not prefixed)
        local_audio_path = os.path.join(temp_audio_dir, filename)

        # Stream and save the audio file locally
        with open(local_audio_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Verify the file was saved successfully
        if not os.path.exists(local_audio_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to save audio file locally"
            )

        file_size = os.path.getsize(local_audio_path)
        logger.info(f"Successfully retrieved audio file: {filename} ({file_size} bytes)")
        logger.info(f"Audio file cached at: {local_audio_path}")

        # Return the audio file with proper headers
        return FileResponse(
            path=local_audio_path,
            media_type="audio/mpeg",
            filename=filename,
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "X-Audio-Source": f"{target_server}:{target_port}",
                "X-File-Size": str(file_size),
                "X-Cache-Location": local_audio_path,
                "X-Cache-Directory": temp_audio_dir
            }
        )

    except requests.Timeout:
        logger.error(f"Timeout retrieving audio file from {target_server}:{target_port}")
        raise HTTPException(
            status_code=408,
            detail={
                "message": f"Request to external server timed out",
                "external_server": f"{target_server}:{target_port}",
                "suggestion": "The external server may be slow or unresponsive"
            }
        )

    except requests.ConnectionError:
        logger.error(f"Connection error retrieving audio file from {target_server}:{target_port}")
        raise HTTPException(
            status_code=503,
            detail={
                "message": f"Could not connect to external server",
                "external_server": f"{target_server}:{target_port}",
                "suggestion": "Check if the external server is running and accessible"
            }
        )

    except requests.RequestException as e:
        logger.error(f"Request error retrieving audio file: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "message": f"Error communicating with external server: {str(e)}",
                "external_server": f"{target_server}:{target_port}"
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error retrieving audio file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Unexpected error: {str(e)}",
                "filename": filename
            }
        )


# GET endpoint to list available audio files from 192.168.0.119:8001
@app.get("/api/audio-files")
async def list_audio_files_from_external_server():
    """
    Get a list of available audio files from the external server at 192.168.0.119:8001

    This endpoint retrieves the list of audio files available on the external TTS service.

    Returns:
        Dict: List of available audio files with metadata

    Example usage:
        GET /api/audio-files
    """
    try:
        target_server = "192.168.0.119"
        target_port = 8001

        # Build the URL to the external server's list endpoint
        external_list_url = f"http://{target_server}:{target_port}/api/list-audio-files"

        logger.info(f"Fetching audio file list from external server: {external_list_url}")

        # Make request to the external server
        response = requests.get(external_list_url, timeout=10)

        if response.status_code == 200:
            audio_list = response.json()

            # Enhance the response with additional metadata
            enhanced_response = {
                "status": "success",
                "external_server": f"{target_server}:{target_port}",
                "audio_files": audio_list.get("audio_files", []),
                "count": audio_list.get("count", 0),
                "access_info": {
                    "base_url": f"http://192.168.0.83:8000/api/audio/",
                    "example": f"http://192.168.0.83:8000/api/audio/filename.mp3",
                    "note": "Use the base_url + filename to access audio files through this API"
                },
                "retrieved_at": datetime.now().isoformat()
            }

            logger.info(f"Successfully retrieved {enhanced_response['count']} audio files from external server")
            return enhanced_response

        else:
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    "message": f"External server returned error: {response.status_code}",
                    "external_server": f"{target_server}:{target_port}",
                    "external_response": response.text[:200] if response.text else "No response body"
                }
            )

    except requests.Timeout:
        logger.error(f"Timeout retrieving audio file list from {target_server}:{target_port}")
        raise HTTPException(
            status_code=408,
            detail={
                "message": f"Request to external server timed out",
                "external_server": f"{target_server}:{target_port}",
                "suggestion": "The external server may be slow or unresponsive"
            }
        )

    except requests.ConnectionError:
        logger.error(f"Connection error retrieving audio file list from {target_server}:{target_port}")
        raise HTTPException(
            status_code=503,
            detail={
                "message": f"Could not connect to external server",
                "external_server": f"{target_server}:{target_port}",
                "suggestion": "Check if the external server is running and accessible"
            }
        )

    except requests.RequestException as e:
        logger.error(f"Request error retrieving audio file list: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "message": f"Error communicating with external server: {str(e)}",
                "external_server": f"{target_server}:{target_port}"
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error retrieving audio file list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Unexpected error: {str(e)}"
            }
        )


# Health check endpoint for external server connectivity
@app.get("/check_external_server")
async def check_external_server_connectivity():
    """
    Check if the external server at 192.168.0.119 is reachable

    Returns:
        Dict: Connectivity status and server information
    """
    try:
        target_server = "192.168.0.119"
        target_port = 8001

        # Try to connect to the external server
        start_time = time.time()

        try:
            response = requests.get(
                f"http://{target_server}:{target_port}/",
                timeout=10,
                headers={"User-Agent": "Gurukul-AI-HealthCheck/1.0"}
            )

            end_time = time.time()
            response_time = end_time - start_time

            return {
                "status": "reachable",
                "server": f"{target_server}:{target_port}",
                "response_code": response.status_code,
                "response_time_seconds": round(response_time, 3),
                "server_response": response.text[:200] if response.text else "No response body",
                "checked_at": datetime.now().isoformat()
            }

        except requests.Timeout:
            return {
                "status": "timeout",
                "server": f"{target_server}:{target_port}",
                "message": "Server did not respond within 10 seconds",
                "checked_at": datetime.now().isoformat()
            }

        except requests.ConnectionError:
            return {
                "status": "unreachable",
                "server": f"{target_server}:{target_port}",
                "message": "Could not establish connection to server",
                "checked_at": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Error checking external server: {str(e)}")
        return {
            "status": "error",
            "server": f"{target_server}:{target_port}",
            "message": f"Error checking connectivity: {str(e)}",
            "checked_at": datetime.now().isoformat()
        }


# Agent-related endpoints
@app.get("/get_agent_output")
async def get_agent_output():
    """
    Get agent outputs for the dashboard
    Returns a list of agent interactions and responses
    """
    try:
        # Return mock data for now - in production, this would come from a database
        mock_agent_outputs = [
            {
                "id": 1,
                "agent_type": "financial",
                "query": "How should I invest my savings?",
                "response": "Based on your risk profile, I recommend a mix of 60% index funds, 30% bonds, and 10% cash reserves.",
                "confidence": 0.87,
                "tags": ["risk", "investment"],
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
            },
            {
                "id": 2,
                "agent_type": "education",
                "query": "Explain the Pythagorean theorem",
                "response": "The Pythagorean theorem states that in a right triangle, the square of the hypotenuse equals the sum of squares of the other two sides: a² + b² = c².",
                "confidence": 0.95,
                "tags": ["math", "geometry"],
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
            },
            {
                "id": 3,
                "agent_type": "wellness",
                "query": "Tips for better sleep",
                "response": "For better sleep: maintain a consistent schedule, avoid screens 1 hour before bed, keep your room cool and dark, and try relaxation techniques.",
                "confidence": 0.91,
                "tags": ["sleep", "health"],
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            }
        ]

        # Combine with any stored agent outputs
        all_outputs = mock_agent_outputs + agent_outputs

        logger.info(f"Returning {len(all_outputs)} agent outputs")
        return all_outputs

    except Exception as e:
        logger.error(f"Error getting agent outputs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving agent outputs: {str(e)}"
        )


@app.get("/agent_logs")
async def get_agent_logs():
    """
    Get agent logs for monitoring and debugging
    Returns a list of agent session logs
    """
    try:
        # Return mock data for now - in production, this would come from a database
        mock_agent_logs = [
            {
                "id": str(uuid.uuid4()),
                "user_id": "guest-user",
                "agent_id": 1,
                "agent_name": "EduMentor",
                "agent_type": "education",
                "action_type": "start",
                "start_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "end_time": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "duration": 900,  # 15 minutes in seconds
                "status": "completed",
                "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "guest-user",
                "agent_id": 2,
                "agent_name": "FinancialCrew",
                "agent_type": "financial",
                "action_type": "start",
                "start_time": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "end_time": None,
                "duration": None,
                "status": "active",
                "created_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
            }
        ]

        # Combine with any stored agent logs
        all_logs = mock_agent_logs + agent_logs

        logger.info(f"Returning {len(all_logs)} agent logs")
        return all_logs

    except Exception as e:
        logger.error(f"Error getting agent logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving agent logs: {str(e)}"
        )


# Pydantic models for agent requests
class AgentMessageRequest(BaseModel):
    message: str
    agent_id: int
    user_id: str = "guest-user"
    timestamp: str


class AgentSimulationRequest(BaseModel):
    agent_id: int
    user_id: str = "guest-user"
    timestamp: str


class AgentResetRequest(BaseModel):
    user_id: str = "guest-user"
    timestamp: str


@app.post("/agent_message")
async def send_agent_message(request: AgentMessageRequest):
    """
    Send a message to an agent and get a response
    """
    try:
        logger.info(f"Received agent message: {request.message} for agent {request.agent_id}")

        # Mock response based on agent type
        agent_responses = {
            1: "As an educational agent, I can help you understand complex topics. What would you like to learn about?",
            2: "As a financial advisor agent, I can help with investment strategies and financial planning. What's your financial goal?",
            3: "As a wellness agent, I focus on your physical and mental wellbeing. How can I help you today?"
        }

        response_text = agent_responses.get(request.agent_id, "I'm here to help! What can I do for you?")

        # Store the interaction
        agent_output = {
            "id": len(agent_outputs) + 1,
            "agent_type": "education" if request.agent_id == 1 else "financial" if request.agent_id == 2 else "wellness",
            "query": request.message,
            "response": response_text,
            "confidence": 0.85,
            "tags": ["conversation"],
            "timestamp": datetime.now().isoformat(),
            "user_id": request.user_id
        }

        agent_outputs.append(agent_output)

        return {
            "status": "success",
            "message": "Message sent successfully",
            "response": response_text,
            "agent_id": request.agent_id
        }

    except Exception as e:
        logger.error(f"Error sending agent message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending message to agent: {str(e)}"
        )


@app.post("/start_agent_simulation")
async def start_agent_simulation(request: AgentSimulationRequest):
    """
    Start an agent simulation session
    """
    try:
        logger.info(f"Starting agent simulation for agent {request.agent_id}, user {request.user_id}")

        # Create a simulation session
        simulation_id = str(uuid.uuid4())
        agent_simulations[request.user_id] = {
            "simulation_id": simulation_id,
            "agent_id": request.agent_id,
            "status": "active",
            "start_time": datetime.now().isoformat(),
            "user_id": request.user_id
        }

        # Log the start event
        agent_log = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "agent_id": request.agent_id,
            "agent_name": f"Agent-{request.agent_id}",
            "agent_type": "education" if request.agent_id == 1 else "financial" if request.agent_id == 2 else "wellness",
            "action_type": "start",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": None,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }

        agent_logs.append(agent_log)

        return {
            "status": "success",
            "message": "Agent simulation started",
            "simulation_id": simulation_id,
            "agent_id": request.agent_id
        }

    except Exception as e:
        logger.error(f"Error starting agent simulation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting agent simulation: {str(e)}"
        )


@app.post("/stop_agent_simulation")
async def stop_agent_simulation(request: AgentSimulationRequest):
    """
    Stop an agent simulation session
    """
    try:
        logger.info(f"Stopping agent simulation for agent {request.agent_id}, user {request.user_id}")

        # Find and stop the simulation
        if request.user_id in agent_simulations:
            simulation = agent_simulations[request.user_id]
            simulation["status"] = "stopped"
            simulation["end_time"] = datetime.now().isoformat()

            # Update the corresponding log
            for log in agent_logs:
                if (log["user_id"] == request.user_id and
                    log["agent_id"] == request.agent_id and
                    log["status"] == "active"):
                    log["status"] = "completed"
                    log["end_time"] = datetime.now().isoformat()
                    # Calculate duration if start_time exists
                    if log["start_time"]:
                        start_time = datetime.fromisoformat(log["start_time"].replace('Z', '+00:00'))
                        end_time = datetime.now()
                        log["duration"] = int((end_time - start_time).total_seconds())
                    break

        return {
            "status": "success",
            "message": "Agent simulation stopped",
            "agent_id": request.agent_id
        }

    except Exception as e:
        logger.error(f"Error stopping agent simulation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping agent simulation: {str(e)}"
        )


@app.post("/reset_agent_simulation")
async def reset_agent_simulation(request: AgentResetRequest):
    """
    Reset agent simulation for a user
    """
    try:
        logger.info(f"Resetting agent simulation for user {request.user_id}")

        # Clear simulation data for the user
        if request.user_id in agent_simulations:
            del agent_simulations[request.user_id]

        # Mark all active logs as interrupted
        for log in agent_logs:
            if log["user_id"] == request.user_id and log["status"] == "active":
                log["status"] = "interrupted"
                log["end_time"] = datetime.now().isoformat()
                if log["start_time"]:
                    start_time = datetime.fromisoformat(log["start_time"].replace('Z', '+00:00'))
                    end_time = datetime.now()
                    log["duration"] = int((end_time - start_time).total_seconds())

        # Add reset log entry
        reset_log = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "agent_id": 0,  # Special ID for reset actions
            "agent_name": "System",
            "agent_type": "system",
            "action_type": "reset",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": 0,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }

        agent_logs.append(reset_log)

        return {
            "status": "success",
            "message": "Agent simulation reset successfully"
        }

    except Exception as e:
        logger.error(f"Error resetting agent simulation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting agent simulation: {str(e)}"
        )


# Run on multiple IP addresses
import asyncio
import socket

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

async def run_server():
    """Run the server on multiple IP addresses"""
    local_ip = get_local_ip()

    # List of IPs to try
    ips_to_try = [
        "127.0.0.1",     # Always try localhost first
        "0.0.0.0"        # All interfaces
    ]

    port = 8000

    for ip in ips_to_try:
        try:
            logger.info(f"Attempting to start server on {ip}:{port}")
            config = uvicorn.Config(
                app=app,
                host=ip,
                port=port,
                log_level="info",
                access_log=True
            )
            server = uvicorn.Server(config)
            await server.serve()
            break
        except Exception as e:
            logger.warning(f"Failed to start server on {ip}:{port}: {e}")
            if ip == ips_to_try[-1]:  # Last IP in the list
                logger.error("Failed to start server on any IP address")
                raise

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

