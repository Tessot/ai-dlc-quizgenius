"""
Test Creation Service for QuizGenius MVP
Handles test creation, configuration, and management
Implements Step 4.2.1: Test Creation Interface (US-2.5.1 - 5 points)
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError

from services.question_storage_service import QuestionStorageService, QuestionStorageError
from utils.dynamodb_utils import get_current_timestamp, generate_id
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestConfiguration:
    """Test configuration data structure"""
    test_id: str
    title: str
    description: str
    instructor_id: str
    question_ids: List[str]
    time_limit: int  # in minutes
    attempts_allowed: int
    randomize_questions: bool
    randomize_options: bool
    show_results_immediately: bool
    passing_score: float  # percentage
    instructions: str
    tags: List[str]
    created_at: str
    updated_at: str
    status: str  # draft, published, archived
    
class TestCreationError(Exception):
    """Custom exception for test creation errors"""
    pass

class TestCreationService:
    """
    Service for creating and managing tests
    """
    
    def __init__(self):
        """Initialize the test creation service"""
        try:
            self.config = Config()
            self.question_service = QuestionStorageService()
            
            # Initialize DynamoDB client
            self.dynamodb = boto3.resource('dynamodb', region_name=self.config.AWS_REGION)
            
            # Table references
            self.tests_table = self.dynamodb.Table('QuizGenius_Tests')
            self.questions_table = self.dynamodb.Table('QuizGenius_Questions')
            
            # Verify table access
            self._verify_table_access()
            
            logger.info("TestCreationService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TestCreationService: {str(e)}")
            raise TestCreationError(f"Service initialization failed: {str(e)}")
    
    def _verify_table_access(self):
        """Verify access to required tables"""
        try:
            self.tests_table.load()
            self.questions_table.load()
        except Exception as e:
            logger.error(f"Cannot access DynamoDB tables: {str(e)}")
            raise TestCreationError(f"Cannot access DynamoDB tables: {str(e)}")
    
    def create_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new test
        
        Args:
            test_config: Test configuration data
            
        Returns:
            Created test data
        """
        try:
            # Validate test configuration
            validation_result = self.validate_test_config(test_config)
            if not validation_result['valid']:
                raise TestCreationError(f"Invalid test configuration: {validation_result['errors']}")
            
            # Generate test ID and timestamps
            test_id = generate_id()
            current_time = get_current_timestamp()
            
            # Create test configuration object
            test_data = TestConfiguration(
                test_id=test_id,
                title=test_config['title'],
                description=test_config.get('description', ''),
                instructor_id=test_config['instructor_id'],
                question_ids=test_config['question_ids'],
                time_limit=test_config.get('time_limit', 60),
                attempts_allowed=test_config.get('attempts_allowed', 1),
                randomize_questions=test_config.get('randomize_questions', False),
                randomize_options=test_config.get('randomize_options', False),
                show_results_immediately=test_config.get('show_results_immediately', True),
                passing_score=test_config.get('passing_score', 70.0),
                instructions=test_config.get('instructions', ''),
                tags=test_config.get('tags', []),
                created_at=current_time,
                updated_at=current_time,
                status='draft'
            )
            
            # Save to database
            self.tests_table.put_item(Item=asdict(test_data))
            
            # Update question associations
            self._associate_questions_with_test(test_id, test_config['question_ids'])
            
            logger.info(f"Test created successfully: {test_id}")
            return {
                'success': True,
                'test_id': test_id,
                'test_data': asdict(test_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to create test: {str(e)}")
            raise TestCreationError(f"Test creation failed: {str(e)}")
    
    def update_test(self, test_id: str, updates: Dict[str, Any], instructor_id: str) -> Dict[str, Any]:
        """
        Update an existing test
        
        Args:
            test_id: ID of test to update
            updates: Updates to apply
            instructor_id: ID of instructor making updates
            
        Returns:
            Update result
        """
        try:
            # Verify ownership
            test_data = self.get_test_by_id(test_id)
            if not test_data or test_data.get('instructor_id') != instructor_id:
                raise TestCreationError(f"Test {test_id} not found or not owned by instructor")
            
            # Prepare update expression
            update_expression = "SET updated_at = :updated_at"
            expression_values = {':updated_at': get_current_timestamp()}
            
            # Add updates
            for key, value in updates.items():
                if key in ['title', 'description', 'time_limit', 'attempts_allowed', 
                          'randomize_questions', 'randomize_options', 'show_results_immediately',
                          'passing_score', 'instructions', 'tags']:
                    update_expression += f", {key} = :{key}"
                    expression_values[f":{key}"] = value
            
            # Handle question_ids separately
            if 'question_ids' in updates:
                # Validate questions
                validation_result = self._validate_questions(updates['question_ids'], instructor_id)
                if not validation_result['valid']:
                    raise TestCreationError(f"Invalid questions: {validation_result['errors']}")
                
                update_expression += ", question_ids = :question_ids"
                expression_values[':question_ids'] = updates['question_ids']
                
                # Update question associations
                self._associate_questions_with_test(test_id, updates['question_ids'])
            
            # Perform update
            response = self.tests_table.update_item(
                Key={'test_id': test_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            logger.info(f"Test updated successfully: {test_id}")
            return {
                'success': True,
                'test_id': test_id,
                'updated_data': response.get('Attributes', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to update test {test_id}: {str(e)}")
            raise TestCreationError(f"Test update failed: {str(e)}")
    
    def get_test_by_id(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Get test by ID
        
        Args:
            test_id: Test ID
            
        Returns:
            Test data or None
        """
        try:
            if not self.tests_table:
                raise TestCreationError("Database connection not available")
                
            response = self.tests_table.get_item(Key={'test_id': test_id})
            return response.get('Item')
            
        except Exception as e:
            logger.error(f"Failed to retrieve test {test_id}: {str(e)}")
            return None
    
    def get_tests_by_instructor(self, instructor_id: str, status: str = None) -> List[Dict[str, Any]]:
        """
        Get tests created by an instructor
        
        Args:
            instructor_id: Instructor ID
            status: Optional status filter
            
        Returns:
            List of tests
        """
        try:
            # Use GSI to query by instructor (created_by)
            if status:
                response = self.tests_table.query(
                    IndexName='TestsByCreator-Index',
                    KeyConditionExpression='created_by = :instructor_id',
                    FilterExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':instructor_id': instructor_id,
                        ':status': status
                    }
                )
            else:
                response = self.tests_table.query(
                    IndexName='TestsByCreator-Index',
                    KeyConditionExpression='created_by = :instructor_id',
                    ExpressionAttributeValues={':instructor_id': instructor_id}
                )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Failed to retrieve tests for instructor {instructor_id}: {str(e)}")
            return []
    
    def validate_test_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate test configuration
        
        Args:
            config: Test configuration to validate
            
        Returns:
            Validation result
        """
        errors = []
        
        # Required fields
        required_fields = ['title', 'instructor_id', 'question_ids']
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"Missing required field: {field}")
        
        # Title validation
        if 'title' in config:
            try:
                title = str(config['title']).strip()
                if len(title) < 3:
                    errors.append("Title must be at least 3 characters long")
                elif len(title) > 200:
                    errors.append("Title must be less than 200 characters")
            except (TypeError, AttributeError):
                errors.append("Title must be a valid string")
        
        # Question validation
        if 'question_ids' in config:
            try:
                question_ids = config['question_ids']
                if not isinstance(question_ids, list):
                    errors.append("Question IDs must be provided as a list")
                elif len(question_ids) == 0:
                    errors.append("At least one question must be selected")
                elif len(question_ids) > 100:
                    errors.append("Maximum 100 questions allowed per test")
                else:
                    # Validate questions exist and belong to instructor
                    validation_result = self._validate_questions(question_ids, config.get('instructor_id'))
                    if not validation_result['valid']:
                        errors.extend(validation_result['errors'])
            except (TypeError, AttributeError):
                errors.append("Question IDs must be provided as a valid list")
        
        # Time limit validation
        if 'time_limit' in config:
            try:
                time_limit = int(config['time_limit'])
                if time_limit < 1 or time_limit > 480:
                    errors.append("Time limit must be between 1 and 480 minutes")
            except (ValueError, TypeError):
                errors.append("Time limit must be a valid number between 1 and 480 minutes")
        
        # Attempts validation
        if 'attempts_allowed' in config:
            try:
                attempts = int(config['attempts_allowed'])
                if attempts < 1 or attempts > 10:
                    errors.append("Attempts allowed must be between 1 and 10")
            except (ValueError, TypeError):
                errors.append("Attempts allowed must be a valid number between 1 and 10")
        
        # Passing score validation
        if 'passing_score' in config:
            try:
                score = float(config['passing_score'])
                if score < 0 or score > 100:
                    errors.append("Passing score must be between 0 and 100")
            except (ValueError, TypeError):
                errors.append("Passing score must be a valid number between 0 and 100")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_questions(self, question_ids: List[str], instructor_id: str) -> Dict[str, Any]:
        """
        Validate that questions exist and belong to instructor
        
        Args:
            question_ids: List of question IDs
            instructor_id: Instructor ID
            
        Returns:
            Validation result
        """
        errors = []
        
        try:
            # Get questions from storage service
            for question_id in question_ids:
                question = self.question_service.get_question_by_id(question_id)
                if not question:
                    errors.append(f"Question not found: {question_id}")
                elif question.get('created_by') != instructor_id:
                    errors.append(f"Question not owned by instructor: {question_id}")
                elif question.get('status') != 'active':
                    errors.append(f"Question not active: {question_id}")
        
        except Exception as e:
            errors.append(f"Error validating questions: {str(e)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _associate_questions_with_test(self, test_id: str, question_ids: List[str]):
        """
        Associate questions with a test
        
        Args:
            test_id: Test ID
            question_ids: List of question IDs
        """
        try:
            # This could update a separate association table or add test_id to questions
            # For now, we'll just log the association
            logger.info(f"Associated {len(question_ids)} questions with test {test_id}")
            
        except Exception as e:
            logger.warning(f"Failed to associate questions with test: {str(e)}")
    
    def get_test_preview(self, test_id: str, instructor_id: str) -> Dict[str, Any]:
        """
        Get test preview data
        
        Args:
            test_id: Test ID
            instructor_id: Instructor ID
            
        Returns:
            Test preview data
        """
        try:
            # Get test data
            test_data = self.get_test_by_id(test_id)
            if not test_data or test_data.get('instructor_id') != instructor_id:
                raise TestCreationError(f"Test {test_id} not found or not owned by instructor")
            
            # Get question details
            questions = []
            for question_id in test_data.get('question_ids', []):
                question = self.question_service.get_question_by_id(question_id)
                if question:
                    questions.append({
                        'question_id': question_id,
                        'question_text': question.get('question_text', ''),
                        'question_type': question.get('question_type', ''),
                        'options': question.get('options', []),
                        'correct_answer': question.get('correct_answer', ''),
                        'difficulty_level': question.get('difficulty_level', ''),
                        'topic': question.get('topic', '')
                    })
            
            # Calculate test statistics
            stats = self._calculate_test_stats(questions)
            
            return {
                'test_data': test_data,
                'questions': questions,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get test preview for {test_id}: {str(e)}")
            raise TestCreationError(f"Test preview failed: {str(e)}")
    
    def _calculate_test_stats(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate test statistics
        
        Args:
            questions: List of questions
            
        Returns:
            Test statistics
        """
        if not questions:
            return {
                'total_questions': 0,
                'question_types': {},
                'difficulty_distribution': {},
                'topics': [],
                'estimated_time': 0
            }
        
        # Count question types
        type_counts = {}
        difficulty_counts = {}
        topics = set()
        
        for question in questions:
            q_type = question.get('question_type', 'unknown')
            difficulty = question.get('difficulty_level', 'unknown')
            topic = question.get('topic', 'unknown')
            
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            topics.add(topic)
        
        # Estimate time (rough calculation)
        estimated_time = len(questions) * 2  # 2 minutes per question average
        
        return {
            'total_questions': len(questions),
            'question_types': type_counts,
            'difficulty_distribution': difficulty_counts,
            'topics': list(topics),
            'estimated_time': estimated_time
        }
    
    def delete_test(self, test_id: str, instructor_id: str) -> Dict[str, Any]:
        """
        Delete a test
        
        Args:
            test_id: Test ID
            instructor_id: Instructor ID
            
        Returns:
            Deletion result
        """
        try:
            # Verify ownership
            test_data = self.get_test_by_id(test_id)
            if not test_data or test_data.get('instructor_id') != instructor_id:
                raise TestCreationError(f"Test {test_id} not found or not owned by instructor")
            
            # Check if test can be deleted (not published with attempts)
            if test_data.get('status') == 'published':
                # In a real system, we'd check for existing attempts
                # For now, we'll allow deletion but warn
                logger.warning(f"Deleting published test {test_id}")
            
            # Soft delete by updating status
            self.tests_table.update_item(
                Key={'test_id': test_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'deleted',
                    ':updated_at': get_current_timestamp()
                }
            )
            
            logger.info(f"Test deleted successfully: {test_id}")
            return {
                'success': True,
                'test_id': test_id,
                'deleted_at': get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Failed to delete test {test_id}: {str(e)}")
            raise TestCreationError(f"Test deletion failed: {str(e)}")
    
    def duplicate_test(self, test_id: str, instructor_id: str, new_title: str = None) -> Dict[str, Any]:
        """
        Duplicate an existing test
        
        Args:
            test_id: Test ID to duplicate
            instructor_id: Instructor ID
            new_title: Optional new title
            
        Returns:
            Duplicated test data
        """
        try:
            # Get original test
            original_test = self.get_test_by_id(test_id)
            if not original_test or original_test.get('instructor_id') != instructor_id:
                raise TestCreationError(f"Test {test_id} not found or not owned by instructor")
            
            # Create duplicate configuration
            duplicate_config = {
                'title': new_title or f"{original_test['title']} (Copy)",
                'description': original_test.get('description', ''),
                'instructor_id': instructor_id,
                'question_ids': original_test.get('question_ids', []),
                'time_limit': original_test.get('time_limit', 60),
                'attempts_allowed': original_test.get('attempts_allowed', 1),
                'randomize_questions': original_test.get('randomize_questions', False),
                'randomize_options': original_test.get('randomize_options', False),
                'show_results_immediately': original_test.get('show_results_immediately', True),
                'passing_score': original_test.get('passing_score', 70.0),
                'instructions': original_test.get('instructions', ''),
                'tags': original_test.get('tags', [])
            }
            
            # Create duplicate
            return self.create_test(duplicate_config)
            
        except Exception as e:
            logger.error(f"Failed to duplicate test {test_id}: {str(e)}")
            raise TestCreationError(f"Test duplication failed: {str(e)}")