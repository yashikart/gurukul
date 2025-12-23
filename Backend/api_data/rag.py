from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
from fastapi.responses import FileResponse
import os
import fitz  # PyMuPDF
import easyocr
from PIL import Image
import re
import time
import socket
import cv2
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_community.vectorstores import FAISS
from langchain_classic.chains.retrieval_qa.base import RetrievalQA
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    # Fallback: simple text splitter if langchain_text_splitters is not available
    class RecursiveCharacterTextSplitter:
        def __init__(self, chunk_size=1000, chunk_overlap=200, length_function=len, separators=None):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.length_function = length_function
            self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        
        def split_text(self, text: str) -> List[str]:
            """Simple text splitting implementation"""
            if self.length_function(text) <= self.chunk_size:
                return [text]
            
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + self.chunk_size
                if end >= len(text):
                    chunks.append(text[start:])
                    break
                
                # Try to split at a separator
                best_split = end
                for sep in self.separators:
                    split_pos = text.rfind(sep, start, end)
                    if split_pos > start:
                        best_split = split_pos + len(sep)
                        break
                
                chunks.append(text[start:best_split])
                start = best_split - self.chunk_overlap
                if start < 0:
                    start = 0
            
            return chunks
import pytesseract
from PIL import Image
from langchain_huggingface import HuggingFaceEmbeddings
from gtts import gTTS
from typing import List, Dict
import shutil
import logging
from langchain_core.language_models.llms import LLM
from typing import Optional, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create temporary directory for files
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Pydantic models for response structure
class Section(BaseModel):
    heading: str
    content: str

class PDFResponse(BaseModel):
    title: str
    sections: List[Section]
    query: str
    answer: str
    audio_file: str
    llm: str

class ImageResponse(BaseModel):
    ocr_text: str
    query: str
    answer: str
    audio_file: str
    llm: str

pdf_response: PDFResponse | None = None
image_response: ImageResponse| None = None

class SimpleGroqLLM(LLM):
    groq_api_key: str
    model: str = "llama-3.1-8b-instant"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

        try:
            result = response.json()

            # Check for HTTP errors first
            if response.status_code != 200:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                logger.error(f"Groq API HTTP {response.status_code}: {error_msg}")
                raise RuntimeError(f"Groq API error: {error_msg}")

            # Check for successful response format
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Unexpected response format from Groq API: {result}")

        except requests.exceptions.JSONDecodeError:
            logger.error(f"Groq API returned invalid JSON: {response.text}")
            raise RuntimeError("Failed to parse Groq API response.")
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise RuntimeError(f"Failed to generate response from Groq API: {str(e)}")
    
    @property
    def _llm_type(self) -> str:
        return "groq-llm"
    
def parse_pdf(file_path: str) -> Dict:
    try:
        doc = fitz.open(file_path)
        raw_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            raw_text += text + "\n"
        doc.close()
        lines = raw_text.strip().split('\n')
        title = next((line.strip() for line in lines if line.strip()), "")
        section_pattern = re.compile(r'^(?:\d+\.?)+\s+.+', re.MULTILINE)
        matches = list(section_pattern.finditer(raw_text))
        sections = []
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            section_title = match.group().strip()
            section_body = raw_text[start:end].strip()
            sections.append({"heading": section_title, "content": section_body})
        return {
            "title": title,
            "body": raw_text.strip(),
            "sections": sections
        }
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        return {"title": "", "body": "", "sections": []}

def extract_text_easyocr(image_path: str) -> str:
    reader = easyocr.Reader(['en' , 'hi'], gpu=False)
    result = reader.readtext(image_path, detail=0)
    print("OCR result list:", result)
    return " ".join(result)

#def extract_text_tesseract(image_path: str) -> str:
#    try:
#        # Use 'with' to automatically close the file
#        with Image.open(image_path) as img:
#            # Use Tesseract to extract text
#           extracted_text = pytesseract.image_to_string(img, lang='eng+hin')
#
#        print("OCR result:", extracted_text)
#        return extracted_text.strip()
#    
#    except Exception as e:
#        print(f"Error during OCR: {e}")
#        raise e

def build_qa_agent(texts: List[str], groq_api_key: str, chunk_size: int = 800, chunk_overlap: int = 150) -> RetrievalQA:
    """
    Build a QA agent with text chunking to handle large documents.
    
    Args:
        texts: List of text strings to process
        groq_api_key: Groq API key
        chunk_size: Size of each text chunk (default 800 chars, ~200 tokens)
        chunk_overlap: Overlap between chunks (default 150 chars)
    """
    llm = SimpleGroqLLM(groq_api_key=groq_api_key, model="llama-3.1-8b-instant")
    
    # Combine all texts
    combined_text = "\n\n".join([t.strip() for t in texts if t.strip()])
    
    # Estimate token count (rough approximation: 1 token ≈ 4 characters)
    estimated_tokens = len(combined_text) // 4
    logger.info(f"PDF content length: {len(combined_text)} chars (~{estimated_tokens} tokens)")
    
    # Split text into chunks to avoid token limits
    # Using smaller chunks (800 chars ≈ 200 tokens) to stay well under 6000 token limit
    # With k=2 chunks retrieved, that's ~400 tokens of context + query + response
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Split the text into chunks
    text_chunks = text_splitter.split_text(combined_text)
    logger.info(f"Split text into {len(text_chunks)} chunks (chunk_size={chunk_size}, overlap={chunk_overlap})")
    
    # Create documents from chunks
    documents = [Document(page_content=chunk) for chunk in text_chunks]
    
    # Create embeddings and vector store
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(documents, embeddings)
    
    # Create custom prompt template that enforces paragraph formatting
    prompt_template = """Use the following pieces of context to answer the question at the end. 

CRITICAL FORMATTING REQUIREMENT: Write your answer ONLY in well-formed paragraphs. DO NOT use bullet points, numbered lists, dashes, asterisks, or any list formatting. Write in complete sentences that flow naturally into paragraphs. Each paragraph should be 3-5 sentences covering a complete thought. Use double line breaks between paragraphs.

Context:
{context}

Question: {question}

Answer (write in paragraphs only, no bullet points or lists):"""
    
    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # Create QA agent with retriever that only gets relevant chunks
    # Using k=2 to limit context size (2 chunks × 200 tokens = 400 tokens max)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=db.as_retriever(
            search_kwargs={"k": 2}  # Only retrieve top 2 most relevant chunks to stay under token limit
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}  # Use custom prompt template
    )
    return qa

def text_to_speech(text: str, file_prefix: str = "output") -> str:
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(TEMP_DIR, f"{file_prefix}_{timestamp}.mp3")
        logger.info(f"Generating audio with Google TTS to {output_file}")
        tts = gTTS(text=text, lang="en")
        tts.save(output_file)
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            logger.error(f"Audio file {output_file} was not created or is empty")
            return ""
        return output_file
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        return ""

