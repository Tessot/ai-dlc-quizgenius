#!/usr/bin/env python3
"""
Test Script for Phase 4.2.2: Test Publishing
Tests the test publishing functionality including publication controls and status management.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.test_publishing_service import TestPublishingService, TestPublishingError
from services.test_creation_service import TestCreationService, TestCreationError
from services.question_storage_service import QuestionStorageService
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPhase422:
    """Test class for Phase 4.2.2: Test Publishing"""
    
    def __init__(self):
        """Initialize test environment"""
        self.config = Config()
        self.test_results = []
        self.test_instructor_id = "test_instructor_422"
        self.test_test_id = None
        
        # Initialize services
        try:
            self.publishing_service = TestPublishingService()
            self.test_service = TestCreationService()
            self.question_service = QuestionStorageService()
            logger.info("✅ Services initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    def run_all_tests(self):
        """Run all Phase 4.2.2 tests"""
        logger.info("🚀 Starting Phase 4.2.2: Test Publishing Tests")
        
        test_methods = [
            self.test_service_initialization,
            self.test_create_test_for_publishing,
            self.test_publication_validation,
            self.test_publish_test,
            self.test_publication_status,
            self.test_schedule_publication,
            self.test_unpublish_test,
            self.test_publication_settings_validation,
            self.test_access_code_generation,
            self.test_availability_window_validation
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"Running {test_method.__name__}...")
                test_method()
                self.test_results.append({"test": test_method.__name__, "status": "PASS", "error": None})
                logger.info(f"✅ {test_method.__name__} PASSED")
            except Exception as e:
                self.test_results.append({"test": test_method.__name__, "status": "FAIL", "error": str(e)})
                logger.error(f"❌ {test_method.__name__} FAILED: {e}")
        
        self.print_test_summary()
    
    def test_service_initialization(self):
        """Test 1: Service Initialization"""
        assert self.publishing_service is not None, "Publishing service should be initialized"
        assert self.test_service is not None, "Test service should be initialized"
        assert hasattr(self.publishing_service, 'publish_test'), "Publishing service should have publish_test method"
        assert hasattr(self.publishing_service, 'unpublish_test'), "Publishing service should have unpublish_test method"
        assert hasattr(self.publishing_service, 'schedule_test_publication'), "Publishing service should have schedule_test_publication method"
        logger.info("Service initialization test passed")
    
    def test_create_test_for_publishing(self):
        """Test 2: Create Test for Publishing"""
        # First create some questions using the question processor
        from services.question_processor import QuestionProcessor, GeneratedQuestion
        
        # Create a GeneratedQuestion object
        from decimal import Decimal
        generated_question = GeneratedQuestion(
            question_id='test_q_422_1',
            question_text='What is the capital of France?',
            question_type='multiple_choice',
            options=['London', 'Berlin', 'Paris', 'Madrid'],
            correct_answer='Paris',
            difficulty_level='easy',
            topic='Geography',
            source_content='Test content for publishing',
            confidence_score=Decimal('0.9'),
            metadata={'test': True}
        )
        
        question_result = self.question_service.store_question(
            generated_question, 'test_doc_422', self.test_instructor_id
        )
        assert question_result['success'], f"Question creation failed: {question_result.get('error')}"
        question_id = question_result['question_id']
        
        # Create test
        test_data = {
            'title': 'Test Publishing Sample Test',
            'description': 'A test created for testing publishing functionality',
            'question_ids': [question_id],
            'time_limit': 30,
            'passing_score': 70,
            'attempts_allowed': 2,
            'randomize_questions': True,
            'show_results_immediately': True
        }
        
        test_result = self.test_service.create_test(test_data, self.test_instructor_id)
        assert test_result['success'], f"Test creation failed: {test_result.get('error')}"
        
        self.test_test_id = test_result['test_id']
        logger.info(f"Created test for publishing: {self.test_test_id}")
    
    def test_publication_validation(self):
        """Test 3: Publication Validation"""
        assert self.test_test_id is not None, "Test ID should be available"
        
        # Get test data
        test_data = self.test_service.get_test_by_id(self.test_test_id)
        assert test_data is not None, "Test data should be retrievable"
        
        # Test validation
        validation_result = self.publishing_service._validate_test_for_publication(test_data)
        assert validation_result['valid'], f"Test should be valid for publication: {validation_result['errors']}"
        logger.info("Publication validation test passed")
    
    def test_publish_test(self):
        """Test 4: Publish Test"""
        assert self.test_test_id is not None, "Test ID should be available"
        
        publication_settings = {
            'auto_grade': True,
            'results_visible_to_students': True,
            'allow_late_submissions': False,
            'require_access_code': True,
            'notes': 'Test publication for Phase 4.2.2'
        }
        
        result = self.publishing_service.publish_test(
            self.test_test_id, self.test_instructor_id, publication_settings
        )
        
        assert result['success'], f"Test publication failed: {result}"
        assert result['publication_status'] == 'published', "Test should be marked as published"
        assert result['access_code'] is not None, "Access code should be generated"
        assert 'published_at' in result, "Publication timestamp should be included"
        
        logger.info(f"Test published successfully with access code: {result['access_code']}")
    
    def test_publication_status(self):
        """Test 5: Publication Status"""
        assert self.test_test_id is not None, "Test ID should be available"
        
        status_data = self.publishing_service.get_publication_status(
            self.test_test_id, self.test_instructor_id
        )
        
        assert status_data['test_id'] == self.test_test_id, "Test ID should match"
        assert status_data['publication_status'] == 'published', "Status should be published"
        assert 'publication_data' in status_data, "Publication data should be included"
        assert 'statistics' in status_data, "Statistics should be included"
        assert 'is_available_now' in status_data, "Availability status should be included"
        
        logger.info("Publication status test passed")
    
    def test_schedule_publication(self):
        """Test 6: Schedule Publication"""
        # Create another test for scheduling
        from services.question_processor import GeneratedQuestion
        
        from decimal import Decimal
        generated_question = GeneratedQuestion(
            question_id='test_q_422_2',
            question_text='What is 2 + 2?',
            question_type='multiple_choice',
            options=['3', '4', '5', '6'],
            correct_answer='4',
            difficulty_level='easy',
            topic='Mathematics',
            source_content='Test content for scheduling',
            confidence_score=Decimal('0.95'),
            metadata={'test': True}
        )
        
        question_result = self.question_service.store_question(
            generated_question, 'test_doc_422_sched', self.test_instructor_id
        )
        assert question_result['success'], "Question creation should succeed"
        
        test_data = {
            'title': 'Scheduled Test',
            'description': 'A test for testing scheduling functionality',
            'question_ids': [question_result['question_id']],
            'time_limit': 15,
            'passing_score': 80,
            'attempts_allowed': 1
        }
        
        test_result = self.test_service.create_test(test_data, self.test_instructor_id)
        assert test_result['success'], "Test creation should succeed"
        scheduled_test_id = test_result['test_id']
        
        # Schedule publication for tomorrow
        future_time = datetime.now() + timedelta(days=1)
        schedule_settings = {
            'publish_at': future_time.isoformat(),
            'auto_grade': True,
            'results_visible_to_students': False,
            'notes': 'Scheduled publication test'
        }
        
        result = self.publishing_service.schedule_test_publication(
            scheduled_test_id, self.test_instructor_id, schedule_settings
        )
        
        assert result['success'], f"Test scheduling failed: {result}"
        assert result['publication_status'] == 'scheduled', "Test should be marked as scheduled"
        assert 'scheduled_at' in result, "Scheduling timestamp should be included"
        assert 'publish_at' in result, "Publication time should be included"
        
        logger.info(f"Test scheduled successfully for: {result['publish_at']}")
    
    def test_unpublish_test(self):
        """Test 7: Unpublish Test"""
        assert self.test_test_id is not None, "Test ID should be available"
        
        result = self.publishing_service.unpublish_test(
            self.test_test_id, self.test_instructor_id, "Testing unpublish functionality"
        )
        
        assert result['success'], f"Test unpublishing failed: {result}"
        assert result['publication_status'] == 'unpublished', "Test should be marked as unpublished"
        assert 'unpublished_at' in result, "Unpublication timestamp should be included"
        
        # Verify status change
        status_data = self.publishing_service.get_publication_status(
            self.test_test_id, self.test_instructor_id
        )
        assert status_data['publication_status'] == 'draft', "Test status should be reverted to draft"
        
        logger.info("Test unpublished successfully")
    
    def test_publication_settings_validation(self):
        """Test 8: Publication Settings Validation"""
        # Test invalid availability window
        invalid_settings = {
            'available_from': '2024-12-31T23:59:59',
            'available_until': '2024-01-01T00:00:00'  # Before available_from
        }
        
        validation_result = self.publishing_service._validate_publication_settings(invalid_settings)
        assert not validation_result['valid'], "Invalid settings should fail validation"
        assert len(validation_result['errors']) > 0, "Validation errors should be provided"
        
        # Test valid settings
        valid_settings = {
            'available_from': '2024-01-01T00:00:00',
            'available_until': '2024-12-31T23:59:59',
            'max_students': 50
        }
        
        validation_result = self.publishing_service._validate_publication_settings(valid_settings)
        assert validation_result['valid'], f"Valid settings should pass validation: {validation_result['errors']}"
        
        logger.info("Publication settings validation test passed")
    
    def test_access_code_generation(self):
        """Test 9: Access Code Generation"""
        test_id = "test_123"
        
        # Generate multiple access codes to ensure uniqueness
        codes = set()
        for _ in range(10):
            code = self.publishing_service._generate_access_code(test_id)
            assert len(code) >= 6, "Access code should be at least 6 characters"
            assert code.isalnum(), "Access code should be alphanumeric"
            codes.add(code)
        
        # Codes should be unique (with high probability)
        assert len(codes) > 1, "Generated codes should be unique"
        
        logger.info("Access code generation test passed")
    
    def test_availability_window_validation(self):
        """Test 10: Availability Window Validation"""
        # Test current availability
        publication_data = {
            'publication_status': 'published'
        }
        
        is_available = self.publishing_service._is_test_available_now(publication_data)
        assert is_available, "Test without time restrictions should be available"
        
        # Test future availability
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        publication_data = {
            'publication_status': 'published',
            'available_from': future_time
        }
        
        is_available = self.publishing_service._is_test_available_now(publication_data)
        assert not is_available, "Test with future start time should not be available"
        
        # Test past availability
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        publication_data = {
            'publication_status': 'published',
            'available_until': past_time
        }
        
        is_available = self.publishing_service._is_test_available_now(publication_data)
        assert not is_available, "Test with past end time should not be available"
        
        logger.info("Availability window validation test passed")
    
    def print_test_summary(self):
        """Print test execution summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("📊 PHASE 4.2.2: TEST PUBLISHING - TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['error']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["status"] == "PASS":
                print(f"  - {result['test']}")
        
        print("="*80)
        
        # Overall assessment
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Phase 4.2.2 implementation is working correctly.")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️  Most tests passed, but some issues need attention.")
        else:
            print("❌ Multiple test failures detected. Implementation needs review.")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    try:
        print("🚀 Starting Phase 4.2.2: Test Publishing Tests")
        print("="*80)
        
        tester = TestPhase422()
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 Phase 4.2.2: Test Publishing - ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print("\n❌ Phase 4.2.2: Test Publishing - SOME TESTS FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()