"""
Quiz Generation Module for Gurukul Learning Platform
Generates intelligent quizzes based on lesson content using AI
"""

import json
import re
import random
import os
import requests
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizGenerator:
    """Generates quizzes based on lesson content using AI"""
    
    def __init__(self):
        self.question_types = [
            "multiple_choice",
            "true_false", 
            "fill_in_blank",
            "short_answer"
        ]
        
        self.difficulty_levels = ["easy", "medium", "hard"]
        self.groq_api_key = os.getenv('GROQ_API_KEY', '').strip("'\"")
        self.use_ai = bool(self.groq_api_key)
        
        if self.use_ai:
            logger.info("✅ AI quiz generation enabled (Groq API)")
        else:
            logger.warning("⚠️ AI quiz generation disabled - using template fallback")
    
    def _call_ai_llm(self, prompt: str, model: str = "llama-3.1-8b-instant") -> Optional[str]:
        """Call Groq API to generate content using AI"""
        if not self.groq_api_key:
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an expert educational quiz generator. Generate high-quality, educational quiz questions based on the provided content."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 1.0
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.warning(f"Groq API returned status {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.warning(f"AI API call failed: {e}")
            return None
        
    def generate_quiz_from_content(
        self, 
        lesson_content: str, 
        subject: str, 
        topic: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        question_types: Optional[List[str]] = None,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive quiz based on lesson content
        
        Args:
            lesson_content: The lesson text content
            subject: Subject name (e.g., "Mathematics", "Science")
            topic: Specific topic (e.g., "Algebra", "Photosynthesis")
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy/medium/hard)
            question_types: Types of questions to include
            
        Returns:
            Dict containing quiz data with questions, metadata, and scoring info
        """
        try:
            logger.info(f"Generating quiz for {subject} - {topic} with {num_questions} questions")
            
            # Extract key concepts from content
            key_concepts = self._extract_key_concepts(lesson_content)
            
            # Generate questions based on content
            questions = self._generate_questions(
                lesson_content, 
                key_concepts, 
                subject, 
                topic, 
                num_questions,
                difficulty,
                question_types or ["multiple_choice", "true_false"],
                language
            )
            
            # Create quiz metadata
            quiz_data = {
                "quiz_id": f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "subject": subject,
                "topic": topic,
                "difficulty": difficulty,
                "total_questions": len(questions),
                "estimated_time": len(questions) * 2,  # 2 minutes per question
                "questions": questions,
                "scoring": {
                    "total_points": len(questions) * 10,
                    "passing_score": len(questions) * 6,  # 60% to pass
                    "points_per_question": 10
                },
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "content_length": len(lesson_content),
                    "key_concepts_count": len(key_concepts),
                    "question_types_used": list(set([q["type"] for q in questions]))
                }
            }
            
            logger.info(f"Successfully generated quiz with {len(questions)} questions")
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return self._generate_fallback_quiz(subject, topic, num_questions)
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts and important terms from lesson content"""
        try:
            # Remove common words and extract meaningful terms
            sentences = re.split(r'[.!?]+', content)
            key_concepts = []
            
            # Look for capitalized terms, technical terms, and important phrases
            for sentence in sentences:
                # Find capitalized words (likely important terms)
                caps_words = re.findall(r'\b[A-Z][a-z]+\b', sentence)
                key_concepts.extend(caps_words)
                
                # Find terms in quotes or emphasized
                quoted_terms = re.findall(r'"([^"]*)"', sentence)
                key_concepts.extend(quoted_terms)
                
                # Find numbered points or definitions
                definitions = re.findall(r'\b\w+(?:\s+\w+){0,2}(?:\s+is\s+|\s+are\s+|\s+means\s+)', sentence)
                key_concepts.extend([d.split()[0] for d in definitions])
            
            # Clean and deduplicate
            key_concepts = list(set([concept.strip() for concept in key_concepts if len(concept.strip()) > 2]))
            return key_concepts[:20]  # Limit to top 20 concepts
            
        except Exception as e:
            logger.error(f"Error extracting key concepts: {e}")
            return []
    
    def _generate_questions(
        self, 
        content: str, 
        key_concepts: List[str], 
        subject: str, 
        topic: str,
        num_questions: int,
        difficulty: str,
        question_types: List[str],
        language: str = "english"
    ) -> List[Dict[str, Any]]:
        """Generate specific questions based on content analysis using AI"""
        questions = []
        
        try:
            # Try AI generation first
            if self.use_ai and len(content) > 100:
                ai_questions = self._generate_questions_with_ai(
                    content, subject, topic, num_questions, difficulty, question_types, language
                )
                if ai_questions and len(ai_questions) >= num_questions:
                    logger.info(f"✅ Generated {len(ai_questions)} questions using AI")
                    return ai_questions[:num_questions]
                elif ai_questions:
                    logger.info(f"⚠️ AI generated {len(ai_questions)} questions, filling rest with templates")
                    questions.extend(ai_questions)
                    num_remaining = num_questions - len(ai_questions)
                else:
                    logger.warning("AI generation failed, falling back to templates")
                    num_remaining = num_questions
            else:
                num_remaining = num_questions
            
            # Fallback to template-based generation for remaining questions
            if num_remaining > 0:
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                
                for i in range(len(questions), len(questions) + num_remaining):
                    question_type = random.choice(question_types)
                    
                    if question_type == "multiple_choice":
                        question = self._generate_multiple_choice(paragraphs, key_concepts, subject, topic, difficulty)
                    elif question_type == "true_false":
                        question = self._generate_true_false(paragraphs, key_concepts, subject, topic)
                    elif question_type == "fill_in_blank":
                        question = self._generate_fill_in_blank(paragraphs, key_concepts, subject, topic)
                    else:
                        question = self._generate_short_answer(paragraphs, key_concepts, subject, topic)
                    
                    if question:
                        question["question_id"] = f"q_{len(questions) + 1}"
                        question["points"] = 10
                        questions.append(question)
            
            # Ensure all questions have IDs
            for i, q in enumerate(questions):
                if "question_id" not in q:
                    q["question_id"] = f"q_{i+1}"
                if "points" not in q:
                    q["points"] = 10
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._generate_basic_questions(subject, topic, num_questions)
    
    def _generate_questions_with_ai(
        self,
        content: str,
        subject: str,
        topic: str,
        num_questions: int,
        difficulty: str,
        question_types: List[str],
        language: str = "english"
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions using AI"""
        try:
            # Truncate content if too long (keep first 3000 chars for context)
            content_preview = content[:3000] + "..." if len(content) > 3000 else content
            
            # Add language instruction if Arabic is selected
            language_instruction = ""
            if language.lower() == "arabic":
                language_instruction = "\n\nLANGUAGE REQUIREMENT: Generate ALL questions, options, explanations, and all text content ENTIRELY in Arabic (العربية). Use proper Arabic script and formatting. All question text, answer options, and explanations must be in Arabic."
            
            # Create comprehensive prompt for AI
            question_types_str = ", ".join(question_types)
            prompt = f"""Generate {num_questions} high-quality quiz questions about "{topic}" in the subject "{subject}".

CONTEXT:
{content_preview}

REQUIREMENTS:
- Generate exactly {num_questions} questions
- Question types to use: {question_types_str}
- Difficulty level: {difficulty}
- Questions should test understanding of the actual content, not generic knowledge
- Make questions specific to the topic and subject matter
- Ensure variety in question types
{language_instruction}

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "type": "multiple_choice",
      "question": "Question text here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Brief explanation of the correct answer"
    }},
    {{
      "type": "true_false",
      "question": "Statement that is true or false",
      "correct_answer": true,
      "explanation": "Explanation of why this is true/false"
    }}
  ]
}}

Generate questions that are specific, educational, and test real understanding of the content provided."""

            logger.info(f"🤖 Calling AI to generate {num_questions} questions for {subject} - {topic}")
            ai_response = self._call_ai_llm(prompt, model="llama-3.3-70b-versatile")
            
            if not ai_response:
                return []
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (might have markdown code blocks)
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed = json.loads(json_str)
                    
                    if "questions" in parsed and isinstance(parsed["questions"], list):
                        questions = []
                        for i, q in enumerate(parsed["questions"]):
                            # Validate and format question
                            if self._validate_question(q):
                                q["question_id"] = f"q_{i+1}"
                                q["points"] = 10
                                questions.append(q)
                        
                        if questions:
                            logger.info(f"✅ Successfully parsed {len(questions)} AI-generated questions")
                            return questions
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI response as JSON: {e}")
                # Try to extract questions from text response
                return self._parse_questions_from_text(ai_response, num_questions, subject, topic)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in AI question generation: {e}")
            return []
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate that a question has required fields"""
        required_fields = ["type", "question"]
        if not all(field in question for field in required_fields):
            return False
        
        if question["type"] == "multiple_choice":
            return "options" in question and "correct_answer" in question and len(question["options"]) >= 2
        elif question["type"] == "true_false":
            return "correct_answer" in question and isinstance(question["correct_answer"], bool)
        
        return True
    
    def _parse_questions_from_text(self, text: str, num_questions: int, subject: str, topic: str) -> List[Dict[str, Any]]:
        """Fallback: Try to extract questions from unstructured AI text response"""
        questions = []
        # This is a fallback parser - basic implementation
        # In practice, AI should return JSON, but this handles edge cases
        lines = text.split('\n')
        current_question = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for question patterns
            if re.match(r'^\d+[\.\)]', line) or line.startswith('Q:'):
                if current_question and self._validate_question(current_question):
                    questions.append(current_question)
                current_question = {"type": "multiple_choice", "question": line, "options": [], "correct_answer": 0}
            elif current_question and re.match(r'^[A-D][\.\)]', line):
                option = re.sub(r'^[A-D][\.\)]\s*', '', line)
                current_question["options"].append(option)
        
        if current_question and self._validate_question(current_question):
            questions.append(current_question)
        
        return questions[:num_questions]
    
    def _generate_multiple_choice(self, paragraphs: List[str], concepts: List[str], subject: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Generate a multiple choice question"""
        try:
            # Select a paragraph with good content
            selected_paragraph = random.choice([p for p in paragraphs if len(p) > 100])
            
            # Extract a key fact or concept
            sentences = re.split(r'[.!?]+', selected_paragraph)
            fact_sentence = random.choice([s for s in sentences if len(s.strip()) > 20])
            
            # Create question based on the fact
            if concepts:
                concept = random.choice(concepts)
                question_text = f"What is the significance of {concept} in {topic}?"
                
                options = [
                    f"{concept} is fundamental to understanding {topic}",
                    f"{concept} is rarely used in {topic}",
                    f"{concept} contradicts the principles of {topic}",
                    f"{concept} is only theoretical in {topic}"
                ]
                correct_answer = 0
            else:
                # Fallback question
                question_text = f"Which statement best describes {topic}?"
                options = [
                    f"{topic} is an important concept in {subject}",
                    f"{topic} is outdated in modern {subject}",
                    f"{topic} is only for advanced students",
                    f"{topic} has no practical applications"
                ]
                correct_answer = 0
            
            return {
                "type": "multiple_choice",
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": f"This concept is central to understanding {topic} in {subject}."
            }
            
        except Exception as e:
            logger.error(f"Error generating multiple choice: {e}")
            return None
    
    def _generate_true_false(self, paragraphs: List[str], concepts: List[str], subject: str, topic: str) -> Dict[str, Any]:
        """Generate a true/false question"""
        try:
            # Create a statement that can be true or false
            if concepts:
                concept = random.choice(concepts)
                is_true = random.choice([True, False])
                
                if is_true:
                    statement = f"{concept} is an important element in {topic}"
                    explanation = f"Yes, {concept} plays a significant role in understanding {topic}."
                else:
                    statement = f"{concept} is completely unrelated to {topic}"
                    explanation = f"No, {concept} is actually relevant to {topic} in {subject}."
            else:
                is_true = True
                statement = f"Understanding {topic} is beneficial for students of {subject}"
                explanation = f"True, {topic} provides foundational knowledge in {subject}."
            
            return {
                "type": "true_false",
                "question": statement,
                "correct_answer": is_true,
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Error generating true/false: {e}")
            return None
    
    def _generate_fill_in_blank(self, paragraphs: List[str], concepts: List[str], subject: str, topic: str) -> Dict[str, Any]:
        """Generate a fill-in-the-blank question"""
        try:
            if concepts:
                concept = random.choice(concepts)
                question_text = f"The concept of _____ is fundamental to understanding {topic} in {subject}."
                correct_answer = concept
                explanation = f"The answer is '{concept}' as it is a key concept in this topic."
            else:
                question_text = f"_____ is the main subject area that encompasses {topic}."
                correct_answer = subject
                explanation = f"The answer is '{subject}' as {topic} is part of this subject."
            
            return {
                "type": "fill_in_blank",
                "question": question_text,
                "correct_answer": correct_answer,
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Error generating fill in blank: {e}")
            return None
    
    def _generate_short_answer(self, paragraphs: List[str], concepts: List[str], subject: str, topic: str) -> Dict[str, Any]:
        """Generate a short answer question"""
        try:
            question_text = f"Explain the importance of {topic} in {subject}."
            sample_answer = f"{topic} is important in {subject} because it provides foundational understanding and practical applications."
            
            return {
                "type": "short_answer",
                "question": question_text,
                "sample_answer": sample_answer,
                "explanation": "This question tests understanding of the topic's significance and applications."
            }
            
        except Exception as e:
            logger.error(f"Error generating short answer: {e}")
            return None
    
    def _generate_basic_questions(self, subject: str, topic: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate basic fallback questions when content analysis fails"""
        questions = []
        
        for i in range(num_questions):
            question = {
                "question_id": f"q_{i+1}",
                "type": "multiple_choice",
                "question": f"What is the main focus of {topic} in {subject}?",
                "options": [
                    f"Understanding fundamental concepts of {topic}",
                    f"Memorizing facts about {topic}",
                    f"Ignoring {topic} completely",
                    f"Only theoretical study of {topic}"
                ],
                "correct_answer": 0,
                "explanation": f"The main focus is understanding the fundamental concepts of {topic}.",
                "points": 10
            }
            questions.append(question)
        
        return questions
    
    def _generate_fallback_quiz(self, subject: str, topic: str, num_questions: int) -> Dict[str, Any]:
        """Generate a basic fallback quiz when main generation fails"""
        return {
            "quiz_id": f"fallback_quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "subject": subject,
            "topic": topic,
            "difficulty": "medium",
            "total_questions": num_questions,
            "estimated_time": num_questions * 2,
            "questions": self._generate_basic_questions(subject, topic, num_questions),
            "scoring": {
                "total_points": num_questions * 10,
                "passing_score": num_questions * 6,
                "points_per_question": 10
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "fallback_mode": True
            }
        }
