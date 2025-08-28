#!/usr/bin/env python3
"""
Phase 5.4.1: End-to-End Testing Script
Comprehensive system integration testing for QuizGenius MVP
Tests complete workflows from PDF upload to student results
"""

import sys
import os
import time
import json
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService
from services.user_service import UserService
from services.question_generation_service import QuestionGenerationService
from services.question_storage_service import QuestionStorageService
from services.test_creation_service import TestCreationService
from services.test_publishing_service import TestPublishingService
from services.student_test_service import StudentTestService
from services.auto_grading_service import AutoGradingService
from services.instructor_analytics_service import InstructorAnalyticsService
from utils.dynamodb_utils import DynamoDBManager


class EndToEndTester:
    """Comprehensive end-to-end testing for QuizGenius MVP"""
    
    def __init__(self):
        """Initialize the end-to-end tester"""
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'start_time': datetime.now(),
            'workflows_tested': []
        }
        
        # Test data
        self.test_instructor_email = f"test_instructor_{int(time.time())}@example.com"
        self.test_student_email = f"test_student_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        
        # Initialize services
        try:
            self.auth_service = AuthService()
            self.user_service = UserService()
            self.question_gen_service = QuestionGenerationService()
            self.question_storage_service = QuestionStorageService()
            self.test_creation_service = TestCreationService()
            self.test_publishing_service = TestPublishingService()
            self.student_test_service = StudentTestService()
            self.grading_service = AutoGradingService()
            self.analytics_service = InstructorAnalyticsService()
            self.dynamodb_manager = DynamoDBManager()
            
            self.services_initialized = True
            print("✅ All services initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize services: {e}")
            self.services_initialized = False
    
    def log_test(self, test_name: str, passed: bool, details: str = "", duration: float = 0):
        """Log test result"""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            status = "✅ PASS"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌ FAIL"
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'status': status,
            'details': details,
            'duration': duration
        })
        
        print(f"{status}: {test_name} ({duration:.2f}s)")
        if details:
            print(f"    Details: {details}")
    
    def test_user_registration_workflow(self) -> Dict[str, Any]:
        """Test complete user registration workflow"""
        print("\n🔄 Testing User Registration Workflow...")
        workflow_results = {'instructor_id': None, 'student_id': None}
        
        # Test instructor registration
        start_time = time.time()
        try:
            instructor_result = self.user_service.register_user(
                email=self.test_instructor_email,
                password=self.test_password,
                role='instructor',
                first_name='Test',
                last_name='Instructor'
            )
            
            if instructor_result.get('success'):
                workflow_results['instructor_id'] = instructor_result.get('user_id')
                self.log_test(
                    "Instructor Registration",
                    True,
                    f"Instructor registered with ID: {workflow_results['instructor_id']}",
                    time.time() - start_time
                )
            else:
                self.log_test(
                    "Instructor Registration",
                    False,
                    f"Registration failed: {instructor_result.get('error', 'Unknown error')}",
                    time.time() - start_time
                )
        except Exception as e:
            self.log_test("Instructor Registration", False, f"Exception: {str(e)}", time.time() - start_time)
        
        # Test student registration
        start_time = time.time()
        try:
            student_result = self.user_service.register_user(
                email=self.test_student_email,
                password=self.test_password,
                role='student',
                first_name='Test',
                last_name='Student'
            )
            
            if student_result.get('success'):
                workflow_results['student_id'] = student_result.get('user_id')
                self.log_test(
                    "Student Registration",
                    True,
                    f"Student registered with ID: {workflow_results['student_id']}",
                    time.time() - start_time
                )
            else:
                self.log_test(
                    "Student Registration",
                    False,
                    f"Registration failed: {student_result.get('error', 'Unknown error')}",
                    time.time() - start_time
                )
        except Exception as e:
            self.log_test("Student Registration", False, f"Exception: {str(e)}", time.time() - start_time)
        
        return workflow_results
    
    def test_question_generation_workflow(self, instructor_id: str) -> List[str]:
        """Test question generation from PDF content"""
        print("\n🔄 Testing Question Generation Workflow...")
        
        # Sample PDF content for testing
        sample_content = """
        Machine Learning Fundamentals
        
        Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. There are three main types of machine learning:
        
        1. Supervised Learning: Uses labeled training data to learn a mapping from inputs to outputs.
        2. Unsupervised Learning: Finds hidden patterns in data without labeled examples.
        3. Reinforcement Learning: Learns through interaction with an environment using rewards and penalties.
        
        Common algorithms include linear regression, decision trees, neural networks, and support vector machines.
        """
        
        start_time = time.time()
        question_ids = []
        
        try:
            # Generate questions from content
            questions = self.question_gen_service.generate_questions_from_content(
                content=sample_content,
                num_questions=5
            )
            
            if questions and len(questions) > 0:
                # Store generated questions
                for question in questions:
                    question_data = {
                        'instructor_id': instructor_id,
                        'question_text': question.get('question', ''),
                        'question_type': question.get('type', 'multiple_choice'),
                        'options': question.get('options', []),
                        'correct_answer': question.get('correct_answer', ''),
                        'explanation': question.get('explanation', ''),
                        'difficulty': question.get('difficulty', 'medium'),
                        'topic': 'Machine Learning'
                    }
                    
                    stored_result = self.question_storage_service.store_question(question_data)
                    if stored_result.get('success'):
                        question_ids.append(stored_result.get('question_id'))
                
                self.log_test(
                    "Question Generation & Storage",
                    len(question_ids) > 0,
                    f"Generated and stored {len(question_ids)} questions",
                    time.time() - start_time
                )
            else:
                self.log_test(
                    "Question Generation & Storage",
                    False,
                    "No questions generated from content",
                    time.time() - start_time
                )
        except Exception as e:
            self.log_test("Question Generation & Storage", False, f"Exception: {str(e)}", time.time() - start_time)
        
        return question_ids
    
    def test_test_creation_workflow(self, instructor_id: str, question_ids: List[str]) -> Optional[str]:
        """Test test creation and publishing workflow"""
        print("\n🔄 Testing Test Creation & Publishing Workflow...")
        
        if not question_ids:
            self.log_test("Test Creation", False, "No questions available for test creation", 0)
            return None
        
        start_time = time.time()
        test_id = None
        
        try:
            # Create test
            test_data = {
                'instructor_id': instructor_id,
                'title': 'End-to-End Test Quiz',
                'description': 'Comprehensive test for E2E validation',
                'question_ids': question_ids[:3],  # Use first 3 questions
                'time_limit': 30,  # 30 minutes
                'max_attempts': 2,
                'randomize_questions': True,
                'show_results_immediately': True
            }
            
            creation_result = self.test_creation_service.create_test(test_data)
            
            if creation_result.get('success'):
                test_id = creation_result.get('test_id')
                
                # Publish the test
                publish_result = self.test_publishing_service.publish_test(
                    test_id=test_id,
                    instructor_id=instructor_id,
                    access_code=f"E2E{int(time.time())}"
                )
                
                if publish_result.get('success'):
                    self.log_test(
                        "Test Creation & Publishing",
                        True,
                        f"Test created and published with ID: {test_id}",
                        time.time() - start_time
                    )
                else:
                    self.log_test(
                        "Test Creation & Publishing",
                        False,
                        f"Test created but publishing failed: {publish_result.get('error')}",
                        time.time() - start_time
                    )
            else:
                self.log_test(
                    "Test Creation & Publishing",
                    False,
                    f"Test creation failed: {creation_result.get('error')}",
                    time.time() - start_time
                )
        except Exception as e:
            self.log_test("Test Creation & Publishing", False, f"Exception: {str(e)}", time.time() - start_time)
        
        return test_id
    
    def test_student_test_taking_workflow(self, student_id: str, test_id: str) -> Optional[str]:
        """Test student test taking workflow"""
        print("\n🔄 Testing Student Test Taking Workflow...")
        
        if not test_id:
            self.log_test("Student Test Taking", False, "No test available for taking", 0)
            return None
        
        start_time = time.time()
        submission_id = None
        
        try:
            # Get available tests
            available_tests = self.student_test_service.get_available_tests(student_id)
            
            if not available_tests or len(available_tests) == 0:
                self.log_test(
                    "Student Test Taking",
                    False,
                    "No available tests found for student",
                    time.time() - start_time
                )
                return None
            
            # Start test session
            session_result = self.student_test_service.start_test_session(
                student_id=student_id,
                test_id=test_id
            )
            
            if not session_result.get('success'):
                self.log_test(
                    "Student Test Taking",
                    False,
                    f"Failed to start test session: {session_result.get('error')}",
                    time.time() - start_time
                )
                return None
            
            session_id = session_result.get('session_id')
            questions = session_result.get('questions', [])
            
            # Answer questions
            answers = {}
            for i, question in enumerate(questions):
                if question.get('type') == 'multiple_choice':
                    # Choose first option for testing
                    answers[question['question_id']] = question.get('options', ['A'])[0]
                elif question.get('type') == 'true_false':
                    answers[question['question_id']] = 'True'
            
            # Submit test
            submission_result = self.student_test_service.submit_test(
                session_id=session_id,
                student_id=student_id,
                answers=answers
            )
            
            if submission_result.get('success'):
                submission_id = submission_result.get('submission_id')
                self.log_test(
                    "Student Test Taking",
                    True,
                    f"Test completed and submitted with ID: {submission_id}",
                    time.time() - start_time
                )
            else:
                self.log_test(
                    "Student Test Taking",
                    False,
                    f"Test submission failed: {submission_result.get('error')}",
                    time.time() - start_time
                )
        except Exception as e:
            self.log_test("Student Test Taking", False, f"Exception: {str(e)}", time.time() - start_time)
        
        return submission_id
    
    def test_auto_grading_workflow(self, submission_id: str) -> bool:
        """Test auto-grading workflow"""
        print("\n🔄 Testing Auto-Grading Workflow...")
        
        if not submission_id:
            self.log_test("Auto-Grading", False, "No submission available for grading", 0)
            return False
        
        start_time = time.time()
        
        try:
            # Grade the submission
            grading_result = self.grading_service.grade_submission(submission_id)
            
            if grading_result.get('success'):
                test_result = grading_result.get('test_result')
                if test_result:
                    self.log_test(
                        "Auto-Grading",
                        True,
                        f"Submission graded - Score: {test_result.total_score}/{test_result.total_possible}",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test(
                        "Auto-Grading",
                        False,
                        "Grading succeeded but no test result returned",
                        time.time() - start_time
                    )
            else:
                self.log_test(
                    "Auto-Grading",
                    False,
                    f"Grading failed: {grading_result.get('error')}",
                    time.time() - start_time
                )
        except Exception as e:
            self.log_test("Auto-Grading", False, f"Exception: {str(e)}", time.time() - start_time)
        
        return False
    
    def test_analytics_workflow(self, instructor_id: str, test_id: str) -> bool:
        """Test instructor analytics workflow"""
        print("\n🔄 Testing Instructor Analytics Workflow...")
        
        start_time = time.time()
        
        try:
            # Generate instructor dashboard
            dashboard_result = self.analytics_service.generate_instructor_dashboard(instructor_id)
            
            if dashboard_result.get('success'):
                dashboard = dashboard_result.get('dashboard')
                if dashboard:
                    self.log_test(
                        "Instructor Analytics",
                        True,
                        f"Dashboard generated with {len(dashboard.test_summaries)} test summaries",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test(
                        "Instructor Analytics",
                        False,
                        "Analytics succeeded but no dashboard returned",
                        time.time() - start_time
                    )
            else:
                self.log_test(
                    "Instructor Analytics",
                    False,
                    f"Analytics failed: {dashboard_result.get('error')}",
                    time.time() - start_time
                )
        except Exception as e:
            self.log_test("Instructor Analytics", False, f"Exception: {str(e)}", time.time() - start_time)
        
        return False
    
    def run_complete_end_to_end_test(self):
        """Run complete end-to-end system test"""
        print("🚀 Starting Complete End-to-End System Test")
        print("=" * 60)
        
        if not self.services_initialized:
            print("❌ Cannot run tests - services not initialized")
            return
        
        # Test 1: User Registration Workflow
        user_data = self.test_user_registration_workflow()
        self.test_results['workflows_tested'].append('User Registration')
        
        instructor_id = user_data.get('instructor_id')
        student_id = user_data.get('student_id')
        
        if not instructor_id or not student_id:
            print("❌ Cannot continue - user registration failed")
            return
        
        # Test 2: Question Generation Workflow
        question_ids = self.test_question_generation_workflow(instructor_id)
        self.test_results['workflows_tested'].append('Question Generation')
        
        # Test 3: Test Creation & Publishing Workflow
        test_id = self.test_test_creation_workflow(instructor_id, question_ids)
        self.test_results['workflows_tested'].append('Test Creation & Publishing')
        
        # Test 4: Student Test Taking Workflow
        submission_id = self.test_student_test_taking_workflow(student_id, test_id)
        self.test_results['workflows_tested'].append('Student Test Taking')
        
        # Test 5: Auto-Grading Workflow
        grading_success = self.test_auto_grading_workflow(submission_id)
        self.test_results['workflows_tested'].append('Auto-Grading')
        
        # Test 6: Analytics Workflow
        analytics_success = self.test_analytics_workflow(instructor_id, test_id)
        self.test_results['workflows_tested'].append('Instructor Analytics')
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📊 END-TO-END TEST RESULTS SUMMARY")
        print("=" * 60)
        
        end_time = datetime.now()
        duration = end_time - self.test_results['start_time']
        
        print(f"🕒 Test Duration: {duration.total_seconds():.2f} seconds")
        print(f"📈 Total Tests: {self.test_results['total_tests']}")
        print(f"✅ Passed: {self.test_results['passed_tests']}")
        print(f"❌ Failed: {self.test_results['failed_tests']}")
        
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        print(f"\n🔄 Workflows Tested: {len(self.test_results['workflows_tested'])}")
        for workflow in self.test_results['workflows_tested']:
            print(f"  • {workflow}")
        
        print("\n📋 Detailed Test Results:")
        for test in self.test_results['test_details']:
            print(f"  {test['status']}: {test['test_name']} ({test['duration']:.2f}s)")
            if test['details']:
                print(f"    └─ {test['details']}")
        
        # Overall assessment
        if success_rate >= 80:
            print(f"\n🎉 OVERALL ASSESSMENT: EXCELLENT ({success_rate:.1f}%)")
            print("✅ System is ready for production deployment!")
        elif success_rate >= 60:
            print(f"\n⚠️  OVERALL ASSESSMENT: GOOD ({success_rate:.1f}%)")
            print("🔧 Some issues need attention before deployment")
        else:
            print(f"\n❌ OVERALL ASSESSMENT: NEEDS WORK ({success_rate:.1f}%)")
            print("🚨 Significant issues must be resolved before deployment")


def main():
    """Main function to run end-to-end tests"""
    print("🧪 QuizGenius MVP - End-to-End Testing Suite")
    print("Phase 5.4.1: Complete System Integration Testing")
    print("=" * 60)
    
    tester = EndToEndTester()
    tester.run_complete_end_to_end_test()


if __name__ == "__main__":
    main()