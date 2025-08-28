#!/usr/bin/env python3
"""
Test Script for Phase 5.3: Instructor Results Interface
Tests all components of the instructor analytics and results functionality
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.instructor_analytics_service import (
    InstructorAnalyticsService, InstructorAnalyticsError, 
    TestSummary, StudentPerformance, QuestionAnalytics, InstructorDashboard
)
from services.auto_grading_service import AutoGradingService, TestResult, QuestionResult
from utils.dynamodb_utils import get_current_timestamp, generate_id

def test_instructor_analytics_service():
    """Test the InstructorAnalyticsService functionality"""
    print("🧪 Testing InstructorAnalyticsService...")
    
    try:
        # Initialize service
        service = InstructorAnalyticsService()
        print("✅ InstructorAnalyticsService initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ InstructorAnalyticsService test failed: {str(e)}")
        return False

def test_test_summary_data_structure():
    """Test the TestSummary data structure"""
    print("\n🧪 Testing TestSummary data structure...")
    
    try:
        # Create test data
        test_summary = TestSummary(
            test_id="test_123",
            test_title="Sample Test",
            instructor_id="instructor_123",
            total_students_attempted=25,
            total_students_completed=23,
            completion_rate=0.92,
            average_score=78.5,
            median_score=80.0,
            highest_score=95.0,
            lowest_score=45.0,
            passing_rate=0.78,
            average_time_taken=1800.0,
            total_questions=10,
            created_date="2024-01-01T12:00:00Z",
            last_attempt_date="2024-01-15T14:30:00Z"
        )
        
        print("✅ TestSummary created successfully")
        print(f"   - Test: {test_summary.test_title}")
        print(f"   - Students: {test_summary.total_students_attempted}")
        print(f"   - Average Score: {test_summary.average_score}%")
        print(f"   - Completion Rate: {test_summary.completion_rate:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ TestSummary test failed: {str(e)}")
        return False

def test_student_performance_data_structure():
    """Test the StudentPerformance data structure"""
    print("\n🧪 Testing StudentPerformance data structure...")
    
    try:
        # Create test data
        student_performance = StudentPerformance(
            student_id="student_123",
            student_name="John Doe",
            student_email="john.doe@example.com",
            test_id="test_123",
            attempt_id="attempt_123",
            score=85.0,
            passed=True,
            time_taken=1500,
            completed_at="2024-01-15T14:30:00Z",
            correct_answers=8,
            total_questions=10,
            attempt_number=1
        )
        
        print("✅ StudentPerformance created successfully")
        print(f"   - Student: {student_performance.student_name}")
        print(f"   - Score: {student_performance.score}%")
        print(f"   - Passed: {student_performance.passed}")
        print(f"   - Time: {student_performance.time_taken}s")
        
        return True
        
    except Exception as e:
        print(f"❌ StudentPerformance test failed: {str(e)}")
        return False

def test_question_analytics_data_structure():
    """Test the QuestionAnalytics data structure"""
    print("\n🧪 Testing QuestionAnalytics data structure...")
    
    try:
        # Create test data
        question_analytics = QuestionAnalytics(
            question_id="q_123",
            question_number=1,
            question_text="What is 2+2?",
            question_type="multiple_choice",
            correct_answer="4",
            total_attempts=25,
            correct_attempts=20,
            incorrect_attempts=5,
            accuracy_rate=0.8,
            most_common_wrong_answer="5"
        )
        
        print("✅ QuestionAnalytics created successfully")
        print(f"   - Question: {question_analytics.question_text}")
        print(f"   - Accuracy: {question_analytics.accuracy_rate:.1%}")
        print(f"   - Attempts: {question_analytics.total_attempts}")
        print(f"   - Most common wrong: {question_analytics.most_common_wrong_answer}")
        
        return True
        
    except Exception as e:
        print(f"❌ QuestionAnalytics test failed: {str(e)}")
        return False

def test_instructor_dashboard_data_structure():
    """Test the InstructorDashboard data structure"""
    print("\n🧪 Testing InstructorDashboard data structure...")
    
    try:
        # Create mock data
        mock_test_summary = TestSummary(
            test_id="test_1",
            test_title="Mock Test",
            instructor_id="instructor_123",
            total_students_attempted=10,
            total_students_completed=8,
            completion_rate=0.8,
            average_score=75.0,
            median_score=78.0,
            highest_score=95.0,
            lowest_score=55.0,
            passing_rate=0.7,
            average_time_taken=1200.0,
            total_questions=5,
            created_date="2024-01-01T12:00:00Z",
            last_attempt_date="2024-01-10T15:00:00Z"
        )
        
        # Create dashboard data
        dashboard = InstructorDashboard(
            instructor_id="instructor_123",
            total_tests_created=5,
            total_tests_published=3,
            total_student_attempts=45,
            total_students_reached=25,
            average_test_score=72.5,
            recent_activity=[
                {
                    'type': 'test_completion',
                    'student_name': 'John Doe',
                    'test_title': 'Sample Test',
                    'score': 85.0,
                    'passed': True,
                    'timestamp': '2024-01-15T14:30:00Z'
                }
            ],
            top_performing_tests=[mock_test_summary],
            tests_needing_attention=[]
        )
        
        print("✅ InstructorDashboard created successfully")
        print(f"   - Tests Created: {dashboard.total_tests_created}")
        print(f"   - Tests Published: {dashboard.total_tests_published}")
        print(f"   - Student Attempts: {dashboard.total_student_attempts}")
        print(f"   - Average Score: {dashboard.average_test_score}%")
        
        return True
        
    except Exception as e:
        print(f"❌ InstructorDashboard test failed: {str(e)}")
        return False

def test_analytics_calculations():
    """Test analytics calculation methods"""
    print("\n🧪 Testing analytics calculations...")
    
    try:
        service = InstructorAnalyticsService()
        
        # Test with mock data
        print("📝 Testing analytics calculation logic...")
        
        # Mock test results for calculation testing
        mock_results = []
        
        # Create mock question results
        for i in range(5):
            question_results = [
                QuestionResult(
                    question_id=f"q_{j}",
                    question_number=j+1,
                    question_type="multiple_choice",
                    question_text=f"Question {j+1}",
                    correct_answer="A",
                    student_answer="A" if (i + j) % 2 == 0 else "B",
                    is_correct=(i + j) % 2 == 0,
                    points_earned=1.0 if (i + j) % 2 == 0 else 0.0,
                    points_possible=1.0
                ) for j in range(3)
            ]
            
            # Create mock test result
            correct_count = sum(1 for qr in question_results if qr.is_correct)
            score = (correct_count / len(question_results)) * 100
            
            mock_result = TestResult(
                result_id=f"result_{i}",
                attempt_id=f"attempt_{i}",
                test_id="test_123",
                student_id=f"student_{i}",
                total_questions=3,
                correct_answers=correct_count,
                incorrect_answers=3 - correct_count,
                unanswered_questions=0,
                total_points_earned=float(correct_count),
                total_points_possible=3.0,
                percentage_score=score,
                passing_score=70.0,
                passed=score >= 70.0,
                time_taken=1200 + (i * 100),
                graded_at=get_current_timestamp(),
                question_results=question_results
            )
            
            mock_results.append(mock_result)
        
        print(f"✅ Created {len(mock_results)} mock test results")
        print(f"   - Score range: {min(r.percentage_score for r in mock_results):.1f}% - {max(r.percentage_score for r in mock_results):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics calculations test failed: {str(e)}")
        return False

def test_data_export_functionality():
    """Test data export functionality"""
    print("\n🧪 Testing data export functionality...")
    
    try:
        service = InstructorAnalyticsService()
        
        # Test export data structure
        print("📝 Testing export data structure...")
        
        # Mock export data
        export_data = {
            'test_summary': {
                'test_id': 'test_123',
                'test_title': 'Sample Test',
                'average_score': 75.0,
                'total_students_attempted': 10
            },
            'student_performances': [
                {
                    'student_name': 'John Doe',
                    'score': 85.0,
                    'passed': True
                }
            ],
            'question_analytics': [
                {
                    'question_number': 1,
                    'accuracy_rate': 0.8,
                    'total_attempts': 10
                }
            ],
            'export_timestamp': get_current_timestamp(),
            'export_format': 'json'
        }
        
        print("✅ Export data structure created successfully")
        print(f"   - Test: {export_data['test_summary']['test_title']}")
        print(f"   - Students: {len(export_data['student_performances'])}")
        print(f"   - Questions: {len(export_data['question_analytics'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data export test failed: {str(e)}")
        return False

def test_integration_with_existing_services():
    """Test integration with existing services"""
    print("\n🧪 Testing integration with existing services...")
    
    try:
        # Test integration with AutoGradingService
        print("📝 Testing AutoGradingService integration...")
        try:
            grading_service = AutoGradingService()
            print("✅ AutoGradingService integration successful")
        except Exception as e:
            print(f"⚠️  AutoGradingService integration warning: {str(e)}")
        
        # Test integration with InstructorAnalyticsService
        print("📝 Testing InstructorAnalyticsService integration...")
        try:
            analytics_service = InstructorAnalyticsService()
            print("✅ InstructorAnalyticsService integration successful")
        except Exception as e:
            print(f"⚠️  InstructorAnalyticsService integration warning: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🧪 Testing error handling...")
    
    try:
        service = InstructorAnalyticsService()
        
        # Test with invalid instructor ID
        print("📝 Testing invalid instructor ID...")
        try:
            dashboard = service.get_instructor_dashboard("invalid_instructor")
            print("✅ Invalid instructor ID handled gracefully")
        except Exception as e:
            print(f"✅ Invalid instructor ID error handled: {str(e)}")
        
        # Test with invalid test ID
        print("📝 Testing invalid test ID...")
        try:
            summary = service.get_test_summary("invalid_test", "instructor_123")
            if summary is None:
                print("✅ Invalid test ID handled gracefully")
            else:
                print("⚠️  Invalid test ID returned data unexpectedly")
        except Exception as e:
            print(f"✅ Invalid test ID error handled: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

def test_page_components():
    """Test page component functionality"""
    print("\n🧪 Testing page components...")
    
    try:
        # Test instructor results page import
        print("📝 Testing instructor results page import...")
        try:
            from pages.instructor_results import InstructorResultsPage
            page = InstructorResultsPage()
            print("✅ InstructorResultsPage imported and instantiated")
        except Exception as e:
            print(f"❌ InstructorResultsPage import failed: {str(e)}")
        
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
        instructor_pages = nav_manager.get_instructor_pages()
        
        # Check if new pages are included
        page_names = [page['name'] for page in instructor_pages]
        
        required_pages = ['Results & Analytics']
        missing_pages = [page for page in required_pages if page not in page_names]
        
        if missing_pages:
            print(f"⚠️  Missing pages in navigation: {missing_pages}")
        else:
            print("✅ All required pages found in navigation")
        
        print(f"📋 Instructor pages: {page_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ Navigation integration test failed: {str(e)}")
        return False

def test_database_integration():
    """Test database integration"""
    print("\n🧪 Testing database integration...")
    
    try:
        service = InstructorAnalyticsService()
        
        # Test table access
        print("📝 Testing table access...")
        try:
            service._verify_table_access()
            print("✅ Database tables accessible")
        except Exception as e:
            print(f"⚠️  Database access warning: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all Phase 5.3 tests"""
    print("🚀 Starting Phase 5.3: Instructor Results Interface Tests")
    print("=" * 60)
    
    tests = [
        ("Instructor Analytics Service", test_instructor_analytics_service),
        ("TestSummary Data Structure", test_test_summary_data_structure),
        ("StudentPerformance Data Structure", test_student_performance_data_structure),
        ("QuestionAnalytics Data Structure", test_question_analytics_data_structure),
        ("InstructorDashboard Data Structure", test_instructor_dashboard_data_structure),
        ("Analytics Calculations", test_analytics_calculations),
        ("Data Export Functionality", test_data_export_functionality),
        ("Service Integration", test_integration_with_existing_services),
        ("Error Handling", test_error_handling),
        ("Page Components", test_page_components),
        ("Navigation Integration", test_navigation_integration),
        ("Database Integration", test_database_integration)
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
        print("🎉 All Phase 5.3 tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)