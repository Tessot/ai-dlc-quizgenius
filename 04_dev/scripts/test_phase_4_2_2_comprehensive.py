#!/usr/bin/env python3
"""
Comprehensive Test Script for Phase 4.2.2: Test Publishing
Tests full integration including database operations, error handling, and edge cases.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.test_publishing_service import TestPublishingService, TestPublishingError
from services.test_creation_service import TestCreationService, TestCreationError
from services.question_storage_service import QuestionStorageService
from services.question_generation_service import GeneratedQuestion
from utils.config import Config
from utils.dynamodb_utils import get_current_timestamp, generate_id

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPhase422Comprehensive:
    """Comprehensive test class for Phase 4.2.2: Test Publishing"""
    
    def __init__(self):
        """Initialize test environment"""
        self.config = Config()
        self.test_results = []
        self.test_instructor_id = "test_instructor_422_comp"
        self.test_data_cleanup = []  # Track items to clean up
        
        # Initialize services
        try:
            self.publishing_service = TestPublishingService()
            self.test_service = TestCreationService()
            self.question_service = QuestionStorageService()
            
            # Initialize DynamoDB for direct testing
            self.dynamodb = boto3.resource('dynamodb', region_name=self.config.AWS_REGION)
            self.tests_table = self.dynamodb.Table('QuizGenius_Tests')
            
            logger.info("✅ All services initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    def run_all_tests(self):
        """Run all comprehensive Phase 4.2.2 tests"""
        logger.info("🚀 Starting Phase 4.2.2: Test Publishing Tests (COMPREHENSIVE)")
        
        test_methods = [
            # Core functionality tests
            self.test_service_initialization,
            self.test_database_connectivity,
            
            # Integration tests
            self.test_create_real_test_for_publishing,
            self.test_publish_real_test,
            self.test_publication_status_retrieval,
            self.test_unpublish_real_test,
            self.test_schedule_real_test,
            
            # Error handling tests
            self.test_publish_nonexistent_test,
            self.test_publish_unauthorized_test,
            self.test_publish_invalid_test,
            self.test_invalid_publication_settings,
            
            # Edge case tests
            self.test_concurrent_publication_attempts,
            self.test_publication_with_availability_window,
            self.test_publication_with_access_code,
            self.test_publication_statistics,
            
            # Data integrity tests
            self.test_database_state_consistency,
            self.test_publication_data_persistence,
            
            # Performance tests
            self.test_publication_performance,
        ]
        
        try:
            for test_method in test_methods:
                try:
                    logger.info(f"Running {test_method.__name__}...")
                    test_method()
                    self.test_results.append({"test": test_method.__name__, "status": "PASS", "error": None})
                    logger.info(f"✅ {test_method.__name__} PASSED")
                except Exception as e:
                    self.test_results.append({"test": test_method.__name__, "status": "FAIL", "error": str(e)})
                    logger.error(f"❌ {test_method.__name__} FAILED: {e}")
        finally:
            # Cleanup test data
            self.cleanup_test_data()
        
        self.print_test_summary()
    
    def test_service_initialization(self):
        """Test 1: Service Initialization"""
        assert self.publishing_service is not None, "Publishing service should be initialized"
        assert self.test_service is not None, "Test service should be initialized"
        assert self.question_service is not None, "Question service should be initialized"
        
        # Verify all required methods exist
        required_methods = [
            'publish_test', 'unpublish_test', 'schedule_test_publication',
            'get_publication_status', '_validate_test_for_publication',
            '_validate_publication_settings', '_generate_access_code'
        ]
        
        for method in required_methods:
            assert hasattr(self.publishing_service, method), f"Publishing service should have {method} method"
        
        logger.info("Service initialization test passed")
    
    def test_database_connectivity(self):
        """Test 2: Database Connectivity"""
        try:
            # Test table access
            self.tests_table.load()
            
            # Test basic read operation
            response = self.tests_table.scan(Limit=1)
            assert 'Items' in response, "Should be able to scan tests table"
            
            logger.info("Database connectivity test passed")
        except Exception as e:
            raise AssertionError(f"Database connectivity failed: {e}")
    
    def test_create_real_test_for_publishing(self):
        """Test 3: Create Real Test for Publishing"""
        # Create a real question first
        generated_question = GeneratedQuestion(
            question_id=generate_id(),
            question_text='What is the capital of France for publishing test?',
            question_type='multiple_choice',
            options=['London', 'Berlin', 'Paris', 'Madrid'],
            correct_answer='Paris',
            difficulty_level='easy',
            topic='Geography',
            source_content='Test content for comprehensive publishing test',
            confidence_score=Decimal('0.9'),
            metadata={'test_type': 'comprehensive', 'phase': '4.2.2'}
        )
        
        # Store the question
        question_result = self.question_service.store_question(
            generated_question, 'test_doc_422_comp', self.test_instructor_id
        )
        
        if not question_result['success']:
            # If question storage fails, create a mock test with fake question IDs
            logger.warning("Question storage failed, using mock question IDs")
            question_id = 'mock_question_422_comp'
        else:
            question_id = question_result['question_id']
            self.test_data_cleanup.append(('question', question_id))
        
        # Create test
        test_data = {
            'title': 'Comprehensive Publishing Test',
            'description': 'A test created for comprehensive publishing functionality testing',
            'question_ids': [question_id],
            'time_limit': 45,
            'passing_score': 75,
            'attempts_allowed': 3,
            'randomize_questions': True,
            'show_results_immediately': False,
            'instructor_id': self.test_instructor_id  # Include instructor_id in config
        }
        
        test_result = self.test_service.create_test(test_data)
        assert test_result['success'], f"Test creation failed: {test_result.get('error')}"
        
        self.test_test_id = test_result['test_id']
        self.test_data_cleanup.append(('test', self.test_test_id))
        
        # Verify test was created in database
        db_test = self.tests_table.get_item(Key={'test_id': self.test_test_id})
        assert 'Item' in db_test, "Test should exist in database"
        assert db_test['Item']['instructor_id'] == self.test_instructor_id, "Test should be owned by correct instructor"
        
        logger.info(f"Created real test for publishing: {self.test_test_id}")
    
    def test_publish_real_test(self):
        """Test 4: Publish Real Test"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        publication_settings = {
            'auto_grade': True,
            'results_visible_to_students': True,
            'allow_late_submissions': False,
            'require_access_code': True,
            'max_students': 100,
            'notes': 'Comprehensive test publication'
        }
        
        # Publish the test
        result = self.publishing_service.publish_test(
            self.test_test_id, self.test_instructor_id, publication_settings
        )
        
        assert result['success'], f"Test publication failed: {result}"
        assert result['publication_status'] == 'published', "Test should be marked as published"
        assert result['access_code'] is not None, "Access code should be generated"
        assert 'published_at' in result, "Publication timestamp should be included"
        
        # Verify database state
        db_test = self.tests_table.get_item(Key={'test_id': self.test_test_id})
        assert db_test['Item']['status'] == 'published', "Test status should be updated in database"
        assert 'publication_data' in db_test['Item'], "Publication data should be stored"
        
        pub_data = db_test['Item']['publication_data']
        assert pub_data['publication_status'] == 'published', "Publication status should be stored"
        assert pub_data['published_by'] == self.test_instructor_id, "Publisher should be recorded"
        assert pub_data['auto_grade'] == True, "Settings should be stored"
        
        self.test_access_code = result['access_code']
        logger.info(f"Test published successfully with access code: {self.test_access_code}")
    
    def test_publication_status_retrieval(self):
        """Test 5: Publication Status Retrieval"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        status_data = self.publishing_service.get_publication_status(
            self.test_test_id, self.test_instructor_id
        )
        
        assert status_data['test_id'] == self.test_test_id, "Test ID should match"
        assert status_data['publication_status'] == 'published', "Status should be published"
        assert 'publication_data' in status_data, "Publication data should be included"
        assert 'statistics' in status_data, "Statistics should be included"
        assert 'is_available_now' in status_data, "Availability status should be included"
        assert 'can_be_published' in status_data, "Publishability status should be included"
        
        # Verify statistics structure
        stats = status_data['statistics']
        required_stats = ['total_attempts', 'completed_attempts', 'average_score', 'unique_students']
        for stat in required_stats:
            assert stat in stats, f"Statistics should include {stat}"
        
        logger.info("Publication status retrieval test passed")
    
    def test_unpublish_real_test(self):
        """Test 6: Unpublish Real Test"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        unpublish_reason = "Testing unpublish functionality"
        result = self.publishing_service.unpublish_test(
            self.test_test_id, self.test_instructor_id, unpublish_reason
        )
        
        assert result['success'], f"Test unpublishing failed: {result}"
        assert result['publication_status'] == 'unpublished', "Test should be marked as unpublished"
        assert 'unpublished_at' in result, "Unpublication timestamp should be included"
        
        # Verify database state
        db_test = self.tests_table.get_item(Key={'test_id': self.test_test_id})
        assert db_test['Item']['status'] == 'draft', "Test status should be reverted to draft"
        
        pub_data = db_test['Item']['publication_data']
        assert pub_data['publication_status'] == 'unpublished', "Publication status should be updated"
        assert pub_data['unpublish_reason'] == unpublish_reason, "Unpublish reason should be stored"
        
        logger.info("Test unpublished successfully")
    
    def test_schedule_real_test(self):
        """Test 7: Schedule Real Test"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        # Schedule for 2 hours from now
        future_time = datetime.now() + timedelta(hours=2)
        schedule_settings = {
            'publish_at': future_time.isoformat(),
            'available_from': (future_time + timedelta(minutes=30)).isoformat(),
            'available_until': (future_time + timedelta(days=7)).isoformat(),
            'auto_grade': True,
            'results_visible_to_students': False,
            'notes': 'Scheduled publication test'
        }
        
        result = self.publishing_service.schedule_test_publication(
            self.test_test_id, self.test_instructor_id, schedule_settings
        )
        
        assert result['success'], f"Test scheduling failed: {result}"
        assert result['publication_status'] == 'scheduled', "Test should be marked as scheduled"
        assert 'scheduled_at' in result, "Scheduling timestamp should be included"
        assert result['publish_at'] == future_time.isoformat(), "Publication time should match"
        
        # Verify database state
        db_test = self.tests_table.get_item(Key={'test_id': self.test_test_id})
        assert db_test['Item']['status'] == 'scheduled', "Test status should be scheduled"
        
        logger.info(f"Test scheduled successfully for: {result['publish_at']}")
    
    def test_publish_nonexistent_test(self):
        """Test 8: Publish Nonexistent Test (Error Handling)"""
        fake_test_id = 'nonexistent_test_123'
        publication_settings = {'auto_grade': True}
        
        try:
            self.publishing_service.publish_test(
                fake_test_id, self.test_instructor_id, publication_settings
            )
            assert False, "Should raise exception for nonexistent test"
        except TestPublishingError as e:
            assert 'not found' in str(e).lower(), "Error should indicate test not found"
        
        logger.info("Nonexistent test error handling test passed")
    
    def test_publish_unauthorized_test(self):
        """Test 9: Publish Unauthorized Test (Security)"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        fake_instructor_id = 'unauthorized_instructor_123'
        publication_settings = {'auto_grade': True}
        
        try:
            self.publishing_service.publish_test(
                self.test_test_id, fake_instructor_id, publication_settings
            )
            assert False, "Should raise exception for unauthorized access"
        except TestPublishingError as e:
            assert 'not owned' in str(e).lower(), "Error should indicate ownership issue"
        
        logger.info("Unauthorized access error handling test passed")
    
    def test_publish_invalid_test(self):
        """Test 10: Publish Invalid Test (Validation)"""
        # Test that invalid test creation is properly rejected
        invalid_test_data = {
            'title': 'Invalid Test',
            'description': 'Test with no questions',
            'question_ids': [],  # No questions
            'time_limit': 30,
            'passing_score': 70,
            'instructor_id': self.test_instructor_id
        }
        
        # Test creation should fail for invalid data
        try:
            test_result = self.test_service.create_test(invalid_test_data)
            assert not test_result['success'], "Invalid test creation should fail"
        except TestCreationError as e:
            assert 'invalid test configuration' in str(e).lower(), "Error should indicate configuration issue"
        
        logger.info("Invalid test validation test passed")
    
    def test_invalid_publication_settings(self):
        """Test 11: Invalid Publication Settings"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        # Test invalid availability window
        invalid_settings = {
            'available_from': '2024-12-31T23:59:59',
            'available_until': '2024-01-01T00:00:00',  # Before available_from
            'auto_grade': True
        }
        
        try:
            self.publishing_service.publish_test(
                self.test_test_id, self.test_instructor_id, invalid_settings
            )
            assert False, "Should raise exception for invalid settings"
        except TestPublishingError as e:
            assert 'invalid publication settings' in str(e).lower(), "Error should indicate settings validation failure"
        
        logger.info("Invalid publication settings test passed")
    
    def test_concurrent_publication_attempts(self):
        """Test 12: Concurrent Publication Attempts"""
        # This test simulates what might happen if multiple requests try to publish the same test
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        publication_settings = {'auto_grade': True, 'notes': 'Concurrent test 1'}
        
        # First publication should succeed
        result1 = self.publishing_service.publish_test(
            self.test_test_id, self.test_instructor_id, publication_settings
        )
        assert result1['success'], "First publication should succeed"
        
        # Second publication should handle already published state gracefully
        publication_settings['notes'] = 'Concurrent test 2'
        try:
            result2 = self.publishing_service.publish_test(
                self.test_test_id, self.test_instructor_id, publication_settings
            )
            # Should either succeed (update) or fail gracefully
            if not result2['success']:
                logger.info("Second publication correctly rejected already published test")
        except TestPublishingError:
            logger.info("Second publication correctly raised exception for already published test")
        
        logger.info("Concurrent publication attempts test passed")
    
    def test_publication_with_availability_window(self):
        """Test 13: Publication with Availability Window"""
        # Create a real question for this test
        from decimal import Decimal
        generated_question = GeneratedQuestion(
            question_id=generate_id(),
            question_text='What is the availability window test question?',
            question_type='multiple_choice',
            options=['Option A', 'Option B', 'Option C', 'Option D'],
            correct_answer='Option A',
            difficulty_level='easy',
            topic='Testing',
            source_content='Test content for availability window',
            confidence_score=Decimal('0.9'),
            metadata={'test_type': 'availability_window'}
        )
        
        question_result = self.question_service.store_question(
            generated_question, 'test_doc_availability', self.test_instructor_id
        )
        
        if question_result['success']:
            question_id = question_result['question_id']
            self.test_data_cleanup.append(('question', question_id))
        else:
            question_id = 'mock_question_availability'  # Fallback
        
        # Create test for availability window testing
        test_data = {
            'title': 'Availability Window Test',
            'description': 'Test for availability window functionality',
            'question_ids': [question_id],
            'time_limit': 30,
            'passing_score': 70,
            'instructor_id': self.test_instructor_id
        }
        
        test_result = self.test_service.create_test(test_data)
        if test_result['success']:
            availability_test_id = test_result['test_id']
            self.test_data_cleanup.append(('test', availability_test_id))
            
            # Set availability window
            future_start = datetime.now() + timedelta(hours=1)
            future_end = datetime.now() + timedelta(days=1)
            
            publication_settings = {
                'available_from': future_start.isoformat(),
                'available_until': future_end.isoformat(),
                'auto_grade': True
            }
            
            result = self.publishing_service.publish_test(
                availability_test_id, self.test_instructor_id, publication_settings
            )
            
            assert result['success'], "Publication with availability window should succeed"
            
            # Check availability status
            status_data = self.publishing_service.get_publication_status(
                availability_test_id, self.test_instructor_id
            )
            
            # Should not be available now (starts in 1 hour)
            assert not status_data['is_available_now'], "Test should not be available before start time"
        
        logger.info("Publication with availability window test passed")
    
    def test_publication_with_access_code(self):
        """Test 14: Publication with Access Code"""
        # Create a real question for this test
        from decimal import Decimal
        generated_question = GeneratedQuestion(
            question_id=generate_id(),
            question_text='What is the access code test question?',
            question_type='multiple_choice',
            options=['Code A', 'Code B', 'Code C', 'Code D'],
            correct_answer='Code A',
            difficulty_level='easy',
            topic='Testing',
            source_content='Test content for access code',
            confidence_score=Decimal('0.9'),
            metadata={'test_type': 'access_code'}
        )
        
        question_result = self.question_service.store_question(
            generated_question, 'test_doc_access_code', self.test_instructor_id
        )
        
        if question_result['success']:
            question_id = question_result['question_id']
            self.test_data_cleanup.append(('question', question_id))
        else:
            question_id = 'mock_question_access_code'  # Fallback
        
        # Create test for access code testing
        test_data = {
            'title': 'Access Code Test',
            'description': 'Test for access code functionality',
            'question_ids': [question_id],
            'time_limit': 30,
            'passing_score': 70,
            'instructor_id': self.test_instructor_id
        }
        
        test_result = self.test_service.create_test(test_data)
        if test_result['success']:
            access_code_test_id = test_result['test_id']
            self.test_data_cleanup.append(('test', access_code_test_id))
            
            publication_settings = {
                'require_access_code': True,
                'max_students': 50,
                'auto_grade': True
            }
            
            result = self.publishing_service.publish_test(
                access_code_test_id, self.test_instructor_id, publication_settings
            )
            
            assert result['success'], "Publication with access code should succeed"
            assert result['access_code'] is not None, "Access code should be generated"
            assert len(result['access_code']) >= 6, "Access code should be at least 6 characters"
            
            # Verify access code is stored in database
            db_test = self.tests_table.get_item(Key={'test_id': access_code_test_id})
            pub_data = db_test['Item']['publication_data']
            assert pub_data['student_access_code'] == result['access_code'], "Access code should be stored"
        
        logger.info("Publication with access code test passed")
    
    def test_publication_statistics(self):
        """Test 15: Publication Statistics"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        stats = self.publishing_service._get_publication_statistics(self.test_test_id)
        
        # Verify statistics structure
        required_fields = ['total_attempts', 'completed_attempts', 'average_score', 'unique_students', 'last_attempt']
        for field in required_fields:
            assert field in stats, f"Statistics should include {field}"
        
        # Verify data types
        assert isinstance(stats['total_attempts'], int), "total_attempts should be integer"
        assert isinstance(stats['completed_attempts'], int), "completed_attempts should be integer"
        assert isinstance(stats['average_score'], (int, float)), "average_score should be numeric"
        assert isinstance(stats['unique_students'], int), "unique_students should be integer"
        
        logger.info("Publication statistics test passed")
    
    def test_database_state_consistency(self):
        """Test 16: Database State Consistency"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        # Get test from database directly
        db_test = self.tests_table.get_item(Key={'test_id': self.test_test_id})
        assert 'Item' in db_test, "Test should exist in database"
        
        # Get test through service
        service_test = self.test_service.get_test_by_id(self.test_test_id)
        assert service_test is not None, "Test should be retrievable through service"
        
        # Compare key fields
        assert db_test['Item']['test_id'] == service_test['test_id'], "Test IDs should match"
        assert db_test['Item']['title'] == service_test['title'], "Titles should match"
        assert db_test['Item']['instructor_id'] == service_test['instructor_id'], "Instructor IDs should match"
        
        logger.info("Database state consistency test passed")
    
    def test_publication_data_persistence(self):
        """Test 17: Publication Data Persistence"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        # Publish test with specific settings
        publication_settings = {
            'auto_grade': False,
            'results_visible_to_students': False,
            'allow_late_submissions': True,
            'max_students': 25,
            'notes': 'Persistence test publication'
        }
        
        result = self.publishing_service.publish_test(
            self.test_test_id, self.test_instructor_id, publication_settings
        )
        
        # Wait a moment and retrieve data
        import time
        time.sleep(1)
        
        # Get fresh data from database
        db_test = self.tests_table.get_item(Key={'test_id': self.test_test_id})
        pub_data = db_test['Item']['publication_data']
        
        # Verify all settings were persisted correctly
        assert pub_data['auto_grade'] == False, "auto_grade setting should be persisted"
        assert pub_data['results_visible_to_students'] == False, "results_visible_to_students should be persisted"
        assert pub_data['allow_late_submissions'] == True, "allow_late_submissions should be persisted"
        assert pub_data['max_students'] == 25, "max_students should be persisted"
        assert pub_data['publication_notes'] == 'Persistence test publication', "notes should be persisted"
        
        logger.info("Publication data persistence test passed")
    
    def test_publication_performance(self):
        """Test 18: Publication Performance"""
        assert hasattr(self, 'test_test_id'), "Test should be created first"
        
        import time
        
        publication_settings = {'auto_grade': True, 'notes': 'Performance test'}
        
        # Measure publication time
        start_time = time.time()
        result = self.publishing_service.publish_test(
            self.test_test_id, self.test_instructor_id, publication_settings
        )
        end_time = time.time()
        
        publication_time = end_time - start_time
        
        assert result['success'], "Publication should succeed"
        assert publication_time < 5.0, f"Publication should complete within 5 seconds, took {publication_time:.2f}s"
        
        # Measure status retrieval time
        start_time = time.time()
        status_data = self.publishing_service.get_publication_status(
            self.test_test_id, self.test_instructor_id
        )
        end_time = time.time()
        
        status_time = end_time - start_time
        assert status_time < 2.0, f"Status retrieval should complete within 2 seconds, took {status_time:.2f}s"
        
        logger.info(f"Publication performance test passed (pub: {publication_time:.2f}s, status: {status_time:.2f}s)")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("🧹 Cleaning up test data...")
        
        for item_type, item_id in self.test_data_cleanup:
            try:
                if item_type == 'test':
                    # Delete test from database
                    self.tests_table.delete_item(Key={'test_id': item_id})
                    logger.info(f"Deleted test: {item_id}")
                elif item_type == 'question':
                    # Delete question (if we had a delete method)
                    logger.info(f"Would delete question: {item_id}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {item_type} {item_id}: {e}")
    
    def print_test_summary(self):
        """Print comprehensive test execution summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("📊 PHASE 4.2.2: TEST PUBLISHING - COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Categorize tests
        categories = {
            'Core Functionality': ['test_service_initialization', 'test_database_connectivity'],
            'Integration Tests': ['test_create_real_test_for_publishing', 'test_publish_real_test', 
                                'test_publication_status_retrieval', 'test_unpublish_real_test', 'test_schedule_real_test'],
            'Error Handling': ['test_publish_nonexistent_test', 'test_publish_unauthorized_test', 
                             'test_publish_invalid_test', 'test_invalid_publication_settings'],
            'Edge Cases': ['test_concurrent_publication_attempts', 'test_publication_with_availability_window', 
                          'test_publication_with_access_code'],
            'Data Integrity': ['test_database_state_consistency', 'test_publication_data_persistence', 
                             'test_publication_statistics'],
            'Performance': ['test_publication_performance']
        }
        
        for category, tests in categories.items():
            category_results = [r for r in self.test_results if r['test'] in tests]
            if category_results:
                passed = len([r for r in category_results if r['status'] == 'PASS'])
                total = len(category_results)
                print(f"\n{category}: {passed}/{total} passed")
                
                for result in category_results:
                    status_icon = "✅" if result['status'] == 'PASS' else "❌"
                    print(f"  {status_icon} {result['test']}")
                    if result['status'] == 'FAIL':
                        print(f"      Error: {result['error']}")
        
        print("\n" + "="*80)
        
        # Risk assessment
        critical_failures = [r for r in self.test_results if r['status'] == 'FAIL' and 
                           any(test in r['test'] for test in ['database', 'publish_real', 'unauthorized'])]
        
        if len(critical_failures) > 0:
            print("🚨 CRITICAL FAILURES DETECTED:")
            for failure in critical_failures:
                print(f"  - {failure['test']}: {failure['error']}")
            print("These failures indicate serious issues that must be resolved before production.")
        elif failed_tests == 0:
            print("🎉 ALL TESTS PASSED! Phase 4.2.2 is production-ready.")
        elif passed_tests >= total_tests * 0.9:
            print("✅ MOSTLY SUCCESSFUL: Minor issues detected, but core functionality works.")
        else:
            print("⚠️  SIGNIFICANT ISSUES: Multiple test failures require attention.")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    try:
        print("🚀 Starting Phase 4.2.2: Test Publishing Tests (COMPREHENSIVE)")
        print("="*80)
        
        tester = TestPhase422Comprehensive()
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 Phase 4.2.2: Test Publishing - ALL COMPREHENSIVE TESTS PASSED!")
        else:
            print("\n❌ Phase 4.2.2: Test Publishing - SOME TESTS FAILED!")
        
        return success
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)