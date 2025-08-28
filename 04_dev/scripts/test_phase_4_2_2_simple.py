#!/usr/bin/env python3
"""
Simplified Test Script for Phase 4.2.2: Test Publishing
Tests the core test publishing functionality with mock data.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.test_publishing_service import TestPublishingService, TestPublishingError
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPhase422Simple:
    """Simplified test class for Phase 4.2.2: Test Publishing"""
    
    def __init__(self):
        """Initialize test environment"""
        self.config = Config()
        self.test_results = []
        
        # Initialize services
        try:
            self.publishing_service = TestPublishingService()
            logger.info("✅ Publishing service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    def run_all_tests(self):
        """Run all Phase 4.2.2 tests"""
        logger.info("🚀 Starting Phase 4.2.2: Test Publishing Tests (Simplified)")
        
        test_methods = [
            self.test_service_initialization,
            self.test_publication_validation,
            self.test_publication_settings_validation,
            self.test_access_code_generation,
            self.test_availability_window_validation,
            self.test_publication_status_methods
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
        assert hasattr(self.publishing_service, 'publish_test'), "Publishing service should have publish_test method"
        assert hasattr(self.publishing_service, 'unpublish_test'), "Publishing service should have unpublish_test method"
        assert hasattr(self.publishing_service, 'schedule_test_publication'), "Publishing service should have schedule_test_publication method"
        assert hasattr(self.publishing_service, 'get_publication_status'), "Publishing service should have get_publication_status method"
        logger.info("Service initialization test passed")
    
    def test_publication_validation(self):
        """Test 2: Publication Validation"""
        # Test valid test data
        valid_test_data = {
            'title': 'Sample Test',
            'question_ids': ['q1', 'q2', 'q3'],
            'time_limit': 30,
            'passing_score': 70
        }
        
        validation_result = self.publishing_service._validate_test_for_publication(valid_test_data)
        assert validation_result['valid'], f"Valid test should pass validation: {validation_result['errors']}"
        
        # Test invalid test data
        invalid_test_data = {
            'title': '',  # Empty title
            'question_ids': [],  # No questions
            'time_limit': 0,  # Invalid time limit
            'passing_score': 150  # Invalid passing score
        }
        
        validation_result = self.publishing_service._validate_test_for_publication(invalid_test_data)
        assert not validation_result['valid'], "Invalid test should fail validation"
        assert len(validation_result['errors']) > 0, "Validation errors should be provided"
        
        logger.info("Publication validation test passed")
    
    def test_publication_settings_validation(self):
        """Test 3: Publication Settings Validation"""
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
        
        # Test invalid max_students
        invalid_max_students = {
            'max_students': -5
        }
        
        validation_result = self.publishing_service._validate_publication_settings(invalid_max_students)
        assert not validation_result['valid'], "Negative max_students should fail validation"
        
        logger.info("Publication settings validation test passed")
    
    def test_access_code_generation(self):
        """Test 4: Access Code Generation"""
        test_id = "test_123"
        
        # Generate multiple access codes to ensure uniqueness
        codes = set()
        for _ in range(10):
            code = self.publishing_service._generate_access_code(test_id)
            assert len(code) >= 6, "Access code should be at least 6 characters"
            assert code.replace('0', '').replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '').replace('6', '').replace('7', '').replace('8', '').replace('9', '').replace('A', '').replace('B', '').replace('C', '').replace('D', '').replace('E', '').replace('F', '') == '', "Access code should be alphanumeric"
            codes.add(code)
        
        # Codes should be unique (with high probability)
        assert len(codes) > 1, "Generated codes should be unique"
        
        logger.info("Access code generation test passed")
    
    def test_availability_window_validation(self):
        """Test 5: Availability Window Validation"""
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
        
        # Test unpublished status
        publication_data = {
            'publication_status': 'draft'
        }
        
        is_available = self.publishing_service._is_test_available_now(publication_data)
        assert not is_available, "Unpublished test should not be available"
        
        logger.info("Availability window validation test passed")
    
    def test_publication_status_methods(self):
        """Test 6: Publication Status Methods"""
        # Test _can_test_be_published
        valid_test_data = {
            'title': 'Sample Test',
            'question_ids': ['q1', 'q2'],
            'time_limit': 30,
            'passing_score': 70
        }
        
        can_publish = self.publishing_service._can_test_be_published(valid_test_data)
        assert can_publish, "Valid test should be publishable"
        
        invalid_test_data = {
            'title': '',
            'question_ids': [],
            'time_limit': 0,
            'passing_score': 150
        }
        
        can_publish = self.publishing_service._can_test_be_published(invalid_test_data)
        assert not can_publish, "Invalid test should not be publishable"
        
        # Test _get_publication_statistics
        stats = self.publishing_service._get_publication_statistics('test_123')
        assert isinstance(stats, dict), "Statistics should be a dictionary"
        assert 'total_attempts' in stats, "Statistics should include total_attempts"
        assert 'completed_attempts' in stats, "Statistics should include completed_attempts"
        assert 'average_score' in stats, "Statistics should include average_score"
        assert 'unique_students' in stats, "Statistics should include unique_students"
        
        # Test _check_active_attempts
        active_attempts = self.publishing_service._check_active_attempts('test_123')
        assert isinstance(active_attempts, int), "Active attempts should be an integer"
        assert active_attempts >= 0, "Active attempts should be non-negative"
        
        logger.info("Publication status methods test passed")
    
    def print_test_summary(self):
        """Print test execution summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("📊 PHASE 4.2.2: TEST PUBLISHING - TEST SUMMARY (SIMPLIFIED)")
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
            print("🎉 ALL TESTS PASSED! Phase 4.2.2 core functionality is working correctly.")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️  Most tests passed, but some issues need attention.")
        else:
            print("❌ Multiple test failures detected. Implementation needs review.")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    try:
        print("🚀 Starting Phase 4.2.2: Test Publishing Tests (Simplified)")
        print("="*80)
        
        tester = TestPhase422Simple()
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 Phase 4.2.2: Test Publishing - ALL CORE TESTS PASSED!")
            return True
        else:
            print("\n❌ Phase 4.2.2: Test Publishing - SOME TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()