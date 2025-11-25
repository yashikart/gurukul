import os
import re
import time
import logging
import requests
import fitz  # PyMuPDF
import easyocr
from PIL import Image
from gtts import gTTS
from typing import List, Dict, Optional

from dotenv import load_dotenv
from fastapi import UploadFile, File, HTTPException

# LangChain imports (for langchain==0.3.x)
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.language_models.llms import LLM

# ===========================
# Logging configuration
# ===========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================
# Temporary file setup
# ===========================
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# ===========================
# Custom Groq LLM Wrapper
# ===========================
class SimpleGroqLLM(LLM):
    groq_api_key: str
    model: str = "llama3-8b-8192"

    def _call(
        self, prompt: str, stop: Optional[List[str]] = None, run_manager=None, **kwargs
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        try:
            result = response.json()
            if response.status_code != 200:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                logger.error(f"Groq API HTTP {response.status_code}: {error_msg}")
                raise RuntimeError(f"Groq API error: {error_msg}")

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Unexpected response format from Groq API: {result}")

        except requests.exceptions.JSONDecodeError:
            logger.error(f"Groq API returned invalid JSON: {response.text}")
            raise RuntimeError("Failed to parse Groq API response.")
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise RuntimeError("Failed to generate response from Groq API.")

    @property
    def _llm_type(self) -> str:
        return "groq-llm"

# ===========================
# PDF Processing
# ===========================
def parse_pdf(file_path: str) -> Dict:
    try:
        doc = fitz.open(file_path)
        raw_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            raw_text += str(text) + "\n"
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

# ===========================
# Image Content Analyzer
# ===========================
def analyze_image_content(image_path: str) -> dict:
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            format_type = img.format
            mode = img.mode
            aspect_ratio = width / height if height > 0 else 1

            if aspect_ratio > 1.3:
                orientation = "landscape"
            elif aspect_ratio < 0.7:
                orientation = "portrait"
            else:
                orientation = "square"

            colors = img.getcolors(maxcolors=256*256*256)
            dominant_colors = []
            if colors:
                sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
                for count, color in sorted_colors:
                    if isinstance(color, tuple) and len(color) >= 3:
                        r, g, b = color[:3]
                        if r > 200 and g > 200 and b > 200:
                            color_name = "light/white"
                        elif r < 50 and g < 50 and b < 50:
                            color_name = "dark/black"
                        elif r > g and r > b:
                            color_name = "reddish"
                        elif g > r and g > b:
                            color_name = "greenish"
                        elif b > r and b > g:
                            color_name = "bluish"
                        else:
                            color_name = "neutral"
                        dominant_colors.append(color_name)

            return {
                "dimensions": f"{width}x{height}",
                "format": format_type,
                "orientation": orientation,
                "aspect_ratio": round(aspect_ratio, 2),
                "color_mode": mode,
                "dominant_colors": dominant_colors[:3],
                "file_size": os.path.getsize(image_path) if os.path.exists(image_path) else 0
            }

    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return {}

# ===========================
# OCR Function
# ===========================
def extract_text_easyocr(image_path: str) -> str:
    try:
        if not os.path.exists(image_path):
            return ""
        reader = easyocr.Reader(['en', 'hi'], gpu=False)
        result = reader.readtext(image_path, detail=0, paragraph=True)
        # Convert all items to strings before joining
        return " ".join(str(item) for item in result)
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        return ""

# ===========================
# Image Description Generator
# ===========================
def generate_image_description(image_analysis: dict, ocr_text: str = "") -> str:
    try:
        description = f"This is a {image_analysis.get('format')} image with dimensions {image_analysis.get('dimensions')} and {image_analysis.get('orientation')} orientation."
        if image_analysis.get("dominant_colors"):
            description += f" Dominant colors are {', '.join(image_analysis['dominant_colors'])}."
        if ocr_text.strip():
            description += f" It contains readable text: {ocr_text[:150]}..."
        return description
    except Exception as e:
        logger.error(f"Image description generation error: {e}")
        return "Unable to describe image."

# ===========================
# Text-to-Speech
# ===========================
def text_to_speech(text: str, file_prefix: str = "output") -> str:
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(TEMP_DIR, f"{file_prefix}_{timestamp}.mp3")
        tts = gTTS(text=text, lang="en")
        tts.save(output_file)
        return output_file
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return ""

# ===========================
# Build RAG QA Agent
# ===========================
def build_qa_agent(texts: List[str], groq_api_key: str) -> RetrievalQA:
    llm = SimpleGroqLLM(groq_api_key=groq_api_key)
    documents = [Document(page_content=t) for t in texts if t.strip()]
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(documents, embeddings)

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=db.as_retriever(),
        return_source_documents=True
    )
    return qa