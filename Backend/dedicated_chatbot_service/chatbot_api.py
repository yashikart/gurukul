"""
Dedicated Chatbot Service - Port 8001
Separated from other backend services to avoid conflicts
"""

import os
import sys
import io
import shutil
import time
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
import uvicorn
import logging

# Note: Emoji characters have been removed from print statements to avoid
# Unicode encoding issues on Windows. No stdout/stderr wrapping needed
# as it conflicts with uvicorn's stream handling.

# Load .env FIRST before anything else
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)
print(f"\n{'='*60}")
print("[INFO] LOADING ENVIRONMENT")
print(f"   .env path: {env_path}")
print(f"   GROQ_API_KEY: {'[OK] SET' if os.getenv('GROQ_API_KEY', '').strip() else '[NOT SET]'}")
print(f"   GROQ_MODEL_NAME: {os.getenv('GROQ_MODEL_NAME', 'llama-3.1-70b-versatile')}")
print(f"{'='*60}\n")

# Add parent directory to path to import required modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import or create LLM service inline
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Base_backend'))
    from llm_service import LLMService
except ImportError:
    # Define LLM service inline if import fails
    import requests
    import json
    
    class LLMService:
        def __init__(self):
            self.groq_api_key = os.getenv('GROQ_API_KEY', '').strip()
            self.openai_api_key = os.getenv('OPENAI_API_KEY', '').strip()
            self.groq_model = os.getenv('GROQ_MODEL_NAME', 'llama-3.1-70b-versatile')
            
            # Log configuration (without secrets)
            print(f"🔧 LLM Service Configuration:")
            print(f"   Groq API Key: {'✅ SET' if self.groq_api_key else '❌ NOT SET'}")
            print(f"   Groq Model: {self.groq_model}")
            print(f"   OpenAI API Key: {'✅ SET' if self.openai_api_key else '❌ NOT SET'}")
        
        def call_groq_api(self, prompt: str) -> dict:
            """Call real Groq API"""
            if not self.groq_api_key:
                return {"ok": False, "error": "Groq API key not configured"}
            
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
                
                print(f"🔄 Calling Groq API: {url}")
                print(f"   Model: {self.groq_model}")
                print(f"   Prompt: {prompt[:100]}...")
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                print(f"📡 Groq API Response: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    message = data['choices'][0]['message']['content']
                    print(f"✅ Groq Success: {message[:100]}...")
                    return {"ok": True, "provider": "groq", "message": message}
                else:
                    error_text = response.text[:200]
                    print(f"❌ Groq Error {response.status_code}: {error_text}")
                    return {"ok": False, "error": f"Groq API error {response.status_code}: {error_text}"}
                    
            except Exception as e:
                print(f"❌ Groq Exception: {str(e)}")
                return {"ok": False, "error": f"Groq exception: {str(e)}"}
        
        def call_openai(self, prompt: str) -> dict:
            """Call OpenAI API"""
            if not self.openai_api_key:
                return {"ok": False, "error": "OpenAI API key not configured"}
            
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
                
                print(f"🔄 Calling OpenAI API")
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                print(f"📡 OpenAI API Response: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    message = data['choices'][0]['message']['content']
                    print(f"✅ OpenAI Success: {message[:100]}...")
                    return {"ok": True, "provider": "openai", "message": message}
                else:
                    error_text = response.text[:200]
                    print(f"❌ OpenAI Error {response.status_code}: {error_text}")
                    return {"ok": False, "error": f"OpenAI API error {response.status_code}"}
                    
            except Exception as e:
                print(f"❌ OpenAI Exception: {str(e)}")
                return {"ok": False, "error": f"OpenAI exception: {str(e)}"}
        
        def get_fallback_response(self, prompt: str) -> dict:
            """Fallback response when all providers fail"""
            prompt_lower = prompt.lower()
            if any(word in prompt_lower for word in ['hello', 'hi', 'hey']):
                message = "Hello! I'm your AI assistant. How can I help you today? (Note: I'm currently running in fallback mode as the main AI services are temporarily unavailable.)"
            else:
                message = f"I understand you're asking about '{prompt[:50]}...'. While I'm currently in fallback mode, I'd be happy to help once our main AI services are restored. Please try again in a moment."
            return {"ok": True, "provider": "fallback", "message": message}
        
        def generate_response(self, prompt: str, preferred_provider: str = None) -> str:
            """Generate response with provider fallback"""
            print(f"\n{'='*60}")
            print(f"🤖 LLM REQUEST: {prompt[:100]}...")
            print(f"   Preferred Provider: {preferred_provider or 'auto'}")
            print(f"{'='*60}")
            
            # Try preferred provider first
            if preferred_provider == "groq":
                result = self.call_groq_api(prompt)
                if result["ok"]:
                    print(f"✅ Using Groq response")
                    return result["message"]
                print(f"⚠️ Groq failed: {result.get('error')}")
            
            elif preferred_provider == "openai":
                result = self.call_openai(prompt)
                if result["ok"]:
                    print(f"✅ Using OpenAI response")
                    return result["message"]
                print(f"⚠️ OpenAI failed: {result.get('error')}")
            
            # Try all providers if no preference or preferred failed
            print(f"🔄 Trying all available providers...")
            
            # Try Groq
            if self.groq_api_key:
                result = self.call_groq_api(prompt)
                if result["ok"]:
                    print(f"✅ Using Groq response (fallback)")
                    return result["message"]
                print(f"⚠️ Groq failed: {result.get('error')}")
            
            # Try OpenAI
            if self.openai_api_key:
                result = self.call_openai(prompt)
                if result["ok"]:
                    print(f"✅ Using OpenAI response (fallback)")
                    return result["message"]
                print(f"⚠️ OpenAI failed: {result.get('error')}")
            
            # All providers failed - use fallback
            print(f"❌ All providers failed - using fallback response")
            result = self.get_fallback_response(prompt)
            return result["message"]

# Define streaming TTS function (always available)
def text_to_speech_stream(text):
    """Generate TTS audio and return as bytes stream"""
    try:
        from gtts import gTTS
        import io

        # Generate TTS audio in memory
        tts = gTTS(text=text, lang="en")

        # Create in-memory buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return audio_buffer.getvalue()
    except Exception as e:
        print(f"TTS Streaming Error: {e}")
        return None

# Import PDF and image processing functions
try:
    from rag import parse_pdf, build_qa_agent, extract_text_easyocr, text_to_speech
    # Use extract_text_easyocr as process_image_with_ocr
    process_image_with_ocr = extract_text_easyocr
    print("[OK] Successfully imported processing modules from rag.py")
except ImportError as e:
    print(f"[WARN] Some processing modules not available: {e}")
    # Define fallback functions
    def parse_pdf(path):
        return {"body": "PDF processing not available"}
    def build_qa_agent(content, groq_api_key):
        class MockAgent:
            def invoke(self, query):
                return {"result": "PDF processing not available"}
        return MockAgent()
    def process_image_with_ocr(path):
        return "Image processing not available"

    # Keep legacy function for backward compatibility (deprecated)
    def text_to_speech(text, file_prefix="output"):
        try:
            from gtts import gTTS
            import time
            import os

            # Create static directory if it doesn't exist
            static_dir = "static"
            if not os.path.exists(static_dir):
                os.makedirs(static_dir)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(static_dir, f"{file_prefix}_{timestamp}.mp3")

            tts = gTTS(text=text, lang="en")
            tts.save(output_file)

            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return output_file
            else:
                return None
        except Exception as e:
            print(f"TTS Error: {e}")
            return None

# Environment already loaded at top of file
# Add parent to path for imports
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

# Try to load shared config but don't fail if it doesn't exist
try:
    from shared_config import load_shared_config
    load_shared_config("dedicated_chatbot_service")
except:
    pass  # .env already loaded

# Configure logging
from utils.logging_config import configure_logging
logger = configure_logging("dedicated_chatbot_service")

# Import centralized CORS helper
from common.cors import configure_cors

# MongoDB Configuration (no hardcoded credentials)
MONGO_URI = (
    os.getenv("MONGODB_URI")
    or os.getenv("MONGO_URI")
    or os.getenv("MONGODB_URL")
    or "mongodb://localhost:27017/"
)

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    logger.info("✅ MongoDB connection successful!")
    
    db = client["gurukul"]
    # Use a separate collection for dedicated chatbot to avoid conflicts
    chat_collection = db["dedicated_chat_messages"]
    mongodb_available = True
    
except Exception as e:
    logger.warning(f"⚠️ MongoDB connection failed: {e}")
    logger.info("📝 Service will continue without MongoDB persistence")
    client = None
    db = None
    chat_collection = None
    mongodb_available = False

# Initialize LLM Service
print("\n" + "="*60)
print("🚀 INITIALIZING LLM SERVICE")
print("="*60)
llm_service = LLMService()
print("="*60 + "\n")

# Create temporary directory for file processing
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Global variables for storing latest processing results
pdf_response = None
image_response = None

# FastAPI App
app = FastAPI(
    title="Dedicated Chatbot Service",
    description="Standalone chatbot service running on port 8001",
    version="1.0.0"
)

# Configure CORS using centralized helper
configure_cors(app)

# Add request logging middleware to debug CORS
from fastapi import Request, Response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin", "no-origin")
    method = request.method
    path = request.url.path
    
    logger.info(f"🌐 {method} {path} | Origin: {origin}")
    
    # Log preflight details
    if method == "OPTIONS":
        req_method = request.headers.get("access-control-request-method", "N/A")
        req_headers = request.headers.get("access-control-request-headers", "N/A")
        logger.info(f"   🔄 PREFLIGHT | Method: {req_method} | Headers: {req_headers}")
    
    response = await call_next(request)
    logger.info(f"   ✅ Response: {response.status_code}")
    return response

# Explicit OPTIONS handlers for chatbot endpoints
@app.options("/chatpost")
async def chatpost_preflight(request: Request):
    logger.info("🔄 PREFLIGHT /chatpost")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

@app.options("/chatbot")
async def chatbot_preflight(request: Request):
    logger.info("🔄 PREFLIGHT /chatbot")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# Catch-all OPTIONS handler
@app.options("/{full_path:path}")
async def options_handler(full_path: str, request: Request):
    logger.info(f"🔄 PREFLIGHT /{full_path}")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# Pydantic Models
class ChatMessage(BaseModel):
    message: str
    llm: Optional[str] = "uniguru"
    type: str = "chat_message"

class ChatResponse(BaseModel):
    message: str
    timestamp: str
    type: str = "chat_response"
    user_id: str

class PDFResponse(BaseModel):
    summary: str
    audio_file: str
    timestamp: str

class ImageResponse(BaseModel):
    summary: str
    audio_file: str
    timestamp: str

# Health Check Endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with provider testing"""
    try:
        # Check MongoDB
        mongodb_status = "connected" if mongodb_available else "unavailable"
        if mongodb_available:
            try:
                client.admin.command('ismaster')
            except:
                mongodb_status = "disconnected"
        
        # Check API keys
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        
        # Test Groq with lightweight call
        groq_status = False
        if groq_key:
            try:
                test_result = llm_service.call_groq_api("Hi")
                groq_status = test_result.get("success", False) or test_result.get("ok", False)
                logger.info(f"🧪 Groq health test: {'PASS' if groq_status else 'FAIL'}")
            except Exception as e:
                logger.warning(f"⚠️ Groq health test failed: {e}")
        
        return {
            "status": "healthy",
            "service": "Dedicated Chatbot Service",
            "port": 8001,
            "mongodb": mongodb_status,
            "groq": groq_status,
            "groq_configured": bool(groq_key),
            "openai_configured": bool(openai_key),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Don't fail health check - return degraded status
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Chat Endpoints
# In-memory storage when MongoDB is unavailable
memory_store = {}

@app.post("/chatpost")
async def receive_chat_message(chat: ChatMessage, user_id: str = "guest-user"):
    """
    Receive and store chat message from frontend
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Create message record
        message_record = {
            "message": chat.message,
            "timestamp": timestamp,
            "type": chat.type,
            "user_id": user_id,
            "llm_model": chat.llm,
            "response": None,
            "status": "pending"
        }
        
        # Store in MongoDB or memory
        if mongodb_available and chat_collection is not None:
            result = chat_collection.insert_one(message_record)
            message_id = str(result.inserted_id)
        else:
            # Use memory storage
            message_id = f"mem_{user_id}_{timestamp}"
            memory_store[message_id] = message_record
        
        logger.info(f"📝 Received message from user {user_id}: {chat.message}")
        
        return {
            "status": "success",
            "message": "Query received",
            "data": {
                "id": message_id,
                "user_id": user_id,
                "timestamp": timestamp
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error storing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store message: {str(e)}")

@app.get("/chatbot")
async def get_chat_response(user_id: str = "guest-user"):
    """
    Generate and return AI response for the latest user message
    """
    try:
        # Find the latest pending message
        if mongodb_available and chat_collection is not None:
            latest_query = chat_collection.find_one(
                {
                    "user_id": user_id,
                    "type": "chat_message", 
                    "response": None,
                    "status": "pending"
                }, 
                sort=[("timestamp", -1)]
            )
        else:
            # Use memory storage
            latest_query = None
            for msg_id, msg in sorted(memory_store.items(), key=lambda x: x[1]['timestamp'], reverse=True):
                if msg['user_id'] == user_id and msg['status'] == 'pending':
                    latest_query = msg
                    latest_query['_id'] = msg_id
                    break
        
        if not latest_query:
            logger.warning(f"⚠️ No pending queries found for user: {user_id}")
            return {"error": "No queries yet"}
        
        query_message = latest_query["message"]
        llm_model = latest_query.get("llm_model", "uniguru")

        logger.info(f"🤖 Processing query for user {user_id}: {query_message}")

        # Generate AI response using LLM service
        logger.info(f"\n{'='*60}")
        logger.info(f"💬 CHAT REQUEST")
        logger.info(f"   User: {user_id}")
        logger.info(f"   Model: {llm_model}")
        logger.info(f"   Query: {query_message}")
        logger.info(f"{'='*60}")
        
        try:
            # Map frontend model names to providers
            if llm_model in ["uniguru", "grok", "llama"]:
                logger.info(f"🎯 Routing to Groq provider")
                ai_response = llm_service.generate_response(query_message, preferred_provider="groq")
            elif llm_model == "chatgpt":
                logger.info(f"🎯 Routing to OpenAI provider")
                ai_response = llm_service.generate_response(query_message, preferred_provider="openai")
            elif llm_model in ["arabic", "local", "arabic-model"]:
                logger.info(f"🎯 Routing to Local Arabic Model provider")
                ai_response = llm_service.generate_response(query_message, preferred_provider="local")
            else:
                logger.info(f"🎯 Using auto provider selection")
                ai_response = llm_service.generate_response(query_message)
            
            logger.info(f"\n✅ FINAL RESPONSE: {ai_response[:150]}...")
            logger.info(f"{'='*60}\n")
                
        except Exception as llm_error:
            logger.error(f"\n❌ LLM GENERATION EXCEPTION")
            logger.error(f"   Error: {llm_error}")
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            logger.error(f"{'='*60}\n")
            # Only use fallback if exception occurs
            fallback_result = llm_service.get_fallback_response(query_message)
            ai_response = fallback_result["message"]
        
        # Create response data
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        response_data = {
            "message": ai_response,
            "timestamp": timestamp,
            "type": "chat_response",
            "user_id": user_id,
            "llm_model": llm_model
        }
        
        # Update the original message with the response
        if mongodb_available and chat_collection is not None:
            chat_collection.update_one(
                {"_id": latest_query["_id"]},
                {
                    "$set": {
                        "response": response_data,
                        "status": "completed"
                    }
                }
            )
        else:
            # Update memory storage
            if latest_query["_id"] in memory_store:
                memory_store[latest_query["_id"]]['response'] = response_data
                memory_store[latest_query["_id"]]['status'] = 'completed'
        
        logger.info(f"✅ Generated response for user {user_id}")
        
        return {
            "_id": str(latest_query["_id"]),
            "query": query_message,
            "response": response_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating chat response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

@app.get("/chat-history")
async def get_chat_history(user_id: str = "guest-user", limit: int = 50):
    """
    Get chat history for a user
    """
    try:
        # Get completed chat messages for the user
        messages = list(chat_collection.find(
            {
                "user_id": user_id,
                "status": "completed"
            },
            sort=[("timestamp", -1)],
            limit=limit
        ))
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": str(msg["_id"]),
                "user_message": msg["message"],
                "ai_response": msg["response"]["message"] if msg["response"] else None,
                "timestamp": msg["timestamp"],
                "llm_model": msg.get("llm_model", "unknown")
            })
        
        return {
            "user_id": user_id,
            "messages": formatted_messages,
            "total": len(formatted_messages)
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

# PDF Processing Endpoints
@app.post("/process-pdf", response_model=PDFResponse)
async def process_pdf(file: UploadFile = File(...)):
    """Process PDF file and generate summary with audio"""
    global pdf_response
    temp_pdf_path = ""

    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Save uploaded file temporarily
        temp_pdf_path = os.path.join(TEMP_DIR, f"temp_pdf_{time.strftime('%Y%m%d_%H%M%S')}.pdf")
        with open(temp_pdf_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)

        # Parse PDF content
        structured_data = parse_pdf(temp_pdf_path)
        if not structured_data["body"]:
            raise HTTPException(status_code=400, detail="Failed to parse PDF content")

        # Generate summary using QA agent with improved prompt for paragraph formatting
        query = """Please provide a comprehensive, well-structured summary of this PDF document. 

IMPORTANT FORMATTING REQUIREMENTS:
- Write ONLY in clear, flowing paragraphs - DO NOT use bullet points, numbered lists, or any list formatting
- Use proper paragraph breaks (double line breaks) to separate different topics or sections
- Start with an overview paragraph that introduces the main subject and purpose of the document
- Follow with detailed paragraphs that cover the key concepts, findings, and important information
- Each paragraph should be substantial (3-5 sentences) and cover a complete thought or topic
- Conclude with a paragraph summarizing the main conclusions or takeaways
- Use smooth transitions between paragraphs for natural flow
- Write in a professional, readable style that flows naturally like an essay or article

Make the summary comprehensive yet concise, focusing on the most valuable information. Write in complete sentences and well-formed paragraphs. Avoid any formatting symbols like dashes, asterisks, or numbers at the start of lines."""
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        agent = build_qa_agent([structured_data["body"]], groq_api_key=groq_api_key)
        result = agent.invoke({"query": query})
        answer = result["result"]
        
        # Post-process to ensure paragraph formatting (convert bullet points to paragraphs)
        import re
        # Split by lines
        lines = answer.split('\n')
        paragraphs = []
        current_para = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty line - end current paragraph
                if current_para:
                    para_text = ' '.join(current_para)
                    if para_text:
                        paragraphs.append(para_text)
                    current_para = []
            elif re.match(r'^[\s]*[•\-\*\d+\.\)]\s+', line):
                # Bullet point found - remove bullet and add to current paragraph
                cleaned = re.sub(r'^[\s]*[•\-\*\d+\.\)]\s+', '', line)
                if cleaned:
                    # Ensure it ends with proper punctuation
                    if not cleaned.endswith(('.', '!', '?', ':', ';')):
                        cleaned += '.'
                    current_para.append(cleaned)
            else:
                # Regular text - add to current paragraph
                current_para.append(line)
        
        # Add final paragraph if exists
        if current_para:
            para_text = ' '.join(current_para)
            if para_text:
                paragraphs.append(para_text)
        
        # Join paragraphs with double newlines
        answer = '\n\n'.join(paragraphs)
        
        # Clean up any remaining formatting issues
        answer = re.sub(r'\n{3,}', '\n\n', answer)  # Remove excessive newlines
        answer = answer.strip()

        # Generate audio
        audio_file = text_to_speech(answer, file_prefix="output_pdf")
        audio_url = f"/static/{os.path.basename(audio_file)}" if audio_file else "No audio generated"

        # Create response
        timestamp = datetime.now(timezone.utc).isoformat()
        pdf_response = PDFResponse(
            summary=answer,
            audio_file=audio_url,
            timestamp=timestamp
        )

        logger.info(f"✅ PDF processed successfully: {file.filename}")
        return pdf_response

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error processing PDF: {error_msg}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {error_msg}")
    finally:
        # Clean up temporary file
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {e}")

@app.post("/process-img", response_model=ImageResponse)
async def process_image(file: UploadFile = File(...)):
    """Process image file and generate summary with audio"""
    global image_response
    temp_image_path = ""

    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed")

        # Save uploaded file temporarily
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        temp_image_path = os.path.join(TEMP_DIR, f"temp_image_{time.strftime('%Y%m%d_%H%M%S')}.{file_extension}")
        with open(temp_image_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)

        # Process image with OCR
        ocr_text = process_image_with_ocr(temp_image_path)

        if not ocr_text or ocr_text.strip() == "":
            answer = "No readable text found in the image."
        else:
            # Generate summary using QA agent
            query = """Please provide a comprehensive, well-structured summary of this image and its content.

IMPORTANT FORMATTING REQUIREMENTS:
- Write ONLY in clear, flowing paragraphs - DO NOT use bullet points, numbered lists, or any list formatting
- Use proper paragraph breaks (double line breaks) to separate different topics or sections
- Start with an overview paragraph describing what the image contains and its main purpose
- Follow with detailed paragraphs covering the key information, text content, and visual elements
- Each paragraph should be substantial (3-5 sentences) and cover a complete thought or topic
- Conclude with a paragraph summarizing the main points or significance
- Use smooth transitions between paragraphs for natural flow
- Write in a professional, readable style that flows naturally like an essay or article

Make the summary comprehensive yet concise, focusing on the most valuable information. Write in complete sentences and well-formed paragraphs. Avoid any formatting symbols like dashes, asterisks, or numbers at the start of lines."""
            groq_api_key = os.getenv("GROQ_API_KEY")
            agent = build_qa_agent([ocr_text], groq_api_key=groq_api_key)
            result = agent.invoke({"query": query})
            answer = result["result"]
            
            # Post-process to ensure paragraph formatting (convert bullet points to paragraphs)
            import re
            # Split by lines
            lines = answer.split('\n')
            paragraphs = []
            current_para = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    # Empty line - end current paragraph
                    if current_para:
                        para_text = ' '.join(current_para)
                        if para_text:
                            paragraphs.append(para_text)
                        current_para = []
                elif re.match(r'^[\s]*[•\-\*\d+\.\)]\s+', line):
                    # Bullet point found - remove bullet and add to current paragraph
                    cleaned = re.sub(r'^[\s]*[•\-\*\d+\.\)]\s+', '', line)
                    if cleaned:
                        # Ensure it ends with proper punctuation
                        if not cleaned.endswith(('.', '!', '?', ':', ';')):
                            cleaned += '.'
                        current_para.append(cleaned)
                else:
                    # Regular text - add to current paragraph
                    current_para.append(line)
            
            # Add final paragraph if exists
            if current_para:
                para_text = ' '.join(current_para)
                if para_text:
                    paragraphs.append(para_text)
            
            # Join paragraphs with double newlines
            answer = '\n\n'.join(paragraphs)
            
            # Clean up any remaining formatting issues
            answer = re.sub(r'\n{3,}', '\n\n', answer)  # Remove excessive newlines
            answer = answer.strip()

        # Generate audio
        audio_file = text_to_speech(answer, file_prefix="output_image")
        audio_url = f"/static/{os.path.basename(audio_file)}" if audio_file else "No audio generated"

        # Create response
        timestamp = datetime.now(timezone.utc).isoformat()
        image_response = ImageResponse(
            summary=answer,
            audio_file=audio_url,
            timestamp=timestamp
        )

        logger.info(f"✅ Image processed successfully: {file.filename}")
        return image_response

    except Exception as e:
        logger.error(f"❌ Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {e}")

@app.get("/summarize-pdf", response_model=PDFResponse)
async def summarize_pdf():
    """Get the latest PDF summary"""
    if pdf_response is None:
        raise HTTPException(status_code=404, detail="No PDF has been processed yet.")
    return pdf_response

@app.get("/summarize-img", response_model=ImageResponse)
async def summarize_image():
    """Get the latest image summary"""
    if image_response is None:
        raise HTTPException(status_code=404, detail="No image has been processed yet.")
    return image_response

# Streaming endpoints for PDF and Image processing
@app.get("/process-pdf-stream")
async def process_pdf_stream(llm: str = "grok"):
    """Stream the latest PDF processing result"""
    global pdf_response
    
    if pdf_response is None:
        raise HTTPException(status_code=404, detail="No PDF has been processed yet. Please upload a PDF first.")
    
    # Return the summary as a streaming response
    def generate_stream():
        summary = pdf_response.summary if hasattr(pdf_response, 'summary') else ""
        
        if not summary:
            yield "data: [ERROR]No summary available\n\n"
            return
        
        # Stream the summary in chunks to simulate streaming
        # Use smaller chunks for smoother streaming effect
        chunk_size = 50
        import time
        
        for i in range(0, len(summary), chunk_size):
            chunk = summary[i:i + chunk_size]
            if chunk.strip():  # Only send non-empty chunks
                yield f"data: {chunk}\n\n"
                time.sleep(0.05)  # Small delay for streaming effect
        
        # Send end marker
        yield "data: [END]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/process-img-stream")
async def process_image_stream(llm: str = "grok"):
    """Stream the latest image processing result"""
    global image_response
    
    if image_response is None:
        raise HTTPException(status_code=404, detail="No image has been processed yet. Please upload an image first.")
    
    # Return the summary as a streaming response
    def generate_stream():
        summary = image_response.summary if hasattr(image_response, 'summary') else ""
        
        if not summary:
            yield "data: [ERROR]No summary available\n\n"
            return
        
        # Stream the summary in chunks to simulate streaming
        chunk_size = 50
        import time
        
        for i in range(0, len(summary), chunk_size):
            chunk = summary[i:i + chunk_size]
            if chunk.strip():  # Only send non-empty chunks
                yield f"data: {chunk}\n\n"
                time.sleep(0.05)  # Small delay for streaming effect
        
        # Send end marker
        yield "data: [END]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

# Streaming TTS Endpoint (New)
@app.post("/tts/stream")
async def generate_tts_stream(request: dict):
    """Generate TTS audio and stream directly without saving to disk"""
    try:
        text = request.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        # Generate audio stream
        audio_data = text_to_speech_stream(text)

        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio stream")

        # Create streaming response
        def generate_audio():
            yield audio_data

        return StreamingResponse(
            generate_audio(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=tts_audio.mp3",
                "Cache-Control": "no-cache",
                "X-Text-Length": str(len(text)),
                "X-Timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    except Exception as e:
        logger.error(f"TTS streaming error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS streaming failed: {str(e)}")

# TTS Endpoint (Legacy - for backward compatibility)
@app.post("/tts")
async def generate_tts(request: dict):
    """Generate TTS audio from text using Google TTS (Legacy - saves to file)"""
    try:
        text = request.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        # Generate audio file
        audio_file = text_to_speech(text, file_prefix="chatbot_tts")

        if not audio_file or not os.path.exists(audio_file):
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # Return audio file info
        filename = os.path.basename(audio_file)
        file_size = os.path.getsize(audio_file)

        return {
            "status": "success",
            "message": "Audio generated successfully",
            "audio_url": f"/static/{filename}",
            "filename": filename,
            "file_size": file_size,
            "text_length": len(text),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

# Static file serving for audio files
@app.get("/static/{filename}")
async def serve_audio_file(filename: str):
    """Serve generated audio files"""
    try:
        temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        file_path = os.path.join(temp_dir, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='audio/mpeg',
            headers={"Cache-Control": "public, max-age=3600"}
        )

    except Exception as e:
        logger.error(f"Error serving audio file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve audio: {str(e)}")

# Test endpoint for debugging
@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify service is working"""
    return {
        "status": "working",
        "service": "Dedicated Chatbot Service",
        "port": 8001,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Chatbot service is running correctly!"
    }

if __name__ == "__main__":
    import socket
    import time

    def check_port_available(port, host="127.0.0.1"):
        """Check if a port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return True
        except OSError:
            return False

    def find_available_port(start_port=8001, max_attempts=10):
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            if check_port_available(port):
                return port
        return None

    # Check if port 8001 is available
    target_port = 8001
    if not check_port_available(target_port):
        logger.warning(f"⚠️ Port {target_port} is already in use. Searching for alternative...")

        # Try to find an available port
        alternative_port = find_available_port(8001, 10)
        if alternative_port:
            target_port = alternative_port
            logger.info(f"🔄 Using alternative port: {target_port}")
        else:
            logger.error("❌ No available ports found in range 8001-8010")
            logger.info("💡 Trying to kill process using port 8001...")

            # Try to kill process using port 8001
            try:
                import subprocess
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    shell=True
                )

                for line in result.stdout.split('\n'):
                    if ':8001' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            logger.info(f"🔍 Found process {pid} using port 8001, attempting to terminate...")
                            subprocess.run(['taskkill', '/F', '/PID', pid], shell=True)
                            time.sleep(2)  # Wait for process to terminate

                            # Check if port is now available
                            if check_port_available(8001):
                                target_port = 8001
                                logger.info("[OK] Successfully freed port 8001")
                            break
            except Exception as e:
                logger.error(f"[ERROR] Failed to free port 8001: {e}")

    try:
        logger.info(f"[INFO] Starting Dedicated Chatbot Service on port {target_port}...")
        uvicorn.run(
            "chatbot_api:app",
            host="0.0.0.0",
            port=target_port,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"[ERROR] Failed to start service: {e}")
        logger.info("💡 Possible solutions:")
        logger.info("   1. Run as administrator")
        logger.info("   2. Check Windows Firewall settings")
        logger.info("   3. Ensure no other services are using the port")
        logger.info("   4. Try restarting your computer")
        raise
