"""
Simple FastAPI with 3 endpoints: ask-vedas, edumentor, wellness
Each endpoint has both GET and POST methods for frontend integration
"""

import os
import uuid
import logging
import time
import requests
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Environment and AI imports
from dotenv import load_dotenv
import google.generativeai as genai

# LangChain imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Local LLM imports
from ollama_client import OllamaClient

# Load environment variables from centralized configuration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared_config import load_shared_config

# Load centralized configuration
load_shared_config("orchestration")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Advanced Forecasting imports (after logger setup)
try:
    from smart_model_selector import SmartModelSelector
    from enhanced_prophet_model import EnhancedProphetModel
    from enhanced_arima_model import EnhancedARIMAModel
    from model_performance_evaluator import ModelPerformanceEvaluator
    FORECASTING_AVAILABLE = True
    logger.info("Advanced forecasting models loaded successfully")
except ImportError as e:
    FORECASTING_AVAILABLE = False
    logger.warning(f"Advanced forecasting not available: {e}")
    logger.info("Install required packages: pip install prophet statsmodels scikit-learn")

def ensure_complete_text(text: str, max_length: int = 2000) -> str:
    """
    Ensures the text ends at a complete sentence and is within max_length.
    If truncated, it tries to find the last complete sentence.
    """
    if not text:
        return ""

    # If text is already within max_length and ends with punctuation, return as is
    if len(text) <= max_length and re.search(r'[.!?:]\s*$', text):
        return text.strip()

    # Truncate to max_length if necessary
    if len(text) > max_length:
        text = text[:max_length]

    # Find the last sentence-ending punctuation
    sentence_enders = re.compile(r'[.!?:]')
    matches = list(sentence_enders.finditer(text))

    if matches:
        # Find the last match that is not too close to the end (to avoid cutting off mid-word)
        last_match = None
        for match in reversed(matches):
            # Ensure there's at least one character after the punctuation or it's the very end
            if match.end() <= len(text) or (match.end() + 1) >= len(text):
                last_match = match
                break
        
        if last_match:
            return text[:last_match.end()].strip()
    
    # If no sentence ender found or it's too short, try to cut at last word boundary
    last_space = text.rfind(' ')
    if last_space != -1 and last_space > len(text) * 0.7:  # Avoid cutting off too much
        return text[:last_space].strip() + "..."
    
    # Fallback: just return the truncated text with ellipsis
    return text.strip() + "..."

class SimpleOrchestrationEngine:
    """Simple orchestration engine for the three main endpoints"""
    
    def __init__(self):
        self.vector_stores = {}
        self.embedding_model = None
        self.gemini_model = None
        self.ollama_client = None
        self.forecasting_enabled = FORECASTING_AVAILABLE
        self.initialize_llms()
        if self.forecasting_enabled:
            self.initialize_forecasting()

    def initialize_llms(self):
        """Initialize both Ollama (primary) and Gemini (fallback) LLMs"""

        # Initialize Ollama as primary LLM
        try:
            self.ollama_client = OllamaClient(model="llama3.2:3b")
            logger.info("✅ Ollama client initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️  Ollama initialization failed: {e}")
            self.ollama_client = None

        # Initialize Gemini as fallback
        self.initialize_gemini()

    def initialize_gemini(self):
        """Initialize Gemini API with failover"""
        # Default Google AI Studio API key
        default_gemini_key = "AIzaSyDSunIIg6InYPa4yaYhrXKGXO2HTWhi_wc"
        primary_key = os.getenv("GEMINI_API_KEY", default_gemini_key)
        backup_key = os.getenv("GEMINI_API_KEY_BACKUP")
        
        # Try primary key
        if primary_key:
            try:
                genai.configure(api_key=primary_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                test_response = self.gemini_model.generate_content("Hello")
                if test_response and test_response.text:
                    logger.info("Gemini API initialized with primary key")
                    return
            except Exception as e:
                logger.warning(f"Primary Gemini API key failed: {e}")
        
        # Try backup key
        if backup_key:
            try:
                genai.configure(api_key=backup_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                test_response = self.gemini_model.generate_content("Hello")
                if test_response and test_response.text:
                    logger.info("Gemini API initialized with backup key")
                    return
            except Exception as e:
                logger.warning(f"Backup Gemini API key failed: {e}")
        
        logger.error("Both Gemini API keys failed. Using fallback responses.")
        self.gemini_model = None
    
    def initialize_vector_stores(self):
        """Initialize vector stores and embedding model"""
        logger.info("Initializing embedding model...")
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Load existing vector stores
        vector_store_dir = Path("vector_stores")
        store_names = ['vedas_index', 'wellness_index', 'educational_index', 'unified_index']
        
        for store_name in store_names:
            store_path = vector_store_dir / store_name
            if store_path.exists():
                try:
                    store = FAISS.load_local(
                        str(store_path), 
                        self.embedding_model, 
                        allow_dangerous_deserialization=True
                    )
                    self.vector_stores[store_name.replace('_index', '')] = store
                    logger.info(f"Loaded vector store: {store_name}")
                except Exception as e:
                    logger.error(f"Failed to load vector store {store_name}: {e}")
        
        logger.info(f"Initialized with {len(self.vector_stores)} vector stores")

    def initialize_forecasting(self):
        """Initialize forecasting capabilities"""
        if not FORECASTING_AVAILABLE:
            logger.warning("Forecasting not available - missing dependencies")
            return

        try:
            # Initialize forecasting components
            self.model_selector = SmartModelSelector()
            self.performance_evaluator = ModelPerformanceEvaluator()
            logger.info("✅ Advanced forecasting capabilities initialized")
        except Exception as e:
            logger.error(f"Failed to initialize forecasting: {e}")
            self.forecasting_enabled = False

    def generate_forecast(self, data: list, metric_type: str = "general",
                         forecast_periods: int = 30) -> dict:
        """
        Generate forecast using advanced models

        Args:
            data: List of data points with 'date' and 'value' fields
            metric_type: Type of metric ('probability', 'load', 'general')
            forecast_periods: Number of periods to forecast

        Returns:
            Forecast results dictionary
        """
        if not self.forecasting_enabled:
            return {
                "status": "error",
                "message": "Advanced forecasting not available",
                "fallback": "simple_forecast"
            }

        try:
            # Convert data to DataFrame format
            import pandas as pd
            df_data = []
            for point in data:
                df_data.append({
                    'ds': point.get('date'),
                    'y': point.get('value')
                })

            df = pd.DataFrame(df_data)

            # Use smart model selector
            selector = SmartModelSelector(metric_type)
            selection_result = selector.select_best_model(df)

            if selection_result['selected_model'] in ['prophet', 'arima']:
                model = selection_result['model_object']
                forecast_df = model.predict(periods=forecast_periods)

                # Convert forecast to list format
                forecast_data = []
                for _, row in forecast_df.iterrows():
                    forecast_data.append({
                        "date": row['ds'].isoformat(),
                        "predicted_value": float(row['yhat']),
                        "lower_bound": float(row.get('yhat_lower', 0)),
                        "upper_bound": float(row.get('yhat_upper', 0))
                    })

                return {
                    "status": "success",
                    "model_used": selection_result['selected_model'],
                    "forecast_data": forecast_data,
                    "selection_reason": selection_result['selection_reason'],
                    "confidence": selection_result.get('confidence', 'medium')
                }
            else:
                return {
                    "status": "fallback",
                    "message": "Using simple forecast method",
                    "selection_reason": selection_result['selection_reason']
                }

        except Exception as e:
            logger.error(f"Forecast generation failed: {e}")
            return {
                "status": "error",
                "message": f"Forecast generation failed: {str(e)}"
            }

    def generate_response(self, prompt: str, fallback: str) -> str:
        """Generate response using Ollama (primary) and Gemini (fallback)"""

        # Try Ollama first (local LLM)
        if self.ollama_client:
            try:
                result = self.ollama_client.generate_wellness_response(prompt)
                if result.get('success') and result.get('response'):
                    response_text = result['response']
                    # Ensure complete text
                    response_text = ensure_complete_text(response_text, max_length=2000)
                    logger.info(f"✅ Response generated using Ollama ({result.get('response_time', 0)}s)")
                    return response_text
                else:
                    logger.warning("⚠️  Ollama failed to generate response")
            except Exception as e:
                logger.warning(f"Ollama error: {e}")

        # Fallback to Gemini
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(prompt)
                if response and response.text:
                    logger.info("✅ Response generated using Gemini (fallback)")
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API error: {e}")

        # Final fallback to hardcoded response
        logger.warning("⚠️  Both Ollama and Gemini failed, using hardcoded fallback")
        return fallback

    def generate_wellness_response(self, query: str, user_context: Optional[Dict[str, Any]] = None, fallback: str = "", language: str = "english") -> str:
        """Generate wellness response with user context using Ollama (primary) and Gemini (fallback)"""

        # Try Ollama first with user context
        if self.ollama_client:
            try:
                result = self.ollama_client.generate_wellness_response(query, user_context, language)
                if result.get('success') and result.get('response'):
                    response_text = result['response']
                    # Ensure complete text
                    response_text = ensure_complete_text(response_text, max_length=2000)
                    logger.info(f"✅ Wellness response generated using Ollama ({result.get('response_time', 0)}s)")
                    return response_text
                else:
                    logger.warning("⚠️  Ollama failed to generate wellness response")
            except Exception as e:
                logger.warning(f"Ollama wellness error: {e}")

        # Add language instruction if Arabic is selected
        language_instruction = ""
        if language.lower() == "arabic":
            language_instruction = "\n\nLANGUAGE REQUIREMENT: Generate the ENTIRE response in Arabic (العربية). All content must be in Arabic using proper Arabic script and formatting."

        # Fallback to Gemini with basic prompt
        if self.gemini_model:
            try:
                prompt = f"""You are a compassionate wellness counselor. Provide caring, helpful advice for: "{query}"

IMPORTANT CONSTRAINTS:
- Generate a concise but COMPLETE response within approximately 1500-2000 characters.
- Prioritize completeness and clarity over length.
- Ensure your response feels complete and doesn't end abruptly.
- Cover essential points clearly and concisely.
- Make every word count.
{language_instruction}

Provide supportive guidance that:
- Shows empathy and understanding
- Offers practical, actionable advice
- Promotes overall wellbeing
- Is encouraging and positive

CRITICAL: Your response must be complete and feel finished. Do not cut off mid-sentence or mid-thought. If you need to be concise, prioritize covering all essential points briefly rather than covering fewer points in detail."""

                response = self.gemini_model.generate_content(prompt)
                if response and response.text:
                    response_text = response.text.strip()
                    # Ensure complete text
                    response_text = ensure_complete_text(response_text, max_length=2000)
                    logger.info("✅ Wellness response generated using Gemini (fallback)")
                    return response_text
            except Exception as e:
                logger.warning(f"Gemini wellness error: {e}")

        # Final fallback
        if not fallback:
            fallback = f"Thank you for reaching out about '{query}'. It's important to take care of your wellbeing. Here are some gentle suggestions: Take time for self-care, practice deep breathing, stay connected with supportive people, and remember that small steps can lead to big improvements. If you're experiencing serious concerns, please consider speaking with a healthcare professional."

        logger.warning("⚠️  Both Ollama and Gemini failed for wellness, using hardcoded fallback")
        # Ensure fallback is also complete
        return ensure_complete_text(fallback, max_length=2000)

    def generate_financial_response(self, query: str, user_context: Optional[Dict[str, Any]] = None, fallback: str = "", language: str = "english") -> str:
        """Generate financial response with user context using Groq (primary), Ollama (secondary), and Gemini (fallback)"""

        # Build financial context prompt
        financial_context = ""
        if user_context:
            if user_context.get('name'):
                financial_context += f"\nName: {user_context['name']}"
            if user_context.get('monthly_income'):
                monthly_income = float(user_context['monthly_income'])
                financial_context += f"\nMonthly Income: ₹{monthly_income:,.2f}"
            
            # Handle expenses - can be list of dicts or list of ExpenseItem objects
            if user_context.get('expenses'):
                expenses = user_context['expenses']
                total_expenses = 0
                expense_details = []
                
                for exp in expenses:
                    if isinstance(exp, dict):
                        amount = float(exp.get('amount', 0))
                        name = exp.get('name', 'Unknown')
                    elif hasattr(exp, 'amount') and hasattr(exp, 'name'):
                        amount = float(exp.amount)
                        name = exp.name
                    else:
                        continue
                    
                    total_expenses += amount
                    if name and amount > 0:
                        expense_details.append(f"{name}: ₹{amount:,.2f}")
                
                financial_context += f"\nTotal Monthly Expenses: ₹{total_expenses:,.2f}"
                if expense_details:
                    financial_context += f"\nExpense Breakdown: {', '.join(expense_details)}"
                
                if user_context.get('monthly_income'):
                    monthly_income = float(user_context['monthly_income'])
                    monthly_savings = monthly_income - total_expenses
                    savings_rate = (monthly_savings / monthly_income * 100) if monthly_income > 0 else 0
                    financial_context += f"\nMonthly Savings: ₹{monthly_savings:,.2f} ({savings_rate:.1f}% savings rate)"
            
            if user_context.get('financial_goal'):
                financial_context += f"\nFinancial Goal: {user_context['financial_goal']}"
            if user_context.get('financial_type'):
                financial_context += f"\nInvestment Style: {user_context['financial_type']}"
            if user_context.get('risk_level'):
                financial_context += f"\nRisk Tolerance: {user_context['risk_level']}"

        # Add language instruction if Arabic is selected
        language_instruction = ""
        if language.lower() == "arabic":
            language_instruction = "\n\nLANGUAGE REQUIREMENT: Generate the ENTIRE response in Arabic (العربية). All content must be in Arabic using proper Arabic script and formatting."

        # Try Groq API first (for Grok/Llama models via Groq)
        groq_api_key = os.getenv('GROQ_API_KEY', '').strip().strip('"').strip("'")
        if groq_api_key:
            try:
                financial_prompt = f"""You are a professional financial advisor with expertise in personal finance, investments, budgeting, and financial planning. Provide helpful, supportive financial guidance.{financial_context}

User's Question: "{query}"

IMPORTANT CONSTRAINTS:
- Generate a concise but COMPLETE response within approximately 1500-2000 characters.
- Prioritize completeness and clarity over length.
- Ensure your response feels complete and doesn't end abruptly.
- Cover essential points clearly and concisely.
- Make every word count.
{language_instruction}

Please provide financial advice that:
- Is empathetic and understanding of their financial situation
- Offers practical, actionable financial strategies and recommendations
- Helps them achieve their stated financial goals
- Is encouraging and supportive
- Considers their financial profile (income, expenses, savings, goals, risk tolerance)
- Provides specific, personalized recommendations based on their situation
- Uses clear, easy-to-understand language
- Includes actionable steps they can take

CRITICAL: Your response must be complete and feel finished. Do not cut off mid-sentence or mid-thought. If you need to be concise, prioritize covering all essential points briefly rather than covering fewer points in detail.

Provide a comprehensive response that addresses their question while considering their complete financial context."""

                api_url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Try Llama models via Groq (primary: llama-3.3-70b, fallback: llama-3.1-70b)
                models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant"]
                
                for model_name in models_to_try:
                    try:
                        payload = {
                            "model": model_name,
                            "messages": [{"role": "user", "content": financial_prompt}],
                            "temperature": 0.7,
                            "max_tokens": 2048,
                            "top_p": 0.9
                        }
                        
                        start_time = time.time()
                        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            message = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                            if message:
                                # Ensure complete text
                                message = ensure_complete_text(message, max_length=2000)
                                logger.info(f"✅ Financial response generated using Groq ({model_name}) ({response_time:.2f}s)")
                                return message
                        else:
                            logger.warning(f"⚠️  Groq API error with {model_name}: HTTP {response.status_code}")
                    except Exception as e:
                        logger.warning(f"⚠️  Groq API error with {model_name}: {e}")
                        continue
                        
                logger.warning("⚠️  All Groq models failed, trying Ollama...")
            except Exception as e:
                logger.warning(f"⚠️  Groq API error: {e}")

        # Try Ollama as secondary option (using direct prompt method for financial advice)
        if self.ollama_client:
            try:
                # Create a comprehensive prompt for financial advice
                financial_prompt = f"""You are a professional financial advisor with expertise in personal finance, investments, budgeting, and financial planning. Provide helpful, supportive financial guidance.{financial_context}

User's Question: "{query}"

IMPORTANT CONSTRAINTS:
- Generate a concise but COMPLETE response within approximately 1500-2000 characters.
- Prioritize completeness and clarity over length.
- Ensure your response feels complete and doesn't end abruptly.
- Cover essential points clearly and concisely.
- Make every word count.
{language_instruction}

Please provide financial advice that:
- Is empathetic and understanding of their financial situation
- Offers practical, actionable financial strategies and recommendations
- Helps them achieve their stated financial goals
- Is encouraging and supportive
- Considers their financial profile (income, expenses, savings, goals, risk tolerance)
- Provides specific, personalized recommendations based on their situation
- Uses clear, easy-to-understand language
- Includes actionable steps they can take

CRITICAL: Your response must be complete and feel finished. Do not cut off mid-sentence or mid-thought. If you need to be concise, prioritize covering all essential points briefly rather than covering fewer points in detail.

Provide a comprehensive response that addresses their question while considering their complete financial context."""

                # Use the Ollama client's internal method to generate response directly
                if hasattr(self.ollama_client, '_make_ollama_request'):
                    start_time = time.time()
                    response = self.ollama_client._make_ollama_request(financial_prompt)
                    response_time = time.time() - start_time
                    
                    if response and response.strip():
                        response_text = response.strip()
                        # Ensure complete text
                        response_text = ensure_complete_text(response_text, max_length=2000)
                        logger.info(f"✅ Financial response generated using Ollama ({response_time:.2f}s)")
                        return response_text
                else:
                    # Fallback: use the wellness method with financial prompt (it just sends the prompt to Ollama)
                    result = self.ollama_client.generate_wellness_response(financial_prompt, user_context)
                    if result.get('success') and result.get('response'):
                        response_text = result['response']
                        # Ensure complete text
                        response_text = ensure_complete_text(response_text, max_length=2000)
                        logger.info(f"✅ Financial response generated using Ollama ({result.get('response_time', 0)}s)")
                        return response_text
                    
                logger.warning("⚠️  Ollama failed to generate financial response")
            except Exception as e:
                logger.warning(f"Ollama financial error: {e}")

        # Fallback to Gemini with financial prompt
        if self.gemini_model:
            try:
                prompt = f"""You are a professional financial advisor. Provide helpful, supportive financial guidance for: "{query}"{financial_context}

IMPORTANT CONSTRAINTS:
- Generate a concise but COMPLETE response within approximately 1500-2000 characters.
- Prioritize completeness and clarity over length.
- Ensure your response feels complete and doesn't end abruptly.
- Cover essential points clearly and concisely.
- Make every word count.
{language_instruction}

Provide financial advice that:
- Is empathetic and understanding
- Offers practical, actionable financial strategies
- Helps achieve financial goals
- Is encouraging and supportive
- Considers the user's financial profile and risk tolerance
- Provides specific recommendations based on their situation

CRITICAL: Your response must be complete and feel finished. Do not cut off mid-sentence or mid-thought. If you need to be concise, prioritize covering all essential points briefly rather than covering fewer points in detail."""

                response = self.gemini_model.generate_content(prompt)
                if response and response.text:
                    response_text = response.text.strip()
                    # Ensure complete text
                    response_text = ensure_complete_text(response_text, max_length=2000)
                    logger.info("✅ Financial response generated using Gemini (fallback)")
                    return response_text
            except Exception as e:
                logger.warning(f"Gemini financial error: {e}")

        # Final fallback
        if not fallback:
            fallback = f"Thank you for your financial question about '{query}'. Based on your financial profile, here are some helpful suggestions: Review your monthly budget regularly, prioritize saving for your financial goals, consider diversifying your investments based on your risk tolerance, and remember that small consistent steps lead to significant financial progress. If you need more specific advice, please provide more details about your financial situation."

        logger.warning("⚠️  Both Ollama and Gemini failed for financial, using hardcoded fallback")
        # Ensure fallback is also complete
        return ensure_complete_text(fallback, max_length=2000)
    
    def search_documents(self, query: str, store_type: str = "unified") -> list:
        """Search relevant documents from vector store"""
        if store_type in self.vector_stores:
            try:
                retriever = self.vector_stores[store_type].as_retriever(search_kwargs={"k": 3})
                docs = retriever.invoke(query)
                return [{"text": doc.page_content[:500], "source": doc.metadata.get("source", "unknown")} for doc in docs]
            except Exception as e:
                logger.error(f"Vector search error: {e}")
        return []

# Global engine instance
engine = SimpleOrchestrationEngine()

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"
    language: Optional[str] = "english"

class WellnessRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"
    mood_score: Optional[float] = None
    stress_level: Optional[float] = None
    language: Optional[str] = "english"

class ExpenseItem(BaseModel):
    """Expense item with name and amount"""
    name: str
    amount: float

class FinancialRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"
    name: Optional[str] = None
    monthly_income: Optional[float] = None
    expenses: Optional[List[ExpenseItem]] = None
    financial_goal: Optional[str] = None
    financial_type: Optional[str] = "Conservative"
    risk_level: Optional[str] = "Low"
    language: Optional[str] = "english"

class SimpleResponse(BaseModel):
    query_id: str
    query: str
    response: str
    sources: list
    timestamp: str
    endpoint: str

# Lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Simple Orchestration API...")
    engine.initialize_vector_stores()
    logger.info("Simple Orchestration API ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Simple Orchestration API...")

# Initialize FastAPI app
app = FastAPI(
    title="Simple Orchestration API",
    description="Three simple endpoints: ask-vedas, edumentor, wellness with GET and POST methods",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ASK-VEDAS ENDPOINTS ====================

@app.get("/ask-vedas")
async def ask_vedas_get(
    query: str = Query(..., description="Your spiritual question"),
    user_id: str = Query("anonymous", description="User ID")
):
    """GET method for Vedas spiritual wisdom"""
    return await process_vedas_query(query, user_id)

@app.post("/ask-vedas")
async def ask_vedas_post(request: QueryRequest):
    """POST method for Vedas spiritual wisdom"""
    return await process_vedas_query(request.query, request.user_id)

async def process_vedas_query(query: str, user_id: str):
    """Process Vedas query and return spiritual wisdom"""
    try:
        # Search relevant documents
        sources = engine.search_documents(query, "vedas")
        context = "\n".join([doc["text"] for doc in sources[:2]])
        
        # Generate response
        prompt = f"""You are a wise spiritual teacher. Based on ancient Vedic wisdom, provide profound guidance for this question: "{query}"

Context from sacred texts:
{context}

Provide spiritual wisdom that is authentic, practical, and inspiring. Keep it concise but meaningful."""

        fallback = f"The ancient Vedic texts teach us to seek truth through self-reflection and righteous action. Regarding '{query}', remember that true wisdom comes from understanding the interconnectedness of all existence. Practice mindfulness, act with compassion, and seek the divine within yourself."
        
        response_text = engine.generate_response(prompt, fallback)
        
        return SimpleResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            response=response_text,
            sources=sources,
            timestamp=datetime.now().isoformat(),
            endpoint="ask-vedas"
        )
        
    except Exception as e:
        logger.error(f"Error in ask-vedas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== EDUMENTOR ENDPOINTS ====================

@app.get("/edumentor")
async def edumentor_get(
    query: str = Query(..., description="Your learning question"),
    user_id: str = Query("anonymous", description="User ID"),
    language: str = Query("english", description="Language for response (english, arabic)")
):
    """GET method for educational content"""
    return await process_edumentor_query(query, user_id, language)

@app.post("/edumentor")
async def edumentor_post(request: QueryRequest):
    """POST method for educational content"""
    language = getattr(request, 'language', 'english')
    return await process_edumentor_query(request.query, request.user_id, language)

async def process_edumentor_query(query: str, user_id: str, language: str = "english"):
    """Process educational query and return learning content"""
    try:
        # Search relevant documents from multiple stores for comprehensive results
        all_sources = []

        # Search in vedas store for spiritual/vedic content
        vedas_sources = engine.search_documents(query, "vedas")
        all_sources.extend(vedas_sources)

        # Search in educational store for curriculum content
        educational_sources = engine.search_documents(query, "educational")
        all_sources.extend(educational_sources)

        # Search in unified store as fallback
        if not all_sources:
            unified_sources = engine.search_documents(query, "unified")
            all_sources.extend(unified_sources)

        # Use the best sources for context
        sources = all_sources[:3]  # Take top 3 sources
        context = "\n".join([doc["text"] for doc in sources])
        
        # Generate response with language instruction
        language_instruction = ""
        if language.lower() == "arabic":
            language_instruction = "\n\nLANGUAGE REQUIREMENT: Generate the ENTIRE response in Arabic (العربية). All content must be in Arabic using proper Arabic script and formatting."
        
        prompt = f"""You are an expert educator. Explain this topic clearly and engagingly: "{query}"

Educational context:
{context}

IMPORTANT CONSTRAINTS:
- Generate a concise but COMPLETE explanation within approximately 1500-2000 characters.
- Prioritize completeness and clarity over length.
- Ensure your explanation feels complete and doesn't end abruptly.
- Cover essential concepts clearly and concisely.
- Make every word count.
{language_instruction}

Provide a clear, comprehensive explanation that:
- Uses simple, understandable language
- Includes practical examples
- Makes the topic interesting and memorable
- Is suitable for students

CRITICAL: Your explanation must be complete and feel finished. Do not cut off mid-sentence or mid-thought. If you need to be concise, prioritize covering all essential points briefly rather than covering fewer points in detail."""

        fallback = f"Great question about '{query}'! This is an important topic to understand. Let me break it down for you in simple terms with practical examples that will help you learn and remember the key concepts. The main idea is to understand the fundamental principles and how they apply in real-world situations."
        
        response_text = engine.generate_response(prompt, fallback)
        # Ensure complete text
        response_text = ensure_complete_text(response_text, max_length=2000)
        
        return SimpleResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            response=response_text,
            sources=sources,
            timestamp=datetime.now().isoformat(),
            endpoint="edumentor"
        )
        
    except Exception as e:
        logger.error(f"Error in edumentor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WELLNESS ENDPOINTS ====================

@app.get("/wellness")
async def wellness_get(
    query: str = Query(..., description="Your wellness concern"),
    user_id: str = Query("anonymous", description="User ID"),
    language: str = Query("english", description="Language for response (english, arabic)")
):
    """GET method for wellness advice"""
    return await process_wellness_query(query, user_id, {}, language)

@app.post("/wellness")
async def wellness_post(request: WellnessRequest):
    """POST method for wellness advice with optional context"""
    user_context = {}
    if request.mood_score is not None:
        user_context['mood_score'] = request.mood_score
    if request.stress_level is not None:
        user_context['stress_level'] = request.stress_level
    if request.user_id:
        user_context['user_id'] = request.user_id

    language = request.language or "english"
    return await process_wellness_query(request.query, request.user_id, user_context, language)

async def process_wellness_query(query: str, user_id: str, user_context: Optional[Dict[str, Any]] = None, language: str = "english"):
    """Process wellness query and return health advice"""
    try:
        # Search relevant documents
        sources = engine.search_documents(query, "wellness")

        # Use the new wellness-specific method with user context and language
        response_text = engine.generate_wellness_response(query, user_context, language=language)
        
        return SimpleResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            response=response_text,
            sources=sources,
            timestamp=datetime.now().isoformat(),
            endpoint="wellness"
        )
        
    except Exception as e:
        logger.error(f"Error in wellness: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-wellness")
async def ask_wellness_post(request: WellnessRequest):
    """Enhanced wellness endpoint with full orchestration and context"""
    try:
        # Search relevant documents
        sources = engine.search_documents(request.query, "wellness")

        # Prepare user context
        user_context = {}
        if request.mood_score is not None:
            user_context['mood_score'] = request.mood_score
        if request.stress_level is not None:
            user_context['stress_level'] = request.stress_level
        if request.user_id:
            user_context['user_id'] = request.user_id

        # Generate enhanced response with context
        response_text = engine.generate_wellness_response(request.query, user_context)

        return {
            "query_id": str(uuid.uuid4()),
            "query": request.query,
            "response": response_text,
            "sources": sources,
            "user_context": user_context,
            "timestamp": datetime.now().isoformat(),
            "endpoint": "ask-wellness",
            "llm_provider": "ollama_primary" if engine.ollama_client else "gemini_fallback"
        }

    except Exception as e:
        logger.error(f"Error in ask-wellness: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== FINANCIAL ENDPOINTS ====================

@app.get("/financial")
async def financial_get(
    query: str = Query(..., description="Your financial concern"),
    user_id: str = Query("anonymous", description="User ID"),
    name: Optional[str] = Query(None, description="Your name"),
    monthly_income: Optional[float] = Query(None, description="Monthly income in currency units"),
    financial_goal: Optional[str] = Query(None, description="Financial goal description"),
    financial_type: Optional[str] = Query("Conservative", description="Investment style: Conservative, Moderate, Aggressive"),
    risk_level: Optional[str] = Query("Low", description="Risk tolerance: Low, Medium, High"),
    expenses: Optional[str] = Query(None, description="Expenses as JSON string: [{'name': 'Expense Name', 'amount': 1000}]"),
    language: str = Query("english", description="Language for response (english, arabic)")
):
    """
    GET method for financial advice using Llama/Grok models
    
    Provides personalized financial advice based on your query and optional profile information.
    Uses Groq API (Llama models) as primary, with Ollama and Gemini as fallbacks.
    """
    user_context = {}
    if name:
        user_context['name'] = name
    if monthly_income:
        user_context['monthly_income'] = monthly_income
    if financial_goal:
        user_context['financial_goal'] = financial_goal
    if financial_type:
        user_context['financial_type'] = financial_type
    if risk_level:
        user_context['risk_level'] = risk_level
    if expenses:
        try:
            import json
            user_context['expenses'] = json.loads(expenses)
        except:
            logger.warning(f"Failed to parse expenses JSON: {expenses}")
    
    return await process_financial_query(query, user_id, user_context, language)

@app.post("/financial")
async def financial_post(request: FinancialRequest):
    """POST method for financial advice with financial profile"""
    user_context = {}
    if request.name:
        user_context['name'] = request.name
    if request.monthly_income:
        user_context['monthly_income'] = request.monthly_income
    if request.expenses:
        # Convert ExpenseItem objects to dictionaries for processing
        expense_list = []
        for exp in request.expenses:
            if isinstance(exp, dict):
                expense_list.append(exp)
            elif hasattr(exp, 'name') and hasattr(exp, 'amount'):
                expense_list.append({"name": exp.name, "amount": exp.amount})
            else:
                expense_list.append(exp)
        user_context['expenses'] = expense_list
    if request.financial_goal:
        user_context['financial_goal'] = request.financial_goal
    if request.financial_type:
        user_context['financial_type'] = request.financial_type
    if request.risk_level:
        user_context['risk_level'] = request.risk_level
    if request.user_id:
        user_context['user_id'] = request.user_id

    language = request.language or "english"
    return await process_financial_query(request.query, request.user_id, user_context, language)

async def process_financial_query(query: str, user_id: str, user_context: Optional[Dict[str, Any]] = None, language: str = "english"):
    """Process financial query and return financial advice"""
    try:
        # Search relevant documents
        sources = engine.search_documents(query, "wellness")  # Use wellness store for now, can add financial store later

        # Use the new financial-specific method with user context and language
        logger.info(f"Processing financial query: {query[:100]}...")
        logger.info(f"User context: {user_context}, language: {language}")
        response_text = engine.generate_financial_response(query, user_context, language=language)
        
        if not response_text or not response_text.strip():
            logger.error("Empty response from generate_financial_response")
            response_text = "I apologize, but I couldn't generate a proper response. Please try again or provide more details about your financial question."
        
        logger.info(f"Financial response generated successfully ({len(response_text)} chars)")
        
        return SimpleResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            response=response_text,
            sources=sources,
            timestamp=datetime.now().isoformat(),
            endpoint="financial"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in process_financial_query: {e}", exc_info=True)
        # Return a proper error response instead of raising
        error_response = "I apologize, but I encountered an error processing your financial query. Please try again or check your connection."
        return SimpleResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            response=error_response,
            sources=[],
            timestamp=datetime.now().isoformat(),
            endpoint="financial"
        )

# ==================== ROOT ENDPOINT ====================

# Forecasting endpoints
class ForecastRequest(BaseModel):
    """Request model for forecasting"""
    data: list
    metric_type: str = "general"
    forecast_periods: int = 30
    user_id: Optional[str] = None

@app.post("/forecast")
async def generate_forecast_endpoint(request: ForecastRequest):
    """Generate time series forecast using advanced models"""
    try:
        result = engine.generate_forecast(
            data=request.data,
            metric_type=request.metric_type,
            forecast_periods=request.forecast_periods
        )

        # Format response for Gurukul system compatibility
        return {
            "report_type": "forecast",
            "language": "en",
            "sentiment": "neutral" if result["status"] == "success" else "negative",
            "content": result,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "user_id": request.user_id,
                "metric_type": request.metric_type,
                "forecast_periods": request.forecast_periods,
                "forecasting_enabled": engine.forecasting_enabled
            }
        }

    except Exception as e:
        logger.error(f"Forecast endpoint error: {e}")
        return {
            "report_type": "forecast",
            "language": "en",
            "sentiment": "negative",
            "content": {
                "status": "error",
                "message": f"Forecast generation failed: {str(e)}"
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "user_id": request.user_id,
                "error": True
            }
        }

@app.get("/forecast/status")
async def forecast_status():
    """Get forecasting system status"""
    return {
        "forecasting_enabled": engine.forecasting_enabled,
        "available_models": ["prophet", "arima", "auto"] if engine.forecasting_enabled else [],
        "metric_types": ["probability", "load", "general"],
        "dependencies_installed": FORECASTING_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    endpoints = {
        "ask-vedas": {
            "GET": "/ask-vedas?query=your_question&user_id=optional",
            "POST": "/ask-vedas with JSON body"
        },
        "edumentor": {
            "GET": "/edumentor?query=your_question&user_id=optional",
            "POST": "/edumentor with JSON body"
        },
        "wellness": {
            "GET": "/wellness?query=your_question&user_id=optional",
            "POST": "/wellness with JSON body"
        }
    }

    # Add forecasting endpoints if available
    if engine.forecasting_enabled:
        endpoints["forecast"] = {
            "POST": "/forecast with JSON body containing data array",
            "GET": "/forecast/status for system status"
        }

    return {
        "message": "Simple Orchestration API with Advanced Forecasting",
        "version": "1.0.0",
        "forecasting_enabled": engine.forecasting_enabled,
        "endpoints": endpoints,
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Simple Orchestration API")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on (default: 0.0.0.0)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  SIMPLE ORCHESTRATION API WITH ADVANCED FORECASTING")
    print("="*60)
    print(f" Server URL: http://{args.host}:{args.port}")
    print(f" API Documentation: http://{args.host}:{args.port}/docs")
    print(f" Forecasting Enabled: {FORECASTING_AVAILABLE}")
    print("\n Endpoints:")
    print("   GET/POST /ask-vedas - Spiritual wisdom")
    print("   GET/POST /edumentor - Educational content")
    print("   GET/POST /wellness - Health advice")
    if FORECASTING_AVAILABLE:
        print("   POST /forecast - Advanced time series forecasting")
        print("   GET /forecast/status - Forecasting system status")
    print("="*60)

    uvicorn.run(app, host=args.host, port=args.port)
