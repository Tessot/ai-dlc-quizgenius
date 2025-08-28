"""
Question Processing Service for QuizGenius MVP
Enhanced question processing with validation and quality assessment
Implements Phase 3.2: Question Processing Backend
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from services.bedrock_service import BedrockService
from services.question_generation_service import GeneratedQuestion
from utils.dynamodb_utils import generate_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QuestionValidationResult:
    """Result of question validation"""
    is_valid: bool
    quality_score: float  # 0.0 to 10.0
    issues: List[str]
    suggestions: List[str]
    validation_details: Dict[str, Any]

@dataclass
class ProcessedQuestion:
    """Enhanced question with processing metadata"""
    question_id: str
    original_question: GeneratedQuestion
    processed_text: str
    processed_options: List[str]
    correct_answer: str
    quality_score: float
    validation_result: QuestionValidationResult
    processing_timestamp: str
    metadata: Dict[str, Any]

class QuestionProcessingError(Exception):
    """Custom exception for question processing errors"""
    pass

class QuestionProcessor:
    """
    Enhanced question processing service with validation and quality assessment
    """
    
    def __init__(self):
        """Initialize the question processor"""
        try:
            self.bedrock_service = BedrockService()
            
            # Quality thresholds
            self.min_quality_score = 6.0
            self.min_option_length = 3
            self.max_option_length = 200
            self.min_question_length = 10
            self.max_question_length = 500
            
            # Validation patterns
            self.ambiguous_words = [
                'sometimes', 'usually', 'often', 'rarely', 'seldom',
                'many', 'few', 'most', 'some', 'several', 'various'
            ]
            
            logger.info("QuestionProcessor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize QuestionProcessor: {str(e)}")
            raise QuestionProcessingError(f"Processor initialization failed: {str(e)}")
    
    def process_multiple_choice_question(self, question: GeneratedQuestion) -> ProcessedQuestion:
        """
        Process and enhance a multiple choice question
        
        Args:
            question: Generated question to process
            
        Returns:
            ProcessedQuestion with enhancements and validation
        """
        try:
            logger.info(f"Processing multiple choice question: {question.question_id}")
            
            # Validate question structure
            validation_result = self._validate_multiple_choice_question(question)
            
            # Enhance question text
            processed_text = self._enhance_question_text(question.question_text)
            
            # Enhance answer options
            processed_options = self._enhance_answer_options(question.options)
            
            # Validate and improve distractors
            improved_options = self._improve_distractors(
                processed_text, processed_options, question.correct_answer
            )
            
            # Calculate overall quality score
            quality_score = self._calculate_question_quality_score(
                processed_text, improved_options, question.correct_answer, validation_result
            )
            
            # Create processed question
            processed_question = ProcessedQuestion(
                question_id=question.question_id,
                original_question=question,
                processed_text=processed_text,
                processed_options=improved_options,
                correct_answer=question.correct_answer,
                quality_score=quality_score,
                validation_result=validation_result,
                processing_timestamp=datetime.now().isoformat(),
                metadata={
                    'processing_version': '1.0',
                    'original_confidence': question.confidence_score,
                    'improvements_applied': self._get_improvements_applied(question, processed_text, improved_options)
                }
            )
            
            logger.info(f"Multiple choice question processed: quality score {quality_score:.1f}")
            return processed_question
            
        except Exception as e:
            logger.error(f"Failed to process multiple choice question: {str(e)}")
            raise QuestionProcessingError(f"MC question processing failed: {str(e)}")
    
    def process_true_false_question(self, question: GeneratedQuestion) -> ProcessedQuestion:
        """
        Process and enhance a true/false question
        
        Args:
            question: Generated question to process
            
        Returns:
            ProcessedQuestion with enhancements and validation
        """
        try:
            logger.info(f"Processing true/false question: {question.question_id}")
            
            # Validate question structure
            validation_result = self._validate_true_false_question(question)
            
            # Enhance question statement
            processed_text = self._enhance_true_false_statement(question.question_text)
            
            # Validate statement clarity and accuracy
            clarity_result = self._validate_statement_clarity(processed_text)
            validation_result.issues.extend(clarity_result['issues'])
            validation_result.suggestions.extend(clarity_result['suggestions'])
            
            # Calculate quality score
            quality_score = self._calculate_tf_quality_score(
                processed_text, question.correct_answer, validation_result
            )
            
            # Create processed question
            processed_question = ProcessedQuestion(
                question_id=question.question_id,
                original_question=question,
                processed_text=processed_text,
                processed_options=['True', 'False'],
                correct_answer=question.correct_answer,
                quality_score=quality_score,
                validation_result=validation_result,
                processing_timestamp=datetime.now().isoformat(),
                metadata={
                    'processing_version': '1.0',
                    'original_confidence': question.confidence_score,
                    'clarity_score': clarity_result['clarity_score'],
                    'ambiguity_detected': clarity_result['ambiguity_detected']
                }
            )
            
            logger.info(f"True/false question processed: quality score {quality_score:.1f}")
            return processed_question
            
        except Exception as e:
            logger.error(f"Failed to process true/false question: {str(e)}")
            raise QuestionProcessingError(f"T/F question processing failed: {str(e)}")
    
    def _validate_multiple_choice_question(self, question: GeneratedQuestion) -> QuestionValidationResult:
        """Validate multiple choice question structure and content"""
        issues = []
        suggestions = []
        validation_details = {}
        
        # Check question text
        if len(question.question_text) < self.min_question_length:
            issues.append("Question text is too short")
            suggestions.append("Expand the question to provide more context")
        
        if len(question.question_text) > self.max_question_length:
            issues.append("Question text is too long")
            suggestions.append("Simplify the question for better readability")
        
        # Check answer options
        if len(question.options) != 4:
            issues.append(f"Expected 4 options, found {len(question.options)}")
            suggestions.append("Ensure exactly 4 answer options are provided")
        
        # Validate correct answer
        if question.correct_answer not in question.options:
            issues.append("Correct answer not found in options")
            suggestions.append("Verify that the correct answer matches one of the options")
        
        # Check option quality
        option_lengths = [len(opt) for opt in question.options]
        if min(option_lengths) < self.min_option_length:
            issues.append("Some options are too short")
            suggestions.append("Expand short options to be more descriptive")
        
        if max(option_lengths) > self.max_option_length:
            issues.append("Some options are too long")
            suggestions.append("Shorten long options for better readability")
        
        # Check for similar options
        similar_options = self._find_similar_options(question.options)
        if similar_options:
            issues.append("Some options are too similar")
            suggestions.append("Make options more distinct from each other")
            validation_details['similar_options'] = similar_options
        
        # Check distractor quality
        distractor_quality = self._assess_distractor_quality(question.options, question.correct_answer)
        validation_details['distractor_quality'] = distractor_quality
        
        if distractor_quality['average_plausibility'] < 0.6:
            issues.append("Distractors are not plausible enough")
            suggestions.append("Create more believable incorrect options")
        
        # Calculate validation score
        validation_score = max(0, 10 - len(issues) * 1.5)
        
        return QuestionValidationResult(
            is_valid=len(issues) == 0,
            quality_score=validation_score,
            issues=issues,
            suggestions=suggestions,
            validation_details=validation_details
        )
    
    def _validate_true_false_question(self, question: GeneratedQuestion) -> QuestionValidationResult:
        """Validate true/false question structure and content"""
        issues = []
        suggestions = []
        validation_details = {}
        
        # Check statement length
        if len(question.question_text) < self.min_question_length:
            issues.append("Statement is too short")
            suggestions.append("Provide more context in the statement")
        
        if len(question.question_text) > self.max_question_length:
            issues.append("Statement is too long")
            suggestions.append("Simplify the statement for clarity")
        
        # Check for ambiguous language
        ambiguous_found = []
        for word in self.ambiguous_words:
            if word.lower() in question.question_text.lower():
                ambiguous_found.append(word)
        
        if ambiguous_found:
            issues.append(f"Ambiguous words found: {', '.join(ambiguous_found)}")
            suggestions.append("Replace ambiguous words with more specific terms")
            validation_details['ambiguous_words'] = ambiguous_found
        
        # Check for double negatives
        if self._has_double_negative(question.question_text):
            issues.append("Statement contains double negatives")
            suggestions.append("Rewrite to avoid double negatives for clarity")
        
        # Check correct answer format
        if question.correct_answer.lower() not in ['true', 'false']:
            issues.append("Correct answer must be 'True' or 'False'")
            suggestions.append("Set correct answer to either 'True' or 'False'")
        
        # Calculate validation score
        validation_score = max(0, 10 - len(issues) * 2)
        
        return QuestionValidationResult(
            is_valid=len(issues) == 0,
            quality_score=validation_score,
            issues=issues,
            suggestions=suggestions,
            validation_details=validation_details
        )
    
    def _enhance_question_text(self, question_text: str) -> str:
        """Enhance question text for clarity and readability"""
        # Remove extra whitespace
        enhanced_text = re.sub(r'\s+', ' ', question_text.strip())
        
        # Ensure question ends with question mark
        if not enhanced_text.endswith('?'):
            enhanced_text += '?'
        
        # Capitalize first letter
        if enhanced_text:
            enhanced_text = enhanced_text[0].upper() + enhanced_text[1:]
        
        return enhanced_text
    
    def _enhance_answer_options(self, options: List[str]) -> List[str]:
        """Enhance answer options for consistency and clarity"""
        enhanced_options = []
        
        for option in options:
            # Clean up whitespace
            enhanced_option = option.strip()
            
            # Ensure consistent capitalization
            if enhanced_option:
                enhanced_option = enhanced_option[0].upper() + enhanced_option[1:]
            
            # Remove trailing punctuation except for abbreviations
            if enhanced_option.endswith('.') and len(enhanced_option) > 3:
                enhanced_option = enhanced_option[:-1]
            
            enhanced_options.append(enhanced_option)
        
        return enhanced_options
    
    def _enhance_true_false_statement(self, statement: str) -> str:
        """Enhance true/false statement for clarity"""
        # Remove extra whitespace
        enhanced_statement = re.sub(r'\s+', ' ', statement.strip())
        
        # Remove question mark if present (T/F should be statements)
        if enhanced_statement.endswith('?'):
            enhanced_statement = enhanced_statement[:-1]
        
        # Ensure statement ends with period
        if not enhanced_statement.endswith('.'):
            enhanced_statement += '.'
        
        # Capitalize first letter
        if enhanced_statement:
            enhanced_statement = enhanced_statement[0].upper() + enhanced_statement[1:]
        
        return enhanced_statement
    
    def _improve_distractors(self, question_text: str, options: List[str], correct_answer: str) -> List[str]:
        """Improve distractor quality for multiple choice questions"""
        # For now, return options as-is
        # In a more advanced implementation, this could use AI to generate better distractors
        return options
    
    def _calculate_question_quality_score(self, question_text: str, options: List[str], 
                                        correct_answer: str, validation_result: QuestionValidationResult) -> float:
        """Calculate overall quality score for multiple choice question"""
        base_score = validation_result.quality_score
        
        # Adjust based on question characteristics
        length_score = self._score_text_length(question_text, self.min_question_length, self.max_question_length)
        option_score = self._score_option_quality(options)
        
        # Weighted average
        final_score = (base_score * 0.5) + (length_score * 0.2) + (option_score * 0.3)
        
        return min(10.0, max(0.0, final_score))
    
    def _calculate_tf_quality_score(self, statement: str, correct_answer: str, 
                                  validation_result: QuestionValidationResult) -> float:
        """Calculate quality score for true/false question"""
        base_score = validation_result.quality_score
        
        # Adjust based on statement characteristics
        length_score = self._score_text_length(statement, self.min_question_length, self.max_question_length)
        clarity_score = 10.0 - len(validation_result.issues) * 1.5
        
        # Weighted average
        final_score = (base_score * 0.4) + (length_score * 0.3) + (clarity_score * 0.3)
        
        return min(10.0, max(0.0, final_score))
    
    def _find_similar_options(self, options: List[str]) -> List[Tuple[str, str]]:
        """Find pairs of similar options"""
        similar_pairs = []
        
        for i, opt1 in enumerate(options):
            for j, opt2 in enumerate(options[i+1:], i+1):
                similarity = self._calculate_text_similarity(opt1, opt2)
                if similarity > 0.7:  # 70% similarity threshold
                    similar_pairs.append((opt1, opt2))
        
        return similar_pairs
    
    def _assess_distractor_quality(self, options: List[str], correct_answer: str) -> Dict[str, Any]:
        """Assess the quality of distractor options"""
        distractors = [opt for opt in options if opt != correct_answer]
        
        # Simple quality assessment
        quality_scores = []
        for distractor in distractors:
            # Score based on length and complexity
            length_score = min(1.0, len(distractor) / 50)  # Normalize to 0-1
            complexity_score = min(1.0, len(distractor.split()) / 10)  # Word count
            quality_scores.append((length_score + complexity_score) / 2)
        
        return {
            'distractors': distractors,
            'individual_scores': quality_scores,
            'average_plausibility': sum(quality_scores) / len(quality_scores) if quality_scores else 0
        }
    
    def _validate_statement_clarity(self, statement: str) -> Dict[str, Any]:
        """Validate clarity of true/false statement"""
        issues = []
        suggestions = []
        
        # Check for ambiguous words
        ambiguous_found = []
        for word in self.ambiguous_words:
            if word.lower() in statement.lower():
                ambiguous_found.append(word)
        
        if ambiguous_found:
            issues.append(f"Contains ambiguous words: {', '.join(ambiguous_found)}")
            suggestions.append("Replace ambiguous words with specific terms")
        
        # Check for complex sentence structure
        if statement.count(',') > 2:
            issues.append("Statement is too complex")
            suggestions.append("Simplify the statement structure")
        
        # Calculate clarity score
        clarity_score = max(0, 10 - len(issues) * 2)
        
        return {
            'clarity_score': clarity_score,
            'ambiguity_detected': len(ambiguous_found) > 0,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _has_double_negative(self, text: str) -> bool:
        """Check if text contains double negatives"""
        negative_words = ['not', 'no', 'never', 'none', 'nothing', 'nowhere', 'nobody']
        found_negatives = []
        
        words = text.lower().split()
        for word in words:
            if any(neg in word for neg in negative_words):
                found_negatives.append(word)
        
        return len(found_negatives) >= 2
    
    def _score_text_length(self, text: str, min_length: int, max_length: int) -> float:
        """Score text based on optimal length"""
        length = len(text)
        
        if length < min_length:
            return (length / min_length) * 5  # Scale to 0-5
        elif length > max_length:
            return max(0, 10 - ((length - max_length) / max_length) * 5)  # Penalty for being too long
        else:
            return 10.0  # Perfect length
    
    def _score_option_quality(self, options: List[str]) -> float:
        """Score the quality of answer options"""
        if not options:
            return 0.0
        
        # Check length consistency
        lengths = [len(opt) for opt in options]
        length_variance = max(lengths) - min(lengths)
        length_score = max(0, 10 - (length_variance / 20))  # Penalty for high variance
        
        # Check for empty or very short options
        short_options = sum(1 for opt in options if len(opt) < self.min_option_length)
        short_penalty = short_options * 2
        
        return max(0, length_score - short_penalty)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simple implementation)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _get_improvements_applied(self, original: GeneratedQuestion, 
                                processed_text: str, processed_options: List[str]) -> List[str]:
        """Get list of improvements applied during processing"""
        improvements = []
        
        if original.question_text != processed_text:
            improvements.append("Enhanced question text")
        
        if original.options != processed_options:
            improvements.append("Enhanced answer options")
        
        return improvements


def create_question_processor() -> QuestionProcessor:
    """Factory function to create a question processor"""
    return QuestionProcessor()


if __name__ == "__main__":
    # Test the question processor
    processor = create_question_processor()
    print("QuestionProcessor initialized successfully")