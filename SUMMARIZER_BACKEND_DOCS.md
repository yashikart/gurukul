# Summarizer Backend Documentation

## Backend File Location
**File:** `Backend/api_data/api.py`

## Main Endpoints

### 1. **POST `/process-pdf`** - Process PDF/DOC/DOCX Files
**Purpose:** Upload and analyze PDF, DOC, or DOCX documents

**Parameters:**
- `file: UploadFile` (required) - The document file to upload
- `llm: str` (query parameter, default: "grok") - LLM model to use: "grok", "llama", or "uniguru"

**Example Request:**
```bash
POST /process-pdf?llm=uniguru
Content-Type: multipart/form-data
Body: file=<PDF file>
```

**Response Model:** `PDFResponse`
```python
{
    "title": str,
    "sections": [
        {
            "heading": str,
            "content": str
        }
    ],
    "query": str,
    "answer": str,  # The summary text
    "audio_file": str,  # URL to audio file
    "llm": str  # Model used
}
```

**Process Flow:**
1. Validates file extension (pdf, doc, docx)
2. Saves file to temporary directory
3. Parses document using `parse_pdf()` or `parse_word_document()`
4. Creates comprehensive summarization prompt
5. Calls `call_llm(prompt, llm)` to generate summary
6. Generates audio file using `text_to_speech()`
7. Stores result in MongoDB (`pdf_collection`)
8. Returns `PDFResponse` with summary

---

### 2. **POST `/process-img`** - Process Image Files
**Purpose:** Upload and analyze images with OCR text extraction

**Parameters:**
- `file: UploadFile` (required) - The image file (JPG, JPEG, PNG)
- `llm: str` (query parameter, default: "grok") - LLM model to use

**Example Request:**
```bash
POST /process-img?llm=uniguru
Content-Type: multipart/form-data
Body: file=<Image file>
```

**Response Model:** `ImageResponse`
```python
{
    "ocr_text": str,  # Extracted text from image
    "query": str,
    "answer": str,  # The analysis/summary
    "audio_file": str,
    "llm": str
}
```

**Process Flow:**
1. Validates file extension (jpg, jpeg, png)
2. Saves image to temporary directory
3. Extracts text using OCR (`extract_text_easyocr()`)
4. If text found, creates analysis prompt
5. Calls `call_llm(prompt, llm)` to generate analysis
6. Generates audio file
7. Stores result in MongoDB (`image_collection`)
8. Returns `ImageResponse` with analysis

---

### 3. **GET `/process-pdf-stream`** - Stream PDF Analysis Results
**Purpose:** Stream already processed PDF results line by line

**Parameters:**
- `file_path: str` (optional)
- `llm: str` (default: "uniguru")

**Response:** Server-Sent Events (SSE) stream

**Stream Format:**
```
data: 🔍 Starting document analysis...
data: 📄 Processing: <title>
data: 🤖 Using UNIGURU AI model
data: 📝 Generating comprehensive summary...
data: <summary content line by line>
data: ✅ Document analysis complete!
data: [END]
```

---

### 4. **GET `/process-img-stream`** - Stream Image Analysis Results
**Purpose:** Stream already processed image results line by line

**Parameters:**
- `file_path: str` (optional)
- `llm: str` (default: "uniguru")

**Response:** Server-Sent Events (SSE) stream

---

### 5. **GET `/summarize-pdf`** - Get Last Processed PDF Summary
**Purpose:** Retrieve the last processed PDF summary

**Response:** `PDFResponse` (same as `/process-pdf`)

---

### 6. **GET `/summarize-img`** - Get Last Processed Image Summary
**Purpose:** Retrieve the last processed image summary

**Response:** `ImageResponse` (same as `/process-img`)

---

## LLM Integration (`call_llm` function)

**Location:** `Backend/api_data/api.py` (lines 243-373)

**Supported Models:**

### 1. **"grok"** (default)
- **API:** Groq API
- **Model:** `gemma2-9b-it`
- **Endpoint:** `https://api.groq.com/openai/v1/chat/completions`
- **Max Tokens:** 512
- **Temperature:** 0.8

### 2. **"llama"**
- **API:** Groq API
- **Model:** `llama3-70b-8192`
- **Endpoint:** `https://api.groq.com/openai/v1/chat/completions`
- **Max Tokens:** 512
- **Temperature:** 0.6

### 3. **"uniguru"** ⭐ (Recommended)
- **API:** UniGuru API via ngrok
- **Model:** `llama3.1`
- **Endpoint:** `{UNIGURU_NGROK_ENDPOINT}/v1/chat/completions`
- **Default Endpoint:** `https://3a46c48e4d91.ngrok-free.app/v1/chat/completions`
- **Max Tokens:** 2048
- **Temperature:** 0.7
- **Timeout:** 60 seconds

### 4. **"chatgpt"**
- **API:** Groq API
- **Model:** `llama-3.1-8b-instant`
- **Max Tokens:** 512

**Error Handling:**
- Raises `Exception` with error message if API call fails
- Error format: `"Failed to generate response from {LLM} API: {error}"`

---

## Helper Functions

### `parse_pdf(file_path: str) -> dict`
Extracts structured data from PDF files
- Returns: `{"title": str, "body": str, "sections": list}`

### `parse_word_document(file_path: str) -> dict`
Extracts structured data from DOC/DOCX files
- Returns: `{"title": str, "body": str, "sections": list}`

### `extract_text_easyocr(image_path: str) -> str`
Extracts text from images using EasyOCR
- Returns: Extracted text string

### `text_to_speech(text: str, file_prefix: str) -> str`
Converts text to audio file
- Returns: Path to generated audio file

---

## Database Storage

### MongoDB Collections:

1. **`pdf_collection`** - Stores PDF processing results
```python
{
    "filename": str,
    "file_type": str,
    "title": str,
    "sections": list,
    "summary": str,
    "llm_model": str,
    "audio_file": str,
    "timestamp": datetime
}
```

2. **`image_collection`** - Stores image processing results
```python
{
    "filename": str,
    "ocr_text": str,
    "query": str,
    "answer": str,
    "llm_model": str,
    "audio_file": str,
    "timestamp": datetime
}
```

---

## Environment Variables Required

```bash
# Groq API (for grok, llama, chatgpt models)
GROQ_API_KEY=your_groq_api_key

# UniGuru ngrok endpoint (optional, has default)
UNIGURU_NGROK_ENDPOINT=https://your-ngrok-url.ngrok-free.app
```

---

## Current Issues & Solutions

### Issue: Backend defaults to "grok" instead of "uniguru"

**Solution Applied:**
1. ✅ Updated endpoints to use `Query()` for `llm` parameter
2. ✅ Added logging to track received `llm` parameter
3. ✅ Frontend sends `llm` as query parameter: `?llm=uniguru`
4. ✅ Frontend also sends `llm` in FormData as backup

**To Fix:**
- **Restart the backend server** after code changes
- Check backend console logs for: `🔍 [process_pdf] Received llm parameter: 'uniguru'`
- If you see `'grok'` instead, the query parameter isn't being received

---

## Testing the Backend

### Test PDF Upload:
```bash
curl -X POST "http://localhost:8000/process-pdf?llm=uniguru" \
  -F "file=@document.pdf"
```

### Test Image Upload:
```bash
curl -X POST "http://localhost:8000/process-img?llm=uniguru" \
  -F "file=@image.jpg"
```

### Check Health:
```bash
curl http://localhost:8000/health
```

---

## File Structure

```
Backend/api_data/
├── api.py              # Main FastAPI application (Summarizer endpoints)
├── rag.py              # RAG functionality
├── llm_service.py      # LLM service wrapper
├── db.py               # MongoDB connection
├── shared_config.py    # Shared configuration
└── temp/               # Temporary file storage
```

---

## Key Code Sections

### Process PDF Endpoint (Lines 419-513)
- File validation
- Document parsing
- Prompt creation
- LLM call
- Audio generation
- MongoDB storage

### Process Image Endpoint (Lines 520-598)
- Image validation
- OCR text extraction
- Prompt creation
- LLM call
- Audio generation
- MongoDB storage

### LLM Call Function (Lines 243-373)
- Model selection logic
- API request handling
- Error handling
- Response parsing

---

## Notes

- **Temporary files** are automatically cleaned up after processing
- **Audio files** are stored and accessible via `/api/stream/{filename}`
- **Global variables** (`pdf_response`, `image_response`) store last processed results
- **Streaming endpoints** read from global variables, not database
- **Error messages** are logged and returned as HTTP 500 errors
