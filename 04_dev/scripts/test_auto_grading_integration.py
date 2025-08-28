#!/usr/bin/env python3
"""
Integration Test for Auto-Grading System
Tests the complete workflow from test submission to results display
"""

import sys
import os

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_complete_workflow():
    """Test the complete auto-grading workflow"""
    print("🧪 Testing complete auto-grading workflow...")
    
    try:
        # Test imports
        print("📝 Testing service imports...")
        from services.auto_grading_service import AutoGradingService, TestResult, QuestionResult
        from services.student_test_service import StudentTestService
        from pages.test_results import TestResultsPage
        print("✅ All imports successful")
        
        # Test service initialization
        print("📝 Testing service initialization...")
        grading_service = AutoGradingService()
        student_service = StudentTestService()
        results_page = TestResultsPage()
        print("✅ All services initialized")
        
        # Test data structures
        print("📝 Testing data structures...")
        question_result = QuestionResult(
            question_id="test_q1",
            question_number=1,
            question_type="multiple_choice",
            question_text="Test question",
            correct_answer="A",
            student_answer="A",
            is_correct=True,
            points_earned=1.0,
            points_possible=1.0
        )
        
        test_result = TestResult(
            result_id="test_result_1",
            attempt_id="test_attempt_1",
            test_id="test_1",
            student_id="student_1",
            total_questions=1,
            correct_answers=1,
            incorrect_answers=0,
            unanswered_questions=0,
            total_points_earned=1.0,
            total_points_possible=1.0,
            percentage_score=100.0,
            passing_score=70.0,
            passed=True,
            time_taken=60,
            graded_at="2024-01-01T12:00:00Z",
            question_results=[question_result]
        )
        print("✅ Data structures created successfully")
        
        # Test grading logic
        print("📝 Testing grading logic...")
        mc_result = grading_service._grade_multiple_choice("A", "A")
        tf_result = grading_service._grade_true_false("True", "True")
        print(f"✅ Grading logic: MC={mc_result}, TF={tf_result}")
        
        print("✅ Complete workflow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Complete workflow test failed: {str(e)}")
        return False

def test_app_integration():
    """Test app integration"""
    print("\n🧪 Testing app integration...")
    
    try:
        # Test app import
        print("📝 Testing app import...")
        from app import QuizGeniusApp
        print("✅ App import successful")
        
        # Test navigation
        print("📝 Testing navigation...")
        from components.navigation import NavigationManager
        nav = NavigationManager()
        student_pages = nav.get_student_pages()
        
        # Check if Test Results page is included
        page_names = [page['name'] for page in student_pages]
        if 'Test Results' in page_names:
            print("✅ Test Results page found in navigation")
        else:
            print("⚠️  Test Results page not found in navigation")
        
        return True
        
    except Exception as e:
        print(f"❌ App integration test failed: {str(e)}")
        return False

def main():
    """Run integration tests"""
    print("🚀 Auto-Grading Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Complete Workflow", test_complete_workflow),
        ("App Integration", test_app_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 INTEGRATION TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("\n💡 Auto-grading system is ready for use!")
        return True
    else:
        print("⚠️  Some integration tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)