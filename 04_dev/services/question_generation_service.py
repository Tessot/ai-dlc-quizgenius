#!/usr/bin/env python3
"""
Question Generation Service for QuizGenius MVP
This service handles AI-powered question generation from PDF content using AWS Bedrock.
Implements Step 2.2.1: Bedrock Question Generation (US-4.2.1 - 8 points)
Author: Expert Software Engineer
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from services.bedrock_service import BedrockService, BedrockServiceError
from utils.dynamodb_utils import get_current_timestamp, generate_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GeneratedQuestion:
    """Represents a generated question"""
    question_id: str
    question_text: str
    question_type: str  # 'multiple_choice' or 'true_false'
    correct_answer: str
    options: List[str]  # For multiple choice questions
    difficulty_level: str
    topic: str
    source_content: str
    confidence_score: float
    metadata: Dict[str, Any]

@dataclass
class QuestionGenerationRequest:
    """Request parameters for question generation"""
    content: str
    question_types: List[str]  # ['multiple_choice', 'true_false']
    num_questions: int
    difficulty_level: str  # 'beginner', 'intermediate', 'advanced', 'mixed'
    topics: List[str]  # Optional topic focus
    user_id: str
    document_id: str

@dataclass
class QuestionGenerationResult:
    """Result of question generation process"""
    request_id: str
    success: bool
    generated_questions: List[GeneratedQuestion]
    failed_attempts: int
    total_attempts: int
    processing_time_seconds: float
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class QuestionGenerationError(Exception):
    """Custom exception for question generation errors"""
    pass

class QuestionGenerationService:
    """
    Service for AI-powered question generation using AWS Bedrock
    """
    
    def __init__(self):
        """Initialize the question generation service"""
        try:
            self.bedrock_service = BedrockService()
            
            # Configuration
            self.max_content_length = 8000  # Max characters per generation request
            self.max_questions_per_request = 10  # Max questions per single API call
            self.min_content_length = 200  # Min characters needed for generation
            
            # Prompt templates
            self.mc_prompt_template = self._load_mc_prompt_template()
            self.tf_prompt_template = self._load_tf_prompt_template()
            
            logger.info("QuestionGenerationService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize QuestionGenerationService: {str(e)}")
            raise QuestionGenerationError(f"Service initialization failed: {str(e)}")
    
    def generate_questions(self, request: QuestionGenerationRequest) -> QuestionGenerationResult:
        """
        Generate questions from content using AI
        
        Args:
            request: Question generation request parameters
            
        Returns:
            QuestionGenerationResult with generated questions
        """
        start_time = datetime.now()
        request_id = generate_id('qgen')
        
        logger.info(f"Starting question generation request {request_id}")
        
        result = QuestionGenerationResult(
            request_id=request_id,
            success=False,
            generated_questions=[],
            failed_attempts=0,
            total_attempts=0,
            processing_time_seconds=0.0,
            errors=[],
            warnings=[],
            metadata={
                'user_id': request.user_id,
                'document_id': request.document_id,
                'start_time': start_time.isoformat()
            }
        )
        
        try:
            # Validate request
            validation_errors = self._validate_request(request)
            if validation_errors:
                result.errors.extend(validation_errors)
                return result
            
            # Process content chunks
            content_chunks = self._prepare_content_chunks(request.content)
            
            # Generate questions for each type requested
            all_questions = []
            
            for question_type in request.question_types:
                if question_type == 'multiple_choice':
                    questions = self._generate_multiple_choice_questions(
                        content_chunks, request, result
                    )
                    all_questions.extend(questions)
                elif question_type == 'true_false':
                    questions = self._generate_true_false_questions(
                        content_chunks, request, result
                    )
                    all_questions.extend(questions)
                else:
                    result.warnings.append(f"Unknown question type: {question_type}")
            
            # Limit to requested number of questions
            if len(all_questions) > request.num_questions:
                # Sort by confidence score and take the best ones
                all_questions.sort(key=lambda q: q.confidence_score, reverse=True)
                all_questions = all_questions[:request.num_questions]
                result.warnings.append(
                    f"Generated more questions than requested. Selected top {request.num_questions} by confidence."
                )
            
            result.generated_questions = all_questions
            result.success = len(all_questions) > 0
            
            # Calculate processing time
            end_time = datetime.now()
            result.processing_time_seconds = (end_time - start_time).total_seconds()
            result.metadata['end_time'] = end_time.isoformat()
            
            logger.info(f"Question generation completed: {len(all_questions)} questions generated")
            return result
            
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            result.errors.append(f"Generation failed: {str(e)}")
            result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            return result
    
    def _validate_request(self, request: QuestionGenerationRequest) -> List[str]:
        """Validate question generation request"""
        errors = []
        
        if not request.content or len(request.content.strip()) < self.min_content_length:
            errors.append(f"Content too short. Minimum {self.min_content_length} characters required.")
        
        if not request.question_types:
            errors.append("At least one question type must be specified.")
        
        valid_types = ['multiple_choice', 'true_false']
        invalid_types = [t for t in request.question_types if t not in valid_types]
        if invalid_types:
            errors.append(f"Invalid question types: {invalid_types}")
        
        if request.num_questions <= 0:
            errors.append("Number of questions must be greater than 0.")
        
        if request.num_questions > 50:
            errors.append("Maximum 50 questions per request.")
        
        valid_difficulties = ['beginner', 'intermediate', 'advanced', 'mixed']
        if request.difficulty_level not in valid_difficulties:
            errors.append(f"Invalid difficulty level. Must be one of: {valid_difficulties}")
        
        return errors
    
    def _prepare_content_chunks(self, content: str) -> List[str]:
        """Prepare content chunks for question generation"""
        # Split content into manageable chunks
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) > self.max_content_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # Single paragraph is too long, split it
                    words = paragraph.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk + " " + word) > self.max_content_length:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                                temp_chunk = word
                            else:
                                # Single word is too long, truncate
                                chunks.append(word[:self.max_content_length])
                        else:
                            temp_chunk += " " + word if temp_chunk else word
                    if temp_chunk:
                        current_chunk = temp_chunk
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if len(chunk.strip()) >= self.min_content_length]
    
    def _generate_multiple_choice_questions(
        self, 
        content_chunks: List[str], 
        request: QuestionGenerationRequest,
        result: QuestionGenerationResult
    ) -> List[GeneratedQuestion]:
        """Generate multiple choice questions from content chunks"""
        questions = []
        questions_per_chunk = max(1, request.num_questions // len(content_chunks))
        
        for chunk in content_chunks:
            try:
                result.total_attempts += 1
                
                # Create prompt for multiple choice questions
                prompt = self._create_mc_prompt(chunk, questions_per_chunk, request.difficulty_level)
                
                # Call Bedrock
                response = self.bedrock_service._call_bedrock_model(prompt, max_tokens=3000)
                
                # Parse response
                chunk_questions = self._parse_mc_response(response, chunk, request)
                questions.extend(chunk_questions)
                
            except Exception as e:
                logger.error(f"Failed to generate MC questions for chunk: {str(e)}")
                result.failed_attempts += 1
                result.warnings.append(f"Failed to generate questions from one content chunk: {str(e)}")
        
        return questions
    
    def _generate_true_false_questions(
        self, 
        content_chunks: List[str], 
        request: QuestionGenerationRequest,
        result: QuestionGenerationResult
    ) -> List[GeneratedQuestion]:
        """Generate true/false questions from content chunks"""
        questions = []
        questions_per_chunk = max(1, request.num_questions // len(content_chunks))
        
        for chunk in content_chunks:
            try:
                result.total_attempts += 1
                
                # Create prompt for true/false questions
                prompt = self._create_tf_prompt(chunk, questions_per_chunk, request.difficulty_level)
                
                # Call Bedrock
                response = self.bedrock_service._call_bedrock_model(prompt, max_tokens=2000)
                
                # Parse response
                chunk_questions = self._parse_tf_response(response, chunk, request)
                questions.extend(chunk_questions)
                
            except Exception as e:
                logger.error(f"Failed to generate T/F questions for chunk: {str(e)}")
                result.failed_attempts += 1
                result.warnings.append(f"Failed to generate questions from one content chunk: {str(e)}")
        
        return questions
    
    def _create_mc_prompt(self, content: str, num_questions: int, difficulty: str) -> str:
        """Create prompt for multiple choice question generation"""
        return f"""
You are an expert educational content creator. Generate {num_questions} high-quality multiple choice questions based on the following content.

Content:
{content}

Requirements:
- Difficulty level: {difficulty}
- Each question must have exactly 4 options (A, B, C, D)
- Only one option should be correct
- Incorrect options should be plausible but clearly wrong
- Questions should test understanding, not just memorization
- Base questions directly on the provided content
- Avoid ambiguous or trick questions

Format your response as a JSON array with this exact structure:
[
  {{
    "question": "What is the main concept discussed?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "A",
    "explanation": "Brief explanation of why this is correct",
    "topic": "Main topic of the question",
    "difficulty": "{difficulty}",
    "confidence": 0.9
  }}
]

Generate exactly {num_questions} questions in this format.
"""
    
    def _create_tf_prompt(self, content: str, num_questions: int, difficulty: str) -> str:
        """Create prompt for true/false question generation"""
        return f"""
You are an expert educational content creator. Generate {num_questions} high-quality true/false questions based on the following content.

Content:
{content}

Requirements:
- Difficulty level: {difficulty}
- Each statement must be clearly true or false based on the content
- Avoid ambiguous statements that could be interpreted either way
- Test important concepts from the content
- Make false statements plausible but clearly incorrect
- Base all statements directly on the provided content

Format your response as a JSON array with this exact structure:
[
  {{
    "statement": "Clear statement that is either true or false",
    "correct_answer": "True",
    "explanation": "Brief explanation of why this is true/false",
    "topic": "Main topic of the statement",
    "difficulty": "{difficulty}",
    "confidence": 0.9
  }}
]

Generate exactly {num_questions} questions in this format.
"""
    
    def _parse_mc_response(
        self, 
        response: str, 
        source_content: str, 
        request: QuestionGenerationRequest
    ) -> List[GeneratedQuestion]:
        """Parse multiple choice response from Bedrock"""
        questions = []
        
        try:
            # Try to extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[json_start:json_end]
            parsed_questions = json.loads(json_str)
            
            for q_data in parsed_questions:
                if not isinstance(q_data, dict):
                    continue
                
                # Validate required fields
                required_fields = ['question', 'options', 'correct_answer']
                if not all(field in q_data for field in required_fields):
                    continue
                
                # Create GeneratedQuestion object
                question = GeneratedQuestion(
                    question_id=generate_id('mcq'),
                    question_text=q_data['question'],
                    question_type='multiple_choice',
                    correct_answer=q_data['correct_answer'],
                    options=q_data['options'],
                    difficulty_level=q_data.get('difficulty', request.difficulty_level),
                    topic=q_data.get('topic', 'General'),
                    source_content=source_content[:500] + "..." if len(source_content) > 500 else source_content,
                    confidence_score=float(q_data.get('confidence', 0.7)),
                    metadata={
                        'explanation': q_data.get('explanation', ''),
                        'generated_at': get_current_timestamp(),
                        'user_id': request.user_id,
                        'document_id': request.document_id
                    }
                )
                
                # Validate question structure
                if self._validate_mc_question(question):
                    questions.append(question)
            
        except Exception as e:
            logger.error(f"Failed to parse MC response: {str(e)}")
            logger.debug(f"Response content: {response[:500]}...")
        
        return questions
    
    def _parse_tf_response(
        self, 
        response: str, 
        source_content: str, 
        request: QuestionGenerationRequest
    ) -> List[GeneratedQuestion]:
        """Parse true/false response from Bedrock"""
        questions = []
        
        try:
            # Try to extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[json_start:json_end]
            parsed_questions = json.loads(json_str)
            
            for q_data in parsed_questions:
                if not isinstance(q_data, dict):
                    continue
                
                # Validate required fields
                required_fields = ['statement', 'correct_answer']
                if not all(field in q_data for field in required_fields):
                    continue
                
                # Create GeneratedQuestion object
                question = GeneratedQuestion(
                    question_id=generate_id('tfq'),
                    question_text=q_data['statement'],
                    question_type='true_false',
                    correct_answer=q_data['correct_answer'],
                    options=['True', 'False'],
                    difficulty_level=q_data.get('difficulty', request.difficulty_level),
                    topic=q_data.get('topic', 'General'),
                    source_content=source_content[:500] + "..." if len(source_content) > 500 else source_content,
                    confidence_score=float(q_data.get('confidence', 0.7)),
                    metadata={
                        'explanation': q_data.get('explanation', ''),
                        'generated_at': get_current_timestamp(),
                        'user_id': request.user_id,
                        'document_id': request.document_id
                    }
                )
                
                # Validate question structure
                if self._validate_tf_question(question):
                    questions.append(question)
            
        except Exception as e:
            logger.error(f"Failed to parse T/F response: {str(e)}")
            logger.debug(f"Response content: {response[:500]}...")
        
        return questions
    
    def _validate_mc_question(self, question: GeneratedQuestion) -> bool:
        """Validate multiple choice question structure"""
        try:
            # Check basic structure
            if not question.question_text or not question.options:
                return False
            
            # Check options count
            if len(question.options) != 4:
                return False
            
            # Check correct answer format
            if question.correct_answer not in ['A', 'B', 'C', 'D']:
                return False
            
            # Check for duplicate options
            if len(set(question.options)) != len(question.options):
                return False
            
            # Check minimum length requirements
            if len(question.question_text.strip()) < 10:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_tf_question(self, question: GeneratedQuestion) -> bool:
        """Validate true/false question structure"""
        try:
            # Check basic structure
            if not question.question_text:
                return False
            
            # Check correct answer format
            if question.correct_answer not in ['True', 'False']:
                return False
            
            # Check minimum length requirements
            if len(question.question_text.strip()) < 10:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _load_mc_prompt_template(self) -> str:
        """Load multiple choice prompt template"""
        # This could be loaded from a file in the future
        return "Multiple choice question generation template"
    
    def _load_tf_prompt_template(self) -> str:
        """Load true/false prompt template"""
        # This could be loaded from a file in the future
        return "True/false question generation template"
    
    def validate_content_for_generation(self, content: str) -> Dict[str, Any]:
        """
        Validate content suitability for question generation
        
        Args:
            content: Text content to validate
            
        Returns:
            Validation results
        """
        try:
            validation = {
                'is_suitable': True,
                'quality_score': 5,
                'estimated_questions': 0,
                'issues': [],
                'recommendations': []
            }
            
            # Length validation
            content_length = len(content.strip())
            word_count = len(content.split())
            
            if content_length < self.min_content_length:
                validation['is_suitable'] = False
                validation['issues'].append(f'Content too short ({content_length} chars). Minimum {self.min_content_length} required.')
                validation['quality_score'] = 1
            
            # Estimate potential questions
            if word_count > 0:
                # Rough estimate: 1 question per 100-200 words
                validation['estimated_questions'] = max(1, word_count // 150)
            
            # Content quality indicators
            educational_keywords = [
                'definition', 'concept', 'principle', 'theory', 'method', 'process',
                'example', 'analysis', 'conclusion', 'research', 'study', 'experiment'
            ]
            
            content_lower = content.lower()
            keyword_count = sum(1 for keyword in educational_keywords if keyword in content_lower)
            
            if keyword_count >= 3:
                validation['quality_score'] = min(validation['quality_score'] + 2, 10)
            elif keyword_count == 0:
                validation['issues'].append('Content may lack educational structure')
                validation['quality_score'] = max(validation['quality_score'] - 1, 1)
            
            # Structure analysis
            sentences = content.count('.') + content.count('!') + content.count('?')
            if sentences < 5:
                validation['issues'].append('Content may be too brief for comprehensive questions')
            
            paragraphs = len([p for p in content.split('\n\n') if p.strip()])
            if paragraphs < 2:
                validation['recommendations'].append('Consider adding more structured content with multiple paragraphs')
            
            return validation
            
        except Exception as e:
            return {
                'is_suitable': False,
                'quality_score': 1,
                'estimated_questions': 0,
                'issues': [f'Validation error: {str(e)}'],
                'recommendations': []
            }
    
    def get_generation_statistics(self, result: QuestionGenerationResult) -> Dict[str, Any]:
        """Get detailed statistics about question generation"""
        try:
            stats = {
                'request_id': result.request_id,
                'success_rate': 0.0,
                'questions_by_type': {},
                'questions_by_difficulty': {},
                'average_confidence': 0.0,
                'processing_time': result.processing_time_seconds,
                'total_questions': len(result.generated_questions)
            }
            
            if result.total_attempts > 0:
                stats['success_rate'] = (result.total_attempts - result.failed_attempts) / result.total_attempts
            
            # Analyze generated questions
            if result.generated_questions:
                # By type
                for question in result.generated_questions:
                    q_type = question.question_type
                    stats['questions_by_type'][q_type] = stats['questions_by_type'].get(q_type, 0) + 1
                
                # By difficulty
                for question in result.generated_questions:
                    difficulty = question.difficulty_level
                    stats['questions_by_difficulty'][difficulty] = stats['questions_by_difficulty'].get(difficulty, 0) + 1
                
                # Average confidence
                total_confidence = sum(q.confidence_score for q in result.generated_questions)
                stats['average_confidence'] = total_confidence / len(result.generated_questions)
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}

# Utility functions
def create_generation_request(
    content: str,
    user_id: str,
    document_id: str,
    question_types: List[str] = None,
    num_questions: int = 5,
    difficulty: str = 'intermediate'
) -> QuestionGenerationRequest:
    """
    Create a question generation request with default parameters
    
    Args:
        content: Source content for questions
        user_id: ID of requesting user
        document_id: ID of source document
        question_types: Types of questions to generate
        num_questions: Number of questions to generate
        difficulty: Difficulty level
        
    Returns:
        QuestionGenerationRequest object
    """
    if question_types is None:
        question_types = ['multiple_choice', 'true_false']
    
    return QuestionGenerationRequest(
        content=content,
        question_types=question_types,
        num_questions=num_questions,
        difficulty_level=difficulty,
        topics=[],
        user_id=user_id,
        document_id=document_id
    )

def generate_questions_from_content(
    content: str,
    user_id: str,
    document_id: str,
    **kwargs
) -> QuestionGenerationResult:
    """
    Convenience function to generate questions from content
    
    Args:
        content: Source content
        user_id: User ID
        document_id: Document ID
        **kwargs: Additional parameters for generation
        
    Returns:
        QuestionGenerationResult
    """
    service = QuestionGenerationService()
    request = create_generation_request(content, user_id, document_id, **kwargs)
    return service.generate_questions(request)