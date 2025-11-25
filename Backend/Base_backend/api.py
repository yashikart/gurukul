import os, sys
# Ensure this directory is on sys.path so same-folder imports work when running as a package
sys.path.append(os.path.dirname(__file__))

from rag import *
from dotenv import load_dotenv
import uvicorn
import requests
import os
from llm_service import llm_service
from datetime import datetime
from subject_data import subjects_data
from lectures_data import lectures_data
# Test data for fallback when database is empty
test_data = [
    {
        "id": 1,
        "title": "Sample Test",
        "subject": "Mathematics",
        "questions": [
            {
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4"
            }
        ]
    }
]
from db import pdf_collection , image_collection, user_collection, subjects_collection, lectures_collection, tests_collection
from datetime import datetime, timezone
from typing import Optional
import json
import httpx
from fastapi import HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response, FileResponse, StreamingResponse
import shutil
import uuid
import asyncio
import time
import logging

# Import orchestration system components
import sys
import asyncio
from pathlib import Path

from utils.logging_config import configure_logging
logger = configure_logging("base_backend")
from orchestration_config import config, validate_integration_setup
from orchestration_db_integration import db_integration, get_user_analytics, sync_user_data

# Add orchestration system to path
orchestration_path = Path(__file__).parent.parent / "orchestration" / "unified_orchestration_system"
sys.path.append(str(orchestration_path))

try:
    if config.is_orchestration_available():
        from orchestration_api import UnifiedOrchestrationEngine, OrchestrationTriggers, AgentMemoryManager
        ORCHESTRATION_AVAILABLE = True
        print("✅ Orchestration system imported successfully")

        # Validate integration setup
        integration_status = validate_integration_setup()
        print(f"🔧 Integration validation: {integration_status}")
    else:
        ORCHESTRATION_AVAILABLE = False
        print("⚠️ Orchestration system disabled in configuration")
except ImportError as e:
    import logging
    from utils.logging_config import configure_logging
    logger = configure_logging("base_backend")
    print(f"⚠️ Orchestration system not available: {e}")
    ORCHESTRATION_AVAILABLE = False

# Load environment variables from centralized configuration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared_config import load_shared_config

# Load centralized configuration
load_shared_config("Base_backend")

# Verify critical environment variables are loaded
if not os.getenv("GROQ_API_KEY"):
    print("⚠️  WARNING: GROQ_API_KEY not found in environment variables")
if not os.getenv("MONGO_URI") and not os.getenv("MONGODB_URI"):
    print("⚠️  WARNING: MONGO_URI/MONGODB_URI not found in environment variables")
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

# CORS configuration via ALLOWED_ORIGINS
# To allow all origins, set ALLOWED_ORIGINS="*" in your environment.
_allowed = os.getenv("ALLOWED_ORIGINS", "").strip()
if _allowed == "*":
    _allow_all_origins = True
    _allowed_list = ["*"]
else:
    _allow_all_origins = False
    _allowed_list = [o.strip() for o in _allowed.split(",") if o.strip()] or [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_list,
    # Credentials cannot be used with wildcard "*" origin. Disable when allowing all origins.
    allow_credentials=False if _allow_all_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestration engine if available
orchestration_engine = None
if ORCHESTRATION_AVAILABLE:
    try:
        orchestration_engine = UnifiedOrchestrationEngine()
        print("🚀 Initializing orchestration engine...")
        # Note: We'll initialize this in a startup event
    except Exception as e:
        print(f"❌ Failed to initialize orchestration engine: {e}")
        orchestration_engine = None

# Add startup event to initialize orchestration
@app.on_event("startup")
async def startup_event():
    """Initialize orchestration engine on startup"""
    global orchestration_engine
    if orchestration_engine and ORCHESTRATION_AVAILABLE:
        try:
            await orchestration_engine.initialize()
            print("✅ Orchestration engine initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize orchestration engine: {e}")
            orchestration_engine = None

# Add a health check endpoint
@app.get("/health")
def health_check():
    orchestration_status = "available" if orchestration_engine else "unavailable"
    return {
        "status": "ok",
        "orchestration": orchestration_status,
        "timestamp": datetime.now().isoformat()
    }

# Global exception handler for consistency
from fastapi.responses import JSONResponse
from uuid import uuid4

@app.exception_handler(Exception)
async def on_error(request, exc):
    trace = str(uuid4())
    logger.exception(f"[{trace}] Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {"code": "INTERNAL_ERROR", "message": "Unexpected error"},
            "trace_id": trace,
        },
    )

@app.get("/integration-status")
def get_integration_status():
    """Get detailed integration status between Base_backend and Orchestration system"""
    try:
        integration_status = validate_integration_setup()

        # Add runtime status
        runtime_status = {
            "orchestration_engine_initialized": orchestration_engine is not None,
            "config_loaded": config is not None,
            "api_endpoints_available": ORCHESTRATION_AVAILABLE,
            "sub_agent_urls": config.get_sub_agent_config() if config else {},
            "trigger_thresholds": config.get_trigger_thresholds() if config else {},
            "vector_store_config": config.get_vector_store_config() if config else {}
        }

        return {
            "integration_status": integration_status,
            "runtime_status": runtime_status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

    except Exception as e:
        return {
            "error": f"Failed to get integration status: {str(e)}",
            "integration_status": {"overall_valid": False},
            "runtime_status": {"orchestration_engine_initialized": False},
            "timestamp": datetime.now().isoformat()
        }

# ==== Subject API Models and Routes ====
class Subject(BaseModel):
    id: int
    name: str
    code: str

# Real subjects endpoint using MongoDB
@app.get("/subjects")
def get_subjects_real():
    try:
        # Try to get subjects from MongoDB first
        subjects = list(subjects_collection.find({}, {"_id": 0}))

        # If no subjects in database, populate with dummy data
        if not subjects:
            # Insert dummy data into database
            subjects_collection.insert_many(subjects_data)
            subjects = subjects_data

        return JSONResponse(content=subjects)
    except Exception as e:
        print(f"Error fetching subjects: {e}")
        # Fallback to dummy data if database fails
        return JSONResponse(content=subjects_data)




# ==== Lectures API Models and Routes ====
class Lecture(BaseModel):
    id: int
    topic: str
    subject_id: int

# Real lectures endpoint using MongoDB
@app.get("/lectures")
def get_lectures_real():
    try:
        # Try to get lectures from MongoDB first
        lectures = list(lectures_collection.find({}, {"_id": 0}))

        # If no lectures in database, populate with dummy data
        if not lectures:
            # Insert dummy data into database
            lectures_collection.insert_many(lectures_data)
            lectures = lectures_data

        return JSONResponse(content=lectures)
    except Exception as e:
        print(f"Error fetching lectures: {e}")
        # Fallback to dummy data if database fails
        return JSONResponse(content=lectures_data)



# ==== Test API Models and Routes ====
class Test(BaseModel):
    id: int
    name: str
    subject_id: int
    date: Optional[str] = None

# Real tests endpoint using MongoDB
@app.get("/tests")
def get_tests_real():
    try:
        # Try to get tests from MongoDB first
        tests = list(tests_collection.find({}, {"_id": 0}))

        # If no tests in database, populate with dummy data
        if not tests:
            # Insert dummy data into database
            tests_collection.insert_many(test_data)
            tests = test_data

        return JSONResponse(content=tests)
    except Exception as e:
        print(f"Error fetching tests: {e}")
        # Fallback to dummy data if database fails
        return JSONResponse(content=test_data)

# ==== Lesson Generation API Models and Routes ====
class LessonRequest(BaseModel):
    subject: str
    topic: str
    user_id: Optional[str] = "guest-user"
    include_wikipedia: Optional[bool] = True
    force_regenerate: Optional[bool] = False

class EnhancedLessonRequest(BaseModel):
    subject: str
    topic: str
    user_id: Optional[str] = "guest-user"
    quiz_score: Optional[float] = None
    use_orchestration: Optional[bool] = True
    include_triggers: Optional[bool] = True
    include_wikipedia: Optional[bool] = True

@app.get("/generate_lesson")
async def generate_lesson(
    subject: str,
    topic: str,
    include_wikipedia: bool = True,
    use_knowledge_store: bool = True
):
    """Generate a lesson using GET parameters with proper knowledge base integration"""
    try:
        print(f"🔍 Generating lesson for {subject}/{topic} with include_wikipedia={include_wikipedia}, use_knowledge_store={use_knowledge_store}")

        # Initialize variables for content sources
        knowledge_content = ""
        wikipedia_content = ""
        sources_used = []

        # Get Knowledge Store content if requested
        if use_knowledge_store:
            try:
                import requests

                print("📚 Calling orchestration system for knowledge base content...")

                # Construct query for the orchestration system
                query = f"Explain {topic} in {subject}"

                # Call the orchestration system's edumentor endpoint
                orchestration_url = "http://localhost:8006/edumentor"

                print(f"🔍 DEBUG: Calling {orchestration_url} with query: {query}")

                orchestration_response = requests.get(
                    orchestration_url,
                    params={"query": query, "user_id": "base_backend_lesson_generator"},
                    timeout=30  # Reduced timeout to 30 seconds
                )

                print(f"🔍 DEBUG: Orchestration response status: {orchestration_response.status_code}")

                if orchestration_response.status_code == 200:
                    orchestration_data = orchestration_response.json()
                    print(f"✅ Successfully retrieved data from orchestration system")
                    print(f"🔍 DEBUG: Orchestration data keys: {list(orchestration_data.keys())}")

                    # Extract content from orchestration response
                    knowledge_content = orchestration_data.get("response", "")
                    orchestration_sources = orchestration_data.get("sources", [])

                    print(f"📄 Knowledge content length: {len(knowledge_content)}")
                    print(f"📄 Knowledge content preview: {knowledge_content[:200]}...")
                    print(f"🔍 Orchestration sources count: {len(orchestration_sources)}")

                    if orchestration_sources:
                        print(f"🔍 DEBUG: First orchestration source: {orchestration_sources[0]}")

                    # Format sources for consistency
                    for doc in orchestration_sources[:5]:  # Limit to top 5 sources
                        sources_used.append({
                            "text": doc.get("text", "")[:500] + "..." if len(doc.get("text", "")) > 500 else doc.get("text", ""),
                            "source": doc.get("source", "Knowledge Base"),
                            "store": "orchestration_system"
                        })
                else:
                    print(f"⚠️ Orchestration system returned status {orchestration_response.status_code}")
                    print(f"🔍 DEBUG: Response text: {orchestration_response.text[:300]}...")
                    knowledge_content = ""

            except requests.exceptions.Timeout:
                print("⏰ Orchestration system timeout - continuing without knowledge base content")
                knowledge_content = ""
            except Exception as e:
                print(f"⚠️ Error calling orchestration system: {e}")
                knowledge_content = ""

        # Get Wikipedia content if requested (independent of knowledge store)
        if include_wikipedia:
            try:
                # Import Wikipedia utilities
                import sys
                import os
                wikipedia_path = os.path.join(os.path.dirname(__file__), '..', 'subject_generation')
                if wikipedia_path not in sys.path:
                    sys.path.append(wikipedia_path)

                from wikipedia_utils import get_relevant_wikipedia_info

                print("🌐 Fetching Wikipedia content...")
                wiki_data = get_relevant_wikipedia_info(subject, topic)

                if wiki_data["wikipedia"]["title"] and wiki_data["wikipedia"]["summary"]:
                    wikipedia_content = f"Wikipedia Article: {wiki_data['wikipedia']['title']}\n{wiki_data['wikipedia']['summary']}"
                    sources_used.append({
                        "text": wiki_data['wikipedia']['summary'][:500],
                        "source": f"Wikipedia: {wiki_data['wikipedia']['title']}",
                        "url": wiki_data['wikipedia']['url'],
                        "store": "wikipedia"
                    })
                    print(f"✅ Found Wikipedia article: {wiki_data['wikipedia']['title']}")
                else:
                    print("⚠️ No relevant Wikipedia content found")

            except Exception as wiki_error:
                print(f"⚠️ Wikipedia search failed: {wiki_error}")
                wikipedia_content = ""

                # If we found knowledge base content or Wikipedia content, use it
                if knowledge_content or wikipedia_content:
                    print("📖 Generating lesson with enhanced content...")

                    # Combine all available content
                    reference_content = ""
                    if wikipedia_content:
                        reference_content += f"WIKIPEDIA CONTENT:\n{wikipedia_content}\n\n"
                    if knowledge_content:
                        reference_content += f"KNOWLEDGE BASE CONTENT:\n{knowledge_content}\n\n"

                    # Create enhanced prompt with all available content
                    prompt = f"""
                    Create a comprehensive lesson on the topic "{topic}" in the subject "{subject}" using the following reference content:

                    {reference_content}

                    Please create a structured lesson that includes:
                    1. Title: A clear, engaging title for the lesson
                    2. Level: Appropriate educational level (beginner, intermediate, advanced)
                    3. Text: Comprehensive explanation incorporating the reference content above
                    4. Quiz: An array of 3-5 multiple choice questions to test understanding
                    5. TTS: Boolean flag (set to true for text-to-speech capability)

                    Format the response as a JSON object with these exact fields:
                    {{
                        "title": "lesson title",
                        "level": "educational level",
                        "text": "detailed lesson content",
                        "quiz": [
                            {{
                                "question": "question text",
                                "options": ["option1", "option2", "option3", "option4"],
                                "correct": 0
                            }}
                        ],
                        "tts": true
                    }}

                    Make sure the lesson is educational, accurate, and incorporates information from the provided reference content.
                    """

                    # Use the LLM service to generate the lesson
                    lesson_content = llm_service.generate_response(prompt)

                    # Try to parse as JSON, if it fails, create structured response
                    try:
                        import json
                        import re

                        # Extract JSON from response
                        json_start = lesson_content.find("{")
                        json_end = lesson_content.rfind("}") + 1

                        if json_start >= 0 and json_end > json_start:
                            json_str = lesson_content[json_start:json_end]
                            lesson_json = json.loads(json_str)

                            # Add metadata
                            lesson_json["subject"] = subject
                            lesson_json["topic"] = topic
                            lesson_json["sources"] = sources_used
                            lesson_json["knowledge_base_used"] = bool(knowledge_content)
                            lesson_json["wikipedia_used"] = bool(wikipedia_content)
                            lesson_json["generated_at"] = datetime.now().isoformat()
                            lesson_json["status"] = "success"

                            print("✅ Successfully generated lesson with knowledge base content")
                            return JSONResponse(content=lesson_json)
                        else:
                            raise ValueError("No valid JSON found in response")

                    except Exception as json_error:
                        print(f"⚠️ JSON parsing failed: {json_error}, using fallback format")
                        # Fallback to structured response
                        lesson_data = {
                            "title": f"Understanding {topic} in {subject}",
                            "level": "intermediate",
                            "text": lesson_content,
                            "quiz": [
                                {
                                    "question": f"What is the main concept discussed in this lesson about {topic}?",
                                    "options": [
                                        f"Basic principles of {topic}",
                                        f"Advanced applications of {topic}",
                                        f"Historical context of {topic}",
                                        f"Future developments in {topic}"
                                    ],
                                    "correct": 0
                                }
                            ],
                            "tts": True,
                            "subject": subject,
                            "topic": topic,
                            "sources": sources_used,
                            "knowledge_base_used": bool(knowledge_content),
                            "wikipedia_used": bool(wikipedia_content),
                            "generated_at": datetime.now().isoformat(),
                            "status": "success"
                        }
                        return JSONResponse(content=lesson_data)

                else:
                    print("⚠️ No relevant content found in knowledge base, falling back to basic generation")

            except Exception as kb_error:
                print(f"⚠️ Knowledge base search failed: {kb_error}, falling back to basic generation")

        # Fallback to basic lesson generation (when knowledge base is not used or fails)
        print("📝 Using basic lesson generation...")

        # Check if we should still try Wikipedia even if knowledge base failed
        wikipedia_content = ""
        sources_used = []

        if include_wikipedia:
            try:
                # Import Wikipedia utilities
                wikipedia_path = os.path.join(os.path.dirname(__file__), '..', 'subject_generation')
                if wikipedia_path not in sys.path:
                    sys.path.append(wikipedia_path)

                from wikipedia_utils import get_relevant_wikipedia_info

                print("🌐 Fetching Wikipedia content for basic generation...")
                wiki_data = get_relevant_wikipedia_info(subject, topic)

                if wiki_data["wikipedia"]["title"] and wiki_data["wikipedia"]["summary"]:
                    wikipedia_content = f"Wikipedia Article: {wiki_data['wikipedia']['title']}\n{wiki_data['wikipedia']['summary']}"
                    sources_used.append({
                        "text": wiki_data['wikipedia']['summary'][:500],
                        "source": f"Wikipedia: {wiki_data['wikipedia']['title']}",
                        "url": wiki_data['wikipedia']['url'],
                        "store": "wikipedia"
                    })
                    print(f"✅ Found Wikipedia article: {wiki_data['wikipedia']['title']}")

            except Exception as wiki_error:
                print(f"⚠️ Wikipedia search failed: {wiki_error}")

        # Create a prompt for basic lesson generation
        if wikipedia_content:
            prompt = f"""
            Create a comprehensive lesson on the topic "{topic}" in the subject "{subject}" using the following Wikipedia content as reference:

            WIKIPEDIA CONTENT:
            {wikipedia_content}

            Please format your response as a JSON object with these exact fields:
            {{
                "title": "lesson title",
                "level": "educational level (beginner/intermediate/advanced)",
                "text": "detailed lesson content incorporating the Wikipedia information",
                "quiz": [
                    {{
                        "question": "question text",
                        "options": ["option1", "option2", "option3", "option4"],
                        "correct": 0
                    }}
                ],
                "tts": true
            }}

            Make the lesson educational, engaging, and based on the Wikipedia content provided.
            Include 3-5 quiz questions to test understanding.
            """
        else:
            prompt = f"""
            Create a comprehensive lesson on the topic "{topic}" in the subject "{subject}".

            Please format your response as a JSON object with these exact fields:
            {{
                "title": "lesson title",
                "level": "educational level (beginner/intermediate/advanced)",
                "text": "detailed lesson content with introduction, key concepts, examples, and summary",
                "quiz": [
                    {{
                        "question": "question text",
                        "options": ["option1", "option2", "option3", "option4"],
                        "correct": 0
                    }}
                ],
                "tts": true
            }}

            Make the lesson educational, engaging, and appropriate for students.
            Include 3-5 quiz questions to test understanding.
            """

        # Use the LLM service to generate the lesson
        lesson_content = llm_service.generate_response(prompt)

        # Try to parse as JSON
        try:
            import json

            json_start = lesson_content.find("{")
            json_end = lesson_content.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = lesson_content[json_start:json_end]
                lesson_json = json.loads(json_str)

                # Add metadata
                lesson_json["subject"] = subject
                lesson_json["topic"] = topic
                lesson_json["sources"] = sources_used
                lesson_json["knowledge_base_used"] = False
                lesson_json["wikipedia_used"] = bool(wikipedia_content)
                lesson_json["generated_at"] = datetime.now().isoformat()
                lesson_json["status"] = "success"

                return JSONResponse(content=lesson_json)
            else:
                raise ValueError("No valid JSON found in response")

        except Exception as json_error:
            print(f"⚠️ JSON parsing failed: {json_error}, using simple format")
            # Simple fallback format
            lesson_data = {
                "title": f"Lesson on {subject}: {topic}",
                "level": "intermediate",
                "text": lesson_content,
                "quiz": [
                    {
                        "question": f"What is the main focus of this lesson on {topic}?",
                        "options": [
                            f"Understanding {topic} fundamentals",
                            f"Advanced {topic} concepts",
                            f"Historical aspects of {topic}",
                            f"Practical applications of {topic}"
                        ],
                        "correct": 0
                    }
                ],
                "tts": True,
                "subject": subject,
                "topic": topic,
                "sources": sources_used,
                "knowledge_base_used": False,
                "wikipedia_used": bool(wikipedia_content),
                "generated_at": datetime.now().isoformat(),
                "status": "success"
            }
            return JSONResponse(content=lesson_data)

    except Exception as e:
        print(f"❌ Error generating lesson: {e}")
        import traceback
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to generate lesson: {str(e)}",
                "subject": subject,
                "topic": topic,
                "status": "error",
                "knowledge_base_used": False,
                "wikipedia_used": False
            }
        )

@app.get("/generate_lesson_stream")
async def generate_lesson_stream(
    subject: str,
    topic: str,
    include_wikipedia: bool = True,
    use_knowledge_store: bool = True
):
    """
    Generate in-depth lesson content with live streaming (no JSON format)
    Returns plain text content that streams progressively for live rendering
    """
    async def generate_content():
        try:
            yield f"data: 🎓 Starting lesson generation for {subject}: {topic}\n\n"
            await asyncio.sleep(0.1)

            # Initialize variables for content sources
            knowledge_content = ""
            wikipedia_content = ""

            yield f"data: 📚 Gathering educational resources...\n\n"
            await asyncio.sleep(0.2)

            # Get Knowledge Store content if requested
            if use_knowledge_store:
                try:
                    yield f"data: 🔍 Accessing knowledge base for {subject}...\n\n"
                    await asyncio.sleep(0.3)

                    import requests
                    query = f"Provide comprehensive, in-depth explanation of {topic} in {subject}. Include detailed concepts, examples, applications, and educational insights."

                    orchestration_url = "http://localhost:8006/edumentor"
                    orchestration_response = requests.get(
                        orchestration_url,
                        params={"query": query, "user_id": "streaming_lesson_generator"},
                        timeout=30
                    )

                    if orchestration_response.status_code == 200:
                        orchestration_data = orchestration_response.json()
                        knowledge_content = orchestration_data.get("response", "")
                        yield f"data: ✅ Knowledge base content retrieved ({len(knowledge_content)} characters)\n\n"
                    else:
                        yield f"data: ⚠️ Knowledge base unavailable, using enhanced generation\n\n"

                except Exception as e:
                    yield f"data: ⚠️ Knowledge base error: {str(e)}\n\n"

            # Get Wikipedia content if requested
            if include_wikipedia:
                try:
                    yield f"data: 🌐 Searching Wikipedia for {topic}...\n\n"
                    await asyncio.sleep(0.2)

                    import sys
                    import os
                    wikipedia_path = os.path.join(os.path.dirname(__file__), '..', 'subject_generation')
                    if wikipedia_path not in sys.path:
                        sys.path.append(wikipedia_path)

                    from wikipedia_utils import get_relevant_wikipedia_info
                    wiki_data = get_relevant_wikipedia_info(subject, topic)

                    if wiki_data["wikipedia"]["title"] and wiki_data["wikipedia"]["summary"]:
                        wikipedia_content = wiki_data["wikipedia"]["summary"]
                        yield f"data: ✅ Wikipedia article found: {wiki_data['wikipedia']['title']}\n\n"
                    else:
                        yield f"data: ⚠️ No relevant Wikipedia content found\n\n"

                except Exception as e:
                    yield f"data: ⚠️ Wikipedia search failed: {str(e)}\n\n"

            # Generate comprehensive lesson content
            yield f"data: 🧠 Generating comprehensive lesson content...\n\n"
            await asyncio.sleep(0.5)

            # Create enhanced prompt for in-depth content
            content_sources = []
            if wikipedia_content:
                content_sources.append(f"Wikipedia Information:\n{wikipedia_content}")
            if knowledge_content:
                content_sources.append(f"Knowledge Base Content:\n{knowledge_content}")

            reference_content = "\n\n".join(content_sources) if content_sources else ""

            prompt = f"""
            Create a comprehensive, in-depth educational lesson on "{topic}" in the subject "{subject}".

            {f"Use the following reference content to enhance your explanation:{chr(10)}{chr(10)}{reference_content}{chr(10)}{chr(10)}" if reference_content else ""}

            Structure your response as a detailed educational lesson with:

            1. **Introduction and Overview**
               - Clear definition and context
               - Importance and relevance
               - Learning objectives

            2. **Fundamental Concepts**
               - Core principles and theories
               - Key terminology and definitions
               - Historical background and development

            3. **Detailed Explanation**
               - Step-by-step breakdown of concepts
               - Multiple examples and illustrations
               - Real-world applications

            4. **Advanced Topics**
               - Complex aspects and nuances
               - Current research and developments
               - Future implications

            5. **Practical Applications**
               - How this knowledge is used
               - Industry applications
               - Problem-solving examples

            6. **Summary and Key Takeaways**
               - Main points recap
               - Important concepts to remember
               - Further learning suggestions

            Make this lesson comprehensive, educational, and engaging. Use clear language but don't oversimplify.
            Provide in-depth coverage that would be suitable for serious learners.
            Do NOT format as JSON - provide as plain educational text.
            """

            # Generate the lesson content
            lesson_content = llm_service.generate_response(prompt)

            # Stream the content progressively
            yield f"data: 📖 Lesson content ready! Streaming now...\n\n"
            await asyncio.sleep(0.3)

            # Split content into chunks for progressive streaming
            content_lines = lesson_content.split('\n')

            for i, line in enumerate(content_lines):
                if line.strip():  # Only send non-empty lines
                    yield f"data: {line}\n\n"
                    await asyncio.sleep(0.05)  # Small delay for live rendering effect
                else:
                    yield f"data: \n\n"  # Send empty line
                    await asyncio.sleep(0.02)

            yield f"data: \n\n"
            yield f"data: ✅ Lesson generation complete!\n\n"
            yield f"data: 📊 Total content: {len(content_lines)} lines\n\n"
            yield f"data: 🎯 Sources used: {'Knowledge Base + ' if knowledge_content else ''}{'Wikipedia + ' if wikipedia_content else ''}Enhanced AI Generation\n\n"
            yield f"data: [END]\n\n"

        except Exception as e:
            yield f"data: ❌ Error generating lesson: {str(e)}\n\n"
            yield f"data: [ERROR]\n\n"

    return StreamingResponse(
        generate_content(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )

@app.post("/lessons")
def create_lesson(lesson_request: LessonRequest):
    """Create a lesson using POST request - Basic Mode"""
    try:
        # Create different prompts based on Wikipedia setting
        if lesson_request.include_wikipedia:
            # Basic mode with Wikipedia - shorter, concise content
            prompt = f"""
            Create a concise lesson on the topic "{lesson_request.topic}" in the subject "{lesson_request.subject}".

            Please include:
            1. Brief introduction to the topic
            2. Key concepts (2-3 main points)
            3. One practical example
            4. 2-3 practice questions

            Keep the lesson focused and educational. Limit to approximately 200-300 words.
            """
        else:
            # Basic mode without Wikipedia - even more concise, pure LLM knowledge
            prompt = f"""
            Create a short, focused lesson on the topic "{lesson_request.topic}" in the subject "{lesson_request.subject}".

            Requirements:
            - Use only your internal knowledge, no external sources
            - Keep it concise and to the point
            - Include:
              1. Simple definition of the topic
              2. 2 key points about the topic
              3. One basic example
              4. One practice question

            Limit to approximately 150-200 words. Do not reference Wikipedia or any external sources.
            """

        # Use the LLM service to generate the lesson
        lesson_content = llm_service.generate_response(prompt)

        lesson_data = {
            "subject": lesson_request.subject,
            "topic": lesson_request.topic,
            "content": lesson_content,
            "user_id": lesson_request.user_id,
            "settings": {
                "include_wikipedia": lesson_request.include_wikipedia,
                "force_regenerate": lesson_request.force_regenerate
            },
            "generated_at": datetime.now().isoformat(),
            "status": "success",
            "source": "basic_mode",
            "content_type": "concise" if not lesson_request.include_wikipedia else "basic"
        }

        return JSONResponse(content=lesson_data)

    except Exception as e:
        print(f"Error creating lesson: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to create lesson: {str(e)}",
                "subject": lesson_request.subject,
                "topic": lesson_request.topic,
                "status": "error"
            }
        )

@app.post("/lessons/enhanced")  
async def create_enhanced_lesson(lesson_request: EnhancedLessonRequest):
    """
    Create an enhanced lesson using orchestration system with RAG and trigger detection
    Falls back to basic lesson generation if orchestration is unavailable
    """
    try:
        # Try orchestration system first if available and requested
        if orchestration_engine and lesson_request.use_orchestration:
            print(f"🎓 Using orchestration system for enhanced lesson generation")

            # Create comprehensive query for orchestration system
            if lesson_request.include_wikipedia:
                query = f"""Create a comprehensive, detailed lesson about {lesson_request.topic} in {lesson_request.subject}.
                Include extensive explanations, multiple examples, practical applications, historical context,
                and advanced concepts. This should be a thorough educational resource with rich content."""
            else:
                query = f"""Create a detailed lesson about {lesson_request.topic} in {lesson_request.subject} using
                only internal knowledge sources. Provide comprehensive explanations, multiple examples,
                and practical applications without referencing external sources like Wikipedia."""

            # Call orchestration system
            orchestration_response = await orchestration_engine.ask_edumentor(
                query=query,
                user_id=lesson_request.user_id,
                quiz_score=lesson_request.quiz_score
            )

            # Transform orchestration response to lesson format
            enhanced_lesson = transform_orchestration_to_lesson(
                orchestration_response,
                lesson_request.subject,
                lesson_request.topic,
                lesson_request.user_id
            )

            # Store lesson in MongoDB if needed
            if lesson_request.user_id != "guest-user":
                store_lesson_in_db(enhanced_lesson)

            return JSONResponse(content=enhanced_lesson)

        else:
            # Fallback to basic lesson generation
            print(f"📚 Using basic lesson generation (orchestration unavailable or disabled)")
            return await create_basic_lesson_fallback(lesson_request)

    except Exception as e:
        print(f"Error in enhanced lesson creation: {e}")
        # Fallback to basic lesson generation on error
        try:
            return await create_basic_lesson_fallback(lesson_request)
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Enhanced lesson generation failed: {str(e)}. Fallback also failed: {str(fallback_error)}",
                    "subject": lesson_request.subject,
                    "topic": lesson_request.topic,
                    "status": "error"
                }
            )

#Chatbot
groq_api_key = os.environ.get('GROQ_API_KEY')

# Temporary in-memory storage
user_queries: List[dict] = []
llm_responses: List[dict] = []

# Pydantic model for request validation
class ChatMessage(BaseModel):
    message: str
    timestamp: str = None
    type: str = "chat_message"


# Route 1: Receive query from frontend
@app.post("/chatpost")
async def receive_query(chat: ChatMessage):
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    query_record = {
        "message": chat.message,
        "timestamp": timestamp,
        "type": "chat_message"
    }
    try:
        chat_collection = user_collection.insert_one(query_record)
        query_record["_id"] = str(chat_collection.inserted_id)  # Add the MongoDB ID to the record
        print(f"Received message: {chat.message}")
        return {"status": "Query received", "data": query_record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store query:{str(e)}")


import requests

# ==== Orchestration Integration Helper Functions ====

def transform_orchestration_to_lesson(orchestration_response: dict, subject: str, topic: str, user_id: str) -> dict:
    """Transform orchestration system response to Base_backend lesson format"""
    try:
        # Extract key components from orchestration response
        explanation = orchestration_response.get("explanation", "")
        activity = orchestration_response.get("activity", {})
        triggers = orchestration_response.get("triggers_detected", [])
        interventions = orchestration_response.get("trigger_interventions", [])
        source_docs = orchestration_response.get("source_documents", [])

        # Create enhanced lesson structure that maintains backward compatibility
        enhanced_lesson = {
            "subject": subject,
            "topic": topic,
            "content": explanation,
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "status": "success",
            "source": "orchestration_enhanced",

            # Enhanced features from orchestration
            "enhanced_features": {
                "activity": activity,
                "triggers_detected": len(triggers),
                "interventions_applied": len(interventions),
                "source_documents_count": len(source_docs),
                "rag_enhanced": True
            },

            # Detailed orchestration data (optional, can be used by frontend)
            "orchestration_data": {
                "query_id": orchestration_response.get("query_id"),
                "activity_details": activity,
                "triggers": triggers,
                "interventions": interventions,
                "source_documents": source_docs[:3],  # Limit to first 3 for size
                "timestamp": orchestration_response.get("timestamp")
            },

            # Settings for backward compatibility
            "settings": {
                "include_wikipedia": True,
                "force_regenerate": False,
                "orchestration_enhanced": True
            }
        }

        return enhanced_lesson

    except Exception as e:
        print(f"Error transforming orchestration response: {e}")
        # Return basic structure on error
        return {
            "subject": subject,
            "topic": topic,
            "content": f"Enhanced lesson content for {topic} in {subject}",
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "status": "success",
            "source": "orchestration_fallback",
            "error": f"Transformation error: {str(e)}"
        }

async def create_basic_lesson_fallback(lesson_request: EnhancedLessonRequest) -> JSONResponse:
    """Fallback to basic lesson generation when orchestration is unavailable"""
    try:
        # Create different prompts based on mode and Wikipedia setting
        if lesson_request.include_wikipedia:
            # Basic mode with Wikipedia - shorter, concise content
            prompt = f"""
            Create a concise lesson on the topic "{lesson_request.topic}" in the subject "{lesson_request.subject}".

            Please include:
            1. Brief introduction to the topic
            2. Key concepts (2-3 main points)
            3. One practical example
            4. 2-3 practice questions

            Keep the lesson focused and educational. Limit to approximately 200-300 words.
            """
        else:
            # Basic mode without Wikipedia - even more concise, pure LLM knowledge
            prompt = f"""
            Create a short, focused lesson on the topic "{lesson_request.topic}" in the subject "{lesson_request.subject}".

            Requirements:
            - Use only your internal knowledge, no external sources
            - Keep it concise and to the point
            - Include:
              1. Simple definition of the topic
              2. 2 key points about the topic
              3. One basic example
              4. One practice question

            Limit to approximately 150-200 words. Do not reference Wikipedia or any external sources.
            """

        # Use the LLM service to generate the lesson
        lesson_content = llm_service.generate_response(prompt)

        lesson_data = {
            "subject": lesson_request.subject,
            "topic": lesson_request.topic,
            "content": lesson_content,
            "user_id": lesson_request.user_id,
            "settings": {
                "include_wikipedia": lesson_request.include_wikipedia,
                "force_regenerate": False,
                "orchestration_enhanced": False
            },
            "generated_at": datetime.now().isoformat(),
            "status": "success",
            "source": "basic_mode",
            "content_type": "concise" if not lesson_request.include_wikipedia else "basic"
        }

        return JSONResponse(content=lesson_data)

    except Exception as e:
        raise Exception(f"Basic lesson generation failed: {str(e)}")

def store_lesson_in_db(lesson_data: dict):
    """Store lesson in MongoDB using the database integration layer"""
    try:
        if config.STORE_ENHANCED_LESSONS:
            lesson_id = db_integration.store_enhanced_lesson(lesson_data)
            print(f"✅ Enhanced lesson stored with ID: {lesson_id}")

            # Sync user data if orchestration is available
            if orchestration_engine and lesson_data.get('user_id') != "guest-user":
                user_session = orchestration_engine.memory_manager.get_user_session(lesson_data['user_id'])
                sync_user_data(lesson_data['user_id'], user_session)
        else:
            # Fallback to basic storage
            lesson_doc = {
                **lesson_data,
                "stored_at": datetime.now().isoformat(),
                "collection_type": "generated_lesson"
            }
            lectures_collection.insert_one(lesson_doc)
            print(f"✅ Basic lesson stored for user {lesson_data.get('user_id')}")

    except Exception as e:
        print(f"⚠️ Failed to store lesson in database: {e}")
        # Don't raise error - lesson generation should still succeed

def call_groq_llama3(prompt: str) -> str:
    """Enhanced LLM function with multiple providers and fallback"""
    try:
        # Use the enhanced LLM service with automatic fallback
        response = llm_service.generate_response(prompt)
        print(f"✅ LLM Response generated successfully")
        return response
    except Exception as e:
        print(f"❌ Error in LLM service: {e}")
        # Final fallback
        return "I apologize, but I'm experiencing technical difficulties right now. Please try again in a few moments."


# Route 2: Send LLM response back
@app.get("/chatbot")
async def send_response():
    try:
        # Fetch the latest query from MongoDB
        latest_query = user_collection.find_one({"type": "chat_message", "response":None}, sort=[("timestamp", -1)])
        if not latest_query:
            return {"error": "No queries yet"}

        query_message = latest_query["message"]
        print(f"Processing query: {query_message}")

        llm_reply = call_groq_llama3(query_message)

        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        response_data = {
            "message": llm_reply,
            "timestamp": timestamp,
            "type": "chat_response",
            "query_id": str(latest_query["_id"])  # Link response to query
        }

        user_collection.update_one(
            {"_id": latest_query["_id"]},
            {"$set": {"response": response_data}}
        )

        return {
            "_id": str(latest_query["_id"]),
            "query": query_message,
            "response": response_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process response:{str(e)}")

# ==== Educational Progress and Trigger Endpoints ====

@app.get("/user-progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get user's educational progress and trigger analysis"""
    try:
        if not orchestration_engine:
            return JSONResponse(
                status_code=503,
                content={"error": "Orchestration system not available", "user_id": user_id}
            )

        # Get user session from orchestration system
        session = orchestration_engine.memory_manager.get_user_session(user_id)
        educational_progress = session.get('educational_progress', {})

        # Check for triggers
        triggers = orchestration_engine.triggers.check_educational_triggers(user_id)

        progress_data = {
            "user_id": user_id,
            "educational_progress": educational_progress,
            "triggers_detected": triggers,
            "last_active": session.get('last_active'),
            "interaction_count": session.get('interaction_count', 0),
            "quiz_scores": educational_progress.get('quiz_scores', []),
            "learning_topics": educational_progress.get('learning_topics', []),
            "recommendations": generate_progress_recommendations(educational_progress, triggers)
        }

        return JSONResponse(content=progress_data)

    except Exception as e:
        print(f"Error getting user progress: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get user progress: {str(e)}", "user_id": user_id}
        )

@app.post("/trigger-intervention/{user_id}")
async def trigger_intervention(user_id: str, quiz_score: Optional[float] = None):
    """Manually trigger educational intervention for a user"""
    try:
        if not orchestration_engine:
            return JSONResponse(
                status_code=503,
                content={"error": "Orchestration system not available", "user_id": user_id}
            )

        # Check for educational triggers
        triggers = orchestration_engine.triggers.check_educational_triggers(user_id, quiz_score)

        if not triggers:
            return JSONResponse(content={
                "user_id": user_id,
                "message": "No interventions needed at this time",
                "triggers_detected": [],
                "interventions": []
            })

        # Execute trigger actions
        interventions = await orchestration_engine.triggers.execute_trigger_actions(user_id, triggers)

        return JSONResponse(content={
            "user_id": user_id,
            "message": f"Executed {len(interventions)} interventions",
            "triggers_detected": triggers,
            "interventions": interventions,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Error triggering intervention: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to trigger intervention: {str(e)}", "user_id": user_id}
        )

def generate_progress_recommendations(educational_progress: dict, triggers: list) -> list:
    """Generate recommendations based on user progress and triggers"""
    recommendations = []

    quiz_scores = educational_progress.get('quiz_scores', [])
    learning_topics = educational_progress.get('learning_topics', [])

    # Analyze quiz performance
    if quiz_scores:
        avg_score = sum(quiz_scores) / len(quiz_scores)
        if avg_score < 60:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "message": f"Average quiz score is {avg_score:.1f}%. Consider reviewing fundamental concepts.",
                "action": "schedule_tutoring"
            })
        elif avg_score < 75:
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "message": f"Good progress with {avg_score:.1f}% average. Focus on challenging topics.",
                "action": "practice_exercises"
            })

    # Analyze learning patterns
    if len(learning_topics) > 5:
        recent_topics = learning_topics[-5:]
        if len(set(recent_topics)) < 3:
            recommendations.append({
                "type": "variety",
                "priority": "medium",
                "message": "Consider exploring more diverse topics to broaden understanding.",
                "action": "topic_diversification"
            })

    # Add trigger-based recommendations
    for trigger in triggers:
        if trigger.get('type') == 'low_quiz_score':
            recommendations.append({
                "type": "intervention",
                "priority": "high",
                "message": "Immediate tutoring support recommended due to low quiz performance.",
                "action": "immediate_tutoring"
            })

    return recommendations

@app.get("/user-analytics/{user_id}")
async def get_user_analytics_endpoint(user_id: str):
    """Get comprehensive user analytics including orchestration data"""
    try:
        # Get analytics from database integration
        analytics = get_user_analytics(user_id)

        # Add orchestration-specific analytics if available
        if orchestration_engine:
            try:
                session = orchestration_engine.memory_manager.get_user_session(user_id)
                orchestration_analytics = {
                    "orchestration_session": {
                        "interaction_count": session.get("interaction_count", 0),
                        "last_active": session.get("last_active"),
                        "educational_progress": session.get("educational_progress", {}),
                        "wellness_metrics": session.get("wellness_metrics", {}),
                        "spiritual_journey": session.get("spiritual_journey", {})
                    },
                    "trigger_analysis": orchestration_engine.triggers.check_educational_triggers(user_id)
                }
                analytics["orchestration_data"] = orchestration_analytics
            except Exception as e:
                analytics["orchestration_error"] = str(e)

        return JSONResponse(content=analytics)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get user analytics: {str(e)}", "user_id": user_id}
        )

@app.post("/process-pdf", response_model=PDFResponse)
async def process_pdf(file: UploadFile = File(...)):
    temp_pdf_path = ""
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        temp_pdf_path = os.path.join(TEMP_DIR, f"temp_pdf_{time.strftime('%Y%m%d_%H%M%S')}.pdf")
        with open(temp_pdf_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)

        structured_data = parse_pdf(temp_pdf_path)
        if not structured_data["body"]:
            raise HTTPException(status_code=400, detail="Failed to parse PDF content")

        query = "give me detail summary of this pdf"
        groq_api_key = os.getenv("GROQ_API_KEY")
        agent = build_qa_agent([structured_data["body"]], groq_api_key=groq_api_key)
        result = agent.invoke({"query": query})
        answer = result["result"]

        audio_file = text_to_speech(answer, file_prefix="output_pdf")
        audio_url = f"/static/{os.path.basename(audio_file)}" if audio_file else "No audio generated"

        # Store to MongoDB
        pdf_doc = {
            "filename": file.filename,
            "title": structured_data["title"],
            "sections": [{"heading": s["heading"], "content": s["content"]} for s in structured_data["sections"]],
            "query": query,
            "answer": answer,
            "audio_file": audio_url,
            "timestamp": datetime.now(timezone.utc)
        }
        pdf_collection.insert_one(pdf_doc)

        global pdf_response
        pdf_response = PDFResponse(
            title=structured_data["title"],
            sections=[Section(heading=s["heading"], content=s["content"]) for s in structured_data["sections"]],
            query=query,
            answer=answer,
            audio_file=audio_url
        )
        return pdf_response

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


@app.post("/process-img", response_model=ImageResponse)
async def process_image(file: UploadFile = File(...)):
    temp_image_path = ""
    try:
        if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(status_code=400, detail="Only JPG, JPEG, or PNG files are allowed")

        temp_image_path = os.path.join(
            TEMP_DIR,
            f"temp_image_{time.strftime('%Y%m%d_%H%M%S')}{os.path.splitext(file.filename)[1]}"
        )

        with open(temp_image_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)

        ocr_text = extract_text_easyocr(temp_image_path).strip()
        logger.info(f"OCR raw output: {repr(ocr_text)}")

        if not ocr_text:
            ocr_text = "No readable text found in the image."
            answer = ocr_text
            query = "N/A"
        else:
            query = "give me detail summary of this image"
            groq_api_key = os.getenv("GROQ_API_KEY")
            agent = build_qa_agent([ocr_text], groq_api_key=groq_api_key)
            result = agent.invoke({"query": query})
            answer = result["result"]

        audio_file = text_to_speech(answer, file_prefix="output_image")
        audio_url = f"/static/{os.path.basename(audio_file)}" if audio_file else "No audio generated"

        # Store to MongoDB
        image_doc = {
            "filename": file.filename,
            "ocr_text": ocr_text,
            "query": query,
            "answer": answer,
            "audio_file": audio_url,
            "timestamp": datetime.now(timezone.utc)
        }
        image_collection.insert_one(image_doc)

        global image_response
        image_response = ImageResponse(
            ocr_text=ocr_text,
            query=query,
            answer=answer,
            audio_file=audio_url
        )
        return image_response

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

@app.get("/summarize-pdf", response_model=PDFResponse)
async def summarize_pdf():
    if pdf_response is None:
        raise HTTPException(status_code=404, detail="No PDF has been processed yet.")
    return pdf_response

@app.get("/summarize-img", response_model=ImageResponse)
async def summarize_image():
    if image_response is None:
        raise HTTPException(status_code=404, detail="No image has been processed yet.")
    return image_response

@app.get("/api/stream/{filename}")
async def stream_audio(filename: str):
    audio_path = os.path.join(TEMP_DIR, filename)

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename
    )

@app.get("/api/audio/{filename}")
async def download_audio(filename: str):
    audio_path = os.path.join(TEMP_DIR, filename)

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename
    )

# ==== OpenAI-compatible Chat Completions Proxy (CORS-enabled) ====
@app.options("/v1/chat/completions")
async def chat_completions_options(request: Request):
    # When allowing all origins, use "*" for preflight responses
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, ngrok-skip-browser-warning",
            "Access-Control-Max-Age": "86400",
        },
    )

@app.post("/v1/chat/completions")
async def chat_completions_proxy(request: Request):
    """
    Proxy OpenAI-compatible chat completions with CORS enabled.
    Tries multiple upstreams automatically if the first one fails (e.g., 404/5xx).
    Upstream priority:
      1) UNIGURU_NGROK_ENDPOINT or UNIGURU_API_BASE_URL (if set)
      2) LOCAL_LLAMA_API_URL (if set)
      3) https://api.groq.com/openai (uses GROQ_API_KEY)
      4) https://api.openai.com (uses OPENAI_API_KEY)
    """
    # Parse JSON body
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Build candidate upstream list
    candidates = []
    # 1) Custom ngrok/api base
    custom_base = os.getenv("UNIGURU_NGROK_ENDPOINT") or os.getenv("UNIGURU_API_BASE_URL")
    if custom_base:
        candidates.append(custom_base)
    # 2) Local LLaMA
    local_llama = os.getenv("LOCAL_LLAMA_API_URL")
    if local_llama:
        candidates.append(local_llama)
    # 3) Groq OpenAI-compatible
    candidates.append("https://api.groq.com/openai")
    # 4) OpenAI
    candidates.append("https://api.openai.com")

    # Prepare incoming auth (if any)
    incoming_auth = request.headers.get("authorization")

    last_error = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for base in candidates:
            # Normalize URL
            if base.rstrip("/").endswith("/v1/chat/completions"):
                url = base
            else:
                # If base already includes '/openai', keep it; we still add '/v1/chat/completions'
                url = base.rstrip("/") + "/v1/chat/completions"

            # Build headers per-provider
            headers = {
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true",
            }
            # Prefer incoming auth if present
            if incoming_auth:
                headers["Authorization"] = incoming_auth

            # Provider-specific auth if not provided
            if "api.groq.com" in url and "Authorization" not in headers:
                groq_key = os.getenv("GROQ_API_KEY")
                if groq_key:
                    headers["Authorization"] = f"Bearer {groq_key}"
            if "api.openai.com" in url and "Authorization" not in headers:
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    headers["Authorization"] = f"Bearer {openai_key}"

            try:
                resp = await client.post(url, json=body, headers=headers)
            except httpx.TimeoutException as te:
                last_error = HTTPException(status_code=504, detail=f"Upstream timeout at {url}")
                continue
            except Exception as e:
                last_error = HTTPException(status_code=502, detail=f"Upstream error at {url}: {str(e)}")
                continue

            # If success, return immediately
            if 200 <= resp.status_code < 300:
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    media_type=resp.headers.get("content-type", "application/json"),
                )
            else:
                # Try next candidate on error status
                last_error = HTTPException(status_code=resp.status_code, detail=f"Upstream {url} returned {resp.status_code}: {resp.text[:200]}")
                continue

    # If we reach here, all candidates failed
    if last_error:
        raise last_error
    raise HTTPException(status_code=502, detail="No upstream providers available")

# Register alias routes for chat completions to avoid 404 due to path variants
# Supports with/without trailing slash and optional /api prefix
app.add_api_route("/v1/chat/completions/", chat_completions_proxy, methods=["POST"])
app.add_api_route("/api/v1/chat/completions", chat_completions_proxy, methods=["POST"])
app.add_api_route("/api/v1/chat/completions/", chat_completions_proxy, methods=["POST"])
app.add_api_route("/v1/chat/completions/", chat_completions_options, methods=["OPTIONS"])
app.add_api_route("/api/v1/chat/completions", chat_completions_options, methods=["OPTIONS"])
app.add_api_route("/api/v1/chat/completions/", chat_completions_options, methods=["OPTIONS"])

# ==== AnimateDiff Video Generation Proxy ====
class VideoGenerationRequest(BaseModel):
    # Old format fields (for backward compatibility)
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = "blurry, low quality, distorted, text, watermark"
    num_frames: Optional[int] = 16
    guidance_scale: Optional[float] = 7.5
    steps: Optional[int] = 25
    seed: Optional[int] = 333
    fps: Optional[int] = 8
    target_endpoint: Optional[str] = None

    # New format fields (comprehensive video format)
    title: Optional[str] = None
    level: Optional[str] = None
    duration: Optional[str] = None
    tts_enabled: Optional[bool] = None
    scenes: Optional[list] = None
    prompts: Optional[list] = None
    text: Optional[str] = None
    video_style: Optional[str] = None
    style_modifiers: Optional[dict] = None
    metadata: Optional[dict] = None

@app.options("/proxy/vision")
async def proxy_video_generation_options():
    """Handle CORS preflight requests for video generation proxy"""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, x-api-key, ngrok-skip-browser-warning",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.post("/proxy/vision")
async def proxy_video_generation(request: VideoGenerationRequest):
    """
    Proxy endpoint to forward video generation requests to AnimateDiff API
    This solves CORS issues by making server-to-server requests
    Supports both old format (prompt-based) and new format (comprehensive video format)
    """
    try:
        # Check if this is the new comprehensive video format
        if request.title and request.scenes and request.prompts:
            # New comprehensive video format - forward as-is
            payload = {
                "title": request.title,
                "level": request.level,
                "duration": request.duration,
                "tts_enabled": request.tts_enabled,
                "scenes": request.scenes,
                "prompts": request.prompts,
                "text": request.text,
                "video_style": request.video_style,
                "style_modifiers": request.style_modifiers,
                "metadata": request.metadata
            }
            print(f"🎬 Using new comprehensive video format")
        else:
            # Old format - convert to old payload structure
            payload = {
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "num_frames": request.num_frames,
                "guidance_scale": request.guidance_scale,
                "steps": request.steps,
                "seed": request.seed,
                "fps": request.fps
            }
            print(f"🎬 Using legacy prompt-based format")

        # Use the target endpoint if provided, otherwise use default
        target_url = request.target_endpoint or "https://a8df3061f7ec.ngrok-free.app/generate-video"

        print(f"🎬 Proxying video generation request to: {target_url}")
        print(f"🎬 Payload: {payload}")

        # Headers for AnimateDiff API (read from env)
        headers = {
            "Content-Type": "application/json",
            "x-api-key": os.getenv("VISION_API_KEY", ""),
            "ngrok-skip-browser-warning": "true"
        }

        # Make the request to AnimateDiff API
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for video generation
            response = await client.post(target_url, json=payload, headers=headers)

            print(f"🎬 AnimateDiff API response status: {response.status_code}")

            if response.status_code == 200:
                # Check if response is video content
                content_type = response.headers.get("content-type", "")

                if "video/" in content_type:
                    # Return video content directly
                    return Response(
                        content=response.content,
                        media_type=content_type,
                        headers={
                            "Content-Disposition": "attachment; filename=generated_video.mp4",
                            "Access-Control-Allow-Origin": "*"
                        }
                    )
                else:
                    # Return JSON response
                    return response.json()
            else:
                # Forward error response
                error_detail = f"AnimateDiff API returned {response.status_code}: {response.text}"
                print(f"🎬 Error: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=error_detail)

    except httpx.TimeoutException:
        print("🎬 Request to AnimateDiff API timed out")
        raise HTTPException(status_code=504, detail="Video generation request timed out")
    except httpx.ConnectError:
        print("🎬 Failed to connect to AnimateDiff API")
        raise HTTPException(status_code=503, detail="Cannot connect to AnimateDiff service at 192.168.0.121:8501")
    except Exception as e:
        print(f"🎬 Proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

@app.options("/test-generate-video")
async def test_video_generation_options():
    """Handle CORS preflight requests for test video generation"""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, x-api-key, ngrok-skip-browser-warning",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.post("/test-generate-video")
async def test_video_generation(request: VideoGenerationRequest):
    """
    Test endpoint that proxies to the test endpoint on AnimateDiff API
    Supports both old format (prompt-based) and new format (comprehensive video format)
    """
    try:
        # Check if this is the new comprehensive video format
        if request.title and request.scenes and request.prompts:
            # New comprehensive video format - forward as-is
            payload = {
                "title": request.title,
                "level": request.level,
                "duration": request.duration,
                "tts_enabled": request.tts_enabled,
                "scenes": request.scenes,
                "prompts": request.prompts,
                "text": request.text,
                "video_style": request.video_style,
                "style_modifiers": request.style_modifiers,
                "metadata": request.metadata
            }
            print(f"🎬 Test endpoint using new comprehensive video format")
        else:
            # Old format - convert to old payload structure
            payload = {
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "num_frames": request.num_frames,
                "guidance_scale": request.guidance_scale,
                "steps": request.steps,
                "seed": request.seed,
                "fps": request.fps
            }
            print(f"🎬 Test endpoint using legacy prompt-based format")

        target_url = "https://a8df3061f7ec.ngrok-free.app/test-generate-video"

        print(f"🎬 Proxying test video generation request to: {target_url}")

        # No API key needed for test endpoint
        headers = {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(target_url, json=payload, headers=headers)

            print(f"🎬 Test AnimateDiff API response status: {response.status_code}")

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")

                if "video/" in content_type:
                    return Response(
                        content=response.content,
                        media_type=content_type,
                        headers={
                            "Content-Disposition": "attachment; filename=test_video.mp4",
                            "Access-Control-Allow-Origin": "*"
                        }
                    )
                else:
                    return response.json()
            else:
                error_detail = f"Test AnimateDiff API returned {response.status_code}: {response.text}"
                print(f"🎬 Test Error: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=error_detail)

    except Exception as e:
        print(f"🎬 Test proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test proxy error: {str(e)}")

@app.post("/proxy/vision-flexible")
async def proxy_video_generation_flexible(request: dict):
    """
    Flexible proxy endpoint that accepts any JSON payload for video generation
    This is useful for debugging and testing new formats
    """
    try:
        print(f"🎬 Flexible proxy received payload keys: {list(request.keys())}")

        # Use the target endpoint if provided, otherwise use default
        target_url = request.get("target_endpoint", "https://a8df3061f7ec.ngrok-free.app/generate-video")

        # Remove target_endpoint from payload before forwarding
        payload = {k: v for k, v in request.items() if k != "target_endpoint"}

        print(f"🎬 Forwarding to: {target_url}")

        # Headers for AnimateDiff API (read from env)
        headers = {
            "Content-Type": "application/json",
            "x-api-key": os.getenv("VISION_API_KEY", ""),
            "ngrok-skip-browser-warning": "true"
        }

        # Make the request to AnimateDiff API
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(target_url, json=payload, headers=headers)

            print(f"🎬 Flexible proxy response status: {response.status_code}")

            if response.status_code == 200:
                # Check if response is video content
                content_type = response.headers.get("content-type", "")

                if "video/" in content_type:
                    # Return video content directly
                    return Response(
                        content=response.content,
                        media_type=content_type,
                        headers={
                            "Content-Disposition": "attachment; filename=generated_video.mp4",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                            "Access-Control-Allow-Headers": "Content-Type, x-api-key, ngrok-skip-browser-warning"
                        }
                    )
                else:
                    # Return JSON response with CORS headers
                    json_response = response.json()
                    return Response(
                        content=json.dumps(json_response),
                        media_type="application/json",
                        headers={
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                            "Access-Control-Allow-Headers": "Content-Type, x-api-key, ngrok-skip-browser-warning"
                        }
                    )
            else:
                # Forward error response
                error_detail = f"AnimateDiff API returned {response.status_code}: {response.text}"
                print(f"🎬 Flexible proxy error: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=error_detail)

    except httpx.TimeoutException:
        print("🎬 Flexible proxy request timed out")
        raise HTTPException(status_code=504, detail="Video generation request timed out")
    except httpx.ConnectError:
        print("🎬 Flexible proxy failed to connect")
        raise HTTPException(status_code=503, detail="Cannot connect to AnimateDiff service")
    except Exception as e:
        print(f"🎬 Flexible proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

# ==== Video Storage and Retrieval System ====

# Create videos directory if it doesn't exist
VIDEOS_DIR = "generated_videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

# In-memory storage for video metadata (in production, use a database)
video_metadata_store = {}

@app.post("/receive-video")
async def receive_video_from_generation_system(
    video: UploadFile = File(...),
    metadata: str = Form(...)
):
    """
    POST endpoint to receive generated videos from the AnimateDiff system
    """
    try:
        # Parse metadata
        video_meta = json.loads(metadata)

        # Generate unique video ID
        video_id = str(uuid.uuid4())

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{video_id}_{timestamp}.mp4"
        file_path = os.path.join(VIDEOS_DIR, filename)

        print(f"🎬 Receiving video from generation system...")
        print(f"🎬 Video ID: {video_id}")
        print(f"🎬 Filename: {filename}")
        print(f"🎬 Metadata: {video_meta}")

        # Save the video file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Store metadata
        video_metadata_store[video_id] = {
            **video_meta,
            "video_id": video_id,
            "filename": filename,
            "file_path": file_path,
            "received_at": datetime.now().isoformat(),
            "file_size": os.path.getsize(file_path)
        }

        # Generate access URL
        access_url = f"/videos/{video_id}"

        print(f"✅ Video received and stored successfully!")
        print(f"🎬 Access URL: {access_url}")

        return {
            "success": True,
            "message": "Video received and stored successfully",
            "video_id": video_id,
            "access_url": access_url,
            "filename": filename,
            "file_size": os.path.getsize(file_path)
        }

    except json.JSONDecodeError as e:
        print(f"❌ Invalid metadata JSON: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {str(e)}")
    except Exception as e:
        print(f"❌ Error receiving video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error receiving video: {str(e)}")

@app.get("/videos/{video_id}")
async def get_video(video_id: str):
    """
    GET endpoint to serve stored videos
    """
    try:
        if video_id not in video_metadata_store:
            raise HTTPException(status_code=404, detail="Video not found")

        video_info = video_metadata_store[video_id]
        file_path = video_info["file_path"]

        if not os.path.exists(file_path):
            print(f"❌ Video file not found on disk: {file_path}")
            raise HTTPException(status_code=404, detail="Video file not found on disk")

        print(f"🎬 Serving video: {video_id}")
        print(f"🎬 File path: {file_path}")

        return FileResponse(
            path=file_path,
            media_type="video/mp4",
            filename=video_info["filename"],
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=3600"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error serving video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving video: {str(e)}")

@app.get("/videos/{video_id}/info")
async def get_video_info(video_id: str):
    """
    GET endpoint to retrieve video metadata
    """
    try:
        if video_id not in video_metadata_store:
            raise HTTPException(status_code=404, detail="Video not found")

        video_info = video_metadata_store[video_id]

        # Remove file_path from response for security
        response_info = {k: v for k, v in video_info.items() if k != "file_path"}

        return {
            "success": True,
            "video_info": response_info
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting video info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting video info: {str(e)}")

@app.get("/videos")
async def list_videos():
    """
    GET endpoint to list all stored videos
    """
    try:
        videos = []
        for video_id, info in video_metadata_store.items():
            # Remove file_path from response for security
            video_summary = {k: v for k, v in info.items() if k != "file_path"}
            videos.append(video_summary)

        return {
            "success": True,
            "count": len(videos),
            "videos": videos
        }

    except Exception as e:
        print(f"❌ Error listing videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing videos: {str(e)}")

if __name__ == "__main__":
    try:
        # Base Backend runs on port 8000 as the main API
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise



