"""
Unified Orchestration API
Manages three main endpoints with sub-agent integration and dynamic RAG responses
"""

import os
import sys
import json
import uuid
import logging
import asyncio
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Environment and AI imports
from dotenv import load_dotenv
import google.generativeai as genai

# LangChain imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Local imports
from data_ingestion import UnifiedDataIngestion

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentMemoryManager:
    """
    Common agent memory and state manager that works across all agents
    """
    
    def __init__(self, storage_dir: str = "agent_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.user_sessions = {}
        self.interaction_history = {}
        
    def get_user_session(self, user_id: str) -> Dict[str, Any]:
        """Get or create user session data"""
        if user_id not in self.user_sessions:
            session_file = self.storage_dir / f"user_{user_id}.json"
            if session_file.exists():
                with open(session_file, 'r') as f:
                    self.user_sessions[user_id] = json.load(f)
            else:
                self.user_sessions[user_id] = {
                    'user_id': user_id,
                    'created_at': datetime.now().isoformat(),
                    'last_active': datetime.now().isoformat(),
                    'interaction_count': 0,
                    'preferences': {},
                    'wellness_metrics': {
                        'mood_trend': [],
                        'stress_level': 'moderate',
                        'last_wellness_check': None
                    },
                    'educational_progress': {
                        'quiz_scores': [],
                        'learning_topics': [],
                        'last_activity': None
                    },
                    'spiritual_journey': {
                        'topics_explored': [],
                        'favorite_teachings': [],
                        'last_vedas_query': None
                    }
                }
        return self.user_sessions[user_id]
    
    def update_user_session(self, user_id: str, updates: Dict[str, Any]):
        """Update user session with new data"""
        session = self.get_user_session(user_id)
        session.update(updates)
        session['last_active'] = datetime.now().isoformat()
        session['interaction_count'] += 1
        
        # Save to file
        session_file = self.storage_dir / f"user_{user_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session, f, indent=2)
        
        self.user_sessions[user_id] = session
    
    def add_interaction(self, user_id: str, agent_type: str, query: str, response: Dict[str, Any]):
        """Record an interaction for trigger analysis"""
        if user_id not in self.interaction_history:
            self.interaction_history[user_id] = []
        
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'agent_type': agent_type,
            'query': query,
            'response_summary': self._summarize_response(response),
            'user_satisfaction': None  # Can be updated later
        }
        
        self.interaction_history[user_id].append(interaction)
        
        # Keep only last 50 interactions per user
        if len(self.interaction_history[user_id]) > 50:
            self.interaction_history[user_id] = self.interaction_history[user_id][-50:]
    
    def _summarize_response(self, response: Dict[str, Any]) -> str:
        """Create a brief summary of the response for memory"""
        if 'wisdom' in response:
            return f"Vedas guidance on {response.get('query', 'spiritual topic')}"
        elif 'explanation' in response:
            return f"Educational content about {response.get('query', 'learning topic')}"
        elif 'advice' in response:
            return f"Wellness advice for {response.get('query', 'health concern')}"
        else:
            return "General response"

class GeminiAPIManager:
    """
    Manages Gemini API with failover support between primary and backup keys
    """
    
    def __init__(self):
        # Default Google AI Studio API key
        default_gemini_key = "AIzaSyDSunIIg6InYPa4yaYhrXKGXO2HTWhi_wc"
        self.primary_key = os.getenv("GEMINI_API_KEY", default_gemini_key)
        self.backup_key = os.getenv("GEMINI_API_KEY_BACKUP")
        self.current_model = None
        self.current_key_type = None
        self.initialize_api()
    
    def initialize_api(self):
        """Initialize Gemini API with failover logic"""
        # Try primary key first
        if self.primary_key:
            try:
                genai.configure(api_key=self.primary_key)
                self.current_model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Test the connection
                test_response = self.current_model.generate_content("Hello")
                if test_response and test_response.text:
                    self.current_key_type = "primary"
                    logger.info("Gemini API initialized with primary key")
                    return
            except Exception as e:
                logger.warning(f"Primary Gemini API key failed: {e}")
        
        # Try backup key
        if self.backup_key:
            try:
                genai.configure(api_key=self.backup_key)
                self.current_model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Test the connection
                test_response = self.current_model.generate_content("Hello")
                if test_response and test_response.text:
                    self.current_key_type = "backup"
                    logger.info("Gemini API initialized with backup key")
                    return
            except Exception as e:
                logger.warning(f"Backup Gemini API key failed: {e}")
        
        logger.error("Both Gemini API keys failed. System will use fallback responses.")
        self.current_model = None
        self.current_key_type = None
    
    def generate_content(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Generate content with automatic failover"""
        if not self.current_model:
            return None
        
        for attempt in range(max_retries):
            try:
                response = self.current_model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API error (attempt {attempt + 1}): {e}")
                
                # Try switching to backup key if primary failed
                if attempt == 0 and self.current_key_type == "primary" and self.backup_key:
                    logger.info("Switching to backup Gemini API key")
                    try:
                        genai.configure(api_key=self.backup_key)
                        self.current_model = genai.GenerativeModel('gemini-1.5-flash')
                        self.current_key_type = "backup"
                    except Exception as backup_error:
                        logger.error(f"Backup key switch failed: {backup_error}")
                        break
        
        return None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return self.current_model is not None

class OrchestrationTriggers:
    """
    Orchestration triggers that detect when users need intervention
    """
    
    def __init__(self, memory_manager: AgentMemoryManager):
        self.memory_manager = memory_manager
        self.trigger_thresholds = {
            'low_quiz_score': 60,  # Below 60% triggers intervention
            'wellness_concern': 3,  # Stress level above 3 triggers intervention
            'inactivity_days': 7,   # No activity for 7 days triggers nudge
            'repeated_queries': 3,  # Same type of query 3+ times triggers deeper help
            'financial_stress': 4,  # Financial stress level above 4 triggers intervention
            'poor_spending': 0.8,   # Spending above 80% of income triggers intervention
            'low_mood_threshold': 3  # Mood below 3 triggers intervention
        }
    
    def check_educational_triggers(self, user_id: str, quiz_score: Optional[float] = None) -> List[Dict[str, Any]]:
        """Check for educational intervention triggers"""
        triggers = []
        session = self.memory_manager.get_user_session(user_id)
        
        # Low quiz score trigger
        if quiz_score and quiz_score < self.trigger_thresholds['low_quiz_score']:
            triggers.append({
                'type': 'low_quiz_score',
                'severity': 'high',
                'message': f"Quiz score of {quiz_score}% indicates need for additional support",
                'recommended_action': 'tutoring_session',
                'sub_agent': 'tutorbot'
            })
        
        # Check quiz score trend
        quiz_scores = session['educational_progress']['quiz_scores']
        if len(quiz_scores) >= 3:
            recent_scores = quiz_scores[-3:]
            if all(score < self.trigger_thresholds['low_quiz_score'] for score in recent_scores):
                triggers.append({
                    'type': 'declining_performance',
                    'severity': 'high',
                    'message': "Consistent low quiz scores detected",
                    'recommended_action': 'intensive_tutoring',
                    'sub_agent': 'tutorbot'
                })
        
        return triggers
    
    def check_wellness_triggers(self, user_id: str, mood_score: Optional[float] = None, 
                               stress_level: Optional[float] = None) -> List[Dict[str, Any]]:
        """Check for wellness intervention triggers"""
        triggers = []
        session = self.memory_manager.get_user_session(user_id)
        
        # High stress trigger
        if stress_level and stress_level > self.trigger_thresholds['wellness_concern']:
            triggers.append({
                'type': 'high_stress',
                'severity': 'high',
                'message': f"Stress level of {stress_level} requires immediate attention",
                'recommended_action': 'emotional_support',
                'sub_agent': 'emotionalwellnessbot'
            })
        
        # Low mood trigger
        if mood_score and mood_score < 3:
            triggers.append({
                'type': 'low_mood',
                'severity': 'medium',
                'message': f"Low mood score of {mood_score} detected",
                'recommended_action': 'wellness_check',
                'sub_agent': 'emotionalwellnessbot'
            })
        
        # Check mood trend
        mood_trend = session['wellness_metrics']['mood_trend']
        if len(mood_trend) >= 5:
            recent_moods = mood_trend[-5:]
            if all(mood < 4 for mood in recent_moods):
                triggers.append({
                    'type': 'persistent_low_mood',
                    'severity': 'high',
                    'message': "Persistent low mood pattern detected",
                    'recommended_action': 'comprehensive_wellness_assessment',
                    'sub_agent': 'emotionalwellnessbot'
                })
        
        return triggers

    def check_financial_triggers(self, user_id: str, spending_ratio: Optional[float] = None,
                                financial_stress: Optional[float] = None) -> List[Dict[str, Any]]:
        """Check for financial wellness intervention triggers"""
        triggers = []
        session = self.memory_manager.get_user_session(user_id)

        # High financial stress trigger
        if financial_stress and financial_stress > self.trigger_thresholds['financial_stress']:
            triggers.append({
                'type': 'high_financial_stress',
                'severity': 'high',
                'message': f"Financial stress level of {financial_stress} requires immediate attention",
                'recommended_action': 'financial_counseling',
                'sub_agent': 'financialwellnessbot'
            })

        # Poor spending pattern trigger
        if spending_ratio and spending_ratio > self.trigger_thresholds['poor_spending']:
            triggers.append({
                'type': 'poor_spending',
                'severity': 'medium',
                'message': f"Spending {spending_ratio*100:.1f}% of income indicates need for budgeting help",
                'recommended_action': 'budget_planning',
                'sub_agent': 'financialwellnessbot'
            })

        # Check for financial wellness queries pattern
        interactions = self.memory_manager.interaction_history.get(user_id, [])
        recent_financial_queries = [
            interaction for interaction in interactions[-10:]  # Last 10 interactions
            if 'financial' in interaction.get('query', '').lower() or
               'money' in interaction.get('query', '').lower() or
               'budget' in interaction.get('query', '').lower()
        ]

        if len(recent_financial_queries) >= 3:
            triggers.append({
                'type': 'repeated_financial_concerns',
                'severity': 'medium',
                'message': "Multiple financial queries indicate ongoing financial stress",
                'recommended_action': 'comprehensive_financial_assessment',
                'sub_agent': 'financialwellnessbot'
            })

        return triggers

    async def execute_trigger_actions(self, user_id: str, triggers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute actions based on triggers"""
        results = []
        
        for trigger in triggers:
            try:
                if trigger['sub_agent'] == 'tutorbot':
                    result = await self._call_tutorbot(user_id, trigger)
                elif trigger['sub_agent'] == 'emotionalwellnessbot':
                    result = await self._call_emotional_wellness_bot(user_id, trigger)
                elif trigger['sub_agent'] == 'financialwellnessbot':
                    result = await self._call_financial_wellness_bot(user_id, trigger)
                elif trigger['sub_agent'] == 'quizbot':
                    result = await self._call_quizbot(user_id, trigger)
                else:
                    result = {'status': 'unknown_agent', 'trigger': trigger}
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error executing trigger action: {e}")
                results.append({'status': 'error', 'error': str(e), 'trigger': trigger})
        
        return results
    
    async def _call_tutorbot(self, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Call tutorbot for educational intervention"""
        try:
            tutorbot_url = os.getenv("TUTORBOT_URL", "http://localhost:8001")

            # Prepare request based on trigger type
            if trigger['type'] in ['low_quiz_score', 'declining_performance']:
                # Call lesson plan generation for struggling students
                request_data = {
                    "user_id": user_id,
                    "user_data": {
                        "learning_preferences": {
                            "difficulty": "beginner",  # Lower difficulty for struggling students
                            "session_length": 30,
                            "subjects": ["general"]
                        },
                        "progress": {
                            "total_study_time": 0,
                            "current_streak": 0,
                            "recent_performance": "struggling"
                        },
                        "goals": ["improve_understanding", "build_confidence"],
                        "concepts": []
                    },
                    "target_days": 7,
                    "daily_time_minutes": 30
                }

                response = requests.post(
                    f"{tutorbot_url}/api/v1/lesson-plan",
                    json=request_data,
                    timeout=30
                )

                if response.status_code == 200:
                    tutorbot_data = response.json()
                    return {
                        'status': 'success',
                        'agent': 'tutorbot',
                        'trigger_type': trigger['type'],
                        'intervention': {
                            'type': 'personalized_lesson_plan',
                            'lesson_plan': tutorbot_data,
                            'message': 'Generated personalized learning plan based on performance analysis'
                        }
                    }
                else:
                    logger.warning(f"Tutorbot API returned {response.status_code}")
                    return self._get_tutorbot_fallback(trigger)

            else:
                # For other triggers, get quick suggestions
                response = requests.get(
                    f"{tutorbot_url}/api/v1/suggestions/quick",
                    params={
                        "user_id": user_id,
                        "subject": "general",
                        "time_minutes": 20,
                        "difficulty": "intermediate"
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    suggestions_data = response.json()
                    return {
                        'status': 'success',
                        'agent': 'tutorbot',
                        'trigger_type': trigger['type'],
                        'intervention': {
                            'type': 'learning_suggestions',
                            'suggestions': suggestions_data,
                            'message': 'Generated learning suggestions to re-engage student'
                        }
                    }
                else:
                    logger.warning(f"Tutorbot API returned {response.status_code}")
                    return self._get_tutorbot_fallback(trigger)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to tutorbot: {e}")
            return self._get_tutorbot_fallback(trigger)
        except Exception as e:
            logger.error(f"Error calling tutorbot: {e}")
            return {'status': 'error', 'error': str(e)}

    def _get_tutorbot_fallback(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback response when tutorbot is unavailable"""
        return {
            'status': 'fallback',
            'agent': 'tutorbot',
            'trigger_type': trigger['type'],
            'intervention': {
                'type': 'personalized_lesson_plan',
                'message': 'Tutorbot service unavailable. Using fallback recommendations.',
                'recommendations': [
                    'Focus on foundational concepts',
                    'Practice with easier questions first',
                    'Schedule regular review sessions',
                    'Seek help from teachers or peers'
                ]
            }
        }
    
    async def _call_emotional_wellness_bot(self, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Call emotional wellness bot for wellness intervention"""
        try:
            wellness_bot_url = os.getenv("EMOTIONAL_WELLNESS_BOT_URL", "http://localhost:8002")

            # Get user session to extract mood and stress data
            session = self.memory_manager.get_user_session(user_id)
            wellness_metrics = session.get('wellness_metrics', {})

            if trigger['type'] in ['high_stress', 'low_mood', 'persistent_low_mood']:
                # Call immediate nudge for urgent situations
                mood_trend = wellness_metrics.get('mood_trend', [])
                current_mood = mood_trend[-1] if mood_trend else 5.0

                # Convert stress level string to numeric
                stress_level_map = {"none": 0, "minimal": 1, "mild": 2, "moderate": 3, "high": 4, "severe": 5, "overwhelming": 6}
                stress_level = stress_level_map.get(wellness_metrics.get('stress_level', 'moderate'), 3)

                request_data = {
                    "user_id": user_id,
                    "current_mood": float(current_mood),
                    "stress_level": float(stress_level),
                    "context": f"Triggered by {trigger['type']}: {trigger['message']}"
                }

                response = requests.post(
                    f"{wellness_bot_url}/api/v1/immediate-nudge",
                    json=request_data,
                    timeout=30
                )

                if response.status_code == 200:
                    nudge_data = response.json()
                    return {
                        'status': 'success',
                        'agent': 'emotionalwellnessbot',
                        'trigger_type': trigger['type'],
                        'intervention': {
                            'type': 'immediate_nudge',
                            'nudge_data': nudge_data,
                            'message': 'Providing immediate emotional support and coping strategies'
                        }
                    }
                else:
                    logger.warning(f"Emotional wellness bot API returned {response.status_code}")
                    return self._get_emotional_wellness_fallback(trigger)

            else:
                # For comprehensive analysis, create a user profile
                profile_data = {
                    "user_id": user_id,
                    "name": f"User_{user_id}",
                    "age": 25,  # Default age
                    "timezone": "UTC",
                    "wellness_goals": ["reduce_stress", "improve_mood"],
                    "preferred_activities": ["meditation", "exercise"],
                    "stress_triggers": ["work", "relationships"],
                    "coping_strategies": ["breathing", "journaling"],
                    "baseline_mood": 5,
                    "baseline_stress": "moderate",
                    "baseline_energy": "moderate",
                    "nudge_frequency": "daily",
                    "entries": []
                }

                request_data = {
                    "profile": profile_data,
                    "analysis_days": 14
                }

                response = requests.post(
                    f"{wellness_bot_url}/api/v1/analyze-wellness",
                    json=request_data,
                    timeout=30
                )

                if response.status_code == 200:
                    analysis_data = response.json()
                    return {
                        'status': 'success',
                        'agent': 'emotionalwellnessbot',
                        'trigger_type': trigger['type'],
                        'intervention': {
                            'type': 'comprehensive_analysis',
                            'analysis_data': analysis_data,
                            'message': 'Comprehensive wellness analysis and coaching advice provided'
                        }
                    }
                else:
                    logger.warning(f"Emotional wellness bot API returned {response.status_code}")
                    return self._get_emotional_wellness_fallback(trigger)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to emotional wellness bot: {e}")
            return self._get_emotional_wellness_fallback(trigger)
        except Exception as e:
            logger.error(f"Error calling emotional wellness bot: {e}")
            return {'status': 'error', 'error': str(e)}

    def _get_emotional_wellness_fallback(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback response when emotional wellness bot is unavailable"""
        return {
            'status': 'fallback',
            'agent': 'emotionalwellnessbot',
            'trigger_type': trigger['type'],
            'intervention': {
                'type': 'immediate_support',
                'message': 'Emotional wellness bot unavailable. Using fallback support.',
                'coping_strategies': [
                    'Take slow, deep breaths for 5 minutes',
                    'Practice mindfulness meditation',
                    'Try progressive muscle relaxation',
                    'Write in a journal about your feelings',
                    'Reach out to a trusted friend or counselor'
                ]
            }
        }
    
    async def _call_financial_wellness_bot(self, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Call financial wellness bot for financial intervention"""
        try:
            financial_bot_url = os.getenv("FINANCIAL_WELLNESS_BOT_URL", "http://localhost:8003")

            # Create a basic financial profile for the user
            profile_data = {
                "user_id": user_id,
                "name": f"User_{user_id}",
                "age": 25,
                "income": 50000,  # Default income
                "currency": "USD",
                "financial_goals": ["emergency_fund", "debt_reduction", "savings"],
                "risk_tolerance": "moderate",
                "budgets": [],
                "transactions": [],
                "debts": [],
                "goals": []
            }

            if trigger['type'] in ['financial_stress', 'poor_spending']:
                # Call quick wellness check for immediate financial concerns
                request_data = {
                    "profile": profile_data
                }

                response = requests.post(
                    f"{financial_bot_url}/api/v1/quick-wellness-check",
                    json=request_data,
                    timeout=30
                )

                if response.status_code == 200:
                    wellness_data = response.json()
                    return {
                        'status': 'success',
                        'agent': 'financialwellnessbot',
                        'trigger_type': trigger['type'],
                        'intervention': {
                            'type': 'quick_wellness_check',
                            'wellness_data': wellness_data,
                            'message': 'Quick financial wellness assessment and immediate recommendations'
                        }
                    }
                else:
                    logger.warning(f"Financial wellness bot API returned {response.status_code}")
                    return self._get_financial_wellness_fallback(trigger)

            else:
                # For comprehensive analysis
                request_data = {
                    "profile": profile_data,
                    "analysis_months": 6
                }

                response = requests.post(
                    f"{financial_bot_url}/api/v1/analyze-wellness",
                    json=request_data,
                    timeout=30
                )

                if response.status_code == 200:
                    analysis_data = response.json()
                    return {
                        'status': 'success',
                        'agent': 'financialwellnessbot',
                        'trigger_type': trigger['type'],
                        'intervention': {
                            'type': 'comprehensive_analysis',
                            'analysis_data': analysis_data,
                            'message': 'Comprehensive financial wellness analysis and recommendations'
                        }
                    }
                else:
                    logger.warning(f"Financial wellness bot API returned {response.status_code}")
                    return self._get_financial_wellness_fallback(trigger)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to financial wellness bot: {e}")
            return self._get_financial_wellness_fallback(trigger)
        except Exception as e:
            logger.error(f"Error calling financial wellness bot: {e}")
            return {'status': 'error', 'error': str(e)}

    def _get_financial_wellness_fallback(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback response when financial wellness bot is unavailable"""
        return {
            'status': 'fallback',
            'agent': 'financialwellnessbot',
            'trigger_type': trigger['type'],
            'intervention': {
                'type': 'financial_guidance',
                'message': 'Financial wellness bot unavailable. Using fallback guidance.',
                'recommendations': [
                    'Track your spending for one week to identify patterns',
                    'Create a simple budget with 50/30/20 rule (needs/wants/savings)',
                    'Build an emergency fund starting with $500',
                    'Review and reduce unnecessary subscriptions',
                    'Consider speaking with a financial advisor'
                ]
            }
        }
    
    async def _call_quizbot(self, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Call quizbot for quiz evaluation and feedback"""
        try:
            quizbot_url = os.getenv("QUIZBOT_URL", "http://localhost:8004")

            # Get user session to extract recent quiz performance
            session = self.memory_manager.get_user_session(user_id)
            educational_progress = session.get('educational_progress', {})
            quiz_scores = educational_progress.get('quiz_scores', [])

            if trigger['type'] in ['low_quiz_score', 'declining_performance'] and quiz_scores:
                # Create a sample quiz evaluation to demonstrate the integration
                # In a real scenario, this would be based on actual quiz data

                # Create sample quiz data for evaluation
                sample_quiz = {
                    "id": f"diagnostic_quiz_{user_id}",
                    "title": "Diagnostic Assessment",
                    "description": "Assessment to identify knowledge gaps",
                    "subject": "general",
                    "questions": [
                        {
                            "id": "q1",
                            "question_text": "What is the basic unit of life?",
                            "options": ["Cell", "Atom", "Molecule", "Tissue"],
                            "correct_answer": "Cell",
                            "subject": "biology",
                            "difficulty": "easy",
                            "topic": "cell_biology",
                            "explanation": "The cell is the basic structural and functional unit of all living organisms.",
                            "points": 1
                        }
                    ],
                    "time_limit_minutes": 30,
                    "passing_score_percentage": 60.0
                }

                # Create sample student response based on recent performance
                recent_score = quiz_scores[-1] if quiz_scores else 50
                sample_response = {
                    "student_id": user_id,
                    "quiz_id": sample_quiz["id"],
                    "answers": [
                        {
                            "question_id": "q1",
                            "selected_option": "Cell" if recent_score > 60 else "Atom",  # Simulate based on performance
                            "time_taken_seconds": 30
                        }
                    ],
                    "total_time_taken_minutes": 5
                }

                request_data = {
                    "quiz": sample_quiz,
                    "response": sample_response
                }

                response = requests.post(
                    f"{quizbot_url}/api/v1/evaluate-quiz",
                    json=request_data,
                    timeout=30
                )

                if response.status_code == 200:
                    evaluation_data = response.json()
                    return {
                        'status': 'success',
                        'agent': 'quizbot',
                        'trigger_type': trigger['type'],
                        'intervention': {
                            'type': 'diagnostic_evaluation',
                            'evaluation_data': evaluation_data,
                            'message': 'Diagnostic quiz evaluation completed with personalized feedback'
                        }
                    }
                else:
                    logger.warning(f"Quizbot API returned {response.status_code}")
                    return self._get_quizbot_fallback(trigger)

            else:
                # For quick evaluation or other triggers
                student_answers = {"q1": "Cell"}
                correct_answers = {"q1": "Cell"}

                response = requests.post(
                    f"{quizbot_url}/api/v1/quick-evaluate",
                    json={
                        "student_answers": student_answers,
                        "correct_answers": correct_answers,
                        "student_id": user_id
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    evaluation_data = response.json()
                    return {
                        'status': 'success',
                        'agent': 'quizbot',
                        'trigger_type': trigger['type'],
                        'intervention': {
                            'type': 'quick_evaluation',
                            'evaluation_data': evaluation_data,
                            'message': 'Quick assessment completed to gauge current understanding'
                        }
                    }
                else:
                    logger.warning(f"Quizbot API returned {response.status_code}")
                    return self._get_quizbot_fallback(trigger)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to quizbot: {e}")
            return self._get_quizbot_fallback(trigger)
        except Exception as e:
            logger.error(f"Error calling quizbot: {e}")
            return {'status': 'error', 'error': str(e)}

    def _get_quizbot_fallback(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback response when quizbot is unavailable"""
        return {
            'status': 'fallback',
            'agent': 'quizbot',
            'trigger_type': trigger['type'],
            'intervention': {
                'type': 'adaptive_assessment',
                'message': 'Quizbot service unavailable. Using fallback assessment guidance.',
                'next_steps': [
                    'Take a diagnostic quiz to identify knowledge gaps',
                    'Review areas where you scored below 70%',
                    'Practice targeted exercises on weak topics',
                    'Seek additional help from teachers or tutors',
                    'Retake assessments after focused study'
                ]
            }
        }

class UnifiedOrchestrationEngine:
    """
    Main orchestration engine that manages all agents and provides unified responses
    """

    def __init__(self):
        self.data_ingestion = UnifiedDataIngestion()
        self.memory_manager = AgentMemoryManager()
        self.gemini_manager = GeminiAPIManager()
        self.triggers = OrchestrationTriggers(self.memory_manager)
        self.vector_stores = {}
        self.embedding_model = None

    async def initialize(self):
        """Initialize the orchestration engine"""
        logger.info("Initializing Unified Orchestration Engine...")

        # Initialize embedding model
        self.embedding_model = self.data_ingestion.initialize_embedding_model()

        # Load or create vector stores
        self.vector_stores = self.data_ingestion.load_existing_vector_stores()

        if not self.vector_stores:
            logger.info("No existing vector stores found. Creating new ones...")
            self.vector_stores = self.data_ingestion.ingest_all_data()

        logger.info(f"Orchestration engine initialized with {len(self.vector_stores)} vector stores")

    def generate_dynamic_response(self, prompt: str, fallback_response: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dynamic response using Gemini API with fallback"""
        if self.gemini_manager.is_available():
            try:
                response = self.gemini_manager.generate_content(prompt)
                if response:
                    # Try to parse as JSON
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            pass

                    # If not JSON, return as content
                    return {"content": response}
            except Exception as e:
                logger.warning(f"Dynamic response generation failed: {e}")

        return fallback_response

    async def ask_vedas(self, query: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """Handle Vedas spiritual wisdom queries"""
        try:
            # Get user session for personalization
            session = self.memory_manager.get_user_session(user_id)

            # Retrieve relevant documents
            if 'vedas' in self.vector_stores:
                retriever = self.vector_stores['vedas'].as_retriever(search_kwargs={"k": 5})
                relevant_docs = retriever.get_relevant_documents(query)
            else:
                relevant_docs = []

            # Create context from documents
            context = "\n\n".join([doc.page_content[:600] for doc in relevant_docs[:4]])

            # Generate dynamic response
            prompt = f"""You are a wise spiritual teacher well-versed in ancient Vedic wisdom. Based on the following sacred texts, provide profound spiritual guidance.

SACRED VEDIC CONTEXT:
{context}

SEEKER'S QUESTION: {query}

Please provide comprehensive spiritual guidance in the following JSON format:
{{
    "core_teaching": "Extract the main spiritual principle or teaching from the texts that directly addresses this question. Be specific and profound.",
    "practical_application": "Provide detailed, actionable guidance on how to apply this ancient wisdom in modern daily life. Include specific practices or mindset shifts.",
    "philosophical_insight": "Share the deeper philosophical meaning and universal truth behind this teaching. Connect it to the broader understanding of existence and consciousness.",
    "relevant_quote": "Include a relevant verse, quote, or teaching from the provided texts. If no direct quote is available, paraphrase the essence of the teaching."
}}

Draw wisdom from the provided texts and make it relevant for a modern spiritual seeker. Be authentic to the Vedic tradition while making it accessible."""

            fallback_response = {
                "core_teaching": "The ancient texts teach us to seek truth through self-reflection and righteous action.",
                "practical_application": "Apply mindfulness and ethical principles in your daily decisions and interactions.",
                "philosophical_insight": "True wisdom comes from understanding the interconnectedness of all existence.",
                "relevant_quote": "As you think, so you become. - Ancient Vedic wisdom"
            }

            wisdom = self.generate_dynamic_response(prompt, fallback_response)

            # Update user session
            self.memory_manager.update_user_session(user_id, {
                'spiritual_journey': {
                    **session.get('spiritual_journey', {}),
                    'last_vedas_query': query,
                    'topics_explored': session.get('spiritual_journey', {}).get('topics_explored', []) + [query]
                }
            })

            # Record interaction
            response = {
                "query_id": str(uuid.uuid4()),
                "query": query,
                "wisdom": wisdom,
                "source_documents": [
                    {"text": doc.page_content[:800], "metadata": doc.metadata}
                    for doc in relevant_docs
                ],
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }

            self.memory_manager.add_interaction(user_id, "vedas", query, response)

            return response

        except Exception as e:
            logger.error(f"Error in ask_vedas: {e}")
            raise HTTPException(status_code=500, detail=f"Vedas query failed: {str(e)}")

    async def ask_wellness(self, query: str, user_id: str = "anonymous",
                          mood_score: Optional[float] = None,
                          stress_level: Optional[float] = None) -> Dict[str, Any]:
        """Handle wellness queries with sub-agent integration"""
        try:
            # Get user session
            session = self.memory_manager.get_user_session(user_id)

            # Check for wellness triggers
            triggers = self.triggers.check_wellness_triggers(user_id, mood_score, stress_level)

            # Also check for financial triggers if query contains financial keywords
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ['money', 'financial', 'budget', 'spending', 'debt', 'income']):
                financial_triggers = self.triggers.check_financial_triggers(user_id)
                triggers.extend(financial_triggers)

            trigger_results = []

            if triggers:
                trigger_results = await self.triggers.execute_trigger_actions(user_id, triggers)

            # Retrieve relevant documents
            if 'wellness' in self.vector_stores:
                retriever = self.vector_stores['wellness'].as_retriever(search_kwargs={"k": 5})
                relevant_docs = retriever.get_relevant_documents(query)
            elif 'unified' in self.vector_stores:
                retriever = self.vector_stores['unified'].as_retriever(search_kwargs={"k": 5})
                relevant_docs = retriever.get_relevant_documents(query)
            else:
                relevant_docs = []

            # Create context
            context = "\n\n".join([doc.page_content[:400] for doc in relevant_docs[:4]])

            # Generate wellness advice
            advice_prompt = f"""You are a compassionate wellness counselor with expertise in holistic health and wellbeing. Based on the wellness content provided, offer caring, evidence-based guidance.

WELLNESS CONTEXT:
{context}

PERSON'S CONCERN: {query}

Provide comprehensive wellness support that addresses both the immediate concern and promotes overall wellbeing. Be empathetic, practical, and empowering.

Respond in JSON format:
{{
    "main_advice": "Primary, compassionate advice that directly addresses their concern with understanding and validation",
    "practical_steps": ["Specific, actionable step they can take today", "Another concrete action for this week", "A longer-term strategy for sustained wellbeing"],
    "tips": ["Evidence-based tip for immediate relief or improvement", "Lifestyle suggestion that supports overall wellness", "Mindfulness or self-care practice they can easily implement"]
}}"""

            advice_fallback = {
                "main_advice": "It's completely understandable to have concerns about your wellbeing. Taking care of yourself is important, and seeking guidance shows strength.",
                "practical_steps": [
                    "Take time to reflect on what you're experiencing",
                    "Consider speaking with a healthcare professional",
                    "Practice self-care activities that bring you comfort"
                ],
                "tips": [
                    "Remember that small steps can lead to big improvements",
                    "Be patient and kind with yourself during this process",
                    "Don't hesitate to reach out for support when you need it"
                ]
            }

            advice = self.generate_dynamic_response(advice_prompt, advice_fallback)

            # Generate emotional support
            emotional_prompt = f"""You are a warm, empathetic counselor providing emotional support. Someone has reached out with this concern: "{query}"

Create heartfelt emotional support that truly connects with their experience and empowers them.

Respond in JSON format:
{{
    "encouragement": "A deeply understanding and validating message that acknowledges their courage in seeking help and normalizes their experience",
    "affirmation": "A powerful, personalized affirmation that highlights their inner strength, resilience, and capability to overcome challenges",
    "mindfulness_tip": "A specific, easy-to-follow mindfulness or coping technique they can use right now, with clear instructions"
}}"""

            emotional_fallback = {
                "encouragement": "You're taking a positive step by seeking guidance. Remember that it's okay to have challenges, and you're not alone in facing them.",
                "affirmation": "You have the inner strength and resilience to work through this situation.",
                "mindfulness_tip": "Take a moment to breathe deeply. Inhale slowly for 4 counts, hold for 4, then exhale for 4. This can help center your thoughts."
            }

            emotional_support = self.generate_dynamic_response(emotional_prompt, emotional_fallback)

            # Update user session with wellness metrics
            wellness_metrics = session.get('wellness_metrics', {})
            if mood_score:
                mood_trend = wellness_metrics.get('mood_trend', [])
                mood_trend.append(mood_score)
                wellness_metrics['mood_trend'] = mood_trend[-10:]  # Keep last 10 entries

            if stress_level:
                wellness_metrics['stress_level'] = stress_level

            wellness_metrics['last_wellness_check'] = datetime.now().isoformat()

            self.memory_manager.update_user_session(user_id, {
                'wellness_metrics': wellness_metrics
            })

            response = {
                "query_id": str(uuid.uuid4()),
                "query": query,
                "advice": advice,
                "emotional_nudge": emotional_support,
                "triggers_detected": triggers,
                "trigger_interventions": trigger_results,
                "source_documents": [
                    {"text": doc.page_content[:800], "metadata": doc.metadata}
                    for doc in relevant_docs
                ],
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }

            self.memory_manager.add_interaction(user_id, "wellness", query, response)

            return response

        except Exception as e:
            logger.error(f"Error in ask_wellness: {e}")
            raise HTTPException(status_code=500, detail=f"Wellness query failed: {str(e)}")

    async def ask_edumentor(self, query: str, user_id: str = "anonymous",
                           quiz_score: Optional[float] = None) -> Dict[str, Any]:
        """Handle educational queries with sub-agent integration"""
        try:
            # Get user session
            session = self.memory_manager.get_user_session(user_id)

            # Check for educational triggers
            triggers = self.triggers.check_educational_triggers(user_id, quiz_score)
            trigger_results = []

            if triggers:
                trigger_results = await self.triggers.execute_trigger_actions(user_id, triggers)

            # Retrieve relevant documents
            if 'educational' in self.vector_stores:
                retriever = self.vector_stores['educational'].as_retriever(search_kwargs={"k": 5})
                relevant_docs = retriever.get_relevant_documents(query)
            elif 'unified' in self.vector_stores:
                retriever = self.vector_stores['unified'].as_retriever(search_kwargs={"k": 5})
                relevant_docs = retriever.get_relevant_documents(query)
            else:
                relevant_docs = []

            # Create context
            context = "\n\n".join([doc.page_content[:500] for doc in relevant_docs[:4]])

            # Generate explanation
            explanation_prompt = f"""You are an expert educator who excels at making complex topics accessible and engaging for students. Based on the educational content provided, create a comprehensive yet understandable explanation.

EDUCATIONAL CONTEXT:
{context}

STUDENT'S QUESTION: {query}

Create an engaging explanation that:
- Uses clear, age-appropriate language
- Includes concrete examples and analogies
- Connects to students' everyday experiences
- Builds understanding step by step
- Sparks curiosity and interest
- Is scientifically/academically accurate

Make the explanation conversational and enthusiastic, as if you're speaking directly to an eager student. Include interesting facts or "did you know" elements to maintain engagement.

Provide a comprehensive explanation in 2-3 paragraphs that thoroughly addresses the question while remaining accessible and engaging."""

            explanation_response = self.gemini_manager.generate_content(explanation_prompt)
            explanation = explanation_response if explanation_response else f"Let me explain {query} in an engaging way! This is a fascinating topic that connects to many aspects of our daily lives."

            # Generate learning activity
            activity_prompt = f"""You are an experienced educator creating engaging learning activities. Based on the educational content provided, design a hands-on activity for students.

EDUCATIONAL CONTEXT:
{context}

LEARNING TOPIC: {query}

Create an innovative, engaging activity that helps students deeply understand this topic. Consider different learning styles and make it interactive.

Respond in JSON format:
{{
    "title": "Creative, engaging title for the activity",
    "description": "Detailed description of what students will learn and do, including the educational objectives",
    "instructions": ["Clear step-by-step instructions that are easy to follow", "Include timing and group arrangements", "Add assessment or reflection components"],
    "materials_needed": ["List all materials needed", "Include alternatives for different settings", "Specify quantities where relevant"]
}}

Make the activity:
- Pedagogically sound and age-appropriate
- Hands-on and interactive
- Safe and practical for classroom/home use
- Aligned with learning objectives
- Inclusive of different learning styles"""

            activity_fallback = {
                "title": f"Exploring {query}",
                "description": "A hands-on exploration activity to learn about this topic through observation and experimentation.",
                "instructions": [
                    "Research the topic using books or reliable online sources",
                    "Create a simple diagram or drawing of what you learned",
                    "Discuss your findings with classmates or family",
                    "Write down three interesting facts you discovered"
                ],
                "materials_needed": ["Paper", "Pencils or pens", "Access to books or internet"]
            }

            activity = self.generate_dynamic_response(activity_prompt, activity_fallback)

            # Update user session with educational progress
            educational_progress = session.get('educational_progress', {})
            if quiz_score:
                quiz_scores = educational_progress.get('quiz_scores', [])
                quiz_scores.append(quiz_score)
                educational_progress['quiz_scores'] = quiz_scores[-10:]  # Keep last 10 scores

            learning_topics = educational_progress.get('learning_topics', [])
            learning_topics.append(query)
            educational_progress['learning_topics'] = learning_topics[-20:]  # Keep last 20 topics
            educational_progress['last_activity'] = datetime.now().isoformat()

            self.memory_manager.update_user_session(user_id, {
                'educational_progress': educational_progress
            })

            response = {
                "query_id": str(uuid.uuid4()),
                "query": query,
                "explanation": explanation,
                "activity": activity,
                "triggers_detected": triggers,
                "trigger_interventions": trigger_results,
                "source_documents": [
                    {"text": doc.page_content[:800], "metadata": doc.metadata}
                    for doc in relevant_docs
                ],
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }

            self.memory_manager.add_interaction(user_id, "edumentor", query, response)

            return response

        except Exception as e:
            logger.error(f"Error in ask_edumentor: {e}")
            raise HTTPException(status_code=500, detail=f"Edumentor query failed: {str(e)}")

# Global orchestration engine instance
orchestration_engine = UnifiedOrchestrationEngine()

# Pydantic models for API requests and responses
class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's question or request")
    user_id: str = Field(default="anonymous", description="User identifier for personalization")

class WellnessQueryRequest(QueryRequest):
    mood_score: Optional[float] = Field(None, ge=1, le=10, description="Current mood score (1-10)")
    stress_level: Optional[float] = Field(None, ge=0, le=6, description="Current stress level (0-6)")

class EdumentorQueryRequest(QueryRequest):
    quiz_score: Optional[float] = Field(None, ge=0, le=100, description="Recent quiz score percentage")

class VedasWisdom(BaseModel):
    core_teaching: str
    practical_application: str
    philosophical_insight: str
    relevant_quote: str

class WellnessAdvice(BaseModel):
    main_advice: str
    practical_steps: List[str]
    tips: List[str]

class EmotionalNudge(BaseModel):
    encouragement: str
    affirmation: str
    mindfulness_tip: str

class LearningActivity(BaseModel):
    title: str
    description: str
    instructions: List[str]
    materials_needed: List[str]

class SourceDocument(BaseModel):
    text: str
    metadata: Dict[str, Any]

class TriggerInfo(BaseModel):
    type: str
    severity: str
    message: str
    recommended_action: str
    sub_agent: str

class VedasResponse(BaseModel):
    query_id: str
    query: str
    wisdom: Union[VedasWisdom, Dict[str, Any]]
    source_documents: List[SourceDocument]
    timestamp: str
    user_id: str

class WellnessResponse(BaseModel):
    query_id: str
    query: str
    advice: Union[WellnessAdvice, Dict[str, Any]]
    emotional_nudge: Union[EmotionalNudge, Dict[str, Any]]
    triggers_detected: List[Dict[str, Any]]
    trigger_interventions: List[Dict[str, Any]]
    source_documents: List[SourceDocument]
    timestamp: str
    user_id: str

class EdumentorResponse(BaseModel):
    query_id: str
    query: str
    explanation: str
    activity: Union[LearningActivity, Dict[str, Any]]
    triggers_detected: List[Dict[str, Any]]
    trigger_interventions: List[Dict[str, Any]]
    source_documents: List[SourceDocument]
    timestamp: str
    user_id: str

# Lifespan handler for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Unified Orchestration System...")
    await orchestration_engine.initialize()
    logger.info("Unified Orchestration System ready!")

    yield

    # Shutdown
    logger.info("Shutting down Unified Orchestration System...")

# Initialize FastAPI app
app = FastAPI(
    title="Unified Orchestration System",
    description="Complete orchestration system with three specialized modules: Vedas (spiritual wisdom), Wellness (health & emotional support), and Edumentor (educational content with activities). Includes sub-agent integration, memory management, and orchestration triggers.",
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

@app.post("/ask-vedas", response_model=VedasResponse)
async def ask_vedas_endpoint(request: QueryRequest):
    """
    Get spiritual wisdom from ancient Vedic texts

    This endpoint provides profound spiritual guidance based on ancient Vedic wisdom,
    including practical applications for modern life and philosophical insights.
    """
    try:
        response = await orchestration_engine.ask_vedas(request.query, request.user_id)
        return VedasResponse(**response)
    except Exception as e:
        logger.error(f"Vedas endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-wellness", response_model=WellnessResponse)
async def ask_wellness_endpoint(request: WellnessQueryRequest):
    """
    Get comprehensive wellness advice with emotional support

    This endpoint provides holistic health guidance, emotional support, and can trigger
    interventions from specialized wellness sub-agents when concerning patterns are detected.
    """
    try:
        response = await orchestration_engine.ask_wellness(
            request.query,
            request.user_id,
            request.mood_score,
            request.stress_level
        )
        return WellnessResponse(**response)
    except Exception as e:
        logger.error(f"Wellness endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-edumentor", response_model=EdumentorResponse)
async def ask_edumentor_endpoint(request: EdumentorQueryRequest):
    """
    Get educational content with interactive learning activities

    This endpoint provides engaging explanations and hands-on learning activities,
    and can trigger interventions from educational sub-agents when learning difficulties are detected.
    """
    try:
        response = await orchestration_engine.ask_edumentor(
            request.query,
            request.user_id,
            request.quiz_score
        )
        return EdumentorResponse(**response)
    except Exception as e:
        logger.error(f"Edumentor endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-session/{user_id}")
async def get_user_session(user_id: str):
    """
    Get user session data including interaction history and metrics
    """
    try:
        session = orchestration_engine.memory_manager.get_user_session(user_id)
        interactions = orchestration_engine.memory_manager.interaction_history.get(user_id, [])

        return {
            "user_session": session,
            "recent_interactions": interactions[-10:],  # Last 10 interactions
            "session_summary": {
                "total_interactions": session.get('interaction_count', 0),
                "wellness_metrics": session.get('wellness_metrics', {}),
                "educational_progress": session.get('educational_progress', {}),
                "spiritual_journey": session.get('spiritual_journey', {})
            }
        }
    except Exception as e:
        logger.error(f"User session endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger-check/{user_id}")
async def manual_trigger_check(user_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger a comprehensive wellness and educational check for a user
    """
    try:
        session = orchestration_engine.memory_manager.get_user_session(user_id)

        # Check all trigger types
        wellness_triggers = orchestration_engine.triggers.check_wellness_triggers(user_id)
        educational_triggers = orchestration_engine.triggers.check_educational_triggers(user_id)

        all_triggers = wellness_triggers + educational_triggers

        # Execute trigger actions in background
        if all_triggers:
            background_tasks.add_task(
                orchestration_engine.triggers.execute_trigger_actions,
                user_id,
                all_triggers
            )

        return {
            "user_id": user_id,
            "triggers_found": len(all_triggers),
            "wellness_triggers": wellness_triggers,
            "educational_triggers": educational_triggers,
            "actions_scheduled": len(all_triggers) > 0
        }
    except Exception as e:
        logger.error(f"Trigger check endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system-status")
async def get_system_status():
    """
    Get comprehensive system status including all components
    """
    try:
        return {
            "system": "Unified Orchestration System",
            "version": "1.0.0",
            "status": "operational",
            "components": {
                "data_ingestion": {
                    "status": "active",
                    "vector_stores": list(orchestration_engine.vector_stores.keys())
                },
                "memory_manager": {
                    "status": "active",
                    "active_users": len(orchestration_engine.memory_manager.user_sessions)
                },
                "gemini_api": {
                    "status": "active" if orchestration_engine.gemini_manager.is_available() else "fallback_mode",
                    "current_key": orchestration_engine.gemini_manager.current_key_type
                },
                "triggers": {
                    "status": "active",
                    "thresholds": orchestration_engine.triggers.trigger_thresholds
                }
            },
            "endpoints": [
                "POST /ask-vedas - Spiritual wisdom from ancient texts",
                "POST /ask-wellness - Health advice with emotional support",
                "POST /ask-edumentor - Educational content with activities",
                "GET /user-session/{user_id} - User session and interaction history",
                "POST /trigger-check/{user_id} - Manual trigger check",
                "GET /system-status - System status information"
            ],
            "sub_agents": {
                "tutorbot": "Educational lesson planning and suggestions",
                "emotionalwellnessbot": "Emotional support and wellness coaching",
                "financialwellnessbot": "Financial wellness and budgeting advice",
                "quizbot": "Quiz evaluation and adaptive assessment"
            }
        }
    except Exception as e:
        logger.error(f"System status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Unified Orchestration System",
        "description": "Dynamic RAG-based orchestration with three main agents and sub-agent integration",
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "/system-status"
    }

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*80)
    print("  UNIFIED ORCHESTRATION SYSTEM")
    print("="*80)
    print(f" Server URL: http://0.0.0.0:8000")
    print(f" API Documentation: http://0.0.0.0:8000/docs")
    print(f" System Status: http://0.0.0.0:8000/system-status")
    print("\n Main Endpoints:")
    print("   POST /ask-vedas - Ancient spiritual wisdom with practical guidance")
    print("   POST /ask-wellness - Holistic health advice with emotional support")
    print("   POST /ask-edumentor - Educational content with interactive activities")
    print("\n Management Endpoints:")
    print("   GET  /user-session/{user_id} - User session and interaction history")
    print("   POST /trigger-check/{user_id} - Manual intervention trigger check")
    print("   GET  /system-status - Comprehensive system status")
    print("\n Features:")
    print("   ✓ Dynamic RAG-based responses using Gemini API")
    print("   ✓ Dual API key failover for robust operation")
    print("   ✓ Common agent memory and state management")
    print("   ✓ Orchestration triggers for automatic interventions")
    print("   ✓ Sub-agent integration (tutorbot, wellness bots, quizbot)")
    print("   ✓ Comprehensive user session tracking")
    print("   ✓ Specialized vector stores for each domain")
    print("="*80)

    uvicorn.run(app, host="0.0.0.0", port=8000)
