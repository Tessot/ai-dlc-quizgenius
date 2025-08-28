"""
Test Publishing Service for QuizGenius MVP
Handles test publication, availability management, and student access control
Implements Step 4.2.2: Test Publishing (US-2.5.2 - 3 points)
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError

from services.test_creation_service import TestCreationService, TestCreationError
from utils.dynamodb_utils import get_current_timestamp, generate_id
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PublicationSettings:
    """Test publication settings data structure"""
    test_id: str
    publication_status: str  # draft, published, scheduled, archived
    published_at: Optional[str]
    available_from: Optional[str]
    available_until: Optional[str]
    student_access_code: Optional[str]
    max_students: Optional[int]
    auto_grade: bool
    results_visible_to_students: bool
    allow_late_submissions: bool
    published_by: str
    publication_notes: str
    
class TestPublishingError(Exception):
    """Custom exception for test publishing errors"""
    pass

class TestPublishingService:
    """
    Service for publishing and managing test availability
    """
    
    def __init__(self):
        """Initialize the test publishing service"""
        try:
            self.config = Config()
            self.test_service = TestCreationService()
            
            # Initialize DynamoDB client
            self.dynamodb = boto3.resource('dynamodb', region_name=self.config.AWS_REGION)
            
            # Table references
            self.tests_table = self.dynamodb.Table('QuizGenius_Tests')
            
            # Verify table access
            self._verify_table_access()
            
            logger.info("TestPublishingService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TestPublishingService: {str(e)}")
            raise TestPublishingError(f"Service initialization failed: {str(e)}")
    
    def _verify_table_access(self):
        """Verify access to required tables"""
        try:
            self.tests_table.load()
        except Exception as e:
            logger.error(f"Cannot access DynamoDB tables: {str(e)}")
            raise TestPublishingError(f"Cannot access DynamoDB tables: {str(e)}")
    
    def publish_test(self, test_id: str, instructor_id: str, 
                    publication_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a test to make it available to students
        
        Args:
            test_id: ID of test to publish
            instructor_id: ID of instructor publishing the test
            publication_settings: Publication configuration
            
        Returns:
            Publication result
        """
        try:
            # Validate test exists and is owned by instructor
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data:
                raise TestPublishingError(f"Test {test_id} not found")
            
            if test_data.get('instructor_id') != instructor_id:
                raise TestPublishingError(f"Test {test_id} not owned by instructor {instructor_id}")
            
            # Validate test is ready for publication
            validation_result = self._validate_test_for_publication(test_data)
            if not validation_result['valid']:
                raise TestPublishingError(f"Test not ready for publication: {validation_result['errors']}")
            
            # Validate publication settings
            settings_validation = self._validate_publication_settings(publication_settings)
            if not settings_validation['valid']:
                raise TestPublishingError(f"Invalid publication settings: {settings_validation['errors']}")
            
            # Generate access code if needed
            access_code = None
            if publication_settings.get('require_access_code', False):
                access_code = self._generate_access_code(test_id)
            
            # Prepare publication data
            current_time = get_current_timestamp()
            publication_data = {
                'test_id': test_id,
                'publication_status': 'published',
                'published_at': current_time,
                'available_from': publication_settings.get('available_from'),
                'available_until': publication_settings.get('available_until'),
                'student_access_code': access_code,
                'max_students': publication_settings.get('max_students'),
                'auto_grade': publication_settings.get('auto_grade', True),
                'results_visible_to_students': publication_settings.get('results_visible_to_students', True),
                'allow_late_submissions': publication_settings.get('allow_late_submissions', False),
                'published_by': instructor_id,
                'publication_notes': publication_settings.get('notes', '')
            }
            
            # Update test status
            self.tests_table.update_item(
                Key={'test_id': test_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at, publication_data = :pub_data',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'published',
                    ':updated_at': current_time,
                    ':pub_data': publication_data
                }
            )
            
            logger.info(f"Test published successfully: {test_id}")
            return {
                'success': True,
                'test_id': test_id,
                'publication_status': 'published',
                'published_at': current_time,
                'access_code': access_code,
                'publication_data': publication_data
            }
            
        except Exception as e:
            logger.error(f"Failed to publish test {test_id}: {str(e)}")
            raise TestPublishingError(f"Test publication failed: {str(e)}")
    
    def unpublish_test(self, test_id: str, instructor_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Unpublish a test to make it unavailable to students
        
        Args:
            test_id: ID of test to unpublish
            instructor_id: ID of instructor unpublishing the test
            reason: Reason for unpublishing
            
        Returns:
            Unpublication result
        """
        try:
            # Validate test exists and is owned by instructor
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data:
                raise TestPublishingError(f"Test {test_id} not found")
            
            if test_data.get('instructor_id') != instructor_id:
                raise TestPublishingError(f"Test {test_id} not owned by instructor {instructor_id}")
            
            # Check if test has active attempts
            active_attempts = self._check_active_attempts(test_id)
            if active_attempts > 0:
                logger.warning(f"Unpublishing test {test_id} with {active_attempts} active attempts")
            
            # Update test status
            current_time = get_current_timestamp()
            
            # Preserve publication data but update status
            publication_data = test_data.get('publication_data', {})
            publication_data.update({
                'publication_status': 'unpublished',
                'unpublished_at': current_time,
                'unpublished_by': instructor_id,
                'unpublish_reason': reason
            })
            
            self.tests_table.update_item(
                Key={'test_id': test_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at, publication_data = :pub_data',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'draft',
                    ':updated_at': current_time,
                    ':pub_data': publication_data
                }
            )
            
            logger.info(f"Test unpublished successfully: {test_id}")
            return {
                'success': True,
                'test_id': test_id,
                'publication_status': 'unpublished',
                'unpublished_at': current_time,
                'active_attempts_affected': active_attempts
            }
            
        except Exception as e:
            logger.error(f"Failed to unpublish test {test_id}: {str(e)}")
            raise TestPublishingError(f"Test unpublication failed: {str(e)}")
    
    def schedule_test_publication(self, test_id: str, instructor_id: str, 
                                 schedule_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a test for future publication
        
        Args:
            test_id: ID of test to schedule
            instructor_id: ID of instructor scheduling the test
            schedule_settings: Scheduling configuration
            
        Returns:
            Scheduling result
        """
        try:
            # Validate test exists and is owned by instructor
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data:
                raise TestPublishingError(f"Test {test_id} not found")
            
            if test_data.get('instructor_id') != instructor_id:
                raise TestPublishingError(f"Test {test_id} not owned by instructor {instructor_id}")
            
            # Validate scheduling settings
            publish_at = schedule_settings.get('publish_at')
            if not publish_at:
                raise TestPublishingError("Publication time is required for scheduling")
            
            # Validate publication time is in the future
            try:
                publish_datetime = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
                if publish_datetime <= datetime.now():
                    raise TestPublishingError("Publication time must be in the future")
            except ValueError:
                raise TestPublishingError("Invalid publication time format")
            
            # Prepare scheduling data
            current_time = get_current_timestamp()
            scheduling_data = {
                'publication_status': 'scheduled',
                'scheduled_at': current_time,
                'publish_at': publish_at,
                'available_from': schedule_settings.get('available_from'),
                'available_until': schedule_settings.get('available_until'),
                'auto_grade': schedule_settings.get('auto_grade', True),
                'results_visible_to_students': schedule_settings.get('results_visible_to_students', True),
                'scheduled_by': instructor_id,
                'scheduling_notes': schedule_settings.get('notes', '')
            }
            
            # Update test status
            self.tests_table.update_item(
                Key={'test_id': test_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at, publication_data = :pub_data',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'scheduled',
                    ':updated_at': current_time,
                    ':pub_data': scheduling_data
                }
            )
            
            logger.info(f"Test scheduled for publication: {test_id} at {publish_at}")
            return {
                'success': True,
                'test_id': test_id,
                'publication_status': 'scheduled',
                'scheduled_at': current_time,
                'publish_at': publish_at,
                'scheduling_data': scheduling_data
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule test {test_id}: {str(e)}")
            raise TestPublishingError(f"Test scheduling failed: {str(e)}")
    
    def get_publication_status(self, test_id: str, instructor_id: str) -> Dict[str, Any]:
        """
        Get publication status and details for a test
        
        Args:
            test_id: Test ID
            instructor_id: Instructor ID
            
        Returns:
            Publication status data
        """
        try:
            # Get test data
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data:
                raise TestPublishingError(f"Test {test_id} not found")
            
            if test_data.get('instructor_id') != instructor_id:
                raise TestPublishingError(f"Test {test_id} not owned by instructor {instructor_id}")
            
            # Extract publication data
            publication_data = test_data.get('publication_data', {})
            status = test_data.get('status', 'draft')
            
            # Get additional statistics
            stats = self._get_publication_statistics(test_id)
            
            return {
                'test_id': test_id,
                'publication_status': status,
                'publication_data': publication_data,
                'statistics': stats,
                'is_available_now': self._is_test_available_now(publication_data),
                'can_be_published': self._can_test_be_published(test_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get publication status for {test_id}: {str(e)}")
            raise TestPublishingError(f"Publication status retrieval failed: {str(e)}")
    
    def get_published_tests_for_students(self, student_access_code: str = None) -> List[Dict[str, Any]]:
        """
        Get list of published tests available to students
        
        Args:
            student_access_code: Optional access code for restricted tests
            
        Returns:
            List of available tests
        """
        try:
            # This would typically scan for published tests
            # For now, we'll return a placeholder structure
            available_tests = []
            
            # In a real implementation, this would:
            # 1. Scan for tests with status='published'
            # 2. Check availability windows
            # 3. Filter by access codes if provided
            # 4. Return student-safe test information
            
            return available_tests
            
        except Exception as e:
            logger.error(f"Failed to get published tests: {str(e)}")
            return []
    
    def _validate_test_for_publication(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a test is ready for publication
        
        Args:
            test_data: Test data to validate
            
        Returns:
            Validation result
        """
        errors = []
        
        # Check required fields
        required_fields = ['title', 'question_ids', 'time_limit', 'passing_score']
        for field in required_fields:
            if field not in test_data or not test_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Check questions exist
        question_ids = test_data.get('question_ids', [])
        if len(question_ids) == 0:
            errors.append("Test must have at least one question")
        
        # Check test configuration
        time_limit = test_data.get('time_limit', 0)
        if time_limit <= 0:
            errors.append("Test must have a valid time limit")
        
        passing_score = test_data.get('passing_score', 0)
        if passing_score < 0 or passing_score > 100:
            errors.append("Passing score must be between 0 and 100")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_publication_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate publication settings
        
        Args:
            settings: Publication settings to validate
            
        Returns:
            Validation result
        """
        errors = []
        
        # Validate availability window
        available_from = settings.get('available_from')
        available_until = settings.get('available_until')
        
        if available_from and available_until:
            try:
                from_dt = datetime.fromisoformat(available_from.replace('Z', '+00:00'))
                until_dt = datetime.fromisoformat(available_until.replace('Z', '+00:00'))
                
                if from_dt >= until_dt:
                    errors.append("Available from time must be before available until time")
                    
            except ValueError:
                errors.append("Invalid date format for availability window")
        
        # Validate max students
        max_students = settings.get('max_students')
        if max_students is not None:
            try:
                max_students = int(max_students)
                if max_students <= 0:
                    errors.append("Maximum students must be a positive number")
            except (ValueError, TypeError):
                errors.append("Maximum students must be a valid number")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _generate_access_code(self, test_id: str) -> str:
        """
        Generate a unique access code for the test
        
        Args:
            test_id: Test ID
            
        Returns:
            Access code
        """
        import hashlib
        import random
        
        # Generate a random access code
        random_part = str(random.randint(1000, 9999))
        hash_part = hashlib.md5(f"{test_id}:{random_part}".encode()).hexdigest()[:4].upper()
        
        return f"{random_part}{hash_part}"
    
    def _check_active_attempts(self, test_id: str) -> int:
        """
        Check for active test attempts
        
        Args:
            test_id: Test ID
            
        Returns:
            Number of active attempts
        """
        # This would query the test attempts table
        # For now, return 0 as placeholder
        return 0
    
    def _get_publication_statistics(self, test_id: str) -> Dict[str, Any]:
        """
        Get publication statistics for a test
        
        Args:
            test_id: Test ID
            
        Returns:
            Statistics data
        """
        return {
            'total_attempts': 0,
            'completed_attempts': 0,
            'average_score': 0.0,
            'unique_students': 0,
            'last_attempt': None
        }
    
    def _is_test_available_now(self, publication_data: Dict[str, Any]) -> bool:
        """
        Check if test is currently available to students
        
        Args:
            publication_data: Publication data
            
        Returns:
            True if available now
        """
        if publication_data.get('publication_status') != 'published':
            return False
        
        now = datetime.now()
        
        # Check availability window
        available_from = publication_data.get('available_from')
        available_until = publication_data.get('available_until')
        
        if available_from:
            try:
                from_dt = datetime.fromisoformat(available_from.replace('Z', '+00:00'))
                if now < from_dt:
                    return False
            except ValueError:
                pass
        
        if available_until:
            try:
                until_dt = datetime.fromisoformat(available_until.replace('Z', '+00:00'))
                if now > until_dt:
                    return False
            except ValueError:
                pass
        
        return True
    
    def _can_test_be_published(self, test_data: Dict[str, Any]) -> bool:
        """
        Check if test can be published
        
        Args:
            test_data: Test data
            
        Returns:
            True if can be published
        """
        validation_result = self._validate_test_for_publication(test_data)
        return validation_result['valid']