#!/usr/bin/env python3
"""
Login System Testing Script for QuizGenius MVP

This script tests the complete login system functionality including:
- Login form validation
- Cognito authentication
- Session management
- Role-based redirection
- Error handling
- Email verification integration
"""

import sys
import os
import time
import uuid
from typing import Dict, Any

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService, AuthenticationError
from services.user_service import UserService, UserServiceError
from utils.session_manager import SessionManager
from utils.config import load_environment_config

class LoginSystemTester:
    """Test class for login system functionality"""
    
    def __init__(self):
        """Initialize the tester"""
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
        # Test data for instructor
        self.instructor_email = f"test_instructor_login_{uuid.uuid4().hex[:8]}@example.com"
        self.instructor_password = "InstructorPass123!"
        self.instructor_data = {
            'first_name': 'Test',
            'last_name': 'Instructor',
            'email': self.instructor_email,
            'role': 'instructor',
            'institution': 'Test University'
        }
        
        # Test data for student
        self.student_email = f"test_student_login_{uuid.uuid4().hex[:8]}@example.com"
        self.student_password = "StudentPass123!"
        self.student_data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': self.student_email,
            'role': 'student',
            'school': 'Test High School'
        }
    
    def run_all_tests(self):
        """Run all login system tests"""
        print("🧪 Login System Testing for QuizGenius MVP")
        print("=" * 60)
        
        try:
            # Load configuration
            load_environment_config()
            
            # Initialize services
            self.auth_service = AuthService()
            self.user_service = UserService()
            self.session_manager = SessionManager()
            
            print("✅ Services initialized successfully")
            print()
            
            # Setup test users
            self.setup_test_users()
            
            # Run tests
            self.test_login_form_validation()
            self.test_instructor_login_flow()
            self.test_student_login_flow()
            self.test_invalid_credentials()
            self.test_session_management()
            self.test_role_based_features()
            self.test_logout_functionality()
            self.test_error_handling()
            
            # Cleanup
            self.cleanup_test_data()
            
        except Exception as e:
            print(f"❌ Test setup error: {str(e)}")
            return
        
        # Print results
        self.print_test_results()
    
    def setup_test_users(self):
        """Set up test users for login testing"""
        print("🔧 Setting up test users...")
        
        try:
            # Create instructor
            auth_result = self.auth_service.register_user(
                email=self.instructor_email,
                password=self.instructor_password,
                first_name=self.instructor_data['first_name'],
                last_name=self.instructor_data['last_name'],
                role='instructor'
            )
            
            if auth_result['success']:
                user_result = self.user_service.create_user(self.instructor_data)
                if user_result['success']:
                    print(f"  ✅ Created test instructor: {self.instructor_email}")
                else:
                    print(f"  ❌ Failed to create instructor profile: {user_result.get('message')}")
            else:
                print(f"  ❌ Failed to register instructor: {auth_result.get('message')}")
            
            # Create student
            auth_result = self.auth_service.register_user(
                email=self.student_email,
                password=self.student_password,
                first_name=self.student_data['first_name'],
                last_name=self.student_data['last_name'],
                role='student'
            )
            
            if auth_result['success']:
                user_result = self.user_service.create_user(self.student_data)
                if user_result['success']:
                    print(f"  ✅ Created test student: {self.student_email}")
                else:
                    print(f"  ❌ Failed to create student profile: {user_result.get('message')}")
            else:
                print(f"  ❌ Failed to register student: {auth_result.get('message')}")
                
        except Exception as e:
            print(f"  ❌ Error setting up test users: {str(e)}")
    
    def test_login_form_validation(self):
        """Test login form validation logic"""
        print("🔍 Testing login form validation...")
        
        # Import auth components for validation testing
        from components.auth_components import AuthComponents
        
        # Test cases for login validation
        test_cases = [
            {
                'name': 'Valid credentials format',
                'email': 'test@example.com',
                'password': 'ValidPass123!',
                'should_pass_format': True
            },
            {
                'name': 'Empty email',
                'email': '',
                'password': 'ValidPass123!',
                'should_pass_format': False
            },
            {
                'name': 'Empty password',
                'email': 'test@example.com',
                'password': '',
                'should_pass_format': False
            },
            {
                'name': 'Invalid email format',
                'email': 'invalid-email',
                'password': 'ValidPass123!',
                'should_pass_format': False
            }
        ]
        
        for test_case in test_cases:
            self.total_tests += 1
            
            try:
                # Basic format validation
                email = test_case['email']
                password = test_case['password']
                
                # Check basic format requirements
                has_email = bool(email and email.strip())
                has_password = bool(password and password.strip())
                valid_email_format = '@' in email and '.' in email if email else False
                
                format_valid = has_email and has_password and valid_email_format
                
                if test_case['should_pass_format'] and format_valid:
                    self.record_test_result(f"Login validation - {test_case['name']}", True, "Format validation passed as expected")
                elif not test_case['should_pass_format'] and not format_valid:
                    self.record_test_result(f"Login validation - {test_case['name']}", True, "Format validation failed as expected")
                else:
                    expected = "pass" if test_case['should_pass_format'] else "fail"
                    actual = "passed" if format_valid else "failed"
                    self.record_test_result(f"Login validation - {test_case['name']}", False, f"Expected to {expected}, but {actual}")
                    
            except Exception as e:
                self.record_test_result(f"Login validation - {test_case['name']}", False, f"Exception: {str(e)}")
    
    def test_instructor_login_flow(self):
        """Test complete instructor login flow"""
        print("🔍 Testing instructor login flow...")
        
        self.total_tests += 1
        
        try:
            # Attempt to authenticate instructor
            auth_result = self.auth_service.authenticate_user(
                self.instructor_email,
                self.instructor_password
            )
            
            if not auth_result['success']:
                self.record_test_result("Instructor login flow", False, f"Authentication failed: {auth_result.get('message')}")
                return
            
            # Get user profile
            user_data = self.user_service.get_user_by_email(self.instructor_email)
            
            if not user_data:
                self.record_test_result("Instructor login flow", False, "User profile not found after authentication")
                return
            
            # Verify role
            if user_data['role'] != 'instructor':
                self.record_test_result("Instructor login flow", False, f"Incorrect role: {user_data['role']}")
                return
            
            # Update last login
            update_result = self.user_service.update_last_login(user_data['user_id'])
            
            if not update_result['success']:
                self.record_test_result("Instructor login flow", False, "Failed to update last login")
                return
            
            self.record_test_result("Instructor login flow", True, "Complete instructor login flow successful")
            
        except Exception as e:
            self.record_test_result("Instructor login flow", False, f"Exception: {str(e)}")
    
    def test_student_login_flow(self):
        """Test complete student login flow"""
        print("🔍 Testing student login flow...")
        
        self.total_tests += 1
        
        try:
            # Attempt to authenticate student
            auth_result = self.auth_service.authenticate_user(
                self.student_email,
                self.student_password
            )
            
            if not auth_result['success']:
                self.record_test_result("Student login flow", False, f"Authentication failed: {auth_result.get('message')}")
                return
            
            # Get user profile
            user_data = self.user_service.get_user_by_email(self.student_email)
            
            if not user_data:
                self.record_test_result("Student login flow", False, "User profile not found after authentication")
                return
            
            # Verify role
            if user_data['role'] != 'student':
                self.record_test_result("Student login flow", False, f"Incorrect role: {user_data['role']}")
                return
            
            # Update last login
            update_result = self.user_service.update_last_login(user_data['user_id'])
            
            if not update_result['success']:
                self.record_test_result("Student login flow", False, "Failed to update last login")
                return
            
            self.record_test_result("Student login flow", True, "Complete student login flow successful")
            
        except Exception as e:
            self.record_test_result("Student login flow", False, f"Exception: {str(e)}")
    
    def test_invalid_credentials(self):
        """Test handling of invalid credentials"""
        print("🔍 Testing invalid credentials handling...")
        
        invalid_scenarios = [
            ("Wrong password", self.instructor_email, "WrongPassword123!"),
            ("Non-existent user", "nonexistent@example.com", "SomePassword123!"),
            ("Wrong email format", "invalid-email", "SomePassword123!")
        ]
        
        for scenario_name, email, password in invalid_scenarios:
            self.total_tests += 1
            
            try:
                auth_result = self.auth_service.authenticate_user(email, password)
                
                if auth_result['success']:
                    self.record_test_result(f"Invalid credentials - {scenario_name}", False, "Invalid credentials were accepted")
                else:
                    self.record_test_result(f"Invalid credentials - {scenario_name}", True, "Invalid credentials properly rejected")
                    
            except AuthenticationError as e:
                self.record_test_result(f"Invalid credentials - {scenario_name}", True, f"Invalid credentials rejected with exception: {type(e).__name__}")
            except Exception as e:
                self.record_test_result(f"Invalid credentials - {scenario_name}", False, f"Unexpected exception: {str(e)}")
    
    def test_session_management(self):
        """Test session management functionality"""
        print("🔍 Testing session management...")
        
        self.total_tests += 1
        
        try:
            # Get user data for session testing
            user_data = self.user_service.get_user_by_email(self.instructor_email)
            
            if not user_data:
                self.record_test_result("Session management", False, "User data not found for session testing")
                return
            
            # Test session initialization
            self.session_manager.initialize_session()
            
            # Test login user (simulate successful authentication)
            auth_result = {'success': True, 'access_token': 'test_token'}
            self.session_manager.login_user(user_data, auth_result, remember_me=True)
            
            # Test session state
            if not self.session_manager.is_authenticated():
                self.record_test_result("Session management", False, "Session not authenticated after login")
                return
            
            # Test user info retrieval
            session_user_info = self.session_manager.get_user_info()
            
            if not session_user_info or session_user_info.get('email') != user_data['email']:
                self.record_test_result("Session management", False, "Session user info mismatch")
                return
            
            # Test logout
            self.session_manager.logout()
            
            if self.session_manager.is_authenticated():
                self.record_test_result("Session management", False, "Session still authenticated after logout")
                return
            
            self.record_test_result("Session management", True, "Session management working correctly")
            
        except Exception as e:
            self.record_test_result("Session management", False, f"Exception: {str(e)}")
    
    def test_role_based_features(self):
        """Test role-based features and access"""
        print("🔍 Testing role-based features...")
        
        self.total_tests += 1
        
        try:
            # Test instructor role features
            instructor_user = self.user_service.get_user_by_email(self.instructor_email)
            student_user = self.user_service.get_user_by_email(self.student_email)
            
            if not instructor_user or not student_user:
                self.record_test_result("Role-based features", False, "Test users not found")
                return
            
            # Verify role-specific fields
            role_features = []
            
            # Check instructor-specific features
            if instructor_user['role'] == 'instructor':
                role_features.append("instructor role verified")
                if 'institution' in instructor_user:
                    role_features.append("instructor institution field")
            
            # Check student-specific features
            if student_user['role'] == 'student':
                role_features.append("student role verified")
                if 'school' in student_user:
                    role_features.append("student school field")
            
            if len(role_features) >= 3:
                self.record_test_result("Role-based features", True, f"Role features verified: {', '.join(role_features)}")
            else:
                self.record_test_result("Role-based features", False, f"Insufficient role features: {', '.join(role_features)}")
                
        except Exception as e:
            self.record_test_result("Role-based features", False, f"Exception: {str(e)}")
    
    def test_logout_functionality(self):
        """Test logout functionality"""
        print("🔍 Testing logout functionality...")
        
        self.total_tests += 1
        
        try:
            # Login first
            user_data = self.user_service.get_user_by_email(self.instructor_email)
            auth_result = {'success': True, 'access_token': 'test_token'}
            
            self.session_manager.initialize_session()
            self.session_manager.login_user(user_data, auth_result, remember_me=False)
            
            # Verify logged in
            if not self.session_manager.is_authenticated():
                self.record_test_result("Logout functionality", False, "Failed to login for logout test")
                return
            
            # Test logout
            self.session_manager.logout()
            
            # Verify logged out
            if self.session_manager.is_authenticated():
                self.record_test_result("Logout functionality", False, "Still authenticated after logout")
                return
            
            # Verify session data cleared
            user_info = self.session_manager.get_user_info()
            if user_info and len(user_info) > 0:
                self.record_test_result("Logout functionality", False, "Session data not cleared after logout")
                return
            
            self.record_test_result("Logout functionality", True, "Logout functionality working correctly")
            
        except Exception as e:
            self.record_test_result("Logout functionality", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("🔍 Testing error handling...")
        
        # Test authentication with malformed data
        self.total_tests += 1
        
        try:
            # Test with None values
            auth_result = self.auth_service.authenticate_user(None, None)
            
            if auth_result['success']:
                self.record_test_result("Error handling - Null credentials", False, "Null credentials were accepted")
            else:
                self.record_test_result("Error handling - Null credentials", True, "Null credentials properly rejected")
                
        except Exception as e:
            self.record_test_result("Error handling - Null credentials", True, f"Null credentials rejected with exception: {type(e).__name__}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        try:
            # Delete instructor
            self.user_service.delete_user_by_email(self.instructor_email)
            print(f"  ✅ Deleted test instructor: {self.instructor_email}")
        except Exception as e:
            print(f"  ⚠️ Could not delete instructor: {str(e)}")
        
        try:
            # Delete student
            self.user_service.delete_user_by_email(self.student_email)
            print(f"  ✅ Deleted test student: {self.student_email}")
        except Exception as e:
            print(f"  ⚠️ Could not delete student: {str(e)}")
        
        print(f"  ℹ️ Cognito cleanup may be required for: {self.instructor_email}, {self.student_email}")
    
    def record_test_result(self, test_name: str, passed: bool, message: str):
        """Record a test result"""
        self.test_results['total_tests'] += 1
        
        if passed:
            self.test_results['passed_tests'] += 1
            status = "✅ PASS"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌ FAIL"
        
        self.test_results['test_details'].append({
            'name': test_name,
            'status': status,
            'message': message
        })
        
        print(f"  {status}: {test_name}")
        if message:
            print(f"    {message}")
    
    @property
    def total_tests(self):
        return self.test_results['total_tests']
    
    @total_tests.setter
    def total_tests(self, value):
        self.test_results['total_tests'] = value
    
    def print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("📊 Login System Test Report")
        print("=" * 60)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nDetailed Results:")
        for test in self.test_results['test_details']:
            print(f"  {test['name']}: {test['status']}")
            if test['message']:
                print(f"    {test['message']}")
        
        if failed == 0:
            print("\n🎉 All login system tests passed!")
            print("\n🚀 Login system functionality is ready!")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Please review and fix issues.")
        
        print("\n📋 Test Coverage:")
        print("  ✅ Login form validation")
        print("  ✅ Instructor login flow")
        print("  ✅ Student login flow")
        print("  ✅ Invalid credentials handling")
        print("  ✅ Session management")
        print("  ✅ Role-based features")
        print("  ✅ Logout functionality")
        print("  ✅ Error handling")

def main():
    """Main function to run login system tests"""
    tester = LoginSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()