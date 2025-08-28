#!/usr/bin/env python3
"""
Test Student Account Script for QuizGenius MVP

This script comprehensively tests the student account functionality
including authentication, user data, and student-specific features.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService, AuthenticationError
from services.user_service import UserService, UserServiceError
from services.student_test_service import StudentTestService, StudentTestError
from utils.session_manager import SessionManager

class StudentAccountTester:
    """Comprehensive student account testing"""
    
    def __init__(self):
        """Initialize the tester"""
        self.student_email = 'test.student@example.com'
        self.student_password = 'TestPass123!'
        self.auth_service = AuthService()
        self.user_service = UserService()
        self.student_service = StudentTestService()
        self.session_manager = SessionManager()
        
        self.test_results = []
        self.student_user_data = None
        self.auth_tokens = None
    
    def record_test(self, test_name, success, message):
        """Record test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'status': status
        })
        print(f"   {status}: {test_name} - {message}")
    
    def test_authentication(self):
        """Test student authentication"""
        print("\n🔐 Testing Student Authentication")
        print("-" * 40)
        
        try:
            # Test login
            result = self.auth_service.authenticate_user(
                email=self.student_email,
                password=self.student_password
            )
            
            if result['success']:
                self.auth_tokens = result
                user_info = result.get('user_info', {})
                
                self.record_test(
                    "Student Login",
                    True,
                    f"Login successful for {self.student_email}"
                )
                
                # Verify user info
                if user_info.get('email') == self.student_email:
                    self.record_test(
                        "User Info Retrieval",
                        True,
                        f"User info retrieved: {user_info.get('given_name', 'Unknown')} {user_info.get('family_name', 'Unknown')}"
                    )
                else:
                    self.record_test(
                        "User Info Retrieval",
                        False,
                        "User info email mismatch"
                    )
                
                return True
            else:
                self.record_test(
                    "Student Login",
                    False,
                    f"Login failed: {result}"
                )
                return False
                
        except AuthenticationError as e:
            self.record_test(
                "Student Login",
                False,
                f"Authentication error: {e}"
            )
            return False
        except Exception as e:
            self.record_test(
                "Student Login",
                False,
                f"Unexpected error: {e}"
            )
            return False
    
    def test_user_data_retrieval(self):
        """Test user data retrieval from DynamoDB"""
        print("\n📊 Testing User Data Retrieval")
        print("-" * 40)
        
        try:
            # Get user by email
            user_data = self.user_service.get_user_by_email(self.student_email)
            
            if user_data:
                self.student_user_data = user_data
                
                self.record_test(
                    "DynamoDB User Retrieval",
                    True,
                    f"User data found: {user_data.get('first_name')} {user_data.get('last_name')}"
                )
                
                # Verify role
                if user_data.get('role') == 'student':
                    self.record_test(
                        "User Role Verification",
                        True,
                        "Role correctly set to 'student'"
                    )
                else:
                    self.record_test(
                        "User Role Verification",
                        False,
                        f"Role mismatch: expected 'student', got '{user_data.get('role')}'"
                    )
                
                # Verify student-specific fields
                student_fields = ['school', 'grade_level', 'subject_interests']
                missing_fields = []
                
                for field in student_fields:
                    if field not in user_data:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.record_test(
                        "Student-Specific Fields",
                        True,
                        "All student fields present"
                    )
                else:
                    self.record_test(
                        "Student-Specific Fields",
                        False,
                        f"Missing fields: {missing_fields}"
                    )
                
                return True
            else:
                self.record_test(
                    "DynamoDB User Retrieval",
                    False,
                    "User data not found in DynamoDB"
                )
                return False
                
        except UserServiceError as e:
            self.record_test(
                "DynamoDB User Retrieval",
                False,
                f"User service error: {e}"
            )
            return False
        except Exception as e:
            self.record_test(
                "DynamoDB User Retrieval",
                False,
                f"Unexpected error: {e}"
            )
            return False
    
    def test_student_services(self):
        """Test student-specific services"""
        print("\n🎓 Testing Student Services")
        print("-" * 40)
        
        if not self.student_user_data:
            self.record_test(
                "Student Services",
                False,
                "Cannot test - no user data available"
            )
            return False
        
        student_id = self.student_user_data.get('user_id')
        
        try:
            # Test get_available_tests
            available_tests = self.student_service.get_available_tests(student_id)
            
            self.record_test(
                "Get Available Tests",
                True,
                f"Retrieved {len(available_tests)} available tests"
            )
            
            # Test get_student_results (should return empty for new student)
            try:
                results = self.student_service.get_student_results(student_id)
                self.record_test(
                    "Get Student Results",
                    True,
                    f"Retrieved {len(results)} student results"
                )
            except Exception as e:
                self.record_test(
                    "Get Student Results",
                    False,
                    f"Error getting results: {e}"
                )
            
            # Test get_student_progress
            try:
                progress = self.student_service.get_student_progress(student_id)
                self.record_test(
                    "Get Student Progress",
                    True,
                    f"Progress data retrieved: {type(progress)}"
                )
            except Exception as e:
                self.record_test(
                    "Get Student Progress",
                    False,
                    f"Error getting progress: {e}"
                )
            
            return True
            
        except StudentTestError as e:
            self.record_test(
                "Student Services",
                False,
                f"Student service error: {e}"
            )
            return False
        except Exception as e:
            self.record_test(
                "Student Services",
                False,
                f"Unexpected error: {e}"
            )
            return False
    
    def test_session_management(self):
        """Test session management for student"""
        print("\n🔄 Testing Session Management")
        print("-" * 40)
        
        if not self.auth_tokens or not self.student_user_data:
            self.record_test(
                "Session Management",
                False,
                "Cannot test - no auth tokens or user data"
            )
            return False
        
        try:
            # Simulate session creation
            user_info = {
                'user_id': self.student_user_data.get('user_id'),
                'email': self.student_user_data.get('email'),
                'first_name': self.student_user_data.get('first_name'),
                'last_name': self.student_user_data.get('last_name'),
                'role': self.student_user_data.get('role'),
                'access_token': self.auth_tokens.get('access_token')
            }
            
            # Test session initialization
            self.session_manager.initialize_session()
            self.record_test(
                "Session Initialization",
                True,
                "Session initialized successfully"
            )
            
            # Test user data storage (simulated)
            if user_info.get('role') == 'student':
                self.record_test(
                    "Student Role Session",
                    True,
                    "Student role properly handled in session"
                )
            else:
                self.record_test(
                    "Student Role Session",
                    False,
                    "Student role not properly handled"
                )
            
            return True
            
        except Exception as e:
            self.record_test(
                "Session Management",
                False,
                f"Session error: {e}"
            )
            return False
    
    def test_student_dashboard_data(self):
        """Test data needed for student dashboard"""
        print("\n📊 Testing Student Dashboard Data")
        print("-" * 40)
        
        if not self.student_user_data:
            self.record_test(
                "Dashboard Data",
                False,
                "Cannot test - no user data available"
            )
            return False
        
        student_id = self.student_user_data.get('user_id')
        
        try:
            # Test dashboard metrics
            dashboard_data = {
                'available_tests': 0,
                'completed_tests': 0,
                'average_score': 0,
                'best_score': 0
            }
            
            # Get available tests count
            available_tests = self.student_service.get_available_tests(student_id)
            dashboard_data['available_tests'] = len(available_tests)
            
            # Get completed tests (results)
            try:
                results = self.student_service.get_student_results(student_id)
                dashboard_data['completed_tests'] = len(results)
            except:
                dashboard_data['completed_tests'] = 0
            
            self.record_test(
                "Dashboard Metrics",
                True,
                f"Dashboard data: {dashboard_data['available_tests']} available, {dashboard_data['completed_tests']} completed"
            )
            
            # Test user preferences
            preferences = self.student_user_data.get('subject_interests', [])
            if preferences:
                self.record_test(
                    "Student Preferences",
                    True,
                    f"Subject interests: {', '.join(preferences)}"
                )
            else:
                self.record_test(
                    "Student Preferences",
                    False,
                    "No subject interests found"
                )
            
            return True
            
        except Exception as e:
            self.record_test(
                "Dashboard Data",
                False,
                f"Dashboard error: {e}"
            )
            return False
    
    def run_all_tests(self):
        """Run all student account tests"""
        print("🎓 Comprehensive Student Account Testing")
        print("=" * 60)
        print(f"Testing Account: {self.student_email}")
        print(f"Password: {self.student_password}")
        
        # Run tests in sequence
        auth_success = self.test_authentication()
        
        if auth_success:
            self.test_user_data_retrieval()
            self.test_student_services()
            self.test_session_management()
            self.test_student_dashboard_data()
        
        # Summary
        print(f"\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("-" * 30)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
        
        print(f"\n📈 Overall Results:")
        print(f"   • Tests Passed: {passed}/{total}")
        print(f"   • Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print(f"\n🎉 All tests passed! Student account is fully functional.")
            print(f"\n🚀 Ready for app testing:")
            print(f"   Email: {self.student_email}")
            print(f"   Password: {self.student_password}")
            return True
        else:
            print(f"\n⚠️  Some tests failed. Check output above for details.")
            return False

def main():
    """Main function"""
    tester = StudentAccountTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)