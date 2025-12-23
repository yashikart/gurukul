from dotenv import load_dotenv
import os

# Load environment variables first, before any other imports
load_dotenv()

from rag import *
import uvicorn
import requests
from datetime import datetime
from subject_data import subjects_data
from lectures_data import lectures_data
# from test_data import test_data  # Commented out - file not found
# Now import from db.py after environment variables are loaded
from db import user_collection, pdf_collection, image_collection
from datetime import datetime, timezone
from fastapi import HTTPException, FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import shutil
import time

import logging
from typing import Optional, List

# Configure logging
logger = logging.getLogger(__name__)

# Environment variables already loaded at the top of the file
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== Subject API Models and Routes ====
class Subject(BaseModel):
    id: int
    name: str
    code: str



# ==== Lectures API Models and Routes ====
class Lecture(BaseModel):
    id: int
    topic: str
    subject_id: int



# ==== Test API Models and Routes ====
class Test(BaseModel):
    id: int
    name: str
    subject_id: int
    date: Optional[str] = None



# ==== Chatbot Models and Routes ====
groq_api_key = os.environ.get('GROQ_API_KEY')
openai_api_key = os.environ.get('OPENAI_API_KEY')
llama_api_key = os.environ.get('LLAMA_API_KEY')
uniguru_api_key = os.environ.get('UNIGURU_API_KEY')

# Temporary in-memory storage
user_queries: List[dict] = []
llm_responses: List[dict] = []

# Pydantic model for chat request
class ChatMessage(BaseModel):
    message: str
    llm: str = Field(..., pattern = "^(grok|llama|chatgpt|uniguru)$")
    timestamp: str = None
    type: str = "chat_message"

# Pydantic models for PDF and Image (assumed, based on response_model)
class Section(BaseModel):
    heading: str
    content: str

class PDFResponse(BaseModel):
    title: str
    sections: List[Section]
    query: str
    answer: str
    audio_file: str
    llm: str  # Added to store selected LLM

class ImageResponse(BaseModel):
    ocr_text: str
    query: str
    answer: str
    audio_file: str
    llm: str  # Added to store selected LLM

# Global variables for storing latest responses
pdf_response = None
image_response = None

def call_llm(prompt: str, llm: str) -> str:
    """
    Call the specified LLM API with the given prompt.
    """
    try:
        if llm == "grok":
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 1.0
            }
            if not prompt.strip():
                raise ValueError("Prompt must not be empty")

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()

        elif llm == "llama":
            headers = {
                "Authorization": f"Bearer {groq_api_key}",  # Using the same Groq API key
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",  # Groq's LLaMA 3 model
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 1.0
            }
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()

        elif llm == "chatgpt":
            headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 1.0
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()

        elif llm == "uniguru":
            headers = {
                "Authorization": f"Bearer {uniguru_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "prompt": prompt,
                "max_tokens": 512,
                "temperature": 0.7
            }
            response = requests.post(
                "https://api.uniguru.com/v1/completions",  # Replace if necessary
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result['text'].strip()  # Adjust based on actual response

        else:
            raise ValueError(f"Unsupported LLM: {llm}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling {llm} API: {e}")
        return f"Failed to fetch response from {llm} model."
    except Exception as e:
        logger.error(f"Unexpected error with {llm}: {e}")
        return "An unexpected error occurred."

# Chatbot Routes
@app.post("/chatpost")
async def receive_query(chat: ChatMessage):
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    query_record = {
        "message": chat.message,
        "llm": chat.llm,
        "timestamp": timestamp,
        "type": "chat_message"
    }
    try:
        chat_collection = user_collection.insert_one(query_record)
        query_record["_id"] = str(chat_collection.inserted_id)
        logger.info(f"Received message: {chat.message} for LLM: {chat.llm}")
        return {"status": "Query received", "data": query_record}
    except Exception as e:
        logger.error(f"Failed to store query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store query: {str(e)}")

@app.get("/chatbot")
async def send_response():
    try:
        latest_query = user_collection.find_one(
            {"type": "chat_message", "response": None},
            sort=[("timestamp", -1)]
        )
        if not latest_query:
            return {"error": "No queries yet"}

        query_message = latest_query["message"]
        selected_llm = latest_query["llm"]
        logger.info(f"Processing query: {query_message} with LLM: {selected_llm}")

        llm_reply = call_llm(query_message, selected_llm)

        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        response_data = {
            "message": llm_reply,
            "timestamp": timestamp,
            "type": "chat_response",
            "query_id": str(latest_query["_id"]),
            "llm": selected_llm
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
        logger.error(f"Failed to process response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

# PDF Processing Route
@app.post("/process-pdf", response_model=PDFResponse)
async def process_pdf(file: UploadFile = File(...), llm: str = Form(..., pattern="^(grok|llama|chatgpt|uniguru)$")):
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
        # Use call_llm instead of build_qa_agent for consistency
        answer = call_llm(f"Summarize the following content: {structured_data['body']}", llm)

        audio_file = text_to_speech(answer, file_prefix="output_pdf")
        audio_url = f"/static/{os.path.basename(audio_file)}" if audio_file else "No audio generated"

        pdf_doc = {
            "filename": file.filename,
            "title": structured_data["title"],
            "sections": [{"heading": s["heading"], "content": s["content"]} for s in structured_data["sections"]],
            "query": query,
            "answer": answer,
            "audio_file": audio_url,
            "llm": llm,  # Store selected LLM
            "timestamp": datetime.now(timezone.utc)
        }
        pdf_collection.insert_one(pdf_doc)

        global pdf_response
        pdf_response = PDFResponse(
            title=structured_data["title"],
            sections=[Section(heading=s["heading"], content=s["content"]) for s in structured_data["sections"]],
            query=query,
            answer=answer,
            audio_file=audio_url,
            llm=llm
        )
        return pdf_response

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

# Image Processing Route
@app.post("/process-img", response_model=ImageResponse)
async def process_image(file: UploadFile = File(...), llm: str = Form(..., pattern="^(grok|llama|chatgpt|uniguru)$")):
    temp_image_path = ""
    try:
        # Enhanced file validation for JPG images
        if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(status_code=400, detail="Only JPG, JPEG, or PNG files are allowed")

        # Log the file being processed
        logger.info(f"Processing image file: {file.filename} (size: {file.size if hasattr(file, 'size') else 'unknown'} bytes)")

        temp_image_path = os.path.join(
            TEMP_DIR,
            f"temp_image_{time.strftime('%Y%m%d_%H%M%S')}{os.path.splitext(file.filename)[1]}"
        )

        # Ensure temp directory exists
        os.makedirs(TEMP_DIR, exist_ok=True)

        with open(temp_image_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)

        # Verify the file was saved correctly
        if not os.path.exists(temp_image_path) or os.path.getsize(temp_image_path) == 0:
            raise HTTPException(status_code=500, detail="Failed to save uploaded image")

        logger.info(f"Image saved to: {temp_image_path}")

        # Enhanced OCR processing with better error handling
        try:
            ocr_text = extract_text_easyocr(temp_image_path).strip()
            logger.info(f"OCR extraction completed. Text length: {len(ocr_text)}")
            logger.info(f"OCR raw output: {repr(ocr_text)}")
        except Exception as ocr_error:
            logger.error(f"OCR processing failed: {ocr_error}")
            ocr_text = ""

        # Enhanced image analysis for comprehensive description
        try:
            from rag import analyze_image_content, generate_image_description
            image_analysis = analyze_image_content(temp_image_path)
            logger.info(f"Image analysis completed: {image_analysis}")
        except Exception as analysis_error:
            logger.error(f"Image analysis failed: {analysis_error}")
            image_analysis = {}

        # Enhanced response generation based on OCR results
        if not ocr_text:
            ocr_text = "No readable text found in the image."
            
            # Generate description even when no text is found
            if image_analysis:
                try:
                    image_description = generate_image_description(image_analysis, "")
                    answer = f"Image Analysis: {image_description} This appears to be a visual image without readable text content, possibly containing graphics, photos, diagrams, or artistic elements."
                except Exception as desc_error:
                    logger.error(f"Description generation failed: {desc_error}")
                    answer = "This image appears to be either blank, contains no text, or the text is not clear enough for optical character recognition. The image may contain graphics, handwriting, or text in a format that is difficult to extract."
            else:
                answer = "This image appears to be either blank, contains no text, or the text is not clear enough for optical character recognition. The image may contain graphics, handwriting, or text in a format that is difficult to extract."
            
            query = "Image analysis - visual content without readable text"
        else:
            query = "Detailed analysis and summary of image content with text"
            
            # Generate comprehensive description including both text and visual analysis
            if image_analysis:
                try:
                    image_description = generate_image_description(image_analysis, ocr_text)
                    base_content = f"Image Properties: {image_description}\n\nExtracted Text Content: {ocr_text}"
                except Exception as desc_error:
                    logger.error(f"Description generation failed: {desc_error}")
                    base_content = f"Extracted Text: {ocr_text}"
            else:
                base_content = f"Extracted Text: {ocr_text}"
            
            # Enhanced prompt for better image text summarization
            enhanced_prompt = f"""You are analyzing a JPG/JPEG image that has been processed using OCR technology. Please provide a comprehensive analysis based on the following information:

{base_content}

Please provide:
1. A clear summary of what the image and text contain
2. The main topics, subjects, or themes covered
3. Key information, data, or insights from the text
4. The likely purpose or context of this image (document type, educational material, diagram, etc.)
5. Any important details that should be highlighted
6. If this appears to be educational content, identify the subject area

Provide your analysis in a well-structured and informative manner that would be helpful for someone who cannot see the image."""
            
            try:
                answer = call_llm(enhanced_prompt, llm)
                logger.info(f"LLM response generated successfully using {llm}")
            except Exception as llm_error:
                logger.error(f"LLM processing failed: {llm_error}")
                answer = f"Text was successfully extracted from the image: {ocr_text[:500]}{'...' if len(ocr_text) > 500 else ''}"

        audio_file = text_to_speech(answer, file_prefix="output_image")
        audio_url = f"/static/{os.path.basename(audio_file)}" if audio_file else "No audio generated"

        image_doc = {
            "filename": file.filename,
            "ocr_text": ocr_text,
            "query": query,
            "answer": answer,
            "audio_file": audio_url,
            "llm": llm,  # Store selected LLM
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

# Summarize Routes
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

# Audio Streaming and Download Routes
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

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise