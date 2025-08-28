#!/usr/bin/env python3
"""
Student Test Service for QuizGenius MVP
Handles student access to published tests and test-taking functionality
Implements Phase 4.3: Student Test Taking
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError

from services.test_publishing_service import TestPublishingService
from services.test_creation_service import TestCreationService
from utils.dynamodb_utils import get_current_timestamp, generate_id
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AvailableTest:
    """Data structure for available test information"""
    test_id: str
    title: str
    description: str
    instructor_name: str
    time_limit: int
    total_questions: int
    passing_score: int
    attempts_allowed: int
    attempts_used: int
    requires_access_code: bool
    available_from: Optional[str]
    available_until: Optional[str]
    is_available_now: bool
    student_can_take: bool
    last_attempt_score: Optional[float]
    best_score: Optional[float]

@dataclass
class TestAttempt:
    """Data structure for test attempt information"""
    attempt_id: str
    test_id: str
    student_id: str
    started_at: str
    submitted_at: Optional[str]
    time_remaining: Optional[int]
    current_question: int
    answers: Dict[str, Any]
    status: str  # 'in_progress', 'submitted', 'expired'
    score: Optional[float]
    passed: Optional[bool]

class StudentTestError(Exception):
    """Custom exception for student test errors"""
    pass

class StudentTestService:
    """
    Service for student test access and management
    """
    
    def __init__(self):
        """Initialize the student test service"""
        try:
            self.config = Config()
            self.publishing_service = TestPublishingService()
            self.test_service = TestCreationService()
            
            # Initialize DynamoDB client
            self.dynamodb = boto3.resource('dynamodb', region_name=self.config.AWS_REGION)
            
            # Table references
            self.tests_table = self.dynamodb.Table('QuizGenius_Tests')
            self.attempts_table = self.dynamodb.Table('QuizGenius_TestAttempts')
            self.users_table = self.dynamodb.Table('QuizGenius_Users')
            
            # Verify table access
            self._verify_table_access()
            
            logger.info("StudentTestService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize StudentTestService: {str(e)}")
            raise StudentTestError(f"Service initialization failed: {str(e)}")
    
    def _verify_table_access(self):
        """Verify access to required tables"""
        try:
            self.tests_table.load()
            self.users_table.load()
            # Test attempts table might not exist yet
            try:
                self.attempts_table.load()
            except:
                logger.warning("Test attempts table not available - some features may be limited")
                self.attempts_table = None
        except Exception as e:
            logger.error(f"Cannot access DynamoDB tables: {str(e)}")
            raise StudentTestError(f"Cannot access DynamoDB tables: {str(e)}")
    
    def get_available_tests(self, student_id: str, access_code: str = None) -> List[AvailableTest]:
        """
        Get list of tests available to a student
        
        Args:
            student_id: ID of the student
            access_code: Optional access code for restricted tests
            
        Returns:
            List of available tests
        """
        try:
            available_tests = []
            
            # Scan for published tests
            response = self.tests_table.scan(
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'published'}
            )
            
            published_tests = response.get('Items', [])
            
            for test in published_tests:
                try:
                    # Check if test is available to student
                    available_test = self._evaluate_test_availability(
                        test, student_id, access_code
                    )
                    
                    if available_test:
                        available_tests.append(available_test)
                        
                except Exception as e:
                    logger.warning(f"Error evaluating test {test.get('test_id', 'unknown')}: {e}")
                    continue
            
            # Sort by availability and title
            available_tests.sort(key=lambda x: (not x.is_available_now, x.title))
            
            logger.info(f"Found {len(available_tests)} available tests for student {student_id}")
            return available_tests
            
        except Exception as e:
            logger.error(f"Failed to get available tests for student {student_id}: {str(e)}")
            raise StudentTestError(f"Failed to retrieve available tests: {str(e)}")
    
    def _evaluate_test_availability(self, test: Dict[str, Any], student_id: str, 
                                  access_code: str = None) -> Optional[AvailableTest]:
        """
        Evaluate if a test is available to a student
        
        Args:
            test: Test data from database
            student_id: Student ID
            access_code: Optional access code
            
        Returns:
            AvailableTest object if available, None otherwise
        """
        try:
            test_id = test['test_id']
            publication_data = test.get('publication_data', {})
            
            # Check if test is currently available
            is_available_now = self.publishing_service._is_test_available_now(publication_data)
            
            # Check access code requirement
            requires_access_code = bool(publication_data.get('student_access_code'))
            if requires_access_code:
                required_code = publication_data.get('student_access_code')
                if access_code != required_code:
                    # Don't show tests that require access codes unless code is provided
                    return None
            
            # Get student's attempt history
            attempts_used, last_score, best_score = self._get_student_attempt_history(
                test_id, student_id
            )
            
            # Check if student can still take the test
            attempts_allowed = test.get('attempts_allowed', 1)
            student_can_take = (
                is_available_now and 
                attempts_used < attempts_allowed and
                not self._has_active_attempt(test_id, student_id)
            )
            
            # Get instructor name
            instructor_name = self._get_instructor_name(test.get('instructor_id', ''))
            
            # Create available test object
            available_test = AvailableTest(
                test_id=test_id,
                title=test.get('title', 'Untitled Test'),
                description=test.get('description', ''),
                instructor_name=instructor_name,
                time_limit=test.get('time_limit', 0),
                total_questions=len(test.get('question_ids', [])),
                passing_score=test.get('passing_score', 0),
                attempts_allowed=attempts_allowed,
                attempts_used=attempts_used,
                requires_access_code=requires_access_code,
                available_from=publication_data.get('available_from'),
                available_until=publication_data.get('available_until'),
                is_available_now=is_available_now,
                student_can_take=student_can_take,
                last_attempt_score=last_score,
                best_score=best_score
            )
            
            return available_test
            
        except Exception as e:
            logger.error(f"Error evaluating test availability: {str(e)}")
            return None
    
    def _get_student_attempt_history(self, test_id: str, student_id: str) -> tuple:
        """
        Get student's attempt history for a test
        
        Args:
            test_id: Test ID
            student_id: Student ID
            
        Returns:
            Tuple of (attempts_used, last_score, best_score)
        """
        try:
            if not self.attempts_table:
                return 0, None, None
            
            # Query attempts for this student and test
            response = self.attempts_table.query(
                IndexName='StudentTestIndex',  # Assuming we have this GSI
                KeyConditionExpression='student_id = :student_id AND test_id = :test_id',
                ExpressionAttributeValues={
                    ':student_id': student_id,
                    ':test_id': test_id
                }
            )
            
            attempts = response.get('Items', [])
            attempts_used = len(attempts)
            
            # Calculate scores
            scores = [attempt.get('score') for attempt in attempts if attempt.get('score') is not None]
            last_score = scores[-1] if scores else None
            best_score = max(scores) if scores else None
            
            return attempts_used, last_score, best_score
            
        except Exception as e:
            logger.warning(f"Could not get attempt history: {str(e)}")
            return 0, None, None
    
    def _has_active_attempt(self, test_id: str, student_id: str) -> bool:
        """
        Check if student has an active (in-progress) attempt
        
        Args:
            test_id: Test ID
            student_id: Student ID
            
        Returns:
            True if student has active attempt
        """
        try:
            if not self.attempts_table:
                return False
            
            # Look for in-progress attempts
            response = self.attempts_table.query(
                IndexName='StudentTestIndex',
                KeyConditionExpression='student_id = :student_id AND test_id = :test_id',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':student_id': student_id,
                    ':test_id': test_id,
                    ':status': 'in_progress'
                }
            )
            
            return len(response.get('Items', [])) > 0
            
        except Exception as e:
            logger.warning(f"Could not check active attempts: {str(e)}")
            return False
    
    def _get_instructor_name(self, instructor_id: str) -> str:
        """
        Get instructor name from user ID
        
        Args:
            instructor_id: Instructor user ID
            
        Returns:
            Instructor name or fallback
        """
        try:
            response = self.users_table.get_item(
                Key={'user_id': instructor_id}
            )
            
            if 'Item' in response:
                user = response['Item']
                return f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            
            return "Unknown Instructor"
            
        except Exception as e:
            logger.warning(f"Could not get instructor name: {str(e)}")
            return "Unknown Instructor"
    
    def start_test_attempt(self, test_id: str, student_id: str, access_code: str = None) -> Dict[str, Any]:
        """
        Start a new test attempt for a student
        
        Args:
            test_id: Test ID
            student_id: Student ID
            access_code: Optional access code
            
        Returns:
            Test attempt information
        """
        try:
            # Validate test availability
            available_tests = self.get_available_tests(student_id, access_code)
            available_test = next((t for t in available_tests if t.test_id == test_id), None)
            
            if not available_test:
                raise StudentTestError(f"Test {test_id} is not available to student")
            
            if not available_test.student_can_take:
                raise StudentTestError(f"Student cannot take test {test_id} at this time")
            
            # Create new attempt
            attempt_id = generate_id()
            current_time = get_current_timestamp()
            
            attempt_data = {
                'attempt_id': attempt_id,
                'test_id': test_id,
                'student_id': student_id,
                'started_at': current_time,
                'submitted_at': None,
                'time_remaining': available_test.time_limit * 60,  # Convert to seconds
                'current_question': 0,
                'answers': {},
                'status': 'in_progress',
                'score': None,
                'passed': None
            }
            
            # Store attempt in database
            if self.attempts_table:
                self.attempts_table.put_item(Item=attempt_data)
            
            logger.info(f"Started test attempt {attempt_id} for student {student_id} on test {test_id}")
            
            return {
                'success': True,
                'attempt_id': attempt_id,
                'test_info': asdict(available_test),
                'time_limit_seconds': attempt_data['time_remaining'],
                'started_at': current_time
            }
            
        except Exception as e:
            logger.error(f"Failed to start test attempt: {str(e)}")
            raise StudentTestError(f"Failed to start test: {str(e)}")
    
    def get_test_attempt(self, attempt_id: str, student_id: str) -> Optional[TestAttempt]:
        """
        Get test attempt information
        
        Args:
            attempt_id: Attempt ID
            student_id: Student ID (for security)
            
        Returns:
            TestAttempt object or None
        """
        try:
            if not self.attempts_table:
                return None
            
            response = self.attempts_table.get_item(
                Key={'attempt_id': attempt_id}
            )
            
            if 'Item' not in response:
                return None
            
            attempt_data = response['Item']
            
            # Verify student ownership
            if attempt_data.get('student_id') != student_id:
                raise StudentTestError("Unauthorized access to test attempt")
            
            # Create TestAttempt object
            test_attempt = TestAttempt(
                attempt_id=attempt_data['attempt_id'],
                test_id=attempt_data['test_id'],
                student_id=attempt_data['student_id'],
                started_at=attempt_data['started_at'],
                submitted_at=attempt_data.get('submitted_at'),
                time_remaining=attempt_data.get('time_remaining'),
                current_question=attempt_data.get('current_question', 0),
                answers=attempt_data.get('answers', {}),
                status=attempt_data.get('status', 'in_progress'),
                score=attempt_data.get('score'),
                passed=attempt_data.get('passed')
            )
            
            return test_attempt
            
        except Exception as e:
            logger.error(f"Failed to get test attempt {attempt_id}: {str(e)}")
            raise StudentTestError(f"Failed to retrieve test attempt: {str(e)}")
    
    def update_test_attempt(self, attempt_id: str, student_id: str, 
                          updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update test attempt data
        
        Args:
            attempt_id: Attempt ID
            student_id: Student ID (for security)
            updates: Updates to apply
            
        Returns:
            Update result
        """
        try:
            if not self.attempts_table:
                raise StudentTestError("Test attempts table not available")
            
            # Verify attempt exists and belongs to student
            attempt = self.get_test_attempt(attempt_id, student_id)
            if not attempt:
                raise StudentTestError("Test attempt not found or unauthorized")
            
            # Prepare update expression
            update_expression = "SET "
            expression_values = {}
            expression_names = {}
            
            for key, value in updates.items():
                if key in ['current_question', 'answers', 'time_remaining', 'status']:
                    update_expression += f"#{key} = :{key}, "
                    expression_names[f"#{key}"] = key
                    expression_values[f":{key}"] = value
            
            # Add updated timestamp
            update_expression += "updated_at = :updated_at"
            expression_values[':updated_at'] = get_current_timestamp()
            
            # Update attempt
            expression_values[':student_id'] = student_id
            
            self.attempts_table.update_item(
                Key={'attempt_id': attempt_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ConditionExpression='student_id = :student_id'
            )
            
            logger.info(f"Updated test attempt {attempt_id}")
            return {'success': True, 'updated_at': expression_values[':updated_at']}
            
        except Exception as e:
            logger.error(f"Failed to update test attempt {attempt_id}: {str(e)}")
            raise StudentTestError(f"Failed to update test attempt: {str(e)}")
    
    def submit_test_attempt(self, attempt_id: str, student_id: str, 
                          final_answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a test attempt and trigger auto-grading
        
        Args:
            attempt_id: Attempt ID
            student_id: Student ID
            final_answers: Final answers
            
        Returns:
            Submission result with grading information
        """
        try:
            if not self.attempts_table:
                raise StudentTestError("Test attempts table not available")
            
            # Get current attempt
            attempt = self.get_test_attempt(attempt_id, student_id)
            if not attempt:
                raise StudentTestError("Test attempt not found")
            
            if attempt.status != 'in_progress':
                raise StudentTestError("Test attempt is not in progress")
            
            # Update attempt with submission
            current_time = get_current_timestamp()
            
            self.attempts_table.update_item(
                Key={'attempt_id': attempt_id},
                UpdateExpression='SET answers = :answers, submitted_at = :submitted_at, #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':answers': final_answers,
                    ':submitted_at': current_time,
                    ':status': 'submitted',
                    ':updated_at': current_time,
                    ':student_id': student_id,
                    ':current_status': 'in_progress'
                },
                ConditionExpression='student_id = :student_id AND #status = :current_status'
            )
            
            logger.info(f"Submitted test attempt {attempt_id} for student {student_id}")
            
            # Trigger auto-grading
            grading_result = None
            try:
                from services.auto_grading_service import AutoGradingService
                grading_service = AutoGradingService()
                grading_result = grading_service.auto_grade_on_submission(attempt_id, student_id)
                logger.info(f"Auto-grading completed: {grading_result.percentage_score:.1f}%")
            except Exception as e:
                logger.error(f"Auto-grading failed for attempt {attempt_id}: {str(e)}")
                # Don't fail submission if grading fails
            
            result = {
                'success': True,
                'attempt_id': attempt_id,
                'submitted_at': current_time,
                'status': 'submitted'
            }
            
            # Add grading results if available
            if grading_result:
                result.update({
                    'graded': True,
                    'score': grading_result.percentage_score,
                    'passed': grading_result.passed,
                    'correct_answers': grading_result.correct_answers,
                    'total_questions': grading_result.total_questions
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to submit test attempt {attempt_id}: {str(e)}")
            raise StudentTestError(f"Failed to submit test: {str(e)}")
    
    def get_test_questions(self, test_id: str, student_id: str, attempt_id: str) -> List[Dict[str, Any]]:
        """
        Get test questions for a student attempt
        
        Args:
            test_id: Test ID
            student_id: Student ID
            attempt_id: Attempt ID
            
        Returns:
            List of questions (without correct answers)
        """
        try:
            # Verify attempt belongs to student
            attempt = self.get_test_attempt(attempt_id, student_id)
            if not attempt or attempt.test_id != test_id:
                raise StudentTestError("Invalid test attempt")
            
            # Get test data
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data:
                raise StudentTestError("Test not found")
            
            # Get questions (this would need to be implemented in test service)
            # For now, return placeholder structure
            questions = []
            question_ids = test_data.get('question_ids', [])
            
            for i, question_id in enumerate(question_ids):
                # This would fetch actual question data
                question = {
                    'question_number': i + 1,
                    'question_id': question_id,
                    'question_text': f'Question {i + 1} placeholder',
                    'question_type': 'multiple_choice',
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    # Note: correct_answer is NOT included for students
                }
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to get test questions: {str(e)}")
            raise StudentTestError(f"Failed to retrieve test questions: {str(e)}")