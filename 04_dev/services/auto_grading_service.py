#!/usr/bin/env python3
"""
Auto-Grading Service for QuizGenius MVP
Handles automatic grading of student test submissions
Implements Phase 5.1: Auto-Grading System
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError

from services.student_test_service import StudentTestService, TestAttempt
from services.test_creation_service import TestCreationService
from services.question_storage_service import QuestionStorageService
from utils.dynamodb_utils import get_current_timestamp, generate_id
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QuestionResult:
    """Data structure for individual question grading result"""
    question_id: str
    question_number: int
    question_type: str
    question_text: str
    correct_answer: str
    student_answer: str
    is_correct: bool
    points_earned: float
    points_possible: float
    time_spent: Optional[float] = None

@dataclass
class TestResult:
    """Data structure for complete test grading result"""
    result_id: str
    attempt_id: str
    test_id: str
    student_id: str
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    unanswered_questions: int
    total_points_earned: float
    total_points_possible: float
    percentage_score: float
    passing_score: float
    passed: bool
    time_taken: Optional[int]  # in seconds
    graded_at: str
    question_results: List[QuestionResult]

class AutoGradingError(Exception):
    """Custom exception for auto-grading errors"""
    pass

class AutoGradingService:
    """
    Service for automatic grading of student test submissions
    """
    
    def __init__(self):
        """Initialize the auto-grading service"""
        try:
            self.config = Config()
            self.student_service = StudentTestService()
            self.test_service = TestCreationService()
            self.question_service = QuestionStorageService()
            
            # Initialize DynamoDB client
            self.dynamodb = boto3.resource('dynamodb', region_name=self.config.AWS_REGION)
            
            # Table references
            self.tests_table = self.dynamodb.Table('QuizGenius_Tests')
            self.attempts_table = self.dynamodb.Table('QuizGenius_TestAttempts')
            self.results_table = self.dynamodb.Table('QuizGenius_Results')
            self.questions_table = self.dynamodb.Table('QuizGenius_Questions')
            
            # Verify table access
            self._verify_table_access()
            
            logger.info("AutoGradingService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AutoGradingService: {str(e)}")
            raise AutoGradingError(f"Service initialization failed: {str(e)}")
    
    def _verify_table_access(self):
        """Verify access to required tables"""
        try:
            self.tests_table.load()
            self.attempts_table.load()
            self.results_table.load()
            self.questions_table.load()
        except Exception as e:
            logger.error(f"Cannot access DynamoDB tables: {str(e)}")
            raise AutoGradingError(f"Cannot access DynamoDB tables: {str(e)}")
    
    def grade_test_attempt(self, attempt_id: str, student_id: str) -> TestResult:
        """
        Grade a completed test attempt
        
        Args:
            attempt_id: Test attempt ID
            student_id: Student ID (for security)
            
        Returns:
            TestResult with complete grading information
        """
        try:
            # Get test attempt
            attempt = self.student_service.get_test_attempt(attempt_id, student_id)
            if not attempt:
                raise AutoGradingError(f"Test attempt {attempt_id} not found")
            
            if attempt.status != 'submitted':
                raise AutoGradingError(f"Test attempt {attempt_id} is not submitted")
            
            # Get test data
            test_data = self.test_service.get_test_by_id(attempt.test_id)
            if not test_data:
                raise AutoGradingError(f"Test {attempt.test_id} not found")
            
            # Get questions with correct answers
            questions = self._get_test_questions_with_answers(test_data)
            
            # Grade each question
            question_results = []
            for i, question in enumerate(questions):
                result = self._grade_question(question, attempt.answers, i)
                question_results.append(result)
            
            # Calculate overall results
            test_result = self._calculate_test_results(
                attempt, test_data, question_results
            )
            
            # Store results
            self._store_test_results(test_result)
            
            # Update attempt with score
            self._update_attempt_with_score(attempt_id, test_result)
            
            logger.info(f"Graded test attempt {attempt_id}: {test_result.percentage_score:.1f}%")
            return test_result
            
        except Exception as e:
            logger.error(f"Failed to grade test attempt {attempt_id}: {str(e)}")
            raise AutoGradingError(f"Failed to grade test: {str(e)}")
    
    def _get_test_questions_with_answers(self, test_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get test questions with correct answers for grading
        
        Args:
            test_data: Test configuration data
            
        Returns:
            List of questions with correct answers
        """
        try:
            questions = []
            question_ids = test_data.get('question_ids', [])
            
            for question_id in question_ids:
                # Get question from database
                response = self.questions_table.get_item(
                    Key={'question_id': question_id}
                )
                
                if 'Item' in response:
                    question = response['Item']
                    questions.append(question)
                else:
                    logger.warning(f"Question {question_id} not found")
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to get test questions: {str(e)}")
            raise AutoGradingError(f"Failed to retrieve questions: {str(e)}")
    
    def _grade_question(self, question: Dict[str, Any], student_answers: Dict[str, Any], 
                       question_number: int) -> QuestionResult:
        """
        Grade an individual question
        
        Args:
            question: Question data with correct answer
            student_answers: Student's answers
            question_number: Question number (0-based)
            
        Returns:
            QuestionResult with grading information
        """
        try:
            question_id = question['question_id']
            question_type = question.get('question_type', 'multiple_choice')
            question_text = question.get('question_text', '')
            correct_answer = question.get('correct_answer', '')
            
            # Get student's answer
            answer_key = f"question_{question_number}"
            student_answer = student_answers.get(answer_key, '')
            
            # Grade based on question type
            if question_type == 'multiple_choice':
                is_correct = self._grade_multiple_choice(correct_answer, student_answer)
            elif question_type == 'true_false':
                is_correct = self._grade_true_false(correct_answer, student_answer)
            else:
                logger.warning(f"Unknown question type: {question_type}")
                is_correct = False
            
            # Calculate points (1 point per question for now)
            points_possible = 1.0
            points_earned = points_possible if is_correct else 0.0
            
            result = QuestionResult(
                question_id=question_id,
                question_number=question_number + 1,
                question_type=question_type,
                question_text=question_text,
                correct_answer=correct_answer,
                student_answer=student_answer,
                is_correct=is_correct,
                points_earned=points_earned,
                points_possible=points_possible
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to grade question {question_number}: {str(e)}")
            # Return a failed result
            return QuestionResult(
                question_id=question.get('question_id', 'unknown'),
                question_number=question_number + 1,
                question_type=question.get('question_type', 'unknown'),
                question_text=question.get('question_text', ''),
                correct_answer=question.get('correct_answer', ''),
                student_answer=student_answers.get(f"question_{question_number}", ''),
                is_correct=False,
                points_earned=0.0,
                points_possible=1.0
            )
    
    def _grade_multiple_choice(self, correct_answer: str, student_answer: str) -> bool:
        """
        Grade a multiple choice question
        
        Args:
            correct_answer: The correct answer
            student_answer: Student's answer
            
        Returns:
            True if correct, False otherwise
        """
        try:
            # Normalize answers for comparison
            correct_normalized = str(correct_answer).strip().lower()
            student_normalized = str(student_answer).strip().lower()
            
            # Direct comparison
            is_correct = correct_normalized == student_normalized
            
            logger.debug(f"MC Grading: '{correct_answer}' vs '{student_answer}' = {is_correct}")
            return is_correct
            
        except Exception as e:
            logger.error(f"Error grading multiple choice: {str(e)}")
            return False
    
    def _grade_true_false(self, correct_answer: str, student_answer: str) -> bool:
        """
        Grade a true/false question
        
        Args:
            correct_answer: The correct answer
            student_answer: Student's answer
            
        Returns:
            True if correct, False otherwise
        """
        try:
            # Normalize boolean answers
            correct_normalized = self._normalize_boolean_answer(correct_answer)
            student_normalized = self._normalize_boolean_answer(student_answer)
            
            is_correct = correct_normalized == student_normalized
            
            logger.debug(f"T/F Grading: '{correct_answer}' vs '{student_answer}' = {is_correct}")
            return is_correct
            
        except Exception as e:
            logger.error(f"Error grading true/false: {str(e)}")
            return False
    
    def _normalize_boolean_answer(self, answer: str) -> bool:
        """
        Normalize a boolean answer to True/False
        
        Args:
            answer: Answer string
            
        Returns:
            Boolean value
        """
        if not answer:
            return False
        
        answer_lower = str(answer).strip().lower()
        
        # True values
        if answer_lower in ['true', 't', 'yes', 'y', '1']:
            return True
        
        # False values
        if answer_lower in ['false', 'f', 'no', 'n', '0']:
            return False
        
        # Default to False for unknown values
        return False
    
    def _calculate_test_results(self, attempt: TestAttempt, test_data: Dict[str, Any], 
                              question_results: List[QuestionResult]) -> TestResult:
        """
        Calculate overall test results
        
        Args:
            attempt: Test attempt data
            test_data: Test configuration
            question_results: Individual question results
            
        Returns:
            TestResult with calculated scores
        """
        try:
            # Count results
            total_questions = len(question_results)
            correct_answers = sum(1 for r in question_results if r.is_correct)
            incorrect_answers = sum(1 for r in question_results if not r.is_correct and r.student_answer)
            unanswered_questions = sum(1 for r in question_results if not r.student_answer)
            
            # Calculate points
            total_points_earned = sum(r.points_earned for r in question_results)
            total_points_possible = sum(r.points_possible for r in question_results)
            
            # Calculate percentage
            percentage_score = (total_points_earned / total_points_possible * 100) if total_points_possible > 0 else 0
            
            # Determine pass/fail
            passing_score = test_data.get('passing_score', 70)
            passed = percentage_score >= passing_score
            
            # Calculate time taken
            time_taken = None
            if attempt.started_at and attempt.submitted_at:
                try:
                    start_time = datetime.fromisoformat(attempt.started_at.replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(attempt.submitted_at.replace('Z', '+00:00'))
                    time_taken = int((end_time - start_time).total_seconds())
                except Exception as e:
                    logger.warning(f"Could not calculate time taken: {str(e)}")
            
            # Create result
            result = TestResult(
                result_id=generate_id(),
                attempt_id=attempt.attempt_id,
                test_id=attempt.test_id,
                student_id=attempt.student_id,
                total_questions=total_questions,
                correct_answers=correct_answers,
                incorrect_answers=incorrect_answers,
                unanswered_questions=unanswered_questions,
                total_points_earned=total_points_earned,
                total_points_possible=total_points_possible,
                percentage_score=percentage_score,
                passing_score=passing_score,
                passed=passed,
                time_taken=time_taken,
                graded_at=get_current_timestamp(),
                question_results=question_results
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate test results: {str(e)}")
            raise AutoGradingError(f"Failed to calculate results: {str(e)}")
    
    def _store_test_results(self, test_result: TestResult):
        """
        Store test results in database
        
        Args:
            test_result: TestResult to store
        """
        try:
            # Convert question results to dict format for storage
            question_results_data = [asdict(qr) for qr in test_result.question_results]
            
            # Prepare result data for storage
            result_data = {
                'result_id': test_result.result_id,
                'attempt_id': test_result.attempt_id,
                'test_id': test_result.test_id,
                'student_id': test_result.student_id,
                'total_questions': test_result.total_questions,
                'correct_answers': test_result.correct_answers,
                'incorrect_answers': test_result.incorrect_answers,
                'unanswered_questions': test_result.unanswered_questions,
                'total_points_earned': test_result.total_points_earned,
                'total_points_possible': test_result.total_points_possible,
                'percentage_score': test_result.percentage_score,
                'passing_score': test_result.passing_score,
                'passed': test_result.passed,
                'time_taken': test_result.time_taken,
                'graded_at': test_result.graded_at,
                'question_results': question_results_data
            }
            
            # Store in results table
            self.results_table.put_item(Item=result_data)
            
            logger.info(f"Stored test results {test_result.result_id}")
            
        except Exception as e:
            logger.error(f"Failed to store test results: {str(e)}")
            raise AutoGradingError(f"Failed to store results: {str(e)}")
    
    def _update_attempt_with_score(self, attempt_id: str, test_result: TestResult):
        """
        Update test attempt with calculated score
        
        Args:
            attempt_id: Test attempt ID
            test_result: Calculated test results
        """
        try:
            self.attempts_table.update_item(
                Key={'attempt_id': attempt_id},
                UpdateExpression='SET score = :score, passed = :passed, graded_at = :graded_at',
                ExpressionAttributeValues={
                    ':score': test_result.percentage_score,
                    ':passed': test_result.passed,
                    ':graded_at': test_result.graded_at
                }
            )
            
            logger.info(f"Updated attempt {attempt_id} with score {test_result.percentage_score:.1f}%")
            
        except Exception as e:
            logger.error(f"Failed to update attempt with score: {str(e)}")
            raise AutoGradingError(f"Failed to update attempt: {str(e)}")
    
    def get_test_results(self, attempt_id: str, student_id: str) -> Optional[TestResult]:
        """
        Get test results for an attempt
        
        Args:
            attempt_id: Test attempt ID
            student_id: Student ID (for security)
            
        Returns:
            TestResult if found, None otherwise
        """
        try:
            # Query results by attempt ID
            response = self.results_table.query(
                IndexName='ResultsByAttempt-Index',
                KeyConditionExpression='attempt_id = :attempt_id',
                ExpressionAttributeValues={':attempt_id': attempt_id}
            )
            
            results = response.get('Items', [])
            if not results:
                return None
            
            result_data = results[0]
            
            # Verify student ownership
            if result_data.get('student_id') != student_id:
                raise AutoGradingError("Unauthorized access to test results")
            
            # Convert question results back to objects
            question_results = []
            for qr_data in result_data.get('question_results', []):
                question_result = QuestionResult(**qr_data)
                question_results.append(question_result)
            
            # Create TestResult object
            test_result = TestResult(
                result_id=result_data['result_id'],
                attempt_id=result_data['attempt_id'],
                test_id=result_data['test_id'],
                student_id=result_data['student_id'],
                total_questions=result_data['total_questions'],
                correct_answers=result_data['correct_answers'],
                incorrect_answers=result_data['incorrect_answers'],
                unanswered_questions=result_data['unanswered_questions'],
                total_points_earned=result_data['total_points_earned'],
                total_points_possible=result_data['total_points_possible'],
                percentage_score=result_data['percentage_score'],
                passing_score=result_data['passing_score'],
                passed=result_data['passed'],
                time_taken=result_data.get('time_taken'),
                graded_at=result_data['graded_at'],
                question_results=question_results
            )
            
            return test_result
            
        except Exception as e:
            logger.error(f"Failed to get test results for attempt {attempt_id}: {str(e)}")
            raise AutoGradingError(f"Failed to retrieve results: {str(e)}")
    
    def get_student_results(self, student_id: str) -> List[TestResult]:
        """
        Get all test results for a student
        
        Args:
            student_id: Student ID
            
        Returns:
            List of TestResult objects
        """
        try:
            # Query results by student ID
            response = self.results_table.query(
                IndexName='ResultsByStudent-Index',
                KeyConditionExpression='student_id = :student_id',
                ExpressionAttributeValues={':student_id': student_id}
            )
            
            results = []
            for result_data in response.get('Items', []):
                # Convert question results back to objects
                question_results = []
                for qr_data in result_data.get('question_results', []):
                    question_result = QuestionResult(**qr_data)
                    question_results.append(question_result)
                
                # Create TestResult object
                test_result = TestResult(
                    result_id=result_data['result_id'],
                    attempt_id=result_data['attempt_id'],
                    test_id=result_data['test_id'],
                    student_id=result_data['student_id'],
                    total_questions=result_data['total_questions'],
                    correct_answers=result_data['correct_answers'],
                    incorrect_answers=result_data['incorrect_answers'],
                    unanswered_questions=result_data['unanswered_questions'],
                    total_points_earned=result_data['total_points_earned'],
                    total_points_possible=result_data['total_points_possible'],
                    percentage_score=result_data['percentage_score'],
                    passing_score=result_data['passing_score'],
                    passed=result_data['passed'],
                    time_taken=result_data.get('time_taken'),
                    graded_at=result_data['graded_at'],
                    question_results=question_results
                )
                
                results.append(test_result)
            
            # Sort by graded date (most recent first)
            results.sort(key=lambda x: x.graded_at, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get student results for {student_id}: {str(e)}")
            raise AutoGradingError(f"Failed to retrieve student results: {str(e)}")
    
    def auto_grade_on_submission(self, attempt_id: str, student_id: str) -> TestResult:
        """
        Automatically grade a test when it's submitted
        This method is called by the test submission process
        
        Args:
            attempt_id: Test attempt ID
            student_id: Student ID
            
        Returns:
            TestResult with grading information
        """
        try:
            logger.info(f"Auto-grading test attempt {attempt_id} for student {student_id}")
            
            # Grade the test
            result = self.grade_test_attempt(attempt_id, student_id)
            
            logger.info(f"Auto-grading complete: {result.percentage_score:.1f}% ({result.correct_answers}/{result.total_questions})")
            
            return result
            
        except Exception as e:
            logger.error(f"Auto-grading failed for attempt {attempt_id}: {str(e)}")
            raise AutoGradingError(f"Auto-grading failed: {str(e)}")