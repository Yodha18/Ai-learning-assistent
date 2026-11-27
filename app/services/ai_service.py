import json
import logging
import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.user import ExplanationStyle
from app.services.gemini_service import GeminiClient

logger = logging.getLogger(__name__)

# Initialize Gemini client lazily
_client = None


def get_gemini_client():
    """Get or create Gemini client instance."""
    global _client
    if _client is None:
        if not settings.gemini_configured:
            logger.error("GEMINI_API_KEY is not configured")
            raise ValueError("GEMINI_API_KEY is not configured. Add it to your .env file.")
        try:
            logger.info("Initializing Gemini client")
            _client = GeminiClient()
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise
    return _client


class AIService:
    """Service for AI-powered functionality using Gemini."""
    
    def __init__(self):
        self.client = None  # Client will be initialized lazily when needed

    def _build_learning_memory(self, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Create a compact student-learning summary from earlier chat turns."""
        if not conversation_history:
            return ""

        recent_user_questions = []
        recent_assistant_answers = []

        for entry in conversation_history:
            role = entry.get("role", "")
            content = (entry.get("content") or "").strip()
            if not content:
                continue

            if role == "user":
                recent_user_questions.append(content)
            elif role == "assistant":
                recent_assistant_answers.append(content)

        if not recent_user_questions and not recent_assistant_answers:
            return ""

        core_topics = []
        for text in recent_user_questions + recent_assistant_answers:
            cleaned = text.replace("\n", " ")
            if len(cleaned) > 80:
                cleaned = cleaned[:80]
            core_topics.append(cleaned)

        # Keep a concise, readable summary that the model can use during follow-up replies.
        summary_parts = [
            "Student learning memory:",
            "- The student has been asking about: " + "; ".join(core_topics[:3]),
            "- The tutor should build on earlier explanations instead of repeating basics.",
            "- Prefer simple, clear steps and examples that match the student's previous questions.",
        ]
        return " ".join(summary_parts)

    @staticmethod
    def _is_follow_up_question(question: str) -> bool:
        follow_up_patterns = (
            r"^\s*(?:and|but|also)\b",
            r"\b(?:this|that|it|they|those|these|above|previous)\b",
            r"\b(?:tell me more|explain more|give me an example|what about|how so|elaborate|continue)\b",
        )
        return any(re.search(pattern, question, re.IGNORECASE) for pattern in follow_up_patterns)
    
    def _get_client(self):
        """Get or create Gemini client instance."""
        if self.client is None:
            self.client = get_gemini_client()
        return self.client
    
    def generate_chat_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        explanation_style: ExplanationStyle = ExplanationStyle.SIMPLE,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        *,
        model: Optional[str] = None,
        system_behavior: str = "",
    ) -> Dict[str, Any]:
        """Generate a chat response based on context chunks."""

        if not settings.ai_configured:
            return self._generate_local_chat_response(question, context_chunks)
        
        # Build context from chunks
        context = ""
        sources = []
        
        for i, chunk in enumerate(context_chunks):
            source_name = chunk.get("source_name") or f"Document {chunk.get('document_id', 'N/A')}"
            context += f"\n--- Source {i+1}: {source_name} (Page {chunk.get('page_number', 'N/A')}) ---\n"
            context += chunk['chunk_text'] + "\n"
            
            sources.append({
                'document_name': source_name,
                'page_number': chunk.get('page_number'),
                'subject': chunk.get('subject'),
                'topic': chunk.get('topic'),
                'url': chunk.get('url'),
            })
        
        # Determine explanation style
        style_instructions = {
            ExplanationStyle.SIMPLE: "Use plain, easy-to-understand language.",
            ExplanationStyle.DETAILED: "Give additional depth when the question asks for it.",
            ExplanationStyle.TECHNICAL: "Use precise technical language when it helps answer the question.",
            ExplanationStyle.PRACTICAL: "Use a practical example only when it helps answer the question."
        }
        
        style_instruction = style_instructions.get(explanation_style, style_instructions[ExplanationStyle.SIMPLE])
        
        relevant_history = (
            conversation_history
            if self._is_follow_up_question(question)
            else None
        )
        learning_memory = self._build_learning_memory(relevant_history)

        # Build system prompt
        system_prompt = f"""You are a helpful, natural conversational tutor.

{style_instruction}

Answer the user's current message directly. Keep ordinary replies to one or two short sentences, and stay under 60 words unless the user asks for detail.
Use a friendly, natural tone that matches the user's tone without forced slang.
Do not add filler introductions, headings, summaries, unsolicited suggestions, or repeated follow-up questions.
Use previous turns only when the current message clearly follows up on them. Do not bring up earlier topics or documents otherwise.
When no study-material context is provided, answer normally and do not mention uploaded files or sources.
When study-material context is provided and relevant, answer the question first and add a brief citation to the document/page. Do not force unrelated context into the answer.
Do not invent facts or sources.

{learning_memory}

{system_behavior}
"""

        # Build user message
        if context:
            user_message = f"""Relevant study-material context:
{context}

Question: {question}"""
        else:
            user_message = question

        # Build messages array
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Add conversation history if provided
        if relevant_history:
            messages = messages[:1] + relevant_history + messages[1:]
        
        try:
            client = self._get_client()
            logger.info("Sending request to Gemini model: %s", model or settings.GEMINI_CHAT_MODEL)
            answer = client.generate_content(
                model=model or settings.GEMINI_CHAT_MODEL,
                messages=messages,
                temperature=0.6,
                max_output_tokens=450,
            )
            logger.info("Successfully received response from Gemini")
            
            return {
                'answer': answer,
                'sources': sources if context_chunks else []
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {str(e)}", exc_info=True)
            return self._generate_local_chat_response(question, context_chunks)

    def _generate_local_chat_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Provide a deterministic offline tutor when no API key is configured."""
        if not context_chunks:
            return {
                "answer": (
                    "Hi! I'm your personal AI assistant. How can I help you today? "
                    "I can help you learn, organize your study, or answer questions from your uploaded notes."
                ),
                "sources": [],
            }

        terms = {term.lower() for term in question.split() if len(term) > 2}
        ranked = sorted(
            context_chunks,
            key=lambda chunk: len(terms & set(chunk["chunk_text"].lower().split())),
            reverse=True,
        )
        excerpt = ranked[0]["chunk_text"].strip()
        is_web_source = bool(ranked[0].get("url"))
        intro = "Here is what I found online:" if is_web_source else "Here is what your uploaded material says:"
        follow_up = (
            "This is the most relevant web source I found. Ask me to explain a term, "
            "simplify it, or search for more sources."
            if is_web_source
            else "This is the most relevant section I found in your notes. Ask me to "
            "explain a term, simplify it, or create a short summary."
        )
        return {
            "answer": (
                f"{intro}\n\n"
                f"{excerpt[:1200]}\n\n"
                f"{follow_up}"
            ),
            "sources": [
                {
                    "document_name": ranked[0].get("source_name")
                    or f"Document {ranked[0].get('document_id')}",
                    "page_number": ranked[0].get("page_number"),
                    "subject": ranked[0].get("subject"),
                    "topic": ranked[0].get("topic"),
                    "url": ranked[0].get("url"),
                }
            ],
        }
    
    def generate_quiz(
        self,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 5,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions using AI."""

        if not settings.gemini_configured:
            return self._generate_local_quiz(topic, num_questions, context)
        
        difficulty_descriptions = {
            "easy": "basic concepts and straightforward questions",
            "medium": "moderate difficulty with some application of concepts",
            "hard": "challenging questions requiring deep understanding and analysis"
        }
        
        difficulty_instruction = difficulty_descriptions.get(difficulty, difficulty_descriptions["medium"])
        
        system_prompt = f"""You are an expert quiz generator for students. Generate multiple-choice questions about the given topic.

Requirements:
- Generate exactly {num_questions} questions
- Difficulty: {difficulty_instruction}
- Each question must have 4 options (A, B, C, D)
- Only one correct answer per question
- Include a brief explanation for the correct answer
- Format your response as valid JSON"""

        user_message = f"""Generate a quiz about: {topic}"""
        
        if context:
            user_message += f"\n\nContext/Reference material:\n{context}"
        
        user_message += f"""
        
Format your response as a JSON array with this structure:
[
  {{
    "question_text": "Question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Explanation of why this is correct",
    "topic": "{topic}"
  }}
]

Where correct_answer is the index (0-3) of the correct option."""

        try:
            client = self._get_client()
            content = client.generate_content(
                model=settings.GEMINI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_output_tokens=2000,
                response_mime_type="application/json",
            )
            
            # Parse JSON response
            try:
                questions = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    questions = json.loads(json_match.group())
                else:
                    raise Exception("Failed to parse AI-generated quiz")
            
            # Validate structure
            validated_questions = []
            for q in questions:
                if len(q.get('options', [])) != 4:
                    continue
                if not isinstance(q.get('correct_answer'), int) or q['correct_answer'] not in [0, 1, 2, 3]:
                    continue
                
                validated_questions.append({
                    'question_text': q['question_text'],
                    'options': q['options'],
                    'correct_answer': q['correct_answer'],
                    'explanation': q.get('explanation', ''),
                    'topic': q.get('topic', topic)
                })
            
            if len(validated_questions) < num_questions:
                logger.warning("AI returned too few quiz questions; using the local generator")
                return self._generate_local_quiz(topic, num_questions, context)
            return validated_questions[:num_questions]
            
        except Exception as e:
            logger.warning("AI quiz generation failed; using local questions: %s", e)
            return self._generate_local_quiz(topic, num_questions, context)

    def _generate_local_quiz(
        self,
        topic: str,
        num_questions: int,
        context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate simple offline questions so quiz workflows work without an API key."""
        if context:
            sentences = [
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])\s+|\n+", context)
                if len(sentence.strip()) >= 20
            ]
            if sentences:
                questions = []
                question_stems = (
                    "Which statement is supported by your uploaded notes?",
                    "Which fact appears in your study material?",
                    "Choose the statement that matches your notes.",
                )
                for index in range(num_questions):
                    answer = sentences[index % len(sentences)]
                    options = [
                        answer,
                        f"Your notes say this is unrelated to {topic}.",
                        f"The material states that {topic} has no concepts to study.",
                        "This information does not appear in the uploaded notes.",
                    ]
                    correct_answer = index % len(options)
                    options[0], options[correct_answer] = options[correct_answer], options[0]
                    questions.append({
                        "question_text": question_stems[index % len(question_stems)],
                        "options": options,
                        "correct_answer": correct_answer,
                        "explanation": f"Your uploaded notes state: {answer}",
                        "topic": topic,
                    })
                return questions

        questions = [
            {
                "question_text": f"Which statement best describes {topic}?",
                "options": [
                    f"A core concept studied in {topic}",
                    "An unrelated file format",
                    "A networking cable standard",
                    "A type of operating system",
                ],
                "correct_answer": 0,
                "explanation": f"The question is focused on the core concepts of {topic}.",
                "topic": topic,
            },
            {
                "question_text": f"What is a useful first step when learning {topic}?",
                "options": [
                    "Ignore the definitions",
                    f"Understand the basic vocabulary of {topic}",
                    "Skip all examples",
                    "Avoid practice questions",
                ],
                "correct_answer": 1,
                "explanation": "Learning the vocabulary makes later concepts easier to understand.",
                "topic": topic,
            },
        ]
        return [questions[index % len(questions)] for index in range(num_questions)]
    
    def generate_interview_question(
        self,
        subject: str,
        topic: str,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """Generate a technical interview question."""
        
        system_prompt = """You are an expert technical interviewer. Generate challenging, relevant interview questions.

Requirements:
- Generate one detailed technical question
- Include what the interviewer is looking for
- Suggest key points that should be covered in the answer
- Format as valid JSON"""

        user_message = f"""Generate a technical interview question for:
- Subject: {subject}
- Topic: {topic}
- Difficulty: {difficulty}

Format as JSON:
{{
  "question": "The interview question",
  "what_looking_for": "What the interviewer is evaluating",
  "key_points": ["Point 1", "Point 2", "Point 3"]
}}"""

        try:
            client = self._get_client()
            content = client.generate_content(
                model=settings.GEMINI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_output_tokens=800,
                response_mime_type="application/json",
            )
            
            try:
                interview_data = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    interview_data = json.loads(json_match.group())
                else:
                    raise Exception("Failed to parse interview question")
            
            return interview_data
            
        except Exception as e:
            raise Exception(f"Failed to generate interview question: {str(e)}")
    
    def evaluate_interview_answer(
        self,
        question: str,
        answer: str,
        key_points: List[str]
    ) -> Dict[str, Any]:
        """Evaluate an interview answer."""
        
        system_prompt = """You are an expert technical interviewer evaluating candidate responses.

Evaluate the answer and provide:
- Score (1-10)
- Concept understanding assessment
- Technical accuracy assessment
- Clarity assessment
- Missing concepts
- Improvement suggestions

Format as valid JSON."""

        user_message = f"""Question: {question}

Key points expected: {', '.join(key_points)}

Candidate's answer: {answer}

Evaluate and provide feedback in this JSON format:
{{
  "score": 8,
  "concept_understanding": "Assessment of concept understanding",
  "technical_accuracy": "Assessment of technical accuracy",
  "clarity": "Assessment of clarity",
  "missing_concepts": ["Concept 1", "Concept 2"],
  "improvement_suggestions": ["Suggestion 1", "Suggestion 2"]
}}"""

        try:
            client = self._get_client()
            content = client.generate_content(
                model=settings.GEMINI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.5,
                max_output_tokens=800,
                response_mime_type="application/json",
            )
            
            try:
                evaluation = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    evaluation = json.loads(json_match.group())
                else:
                    raise Exception("Failed to parse evaluation")
            
            return evaluation
            
        except Exception as e:
            raise Exception(f"Failed to evaluate answer: {str(e)}")
    
    def generate_summary(
        self,
        content: str,
        topic: str
    ) -> Dict[str, Any]:
        """Generate a summary of content."""
        
        system_prompt = """You are an expert educator. Generate comprehensive summaries of educational content.

Provide:
- Short summary (2-3 sentences)
- Important concepts (bulleted list)
- Key points (bulleted list)
- Examples (if applicable)
- Exam tips (if applicable)
- Interview tips (if applicable)

Format as valid JSON."""

        user_message = f"""Generate a summary for:
- Topic: {topic}

Content:
{content}

Format as JSON:
{{
  "short_summary": "Brief summary",
  "important_concepts": ["Concept 1", "Concept 2"],
  "key_points": ["Point 1", "Point 2"],
  "examples": ["Example 1"],
  "exam_tips": ["Tip 1"],
  "interview_tips": ["Tip 1"]
}}"""

        try:
            client = self._get_client()
            response_content = client.generate_content(
                model=settings.GEMINI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.5,
                max_output_tokens=1500,
                response_mime_type="application/json",
            )
            
            try:
                summary = json.loads(response_content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    summary = json.loads(json_match.group())
                else:
                    raise Exception("Failed to parse summary")
            
            return summary
            
        except Exception as e:
            raise Exception(f"Failed to generate summary: {str(e)}")


# Global AI service instance
ai_service = AIService()
