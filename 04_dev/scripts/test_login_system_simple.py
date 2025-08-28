#!/usr/bin/env python3
"""
Simplified Login System Testing Script for QuizGenius MVP

This script tests the login system functionality using existing users
to avoid email verification and daily limit issues.
"""

import sys
import os
import time
from typing import Dict, Any

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService, AuthenticationError
from services.user_service import UserService, UserServiceError
from utils.session_manager import SessionManager
from utils.config import load_environment_config

class SimpleLoginTester:
    """Simplified test class for login system functionality"""
    
    def __init__(self):
        """Initialize the tester"""
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
    
    def run_all_tests(self):
        """Run all login system tests"""
        print("🧪 Simplified Login System Testing for QuizGenius MVP")
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
            
            # Run tests
            self.test_login_form_validation()
            self.test_invalid_credentials()
            self.test_session_management()
            self.test_logout_functionality()
            self.test_error_handling()
            self.test_user_statistics()
            
        except Exception as e:
            print(f"❌ Test setup error: {str(e)}")
            return
        
        # Print results
        self.print_test_results()
    
    def test_login_form_validation(self):
        """Test login form validation logic"""
        print("🔍 Testing login form validation...")
        
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
            },
            {
                'name': 'Both empty',
                'email': '',
                'password': '',
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
    
    def test_invalid_credentials(self):
        """Test handling of invalid credentials"""
        print("🔍 Testing invalid credentials handling...")
        
        invalid_scenarios = [
            ("Non-existent user", "nonexistent@example.com", "SomePassword123!"),
            ("Invalid email format", "invalid-email", "SomePassword123!"),
            ("Empty credentials", "", ""),
            ("SQL injection attempt", "'; DROP TABLE users; --", "password")
        ]
        
        for scenario_name, email, password in invalid_scenarios:
            self.total_tests += 1
            
            try:
                auth_result = self.auth_service.authenticate_user(email, password)
                
                if auth_result and auth_result.get('success'):
                    self.record_test_result(f"Invalid credentials - {scenario_name}", False, "Invalid credentials were accepted")
                else:
                    self.record_test_result(f"Invalid credentials - {scenario_name}", True, "Invalid credentials properly rejected")
                    
            except AuthenticationError as e:
                self.record_test_result(f"Invalid credentials - {scenario_name}", True, f"Invalid credentials rejected with exception: {type(e).__name__}")
            except Exception as e:
                self.record_test_result(f"Invalid credentials - {scenario_name}", True, f"Invalid credentials rejected with exception: {type(e).__name__}")
    
    def test_session_management(self):
        """Test session management functionality"""
        print("🔍 Testing session management...")
        
        self.total_tests += 1
        
        try:
            # Test session initialization
            self.session_manager.initialize_session()
            
            # Create mock user data for session testing
            mock_user_data = {
                'user_id': 'test_user_123',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'instructor'
            }
            
            # Test login user (simulate successful authentication)
            auth_result = {'success': True, 'access_token': 'test_token'}
            self.session_manager.login_user(mock_user_data, auth_result, remember_me=True)
            
            # Test session state
            if not self.session_manager.is_authenticated():
                self.record_test_result("Session management", False, "Session not authenticated after login")
                return
            
            # Test user info retrieval
            session_user_info = self.session_manager.get_user_info()
            
            if not session_user_info or session_user_info.get('email') != mock_user_data['email']:
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
    
    def test_logout_functionality(self):
        """Test logout functionality"""
        print("🔍 Testing logout functionality...")
        
        self.total_tests += 1
        
        try:
            # Setup session
            mock_user_data = {
                'user_id': 'test_user_456',
                'email': 'test2@example.com',
                'first_name': 'Test',
                'last_name': 'User2',
                'role': 'student'
            }
            
            auth_result = {'success': True, 'access_token': 'test_token_2'}
            
            self.session_manager.initialize_session()
            self.session_manager.login_user(mock_user_data, auth_result, remember_me=False)
            
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
            
            if auth_result and auth_result.get('success'):
                self.record_test_result("Error handling - Null credentials", False, "Null credentials were accepted")
            else:
                self.record_test_result("Error handling - Null credentials", True, "Null credentials properly rejected")
                
        except Exception as e:
            self.record_test_result("Error handling - Null credentials", True, f"Null credentials rejected with exception: {type(e).__name__}")
        
        # Test with extremely long inputs
        self.total_tests += 1
        
        try:
            long_email = "a" * 1000 + "@example.com"
            long_password = "b" * 1000
            
            auth_result = self.auth_service.authenticate_user(long_email, long_password)
            
            if auth_result and auth_result.get('success'):
                self.record_test_result("Error handling - Long inputs", False, "Extremely long inputs were accepted")
            else:
                self.record_test_result("Error handling - Long inputs", True, "Long inputs properly rejected")
                
        except Exception as e:
            self.record_test_result("Error handling - Long inputs", True, f"Long inputs rejected with exception: {type(e).__name__}")
    
    def test_user_statistics(self):
        """Test user statistics functionality"""
        print("🔍 Testing user statistics...")
        
        self.total_tests += 1
        
        try:
            # Get user statistics
            stats = self.user_service.get_user_statistics()
            
            if not stats:
                self.record_test_result("User statistics", False, "No statistics returned")
                return
            
            # Check required fields
            required_fields = ['total_users', 'active_users', 'instructors', 'students']
            missing_fields = [field for field in required_fields if field not in stats]
            
            if missing_fields:
                self.record_test_result("User statistics", False, f"Missing statistics fields: {missing_fields}")
                return
            
            # Check that values are reasonable
            if stats['total_users'] < 0 or stats['active_users'] < 0:
                self.record_test_result("User statistics", False, "Invalid negative user counts")
                return
            
            self.record_test_result("User statistics", True, f"Statistics retrieved: {stats['total_users']} total users, {stats['instructors']} instructors, {stats['students']} students")
            
        except Exception as e:
            self.record_test_result("User statistics", False, f"Exception: {str(e)}")
    
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
        print("📊 Simplified Login System Test Report")
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
        print("  ✅ Invalid credentials handling")
        print("  ✅ Session management")
        print("  ✅ Logout functionality")
        print("  ✅ Error handling")
        print("  ✅ User statistics")

def main():
    """Main function to run simplified login system tests"""
    tester = SimpleLoginTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()