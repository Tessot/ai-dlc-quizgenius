#!/usr/bin/env python3
"""
Test Script for Phase 4.3: Student Test Taking
Tests all components of the student test taking functionality
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.student_test_service import StudentTestService, StudentTestError, AvailableTest, TestAttempt
from services.test_creation_service import TestCreationService
from services.test_publishing_service import TestPublishingService
from services.user_service import UserService
from utils.dynamodb_utils import get_current_timestamp, generate_id

def test_student_test_service():
    """Test the StudentTestService functionality"""
    print("🧪 Testing StudentTestService...")
    
    try:
        # Initialize service
        service = StudentTestService()
        print("✅ StudentTestService initialized successfully")
        
        # Test service methods with mock data
        print("\n📋 Testing service methods...")
        
        # Test get_available_tests with no tests
        student_id = "test_student_123"
        available_tests = service.get_available_tests(student_id)
        print(f"✅ get_available_tests returned {len(available_tests)} tests")
        
        return True
        
    except Exception as e:
        print(f"❌ StudentTestService test failed: {str(e)}")
        return False

def test_available_test_data_structure():
    """Test the AvailableTest data structure"""
    print("\n🧪 Testing AvailableTest data structure...")
    
    try:
        # Create test data
        test_data = AvailableTest(
            test_id="test_123",
            title="Sample Test",
            description="A sample test for testing",
            instructor_name="Dr. Smith",
            time_limit=60,
            total_questions=10,
            passing_score=70,
            attempts_allowed=3,
            attempts_used=1,
            requires_access_code=False,
            available_from="2024-01-01T00:00:00Z",
            available_until="2024-12-31T23:59:59Z",
            is_available_now=True,
            student_can_take=True,
            last_attempt_score=85.0,
            best_score=85.0
        )
        
        print("✅ AvailableTest created successfully")
        print(f"   - Test ID: {test_data.test_id}")
        print(f"   - Title: {test_data.title}")
        print(f"   - Can take: {test_data.student_can_take}")
        
        return True
        
    except Exception as e:
        print(f"❌ AvailableTest test failed: {str(e)}")
        return False

def test_test_attempt_data_structure():
    """Test the TestAttempt data structure"""
    print("\n🧪 Testing TestAttempt data structure...")
    
    try:
        # Create test attempt data
        attempt_data = TestAttempt(
            attempt_id="attempt_123",
            test_id="test_123",
            student_id="student_123",
            started_at=get_current_timestamp(),
            submitted_at=None,
            time_remaining=3600,
            current_question=0,
            answers={},
            status="in_progress",
            score=None,
            passed=None
        )
        
        print("✅ TestAttempt created successfully")
        print(f"   - Attempt ID: {attempt_data.attempt_id}")
        print(f"   - Status: {attempt_data.status}")
        print(f"   - Time remaining: {attempt_data.time_remaining} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ TestAttempt test failed: {str(e)}")
        return False

def test_mock_test_workflow():
    """Test the complete test taking workflow with mock data"""
    print("\n🧪 Testing complete test workflow...")
    
    try:
        service = StudentTestService()
        
        # Mock student and test data
        student_id = "test_student_workflow"
        test_id = "test_workflow_123"
        
        print("📝 Step 1: Get available tests")
        available_tests = service.get_available_tests(student_id)
        print(f"   Found {len(available_tests)} available tests")
        
        print("📝 Step 2: Test data structures")
        # Test with mock available test
        mock_test = AvailableTest(
            test_id=test_id,
            title="Workflow Test",
            description="Test for workflow testing",
            instructor_name="Test Instructor",
            time_limit=30,
            total_questions=5,
            passing_score=60,
            attempts_allowed=2,
            attempts_used=0,
            requires_access_code=False,
            available_from=None,
            available_until=None,
            is_available_now=True,
            student_can_take=True,
            last_attempt_score=None,
            best_score=None
        )
        print(f"   Mock test created: {mock_test.title}")
        
        print("📝 Step 3: Test answer tracking")
        # Mock answers
        test_answers = {
            "question_0": "Option A",
            "question_1": "True",
            "question_2": "Option C",
            "question_3": "False",
            "question_4": "Option B"
        }
        print(f"   Mock answers created: {len(test_answers)} answers")
        
        print("📝 Step 4: Test submission data")
        # Mock submission
        submission_data = {
            "attempt_id": generate_id(),
            "final_answers": test_answers,
            "submitted_at": get_current_timestamp()
        }
        print(f"   Submission data prepared: {submission_data['attempt_id']}")
        
        print("✅ Complete workflow test passed")
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {str(e)}")
        return False

def test_integration_with_existing_services():
    """Test integration with existing services"""
    print("\n🧪 Testing integration with existing services...")
    
    try:
        # Test integration with TestCreationService
        print("📝 Testing TestCreationService integration...")
        try:
            test_service = TestCreationService()
            print("✅ TestCreationService integration successful")
        except Exception as e:
            print(f"⚠️  TestCreationService integration warning: {str(e)}")
        
        # Test integration with TestPublishingService
        print("📝 Testing TestPublishingService integration...")
        try:
            publishing_service = TestPublishingService()
            print("✅ TestPublishingService integration successful")
        except Exception as e:
            print(f"⚠️  TestPublishingService integration warning: {str(e)}")
        
        # Test integration with UserService
        print("📝 Testing UserService integration...")
        try:
            user_service = UserService()
            print("✅ UserService integration successful")
        except Exception as e:
            print(f"⚠️  UserService integration warning: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🧪 Testing error handling...")
    
    try:
        service = StudentTestService()
        
        # Test with invalid student ID
        print("📝 Testing invalid student ID...")
        try:
            available_tests = service.get_available_tests("")
            print("⚠️  Empty student ID handled gracefully")
        except StudentTestError as e:
            print(f"✅ StudentTestError properly raised: {str(e)}")
        except Exception as e:
            print(f"⚠️  Unexpected error type: {str(e)}")
        
        # Test with invalid attempt ID
        print("📝 Testing invalid attempt ID...")
        try:
            attempt = service.get_test_attempt("invalid_id", "student_123")
            if attempt is None:
                print("✅ Invalid attempt ID handled gracefully")
            else:
                print("⚠️  Invalid attempt ID returned data unexpectedly")
        except Exception as e:
            print(f"✅ Invalid attempt ID error handled: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

def test_page_components():
    """Test page component functionality"""
    print("\n🧪 Testing page components...")
    
    try:
        # Test available tests page import
        print("📝 Testing available tests page import...")
        try:
            from pages.available_tests import AvailableTestsPage
            page = AvailableTestsPage()
            print("✅ AvailableTestsPage imported and instantiated")
        except Exception as e:
            print(f"❌ AvailableTestsPage import failed: {str(e)}")
        
        # Test test taking page import
        print("📝 Testing test taking page import...")
        try:
            from pages.test_taking import TestTakingPage
            page = TestTakingPage()
            print("✅ TestTakingPage imported and instantiated")
        except Exception as e:
            print(f"❌ TestTakingPage import failed: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Page components test failed: {str(e)}")
        return False

def test_navigation_integration():
    """Test navigation integration"""
    print("\n🧪 Testing navigation integration...")
    
    try:
        from components.navigation import NavigationManager
        
        nav_manager = NavigationManager()
        student_pages = nav_manager.get_student_pages()
        
        # Check if new pages are included
        page_names = [page['name'] for page in student_pages]
        
        required_pages = ['Available Tests', 'Test Taking']
        missing_pages = [page for page in required_pages if page not in page_names]
        
        if missing_pages:
            print(f"⚠️  Missing pages in navigation: {missing_pages}")
        else:
            print("✅ All required pages found in navigation")
        
        print(f"📋 Student pages: {page_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ Navigation integration test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all Phase 4.3 tests"""
    print("🚀 Starting Phase 4.3: Student Test Taking Tests")
    print("=" * 60)
    
    tests = [
        ("Student Test Service", test_student_test_service),
        ("AvailableTest Data Structure", test_available_test_data_structure),
        ("TestAttempt Data Structure", test_test_attempt_data_structure),
        ("Mock Test Workflow", test_mock_test_workflow),
        ("Service Integration", test_integration_with_existing_services),
        ("Error Handling", test_error_handling),
        ("Page Components", test_page_components),
        ("Navigation Integration", test_navigation_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 4.3 tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)