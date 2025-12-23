from api_data.rag import *
import logging
import sys, os
# Ensure Backend is on path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_config import configure_logging
logger = configure_logging("api_data")
from dotenv import load_dotenv
import uvicorn
import requests
import os
import asyncio
from api_data.llm_service import llm_service
from datetime import datetime
from api_data.subject_data import subjects_data
from api_data.lectures_data import lectures_data
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Import Arabic translation utility
try:
    from arabic_translator import translate_to_arabic, translate_to_arabic_with_checkpoint
    ARABIC_TRANSLATOR_AVAILABLE = True
    logger.info("✅ Arabic translator module loaded successfully")
except ImportError as e:
    ARABIC_TRANSLATOR_AVAILABLE = False
    translate_to_arabic_with_checkpoint = None
    logger.warning(f"⚠️ Arabic translator module not available: {e}")
except Exception as e:
    ARABIC_TRANSLATOR_AVAILABLE = False
    translate_to_arabic_with_checkpoint = None
    logger.warning(f"⚠️ Error loading Arabic translator: {e}")
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
from api_data.db import pdf_collection , image_collection, user_collection
from datetime import datetime, timezone
import shutil
import time

# In-memory storage for agent data (in production, use a proper database)
agent_outputs = []
agent_logs = []
agent_simulations = {}  # Track active simulations by user_id
try:
    from docx import Document
    import docx2txt
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️ python-docx not available. DOC/DOCX support will be limited.")

# Load environment variables from centralized configuration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared_config import load_shared_config

# Load centralized configuration
load_shared_config("api_data")

# Create temporary directory for file processing
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from uuid import uuid4

# Initialize FastAPI app
app = FastAPI()

# Import centralized CORS configuration
from common.cors import configure_cors

# Configure CORS using centralized helper
configure_cors(app)

# Global exception handler for consistent errors
@app.exception_handler(Exception)
async def _on_error(request, exc):
    trace = str(uuid4())
    logger.exception(f"[{trace}] Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Unexpected error"}, "trace_id": trace})

# Generic OPTIONS handler for all paths
@app.options("/{path:path}")
async def options_handler(path: str):
    from fastapi.responses import Response
    return Response(status_code=200)

# Add a health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ==== Subject API Models and Routes ====
class Subject(BaseModel):
    id: int
    name: str
    code: str

@app.get("/subjects_dummy")
def get_subjects():
    return JSONResponse(content=subjects_data)


# ==== Lectures API Models and Routes ====
class Lecture(BaseModel):
    id: int
    topic: str
    subject_id: int

@app.get("/lecture_dummy")
def get_lectures():
    return JSONResponse(content=lectures_data)

# ==== Test API Models and Routes ====
class Test(BaseModel):
    id: int
    name: str
    subject_id: int
    date: Optional[str] = None


@app.get("/test_dummy")
def get_test():
    return JSONResponse(content=test_data)

#Chatbot
groq_api_key = os.environ.get('GROQ_API_KEY')

# Temporary in-memory storage
user_queries: List[dict] = []
llm_responses: List[dict] = []

# Pydantic model for request validation
class ChatMessage(BaseModel):
    message: str
    llm: str = "grok"  # Default to grok, accepts: grok, llama, chatgpt, uniguru
    language: str = "english"  # Default to english, accepts: english, arabic
    timestamp: str = None
    type: str = "chat_message"


# Route 1: Receive query from frontend
@app.post("/chatpost")
async def receive_query(chat: ChatMessage):
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    
    # Extract language and llm from the request
    language = chat.language if hasattr(chat, 'language') and chat.language else 'english'
    llm_model = chat.llm if hasattr(chat, 'llm') and chat.llm else 'grok'
    
    # Normalize language
    if not language:
        language = "english"
    language = str(language).lower().strip()
    
    print(f"🌐 [Backend] Received message in {language}: {chat.message[:100]}...")
    print(f"🤖 [Backend] Using model: {llm_model}")
    
    query_record = {
        "message": chat.message,
        "timestamp": timestamp,
        "type": "chat_message",
        "language": language,  # Store language
        "llm": llm_model,  # Store model (use 'llm' to match retrieval)
        "response": None  # Initialize response as None
    }
    try:
        chat_collection = user_collection.insert_one(query_record)
        query_record["_id"] = str(chat_collection.inserted_id)
        print(f"✅ [Backend] Message stored successfully")
        return {"status": "success", "message": "Query received", "data": query_record}
    except Exception as e:
        print(f"❌ [Backend] Error storing message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store query:{str(e)}")


import requests

def parse_word_document(file_path: str) -> dict:
    """Parse Word document (DOC/DOCX) and extract text content"""
    try:
        if not DOCX_AVAILABLE:
            raise Exception("python-docx library not available")

        # Extract text from DOCX file
        if file_path.lower().endswith('.docx'):
            # Method 1: Using python-docx for structured parsing
            try:
                doc = Document(file_path)
                paragraphs = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        paragraphs.append(paragraph.text.strip())

                raw_text = '\n'.join(paragraphs)

                # If no content found, try docx2txt as fallback
                if not raw_text.strip():
                    raw_text = docx2txt.process(file_path)

            except Exception:
                # Fallback to docx2txt
                raw_text = docx2txt.process(file_path)
        else:
            # For .doc files, we'll need a different approach
            # For now, return an error message
            raise Exception("DOC files are not fully supported. Please convert to DOCX format.")

        if not raw_text.strip():
            return {"title": "", "body": "", "sections": []}

        # Extract title (first non-empty line)
        lines = raw_text.strip().split('\n')
        title = next((line.strip() for line in lines if line.strip()), "")

        # Simple section detection (lines that look like headings)
        sections = []
        current_section = {"heading": "Content", "content": ""}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple heuristic for section headings (short lines, possibly numbered)
            if (len(line) < 100 and
                (line.isupper() or
                 any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', 'Chapter', 'Section']) or
                 line.endswith(':'))):
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                # Start new section
                current_section = {"heading": line, "content": ""}
            else:
                current_section["content"] += line + "\n"

        # Add the last section
        if current_section["content"].strip():
            sections.append(current_section)

        # If no sections were detected, put everything in one section
        if not sections:
            sections = [{"heading": "Document Content", "content": raw_text}]

        return {
            "title": title,
            "body": raw_text,
            "sections": sections
        }

    except Exception as e:
        print(f"Error parsing Word document: {e}")
        return {"title": "", "body": f"Error parsing document: {str(e)}", "sections": []}

def call_llm(prompt: str, llm: str, language: str = "english") -> str:
    """
    Call the specified LLM API with the given prompt.
    """
    groq_api_key = os.environ.get('GROQ_API_KEY', '').strip()
    openai_api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    
    # Debug logging
    print(f"🔍 [call_llm] LLM: {llm}, GROQ_API_KEY present: {bool(groq_api_key)}, Length: {len(groq_api_key) if groq_api_key else 0}")
    logger.info(f"Calling LLM: {llm}, API key present: {bool(groq_api_key)}")

    try:
        if llm == "grok":
            # Use Groq API with reliable LLaMA models
            if not groq_api_key:
                raise Exception("GROQ_API_KEY environment variable is not set or is empty")
            
            # Remove any quotes or whitespace from API key
            groq_api_key = groq_api_key.strip().strip('"').strip("'")
            
            if not groq_api_key or len(groq_api_key) < 10:
                raise Exception(f"GROQ_API_KEY appears to be invalid (length: {len(groq_api_key)})")
            
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            
            # Try multiple models with automatic fallback
            models_to_try = ["llama-3.1-70b-versatile", "llama-3.1-8b-instant"]
            last_error = None
            
            for model_name in models_to_try:
                try:
                    # Create system message with language requirement if Arabic
                    system_message = "You are a helpful AI assistant that provides detailed, comprehensive summaries and analysis."
                    if language and str(language).lower() == "arabic":
                        system_message = """أنت مساعد ذكي مفيد. يجب أن ترد دائماً بالكامل باللغة العربية فقط.

⚠️ تعليمات حرجة ⚠️:
- جميع ردودك يجب أن تكون بالكامل باللغة العربية (العربية)
- لا تستخدم أي كلمات إنجليزية أو أحرف لاتينية
- اكتب كل شيء بالعربية فقط
- استخدم النص العربي الصحيح والتنسيق المناسب
- لا ترد بالإنجليزية أبداً عندما يُطلب منك الرد بالعربية"""
                        print(f"🌐 [call_llm] System message set to Arabic for model: {model_name}")
                    else:
                        print(f"ℹ️ [call_llm] System message set to English for model: {model_name}")
                    
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2048,
                        "top_p": 1.0
                    }
                    
                    print(f"🔍 [call_llm] Trying model: {model_name}")
                    print(f"🔍 [call_llm] Prompt length: {len(prompt)} chars")
                    
                    try:
                        response = requests.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=60
                        )
                    except requests.exceptions.Timeout:
                        raise Exception("Groq API request timed out after 60 seconds.")
                    except requests.exceptions.ConnectionError as conn_err:
                        raise Exception(f"Failed to connect to Groq API: {str(conn_err)}")
                    
                    print(f"🔍 [call_llm] Response status: {response.status_code}")
                    
                    if response.status_code == 401:
                        error_detail = response.text[:500] if response.text else "No error details"
                        print(f"❌ [call_llm] 401 Unauthorized - API key issue")
                        raise Exception(f"Invalid GROQ_API_KEY (401). Please verify your API key. Error: {error_detail[:200]}")
                    elif response.status_code == 400:
                        error_detail = response.text[:500] if response.text else "No error details"
                        print(f"⚠️ [call_llm] Model {model_name} returned 400: {error_detail[:200]}")
                        last_error = f"Model {model_name}: {error_detail[:200]}"
                        if model_name == models_to_try[-1]:
                            raise Exception(f"All models failed. Last error: {last_error}")
                        continue  # Try next model
                    elif response.status_code == 429:
                        error_detail = response.text[:500] if response.text else "No error details"
                        raise Exception(f"Rate limit exceeded (429). Error: {error_detail[:200]}")
                    elif response.status_code >= 500:
                        error_detail = response.text[:500] if response.text else "No error details"
                        print(f"⚠️ [call_llm] Server error {response.status_code} with {model_name}")
                        last_error = f"Server error ({response.status_code}): {error_detail[:200]}"
                        if model_name == models_to_try[-1]:
                            raise Exception(f"All models failed. Last error: {last_error}")
                        continue  # Try next model
                    
                    response.raise_for_status()
                    
                    try:
                        result = response.json()
                    except Exception as json_error:
                        error_text = response.text[:500] if response.text else "No response"
                        raise Exception(f"Failed to parse JSON: {str(json_error)}. Response: {error_text[:200]}")
                    
                    if 'choices' not in result or len(result['choices']) == 0:
                        last_error = f"No choices returned: {str(result)[:200]}"
                        if model_name == models_to_try[-1]:
                            raise Exception(f"All models failed. Last error: {last_error}")
                        continue  # Try next model
                    
                    content = result['choices'][0]['message']['content'].strip()
                    print(f"✅ [call_llm] Success with {model_name} (length: {len(content)} chars)")
                    return content
                    
                except Exception as model_error:
                    error_str = str(model_error)
                    if "401" in error_str or "Invalid GROQ_API_KEY" in error_str or "timed out" in error_str.lower() or "connect" in error_str.lower():
                        raise  # Don't try other models for these errors
                    last_error = error_str[:200]
                    if model_name == models_to_try[-1]:
                        raise Exception(f"All models failed. Last error: {last_error}")
                    print(f"⚠️ [call_llm] {model_name} failed: {last_error}, trying next...")
                    continue
            
            raise Exception(f"All models failed: {last_error}")

        elif llm == "llama":
            # Use Groq API with larger LLaMA model
            if not groq_api_key:
                raise Exception("GROQ_API_KEY environment variable is not set or is empty")
            
            # Remove any quotes or whitespace from API key
            groq_api_key = groq_api_key.strip().strip('"').strip("'")
            
            if not groq_api_key or len(groq_api_key) < 10:
                raise Exception(f"GROQ_API_KEY appears to be invalid (length: {len(groq_api_key)})")
            
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            # Add a system message to make LLaMA responses more distinctive
            system_message = "You are LLaMA, a helpful, harmless, and honest AI assistant. You provide detailed, thoughtful responses with a focus on being educational and comprehensive."
            if language and str(language).lower() == "arabic":
                system_message = "You are LLaMA, a helpful, harmless, and honest AI assistant. You provide detailed, thoughtful responses with a focus on being educational and comprehensive. CRITICAL: You MUST respond ENTIRELY in Arabic (العربية). All your responses must be in Arabic using proper Arabic script and formatting. Never respond in English when Arabic is requested."
            
            payload = {
                "model": "llama-3.3-70b-versatile",  # Larger LLaMA model
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,  # Balanced temperature
                "max_tokens": 2048,  # Increased for better summaries
                "top_p": 1.0
            }

            print(f"🔍 [call_llm] Sending request to Groq API...")
            print(f"🔍 [call_llm] Model: {payload['model']}, Max tokens: {payload['max_tokens']}")
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60  # Increased timeout for longer responses
            )
            
            print(f"🔍 [call_llm] Response status: {response.status_code}")
            
            # Better error handling with detailed messages
            if response.status_code == 401:
                error_detail = response.text[:200] if response.text else "No error details"
                raise Exception(f"Invalid GROQ_API_KEY (401 Unauthorized). Error: {error_detail}")
            elif response.status_code == 429:
                error_detail = response.text[:200] if response.text else "No error details"
                raise Exception(f"Rate limit exceeded (429). Please try again later. Error: {error_detail}")
            elif response.status_code >= 500:
                error_detail = response.text[:200] if response.text else "No error details"
                raise Exception(f"Groq API server error ({response.status_code}). Error: {error_detail}")
            
            response.raise_for_status()
            
            try:
                result = response.json()
            except Exception as json_error:
                raise Exception(f"Failed to parse JSON response from Groq API: {str(json_error)}. Response: {response.text[:200]}")
            
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Invalid response from Groq API: no choices returned. Response: {str(result)[:200]}")
            
            content = result['choices'][0]['message']['content'].strip()
            print(f"✅ [call_llm] Successfully received response from Groq API (length: {len(content)} chars)")
            return content

        elif llm == "chatgpt":
            # Use Groq API with LLaMA 3.1 model as ChatGPT alternative
            if not groq_api_key:
                raise Exception("GROQ_API_KEY environment variable is not set or is empty")
            
            # Remove any quotes or whitespace from API key
            groq_api_key = groq_api_key.strip().strip('"').strip("'")
            
            if not groq_api_key or len(groq_api_key) < 10:
                raise Exception(f"GROQ_API_KEY appears to be invalid (length: {len(groq_api_key)})")
            
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            system_message = "You are ChatGPT, a helpful AI assistant created by OpenAI. You provide clear, accurate, and helpful responses."
            if language and str(language).lower() == "arabic":
                system_message = "You are ChatGPT, a helpful AI assistant created by OpenAI. You provide clear, accurate, and helpful responses. CRITICAL: You MUST respond ENTIRELY in Arabic (العربية). All your responses must be in Arabic using proper Arabic script and formatting. Never respond in English when Arabic is requested."
            
            payload = {
                "model": "llama-3.1-8b-instant",  # Using LLaMA 3.1 for ChatGPT
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2048  # Increased for better summaries
            }

            print(f"🔍 [call_llm] Sending request to Groq API...")
            print(f"🔍 [call_llm] Model: {payload['model']}, Max tokens: {payload['max_tokens']}")
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60  # Increased timeout for longer responses
            )
            
            print(f"🔍 [call_llm] Response status: {response.status_code}")
            
            # Better error handling with detailed messages
            if response.status_code == 401:
                error_detail = response.text[:200] if response.text else "No error details"
                raise Exception(f"Invalid GROQ_API_KEY (401 Unauthorized). Error: {error_detail}")
            elif response.status_code == 429:
                error_detail = response.text[:200] if response.text else "No error details"
                raise Exception(f"Rate limit exceeded (429). Please try again later. Error: {error_detail}")
            elif response.status_code >= 500:
                error_detail = response.text[:200] if response.text else "No error details"
                raise Exception(f"Groq API server error ({response.status_code}). Error: {error_detail}")
            
            response.raise_for_status()
            
            try:
                result = response.json()
            except Exception as json_error:
                raise Exception(f"Failed to parse JSON response from Groq API: {str(json_error)}. Response: {response.text[:200]}")
            
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Invalid response from Groq API: no choices returned. Response: {str(result)[:200]}")
            
            content = result['choices'][0]['message']['content'].strip()
            print(f"✅ [call_llm] Successfully received response from Groq API (length: {len(content)} chars)")
            return content

        elif llm == "uniguru":
            # UniGuru API (Llama model) via ngrok
            uniguru_url = os.getenv("UNIGURU_NGROK_ENDPOINT", "https://3a46c48e4d91.ngrok-free.app") + "/v1/chat/completions"
            print(f"🔍 [call_llm] Using UniGuru endpoint: {uniguru_url}")
            logger.info(f"Calling UniGuru API at: {uniguru_url}")
            
            headers = {
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true"
            }
            # Create system message with language requirement if Arabic
            system_message = "You are a helpful AI assistant that provides detailed, comprehensive summaries and analysis."
            if language and str(language).lower() == "arabic":
                system_message = "You are a helpful AI assistant that provides detailed, comprehensive summaries and analysis. CRITICAL: You MUST respond ENTIRELY in Arabic (العربية). All your responses must be in Arabic using proper Arabic script and formatting. Never respond in English when Arabic is requested."
            
            data = {
                "model": "llama3.1",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2048,
                "temperature": 0.7
            }

            print(f"🔍 [call_llm] Sending request to UniGuru...")
            response = requests.post(uniguru_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            print(f"✅ [call_llm] UniGuru response received successfully")
            return result['choices'][0]['message']['content'].strip()

        else:
            # Default fallback
            response = llm_service.generate_response(prompt)
            return response

    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout calling {llm.upper()} API: {str(e)}"
        print(f"❌ Timeout calling {llm} API: {e}")
        logger.error(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error calling {llm.upper()} API: {str(e)}"
        print(f"❌ Connection error calling {llm} API: {e}")
        logger.error(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to generate response from {llm.upper()} API: {str(e)}"
        print(f"❌ Error calling {llm} API: {e}")
        print(f"❌ Error details: {type(e).__name__}: {str(e)}")
        logger.error(error_msg)
        # Include more details in error message
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg += f" | Response: {str(error_detail)[:300]}"
            except:
                error_msg += f" | Response status: {e.response.status_code}, Text: {e.response.text[:200]}"
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error with {llm}: {str(e)}"
        print(f"❌ Unexpected error with {llm}: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)

def call_groq_llama3(prompt: str, language: str = "english") -> str:
    """Enhanced LLM function with STRONG language enforcement"""
    print("\n" + "="*80)
    print("🔍 DEBUG: call_groq_llama3 function called")
    print(f"🌐 Language parameter received: {language}")
    print(f"📝 Original prompt: {prompt[:200]}...")
    print("="*80 + "\n")
    
    try:
        # CRITICAL: Add extremely strong Arabic instruction
        if language.lower() == "arabic":
            enhanced_prompt = f"""أنت مساعد ذكي يجب أن يرد دائماً باللغة العربية فقط.

تعليمات صارمة:
1. يجب أن تكون إجابتك بالكامل باللغة العربية
2. لا تستخدم أي كلمات إنجليزية أبداً
3. استخدم الحروف العربية فقط
4. حتى لو كان السؤال بالإنجليزية، أجب بالعربية

سؤال المستخدم: {prompt}

تذكر: يجب أن تكون الإجابة بالكامل باللغة العربية!"""
            
            print("\n" + "="*80)
            print("🌐 USING ARABIC ENHANCED PROMPT:")
            print(enhanced_prompt[:500] + "...")
            print("="*80 + "\n")
        else:
            enhanced_prompt = prompt
            print("\n" + "="*80)
            print("🌐 USING ENGLISH PROMPT (no enhancement)")
            print(enhanced_prompt[:200] + "...")
            print("="*80 + "\n")
        
        # Use call_llm with the enhanced prompt (always in English for better reliability)
        print("📤 Sending to call_llm...")
        # Always generate in English first - translation will happen separately if needed
        response = call_llm(enhanced_prompt, "grok", "english")
        
        if not response or len(response.strip()) == 0:
            raise Exception("Empty response from LLM")
        
        # Verify language in response
        has_arabic = bool(any('\u0600' <= c <= '\u06FF' for c in response))
        print("\n" + "="*80)
        print("📥 RECEIVED RESPONSE FROM LLM:")
        print(f"Contains Arabic characters: {has_arabic}")
        print(f"Response length: {len(response)}")
        print(f"First 200 characters: {response[:200]}")
        print("="*80 + "\n")
        
        return response
    except Exception as e:
        print(f"❌ [Backend] Error in call_groq_llama3: {e}")
        import traceback
        traceback.print_exc()
        # Re-raise the exception so the caller can handle it properly
        # The chatbot endpoint will handle translation and fallbacks
        raise


# Route 2: Send LLM response back
@app.get("/chatbot")
async def send_response():
    try:
        # Fetch the latest query from MongoDB
        latest_query = user_collection.find_one({"type": "chat_message", "response":None}, sort=[("timestamp", -1)])
        if not latest_query:
            return {"error": "No queries yet"}

        print("\n" + "="*80)
        print("🔍 DEBUG: /chatbot endpoint called")
        print("="*80 + "\n")
        
        query_message = latest_query["message"]
        
        # CRITICAL: Get language from the stored query (try both 'llm' and 'llm_model' for compatibility)
        language = latest_query.get("language", "english")
        llm_model = latest_query.get("llm", latest_query.get("llm_model", "grok"))
        
        print("\n" + "="*80)
        print("📋 QUERY DETAILS FROM DATABASE:")
        print(f"Query: {query_message}")
        print(f"Language: {language} (type: {type(language)})")
        print(f"Model: {llm_model}")
        print(f"All fields: {list(latest_query.keys())}")
        print("="*80 + "\n")
        
        # Normalize language (treat any ar* locale as arabic)
        if not language:
            language = "english"
        language = str(language).lower().strip()
        if language.startswith("ar"):
            language = "arabic"
        
        print(f"🌐 [Backend] Processing query in {language}: {query_message}")
        print(f"🤖 [Backend] Using model: {llm_model}")

        # Generate response in English first using the user's selected model (better quality)
        print(f"🚀 Generating response in English first using model: {llm_model}...")
        try:
            # Use the user's selected model directly (grok, llama, ollama, uniguru, etc.)
            llm_reply = call_llm(query_message, llm_model, "english")
            
            if not llm_reply or len(llm_reply.strip()) == 0:
                raise Exception("Empty response from LLM")
                
            print(f"✅ [Backend] Successfully generated response in English (length: {len(llm_reply)} chars)")
        except Exception as e:
            print(f"❌ [Backend] Error generating English response with {llm_model}: {e}")
            # Try with grok as fallback
            try:
                print(f"⚠️ [Backend] Trying Grok as fallback...")
                llm_reply = call_llm(query_message, "grok", "english")
                if not llm_reply or len(llm_reply.strip()) == 0:
                    raise Exception("Empty response from fallback LLM")
                print(f"✅ [Backend] Successfully generated response using Grok fallback")
            except Exception as fallback_error:
                print(f"❌ [Backend] Fallback also failed: {fallback_error}")
                raise Exception(f"Failed to generate response with {llm_model}: {str(e)}")
        
        # If Arabic is requested, translate the English response to Arabic using checkpoint_info.pkl
        translation_path = "none"  # track how translation was performed
        if language == "arabic":
            print(f"\n{'='*80}")
            print(f"🌐 [Backend] Arabic translation requested - using checkpoint_info.pkl")
            print(f"🌐 [Backend] Original response length: {len(llm_reply)} chars")
            print(f"🌐 [Backend] Original response preview: {llm_reply[:200]}...")
            print(f"{'='*80}\n")
            
            try:
                # STEP 1: Try checkpoint model first (checkpoint_info.pkl)
                checkpoint_result = None
                if ARABIC_TRANSLATOR_AVAILABLE and translate_to_arabic_with_checkpoint:
                    print(f"🔄 [Backend] Attempting translation with checkpoint_info.pkl...")
                    try:
                        checkpoint_result = translate_to_arabic_with_checkpoint(llm_reply)
                        if checkpoint_result and len(checkpoint_result.strip()) > 0:
                            llm_reply = checkpoint_result.strip()
                            translation_path = "checkpoint"
                            print(f"✅ [Backend] Successfully translated using checkpoint_info.pkl")
                            print(f"✅ [Backend] Translated response length: {len(llm_reply)} chars")
                            print(f"✅ [Backend] Translated preview: {llm_reply[:200]}...")
                        else:
                            print(f"⚠️ [Backend] Checkpoint model returned empty result, trying LLM fallback...")
                            checkpoint_result = None
                    except Exception as checkpoint_error:
                        print(f"⚠️ [Backend] Checkpoint translation error: {checkpoint_error}")
                        import traceback
                        print(f"⚠️ [Backend] Checkpoint error details: {traceback.format_exc()}")
                        checkpoint_result = None
                
                # STEP 2: Fallback to LLM translation if checkpoint failed or unavailable
                if not checkpoint_result:
                    print(f"🔄 [Backend] Using {llm_model} for LLM-based translation fallback...")
                    translation_prompt = f"""You are a professional translator. Your task is to translate the following English text to Arabic (العربية).

⚠️ CRITICAL REQUIREMENTS:
- You MUST translate the ENTIRE text to Arabic
- Use proper Arabic script (العربية)
- Maintain the exact same structure and formatting
- Translate ALL text including any technical terms naturally
- Do NOT leave any English words untranslated
- The output must be 100% in Arabic

English Text to Translate:
{llm_reply}

Now provide the complete Arabic translation. Your response must be entirely in Arabic:"""
                    
                    try:
                        translated_reply = call_llm(translation_prompt, llm_model, "english")
                        if translated_reply and len(translated_reply.strip()) > 0:
                            llm_reply = translated_reply.strip()
                            translation_path = "llm_fallback"
                            print(f"✅ [Backend] Successfully translated using {llm_model} LLM fallback")
                            print(f"✅ [Backend] Translated response length: {len(llm_reply)} chars")
                            print(f"✅ [Backend] Translated preview: {llm_reply[:200]}...")
                        else:
                            print(f"⚠️ [Backend] LLM translation returned empty, keeping original English")
                    except Exception as llm_error:
                        print(f"❌ [Backend] LLM translation failed: {llm_error}")
                        print(f"⚠️ [Backend] Keeping original English response due to translation failure")
                
            except Exception as translate_error:
                print(f"❌ [Backend] Translation process failed with error: {translate_error}")
                import traceback
                print(f"❌ [Backend] Translation error traceback: {traceback.format_exc()}")
                # Continue with English version if translation fails
                print(f"⚠️ [Backend] Using original English response due to translation error")
        
        # Log translation path for debugging
        print(f"🧭 [Backend] translation_path: {translation_path}")

        # Verify the response language
        has_arabic = bool(any('\u0600' <= c <= '\u06FF' for c in llm_reply))
        print("\n" + "="*80)
        print("✅ FINAL RESPONSE READY:")
        print(f"Contains Arabic: {has_arabic}")
        print(f"Response preview: {llm_reply[:200]}")
        print("="*80 + "\n")

        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        response_data = {
            "message": llm_reply,
            "timestamp": timestamp,
            "type": "chat_response",
            "query_id": str(latest_query["_id"]),
            "language": language,  # Include language in response
            "llm": llm_model
        }
        # Include translation path metadata when Arabic translation was attempted
        if language == "arabic":
            response_data["translation_path"] = translation_path

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
        print(f"❌ [Backend] Error in send_response: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process response:{str(e)}")

@app.post("/process-pdf", response_model=PDFResponse)
async def process_pdf(file: UploadFile = File(...), llm: str = Query("grok", description="LLM model to use (grok, llama, uniguru)"), language: str = Query("english", description="Language for summary (english, arabic)")):
    # Log the received parameters for debugging
    print(f"🔍 [process_pdf] Received llm parameter: '{llm}' (type: {type(llm)})")
    print(f"🔍 [process_pdf] Received language parameter: '{language}' (type: {type(language)})")
    
    # Ensure language is a string and normalize to lowercase
    original_language = language
    if not language:
        language = "english"
    language = str(language).lower().strip()
    print(f"🔍 [process_pdf] Received language parameter: '{original_language}'")
    print(f"🔍 [process_pdf] Normalized language: '{language}'")
    print(f"🔍 [process_pdf] Will translate to Arabic: {language == 'arabic'}")
    
    logger.info(f"Processing PDF with LLM model: {llm}, language: {language}")
    
    temp_file_path = ""
    try:
        # Check file extension and validate supported formats
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        supported_formats = ['pdf', 'doc', 'docx']

        if file_ext not in supported_formats:
            raise HTTPException(status_code=400, detail="Only PDF, DOC, and DOCX files are allowed")

        # Create temp file with appropriate extension
        temp_file_path = os.path.join(TEMP_DIR, f"temp_document_{time.strftime('%Y%m%d_%H%M%S')}.{file_ext}")
        with open(temp_file_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)

        # Parse document based on file type
        if file_ext == 'pdf':
            structured_data = parse_pdf(temp_file_path)
        elif file_ext in ['doc', 'docx']:
            structured_data = parse_word_document(temp_file_path)

        if not structured_data["body"]:
            raise HTTPException(status_code=400, detail="Failed to parse document content")

        # Create a comprehensive prompt for document summarization
        document_content = structured_data["body"]
        
        # Add language instruction if Arabic is selected
        language_instruction = ""
        if language == "arabic":
            language_instruction = "\n\n⚠️ CRITICAL LANGUAGE REQUIREMENT ⚠️\nYou MUST generate the ENTIRE summary in Arabic (العربية). This is mandatory.\n- All content including overview, key points, important details, and conclusions MUST be in Arabic\n- Use proper Arabic script and formatting\n- Write all text in Arabic, not English\n- Do NOT include any English text in your response\n\n"
            print(f"✅ [process_pdf] Arabic language instruction added to prompt")
        else:
            print(f"ℹ️ [process_pdf] Using English (language: '{language}')")
        
        prompt = f"""{language_instruction}Please provide a detailed summary of the following document in a clean, well-structured format:

Title: {structured_data.get('title', 'Document')}

Content:
{document_content}

Please provide a comprehensive summary with the following structure:

Overview
Provide a brief overview of the document's main purpose and scope.

Key Points
• List the main topics and important concepts covered
• Highlight significant findings or arguments
• Include relevant data, statistics, or examples

Important Details
• Explain crucial information that readers should understand
• Clarify any complex concepts or terminology
• Mention important dates, names, or references

Conclusions & Insights
• Summarize the main conclusions or outcomes
• Provide actionable insights or recommendations
• Explain the significance or implications of the content

IMPORTANT: Format your response with clear sections and bullet points for easy reading. Do NOT use markdown formatting like ** or * symbols. Use plain text with clear section headers. Make it comprehensive yet concise, focusing on the most valuable information."""

        # Use the selected LLM model for summarization with automatic fallback
        print(f"🔍 [process_pdf] Calling call_llm with llm='{llm}'")
        logger.info(f"Calling LLM with model: {llm}")
        
        # Check API key before calling
        groq_key_check = os.environ.get('GROQ_API_KEY', '').strip()
        print(f"🔍 [process_pdf] GROQ_API_KEY check: present={bool(groq_key_check)}, length={len(groq_key_check)}")
        
        try:
            # Always generate in English first for better quality
            answer = call_llm(prompt, llm, "english")
        except Exception as e:
            error_str = str(e)
            print(f"❌ [process_pdf] Error with {llm}: {error_str}")
            
            # If grok fails, automatically try llama as fallback
            if llm == "grok":
                print(f"⚠️ [process_pdf] Grok failed, trying Llama as fallback...")
                logger.warning(f"Grok failed: {error_str}, falling back to Llama")
                try:
                    answer = call_llm(prompt, "llama", "english")
                    llm = "llama"  # Update llm to reflect what was actually used
                    print(f"✅ [process_pdf] Successfully used Llama as fallback")
                except Exception as llama_error:
                    llama_error_str = str(llama_error)
                    print(f"❌ [process_pdf] Llama also failed: {llama_error_str}")
                    # If llama also fails, try with increased tokens and different model
                    print(f"⚠️ [process_pdf] Trying llama-3.1-8b-instant as final fallback...")
                    try:
                        answer = call_llm(prompt, "chatgpt", "english")  # Uses llama-3.1-8b-instant
                        llm = "chatgpt"
                        print(f"✅ [process_pdf] Successfully used llama-3.1-8b-instant")
                    except Exception as final_error:
                        final_error_str = str(final_error)
                        print(f"❌ [process_pdf] All models failed!")
                        raise Exception(f"All LLM models failed. Grok: {error_str[:200]}, Llama: {llama_error_str[:200]}, Llama-3.1: {final_error_str[:200]}")
            else:
                # If not grok, just raise the original error
                raise
        
        # If Arabic is requested, translate the English summary to Arabic
        print(f"🔍 [process_pdf] Checking if translation needed. Language value: '{language}', Type: {type(language)}, == 'arabic': {language == 'arabic'}")
        if language == "arabic":
            print(f"🌐 [process_pdf] ✓ Language is Arabic, translating summary to Arabic...")
            print(f"🌐 [process_pdf] Original answer length: {len(answer)} chars")
            print(f"🌐 [process_pdf] Original answer preview: {answer[:200]}...")
            try:
                # Use checkpoint model for translation (with LLM fallback)
                if ARABIC_TRANSLATOR_AVAILABLE:
                    print(f"🌐 [process_pdf] Using checkpoint model for translation (with LLM fallback)...")
                    translated_answer = translate_to_arabic(answer, fallback_llm_func=call_llm)
                else:
                    # Fallback to direct LLM translation
                    print(f"🌐 [process_pdf] Checkpoint model not available, using LLM translation...")
                    translation_prompt = f"""You are a professional translator. Your task is to translate the following English text to Arabic (العربية).

⚠️ CRITICAL REQUIREMENTS:
- You MUST translate the ENTIRE text to Arabic
- Use proper Arabic script (العربية)
- Maintain the exact same structure, sections, and formatting
- Translate ALL text including section headers like "Overview", "Key Points", "Important Details", "Conclusions"
- Do NOT leave any English words untranslated
- The output must be 100% in Arabic

English Text to Translate:
{answer}

Now provide the complete Arabic translation. Your response must be entirely in Arabic:"""
                    translated_answer = call_llm(translation_prompt, llm, "english")
                
                print(f"🌐 [process_pdf] Translation response received, length: {len(translated_answer) if translated_answer else 0}")
                
                if translated_answer and len(translated_answer.strip()) > 0:
                    answer = translated_answer.strip()
                    print(f"✅ [process_pdf] Successfully translated summary to Arabic (length: {len(answer)} chars)")
                    print(f"✅ [process_pdf] Translated answer preview: {answer[:200]}...")
                else:
                    print(f"⚠️ [process_pdf] Translation returned empty, using original English")
            except Exception as translate_error:
                print(f"❌ [process_pdf] Translation failed with error: {translate_error}")
                import traceback
                print(f"❌ [process_pdf] Translation error traceback: {traceback.format_exc()}")
                # Continue with English version if translation fails

        audio_file = text_to_speech(answer, file_prefix="output_pdf")
        audio_url = f"/api/stream/{os.path.basename(audio_file)}" if audio_file else "No audio generated"

        # Store to MongoDB
        pdf_doc = {
            "filename": file.filename,
            "file_type": file_ext,
            "title": structured_data["title"],
            "sections": [{"heading": s["heading"], "content": s["content"]} for s in structured_data["sections"]],
            "summary": answer,
            "llm_model": llm,
            "audio_file": audio_url,
            "timestamp": datetime.now(timezone.utc)
        }
        pdf_collection.insert_one(pdf_doc)

        global pdf_response
        pdf_response = PDFResponse(
            title=structured_data["title"],
            sections=[Section(heading=s["heading"], content=s["content"]) for s in structured_data["sections"]],
            query=f"Document summary using {llm.upper()} model",
            answer=answer,
            audio_file=audio_url,
            llm=llm
        )
        return pdf_response

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/process-img", response_model=ImageResponse)
async def process_image(file: UploadFile = File(...), llm: str = Query("grok", description="LLM model to use (grok, llama, uniguru)"), language: str = Query("english", description="Language for summary (english, arabic)")):
    # Log the received parameters for debugging
    print(f"🔍 [process_image] Received llm parameter: '{llm}' (type: {type(llm)})")
    print(f"🔍 [process_image] Received language parameter: '{language}' (type: {type(language)})")
    
    # Ensure language is a string and normalize to lowercase
    if not language:
        language = "english"
    language = str(language).lower().strip()
    print(f"🔍 [process_image] Normalized language: '{language}'")
    
    logger.info(f"Processing image with LLM model: {llm}, language: {language}")
    
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
            answer = "This image does not contain any readable text that can be extracted and summarized."
            query = "Image analysis"
        else:
            # Add language instruction if Arabic is selected
            language_instruction = ""
            if language == "arabic":
                language_instruction = "\n\n⚠️ CRITICAL LANGUAGE REQUIREMENT ⚠️\nYou MUST generate the ENTIRE analysis in Arabic (العربية). This is mandatory.\n- All content including summary, key information, context, and insights MUST be in Arabic\n- Use proper Arabic script and formatting\n- Write all text in Arabic, not English\n- Do NOT include any English text in your response\n\n"
                print(f"✅ [process_image] Arabic language instruction added to prompt")
            else:
                print(f"ℹ️ [process_image] Using English (language: '{language}')")
            
            # Create a comprehensive prompt for image text analysis
            prompt = f"""{language_instruction}Please analyze and summarize the following text extracted from an image:

Extracted Text:
{ocr_text}

Please provide:
1. A summary of what the text contains
2. Key information and main points
3. Context or purpose of the text (if apparent)
4. Any important details or insights
{language_instruction}

Make the analysis comprehensive and helpful."""

            # Use the selected LLM model for analysis with automatic fallback
            print(f"🔍 [process_image] Calling call_llm with llm='{llm}'")
            logger.info(f"Calling LLM with model: {llm}")
            
            try:
                # Always generate in English first for better quality
                answer = call_llm(prompt, llm, "english")
            except Exception as e:
                # If grok fails, automatically try llama as fallback
                if llm == "grok":
                    print(f"⚠️ [process_image] Grok failed, trying Llama as fallback...")
                    logger.warning(f"Grok failed: {e}, falling back to Llama")
                    try:
                        answer = call_llm(prompt, "llama", "english")
                        llm = "llama"  # Update llm to reflect what was actually used
                        print(f"✅ [process_image] Successfully used Llama as fallback")
                    except Exception as llama_error:
                        # If llama also fails, try with different model
                        print(f"⚠️ [process_image] Llama also failed, trying llama-3.1-8b-instant...")
                        try:
                            answer = call_llm(prompt, "chatgpt", "english")  # Uses llama-3.1-8b-instant
                            llm = "chatgpt"
                            print(f"✅ [process_image] Successfully used llama-3.1-8b-instant")
                        except Exception as final_error:
                            raise Exception(f"All LLM models failed. Grok: {str(e)}, Llama: {str(llama_error)}, Llama-3.1: {str(final_error)}")
                else:
                    # If not grok, just raise the original error
                    raise
            
            # If Arabic is requested, translate the English analysis to Arabic
            print(f"🔍 [process_image] Checking if translation needed. Language value: '{language}', Type: {type(language)}, == 'arabic': {language == 'arabic'}")
            if language == "arabic":
                print(f"🌐 [process_image] ✓ Language is Arabic, translating analysis to Arabic...")
                print(f"🌐 [process_image] Original answer length: {len(answer)} chars")
                print(f"🌐 [process_image] Original answer preview: {answer[:200]}...")
                try:
                    # Use checkpoint model for translation (with LLM fallback)
                    if ARABIC_TRANSLATOR_AVAILABLE:
                        print(f"🌐 [process_image] Using checkpoint model for translation (with LLM fallback)...")
                        translated_answer = translate_to_arabic(answer, fallback_llm_func=call_llm)
                    else:
                        # Fallback to direct LLM translation
                        print(f"🌐 [process_image] Checkpoint model not available, using LLM translation...")
                        translation_prompt = f"""You are a professional translator. Your task is to translate the following English text to Arabic (العربية).

⚠️ CRITICAL REQUIREMENTS:
- You MUST translate the ENTIRE text to Arabic
- Use proper Arabic script (العربية)
- Maintain the exact same structure, sections, and formatting
- Translate ALL text including section headers and labels
- Do NOT leave any English words untranslated
- The output must be 100% in Arabic

English Text to Translate:
{answer}

Now provide the complete Arabic translation. Your response must be entirely in Arabic:"""
                        translated_answer = call_llm(translation_prompt, llm, "english")
                    
                    print(f"🌐 [process_image] Translation response received, length: {len(translated_answer) if translated_answer else 0}")
                    
                    if translated_answer and len(translated_answer.strip()) > 0:
                        answer = translated_answer.strip()
                        print(f"✅ [process_image] Successfully translated analysis to Arabic (length: {len(answer)} chars)")
                        print(f"✅ [process_image] Translated answer preview: {answer[:200]}...")
                    else:
                        print(f"⚠️ [process_image] Translation returned empty, using original English")
                except Exception as translate_error:
                    print(f"❌ [process_image] Translation failed with error: {translate_error}")
                    import traceback
                    print(f"❌ [process_image] Translation error traceback: {traceback.format_exc()}")
                    # Continue with English version if translation fails
            
            query = f"Image text analysis using {llm.upper()} model"

        audio_file = text_to_speech(answer, file_prefix="output_image")
        audio_url = f"/api/stream/{os.path.basename(audio_file)}" if audio_file else "No audio generated"

        # Store to MongoDB
        image_doc = {
            "filename": file.filename,
            "ocr_text": ocr_text,
            "query": query,
            "answer": answer,
            "llm_model": llm,
            "audio_file": audio_url,
            "timestamp": datetime.now(timezone.utc)
        }
        image_collection.insert_one(image_doc)

        global image_response
        image_response = ImageResponse(
            ocr_text=ocr_text,
            query=query,
            answer=answer,
            audio_file=audio_url,
            llm=llm
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

@app.get("/process-pdf-stream")
async def process_pdf_stream(
    file_path: str = None,
    llm: str = "uniguru"
):
    """
    Stream PDF processing results line by line for live rendering
    """
    async def generate_content():
        try:
            yield f"data: 🔍 Starting document analysis...\n\n"
            await asyncio.sleep(0.1)

            # Get the latest PDF response
            if pdf_response is None:
                yield f"data: ❌ No PDF has been processed yet. Please upload a document first.\n\n"
                yield f"data: [ERROR]\n\n"
                return

            yield f"data: 📄 Processing: {pdf_response.title}\n\n"
            await asyncio.sleep(0.2)

            yield f"data: 🤖 Using UNIGURU AI model\n\n"
            await asyncio.sleep(0.2)

            yield f"data: 📝 Generating comprehensive summary...\n\n"
            await asyncio.sleep(0.3)

            # Clean the answer content (remove markdown formatting)
            answer = pdf_response.answer

            # Remove markdown formatting
            cleaned_answer = answer.replace('**', '').replace('*', '').replace('##', '').replace('#', '')

            # Split content into lines for streaming
            content_lines = cleaned_answer.split('\n')

            yield f"data: \n\n"
            yield f"data: {pdf_response.title}\n\n"
            yield f"data: \n\n"

            # Stream content line by line
            for i, line in enumerate(content_lines):
                if line.strip():  # Only send non-empty lines
                    yield f"data: {line.strip()}\n\n"
                    await asyncio.sleep(0.05)  # Small delay for live rendering effect
                else:
                    yield f"data: \n\n"  # Send empty line
                    await asyncio.sleep(0.02)

            yield f"data: \n\n"
            yield f"data: ✅ Document analysis complete!\n\n"
            yield f"data: 🎵 Audio summary available for download\n\n"
            yield f"data: [END]\n\n"

        except Exception as e:
            yield f"data: ❌ Error during streaming: {str(e)}\n\n"
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

@app.get("/process-img-stream")
async def process_image_stream(
    file_path: str = None,
    llm: str = "uniguru"
):
    """
    Stream Image processing results line by line for live rendering
    """
    async def generate_content():
        try:
            yield f"data: 🔍 Starting image analysis...\n\n"
            await asyncio.sleep(0.1)

            # Get the latest image response
            if image_response is None:
                yield f"data: ❌ No image has been processed yet. Please upload an image first.\n\n"
                yield f"data: [ERROR]\n\n"
                return

            yield f"data: 🖼️ Processing image with OCR...\n\n"
            await asyncio.sleep(0.2)

            yield f"data: 🤖 Using UNIGURU AI model\n\n"
            await asyncio.sleep(0.2)

            yield f"data: 📝 Generating comprehensive analysis...\n\n"
            await asyncio.sleep(0.3)

            # Clean the answer content (remove markdown formatting)
            answer = image_response.answer

            # Remove markdown formatting
            cleaned_answer = answer.replace('**', '').replace('*', '').replace('##', '').replace('#', '')

            # Split content into lines for streaming
            content_lines = cleaned_answer.split('\n')

            yield f"data: \n\n"
            yield f"data: Image Analysis Results\n\n"
            yield f"data: \n\n"

            # Stream content line by line
            for i, line in enumerate(content_lines):
                if line.strip():  # Only send non-empty lines
                    yield f"data: {line.strip()}\n\n"
                    await asyncio.sleep(0.05)  # Small delay for live rendering effect
                else:
                    yield f"data: \n\n"  # Send empty line
                    await asyncio.sleep(0.02)

            yield f"data: \n\n"
            yield f"data: ✅ Image analysis complete!\n\n"
            yield f"data: 🎵 Audio summary available for download\n\n"
            yield f"data: [END]\n\n"

        except Exception as e:
            yield f"data: ❌ Error during streaming: {str(e)}\n\n"
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


# ==== AGENT SIMULATION ENDPOINTS ====

# Pydantic models for agent simulation
class AgentMessageRequest(BaseModel):
    message: str
    agent_id: Union[str, int] = Field(alias='agentId')  # Can be string or int (1, 2, 3)
    user_id: Optional[str] = Field(default="guest-user", alias='userId')
    timestamp: Optional[str] = None
    
    class Config:
        populate_by_name = True  # Allow both field name and alias

class AgentSimulationRequest(BaseModel):
    agent_id: str = Field(alias='agentId')
    user_id: Optional[str] = Field(default="guest-user", alias='userId')
    timestamp: Optional[str] = None
    # Additional optional fields for extended functionality
    financial_profile: Optional[dict] = Field(default=None, alias='financialProfile')
    edu_mentor_profile: Optional[dict] = Field(default=None, alias='eduMentorProfile')
    wellness_profile: Optional[dict] = Field(default=None, alias='wellnessProfile')
    additional_data: Optional[dict] = None
    
    class Config:
        populate_by_name = True  # Allow both field name and alias

class AgentResetRequest(BaseModel):
    user_id: Optional[str] = Field(default="guest-user", alias='userId')
    timestamp: Optional[str] = None
    # Additional optional fields for flexibility
    additional_data: Optional[dict] = None
    
    class Config:
        populate_by_name = True  # Allow both field name and alias

@app.get("/get_agent_output")
async def get_agent_output():
    """Get agent outputs for the simulation"""
    try:
        # Return mock agent outputs with data processing content
        mock_outputs = [
            {
                "agent_id": "data_processor",
                "message": "Welcome to the data processing simulation! I can help you process documents and analyze content.",
                "timestamp": datetime.now().isoformat(),
                "type": "welcome",
                "status": "active"
            },
            {
                "agent_id": "document_analyzer",
                "message": "I'm here to help with document analysis and content extraction.",
                "timestamp": datetime.now().isoformat(),
                "type": "introduction",
                "status": "idle"
            }
        ]
        
        # Add any stored agent outputs
        all_outputs = mock_outputs + agent_outputs
        
        return {
            "status": "success",
            "outputs": all_outputs[-10:],  # Return last 10 outputs
            "count": len(all_outputs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent output: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent_logs")
async def get_agent_logs():
    """Get agent logs for monitoring"""
    try:
        # Mock agent logs
        mock_agent_logs = [
            {
                "log_id": str(uuid4()),
                "agent_id": "data_processor",
                "level": "INFO",
                "message": "Data processing agent initialized successfully",
                "timestamp": datetime.now().isoformat(),
                "user_id": "system"
            },
            {
                "log_id": str(uuid4()),
                "agent_id": "document_analyzer",
                "level": "INFO",
                "message": "Document analyzer ready for processing",
                "timestamp": datetime.now().isoformat(),
                "user_id": "system"
            }
        ]
        
        # Combine with stored logs
        all_logs = mock_agent_logs + agent_logs
        
        return {
            "status": "success",
            "logs": all_logs[-20:],  # Return last 20 logs
            "count": len(all_logs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent_message")
async def send_agent_message(request: AgentMessageRequest):
    """Send a message to an agent and get AI-powered response"""
    try:
        timestamp = request.timestamp or datetime.now().isoformat()
        
        # Store the message
        message_record = {
            "message_id": str(uuid4()),
            "agent_id": request.agent_id,
            "user_id": request.user_id,
            "message": request.message,
            "timestamp": timestamp,
            "type": "user_message"
        }
        
        agent_outputs.append(message_record)
        
        # Map agent_id to agent type
        # Frontend sends: 1=education, 2=financial, 3=wellness, or string IDs
        agent_type_map = {
            "1": "education",
            "2": "financial", 
            "3": "wellness",
            "education": "education",
            "financial": "financial",
            "wellness": "wellness",
            "data_processor": "education",  # Legacy support
            "document_analyzer": "education"  # Legacy support
        }
        
        agent_type = agent_type_map.get(str(request.agent_id), "education")
        
        # Get simulation context if available
        simulation_context = agent_simulations.get(request.user_id, {})
        financial_profile = simulation_context.get("financial_profile", {})
        edu_mentor_profile = simulation_context.get("edu_mentor_profile", {})
        wellness_profile = simulation_context.get("wellness_profile", {})
        
        # Create agent-specific prompts
        system_prompts = {
            "education": """You are EduMentor, an expert educational AI assistant specialized in teaching and learning. 
Your role is to:
- Explain concepts clearly and comprehensively
- Break down complex topics into understandable parts
- Provide structured learning paths
- Answer academic questions with depth and clarity
- Create engaging educational content
- Help students understand difficult concepts

Be friendly, encouraging, and pedagogically sound. Use examples and analogies when helpful.""",
            
            "financial": """You are FinancialCrew, an expert financial advisor AI assistant specialized in financial planning and analysis.
Your role is to:
- Provide sound financial advice and analysis
- Help with budgeting, investments, and financial planning
- Explain financial concepts clearly
- Offer practical financial strategies
- Analyze financial situations and provide recommendations
- Discuss risk management and financial goals

Be professional, data-driven, and focused on helping users make informed financial decisions.""",
            
            "wellness": """You are WellnessBot, a compassionate wellness AI assistant focused on mental and physical wellbeing.
Your role is to:
- Provide holistic wellness advice
- Support mental health and emotional wellbeing
- Offer lifestyle and self-care recommendations
- Provide mindfulness and stress management guidance
- Encourage healthy habits and balanced living
- Be empathetic and understanding

Be warm, supportive, and evidence-based. Focus on overall wellbeing and balance."""
        }
        
        # Build context-aware prompt
        user_message = request.message.strip()
        
        # Add context based on agent type
        context_info = ""
        if agent_type == "education" and edu_mentor_profile:
            subject = edu_mentor_profile.get("selectedSubject", "")
            topic = edu_mentor_profile.get("topic", "")
            if subject and topic:
                context_info = f"\n\nContext: The user is learning about '{topic}' in the subject '{subject}'. "
        
        if agent_type == "financial" and financial_profile:
            name = financial_profile.get("name", "")
            goal = financial_profile.get("financialGoal", "")
            if name or goal:
                context_info = f"\n\nContext: User's financial profile - "
                if name:
                    context_info += f"Name: {name}. "
                if goal:
                    context_info += f"Financial Goal: {goal}. "
        
        if agent_type == "wellness" and wellness_profile:
            wellness_type = wellness_profile.get("wellnessType", "")
            mood_score = wellness_profile.get("moodScore")
            stress_level = wellness_profile.get("stressLevel")
            if wellness_type or mood_score is not None or stress_level is not None:
                context_info = f"\n\nContext: User's wellness profile - "
                if wellness_type:
                    context_info += f"Wellness Type: {wellness_type}. "
                if mood_score is not None:
                    context_info += f"Current Mood Score: {mood_score}/10. "
                if stress_level is not None:
                    context_info += f"Current Stress Level: {stress_level}/6. "
        
        # Create the full prompt
        system_prompt = system_prompts.get(agent_type, system_prompts["education"])
        full_prompt = f"{system_prompt}{context_info}\n\nUser's message: {user_message}\n\nProvide a helpful, relevant response:"
        
        # Generate AI response
        try:
            logger.info(f"🤖 Generating AI response for agent type: {agent_type}")
            response_message = call_llm(full_prompt, llm="grok")
            
            if not response_message or len(response_message.strip()) == 0:
                raise Exception("Empty response from AI")
                
            logger.info(f"✅ AI response generated successfully (length: {len(response_message)} chars)")
            
        except Exception as ai_error:
            logger.warning(f"⚠️ AI generation failed: {ai_error}, using fallback response")
            # Fallback to template responses if AI fails
            fallback_responses = {
                "education": f"I understand you're asking about: {user_message}. As EduMentor, I can help explain this concept and provide learning resources. Could you provide more details about what specific aspect you'd like to understand?",
                "financial": f"Regarding your financial question about: {user_message}. As FinancialCrew, I can help analyze this and provide financial guidance. Could you share more context about your financial situation or goals?",
                "wellness": f"I hear you're asking about: {user_message}. As WellnessBot, I'm here to support your wellbeing. Could you tell me more about what you're experiencing or what kind of support you're looking for?"
            }
            response_message = fallback_responses.get(agent_type, f"Thank you for your message: {user_message}. I'm here to help!")
        
        # Store agent response
        response_record = {
            "message_id": str(uuid4()),
            "agent_id": request.agent_id,
            "user_id": request.user_id,
            "message": response_message,
            "content": response_message,  # Frontend expects 'content' field
            "timestamp": datetime.now().isoformat(),
            "type": "agent_response",
            "confidence": 0.85
        }
        
        agent_outputs.append(response_record)
        
        # Log the interaction
        agent_log = {
            "log_id": str(uuid4()),
            "agent_id": request.agent_id,
            "level": "INFO",
            "message": f"Processed AI message from user {request.user_id} (agent_type: {agent_type})",
            "timestamp": datetime.now().isoformat(),
            "user_id": request.user_id
        }
        agent_logs.append(agent_log)
        
        return {
            "status": "success",
            "message": "Message sent to agent successfully",
            "agent_response": response_record,
            "content": response_message,  # Frontend expects this
            "confidence": 0.85,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error sending agent message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_agent_simulation")
async def start_agent_simulation(request: AgentSimulationRequest):
    """Start an agent simulation with enhanced data handling"""
    try:
        timestamp = request.timestamp or datetime.now().isoformat()
        
        # Store simulation state with additional data
        simulation_data = {
            "agent_id": request.agent_id,
            "status": "active",
            "started_at": timestamp,
            "user_id": request.user_id
        }
        
        # Include additional profile data if provided
        if request.financial_profile:
            simulation_data["financial_profile"] = request.financial_profile
        if request.edu_mentor_profile:
            simulation_data["edu_mentor_profile"] = request.edu_mentor_profile
        if request.wellness_profile:
            simulation_data["wellness_profile"] = request.wellness_profile
        if request.additional_data:
            simulation_data["additional_data"] = request.additional_data
            
        agent_simulations[request.user_id] = simulation_data
        
        # Log simulation start with additional context
        context_info = []
        if request.financial_profile:
            context_info.append("financial data")
        if request.edu_mentor_profile:
            context_info.append("educational data")
        if request.wellness_profile:
            context_info.append("wellness data")
            
        context_msg = f" with {', '.join(context_info)}" if context_info else ""
        
        agent_log = {
            "log_id": str(uuid4()),
            "agent_id": request.agent_id,
            "level": "INFO",
            "message": f"Agent simulation started for user {request.user_id}{context_msg}",
            "timestamp": timestamp,
            "user_id": request.user_id
        }
        agent_logs.append(agent_log)
        
        # Add welcome message to outputs
        welcome_message = {
            "message_id": str(uuid4()),
            "agent_id": request.agent_id,
            "user_id": request.user_id,
            "message": f"Agent simulation started! Agent {request.agent_id} is now active and ready to assist with data processing{context_msg}.",
            "timestamp": timestamp,
            "type": "simulation_start"
        }
        agent_outputs.append(welcome_message)
        
        return {
            "status": "success",
            "message": f"Agent simulation started for {request.agent_id}",
            "agent_id": request.agent_id,
            "user_id": request.user_id,
            "timestamp": timestamp,
            "additional_context": context_info
        }
        
    except Exception as e:
        logger.error(f"Error starting agent simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop_agent_simulation")
async def stop_agent_simulation(request: AgentSimulationRequest):
    """Stop an agent simulation"""
    try:
        timestamp = request.timestamp or datetime.now().isoformat()
        
        # Update simulation state
        if request.user_id in agent_simulations:
            agent_simulations[request.user_id]["status"] = "stopped"
            agent_simulations[request.user_id]["stopped_at"] = timestamp
            
            # Clear old logs for this user
            for log in agent_logs:
                if log.get("user_id") == request.user_id:
                    log["status"] = "stopped"
        
        # Log simulation stop
        agent_log = {
            "log_id": str(uuid4()),
            "agent_id": request.agent_id,
            "level": "INFO",
            "message": f"Agent simulation stopped for user {request.user_id}",
            "timestamp": timestamp,
            "user_id": request.user_id
        }
        agent_logs.append(agent_log)
        
        return {
            "status": "success",
            "message": f"Agent simulation stopped for {request.agent_id}",
            "agent_id": request.agent_id,
            "user_id": request.user_id,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error stopping agent simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset_agent_simulation")
async def reset_agent_simulation(request: AgentResetRequest):
    """Reset agent simulation for a user"""
    try:
        timestamp = request.timestamp or datetime.now().isoformat()
        
        # Clear simulation state for user
        if request.user_id in agent_simulations:
            del agent_simulations[request.user_id]
        
        # Clear user-specific logs and outputs
        global agent_logs, agent_outputs
        agent_logs = [log for log in agent_logs if log.get("user_id") != request.user_id]
        agent_outputs = [output for output in agent_outputs if output.get("user_id") != request.user_id]
        
        # Log reset
        reset_log = {
            "log_id": str(uuid4()),
            "agent_id": "system",
            "level": "INFO",
            "message": f"Agent simulation reset for user {request.user_id}",
            "timestamp": timestamp,
            "user_id": request.user_id
        }
        agent_logs.append(reset_log)
        
        return {
            "status": "success",
            "message": f"Agent simulation reset for user {request.user_id}",
            "user_id": request.user_id,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error resetting agent simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    try:
        # Use port 8011 to avoid conflict with chatbot service on port 8001
        port = int(os.getenv("API_DATA_PORT", "8011"))
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise



