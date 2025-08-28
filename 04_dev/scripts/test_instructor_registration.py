#!/usr/bin/env python3
"""
Instructor Registration Testing Script for QuizGenius MVP

This script tests the instructor registration functionality including:
- Form validation
- Cognito integration
- DynamoDB user profile creation
- Email verification workflow
- Error handling
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
from utils.config import load_environment_config

class InstructorRegistrationTester:
    """Test class for instructor registration functionality"""
    
    def __init__(self):
        """Initialize the tester"""
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
        # Test data
        self.test_email = f"test_instructor_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "TestPass123!"
        self.test_user_data = {
            'first_name': 'Test',
            'last_name': 'Instructor',
            'email': self.test_email,
            'role': 'instructor',
            'institution': 'Test University',
            'department': 'Computer Science',
            'preferences': {
                'email_notifications': True,
                'newsletter': False
            }
        }
    
    def run_all_tests(self):
        """Run all instructor registration tests"""
        print("🧪 Instructor Registration Testing for QuizGenius MVP")
        print("=" * 60)
        
        try:
            # Load configuration
            load_environment_config()
            
            # Initialize services
            self.auth_service = AuthService()
            self.user_service = UserService()
            
            print("✅ Services initialized successfully")
            print()
            
            # Run tests
            self.test_form_validation()
            self.test_instructor_registration_flow()
            self.test_duplicate_email_handling()
            self.test_password_requirements()
            self.test_user_profile_creation()
            self.test_error_handling()
            
            # Cleanup
            self.cleanup_test_data()
            
        except Exception as e:
            print(f"❌ Test setup error: {str(e)}")
            return
        
        # Print results
        self.print_test_results()
    
    def test_form_validation(self):
        """Test form validation logic"""
        print("🔍 Testing form validation...")
        
        # Import validation function
        from pages.instructor_registration import validate_instructor_registration
        
        test_cases = [
            {
                'name': 'Valid data',
                'data': ('John', 'Doe', 'john@example.com', 'Password123!', 'Password123!', True, True),
                'should_pass': True
            },
            {
                'name': 'Missing first name',
                'data': ('', 'Doe', 'john@example.com', 'Password123!', 'Password123!', True, True),
                'should_pass': False
            },
            {
                'name': 'Short first name',
                'data': ('J', 'Doe', 'john@example.com', 'Password123!', 'Password123!', True, True),
                'should_pass': False
            },
            {
                'name': 'Invalid email',
                'data': ('John', 'Doe', 'invalid-email', 'Password123!', 'Password123!', True, True),
                'should_pass': False
            },
            {
                'name': 'Weak password',
                'data': ('John', 'Doe', 'john@example.com', 'weak', 'weak', True, True),
                'should_pass': False
            },
            {
                'name': 'Password mismatch',
                'data': ('John', 'Doe', 'john@example.com', 'Password123!', 'Different123!', True, True),
                'should_pass': False
            },
            {
                'name': 'Terms not accepted',
                'data': ('John', 'Doe', 'john@example.com', 'Password123!', 'Password123!', False, True),
                'should_pass': False
            },
            {
                'name': 'Instructor terms not accepted',
                'data': ('John', 'Doe', 'john@example.com', 'Password123!', 'Password123!', True, False),
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            self.total_tests += 1
            
            try:
                errors = validate_instructor_registration(*test_case['data'])
                has_errors = len(errors) > 0
                
                if test_case['should_pass'] and not has_errors:
                    self.record_test_result(f"Form validation - {test_case['name']}", True, "Validation passed as expected")
                elif not test_case['should_pass'] and has_errors:
                    self.record_test_result(f"Form validation - {test_case['name']}", True, f"Validation failed as expected: {errors[0]}")
                else:
                    expected = "pass" if test_case['should_pass'] else "fail"
                    actual = "passed" if not has_errors else "failed"
                    self.record_test_result(f"Form validation - {test_case['name']}", False, f"Expected to {expected}, but {actual}")
                    
            except Exception as e:
                self.record_test_result(f"Form validation - {test_case['name']}", False, f"Exception: {str(e)}")
    
    def test_instructor_registration_flow(self):
        """Test complete instructor registration flow"""
        print("🔍 Testing instructor registration flow...")
        
        self.total_tests += 1
        
        try:
            # Step 1: Register with Cognito
            auth_result = self.auth_service.register_user(
                email=self.test_email,
                password=self.test_password,
                first_name=self.test_user_data['first_name'],
                last_name=self.test_user_data['last_name'],
                role='instructor'
            )
            
            if not auth_result['success']:
                self.record_test_result("Instructor registration flow", False, f"Cognito registration failed: {auth_result.get('message')}")
                return
            
            # Step 2: Create user profile in DynamoDB
            user_result = self.user_service.create_user(self.test_user_data)
            
            if not user_result['success']:
                self.record_test_result("Instructor registration flow", False, f"User profile creation failed: {user_result.get('message')}")
                return
            
            # Step 3: Verify user was created
            created_user = self.user_service.get_user_by_email(self.test_email)
            
            if not created_user:
                self.record_test_result("Instructor registration flow", False, "User not found after creation")
                return
            
            # Verify user data
            if (created_user['role'] == 'instructor' and 
                created_user['first_name'] == self.test_user_data['first_name'] and
                created_user['last_name'] == self.test_user_data['last_name']):
                
                self.record_test_result("Instructor registration flow", True, "Complete registration flow successful")
            else:
                self.record_test_result("Instructor registration flow", False, "User data mismatch after creation")
                
        except Exception as e:
            self.record_test_result("Instructor registration flow", False, f"Exception: {str(e)}")
    
    def test_duplicate_email_handling(self):
        """Test handling of duplicate email registration"""
        print("🔍 Testing duplicate email handling...")
        
        self.total_tests += 1
        
        try:
            # Try to register with the same email again
            auth_result = self.auth_service.register_user(
                email=self.test_email,  # Same email as previous test
                password=self.test_password,
                first_name="Another",
                last_name="User",
                role='instructor'
            )
            
            if auth_result['success']:
                self.record_test_result("Duplicate email handling", False, "Duplicate registration should have failed")
            else:
                error_msg = auth_result.get('message', '')
                if 'already exists' in error_msg.lower() or 'username' in error_msg.lower():
                    self.record_test_result("Duplicate email handling", True, "Duplicate email properly rejected")
                else:
                    self.record_test_result("Duplicate email handling", False, f"Unexpected error message: {error_msg}")
                    
        except AuthenticationError as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "UsernameExistsException" in error_msg:
                self.record_test_result("Duplicate email handling", True, "Duplicate email properly rejected with exception")
            else:
                self.record_test_result("Duplicate email handling", False, f"Unexpected authentication error: {error_msg}")
        except Exception as e:
            self.record_test_result("Duplicate email handling", False, f"Exception: {str(e)}")
    
    def test_password_requirements(self):
        """Test password requirement validation"""
        print("🔍 Testing password requirements...")
        
        weak_passwords = [
            ("short", "Too short"),
            ("alllowercase123", "No uppercase"),
            ("ALLUPPERCASE123", "No lowercase"),
            ("NoNumbers!", "No numbers")
            # Note: Special characters are not required by our Cognito policy
        ]
        
        for password, description in weak_passwords:
            self.total_tests += 1
            
            try:
                test_email = f"test_pwd_{uuid.uuid4().hex[:6]}@example.com"
                
                auth_result = self.auth_service.register_user(
                    email=test_email,
                    password=password,
                    first_name="Test",
                    last_name="User",
                    role='instructor'
                )
                
                if auth_result['success']:
                    self.record_test_result(f"Password requirements - {description}", False, "Weak password was accepted")
                    # Clean up if somehow created
                    try:
                        self.user_service.delete_user_by_email(test_email)
                    except:
                        pass
                else:
                    self.record_test_result(f"Password requirements - {description}", True, "Weak password properly rejected")
                    
            except AuthenticationError as e:
                error_msg = str(e)
                if "Password does not meet requirements" in error_msg or "InvalidPasswordException" in error_msg:
                    self.record_test_result(f"Password requirements - {description}", True, "Weak password properly rejected with exception")
                else:
                    self.record_test_result(f"Password requirements - {description}", False, f"Unexpected error: {error_msg}")
            except Exception as e:
                self.record_test_result(f"Password requirements - {description}", False, f"Exception: {str(e)}")
    
    def test_user_profile_creation(self):
        """Test user profile creation with instructor-specific fields"""
        print("🔍 Testing user profile creation...")
        
        self.total_tests += 1
        
        try:
            # Get the created user from previous test
            user = self.user_service.get_user_by_email(self.test_email)
            
            if not user:
                self.record_test_result("User profile creation", False, "User not found")
                return
            
            # Check required fields
            required_fields = ['user_id', 'email', 'first_name', 'last_name', 'role', 'created_date']
            missing_fields = [field for field in required_fields if field not in user or user[field] is None]
            
            if missing_fields:
                self.record_test_result("User profile creation", False, f"Missing required fields: {missing_fields}")
                return
            
            # Check instructor-specific fields
            if user['role'] != 'instructor':
                self.record_test_result("User profile creation", False, f"Incorrect role: {user['role']}")
                return
            
            # Check optional fields were stored
            optional_checks = []
            if 'institution' in user and user['institution']:
                optional_checks.append("institution stored")
            if 'department' in user and user['department']:
                optional_checks.append("department stored")
            if 'preferences' in user and user['preferences']:
                optional_checks.append("preferences stored")
            
            self.record_test_result("User profile creation", True, f"Profile created successfully. Optional fields: {', '.join(optional_checks) if optional_checks else 'none'}")
            
        except Exception as e:
            self.record_test_result("User profile creation", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("🔍 Testing error handling...")
        
        # Test invalid email format
        self.total_tests += 1
        
        try:
            auth_result = self.auth_service.register_user(
                email="invalid-email-format",
                password=self.test_password,
                first_name="Test",
                last_name="User",
                role='instructor'
            )
            
            if auth_result['success']:
                self.record_test_result("Error handling - Invalid email", False, "Invalid email was accepted")
            else:
                self.record_test_result("Error handling - Invalid email", True, "Invalid email properly rejected")
                
        except Exception as e:
            self.record_test_result("Error handling - Invalid email", True, f"Invalid email rejected with exception: {type(e).__name__}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        try:
            # Delete user from DynamoDB
            self.user_service.delete_user_by_email(self.test_email)
            print(f"  ✅ Deleted user from DynamoDB: {self.test_email}")
        except Exception as e:
            print(f"  ⚠️ Could not delete user from DynamoDB: {str(e)}")
        
        try:
            # Note: Cognito users cannot be easily deleted programmatically in test scenarios
            # In production, this would be handled through admin APIs
            print(f"  ℹ️ Cognito user cleanup: {self.test_email} (manual cleanup may be required)")
        except Exception as e:
            print(f"  ⚠️ Cognito cleanup note: {str(e)}")
    
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
        print("📊 Instructor Registration Test Report")
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
            print("\n🎉 All instructor registration tests passed!")
            print("\n🚀 Instructor registration functionality is ready!")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Please review and fix issues.")
        
        print("\n📋 Test Coverage:")
        print("  ✅ Form validation (multiple scenarios)")
        print("  ✅ Complete registration flow")
        print("  ✅ Duplicate email handling")
        print("  ✅ Password requirements")
        print("  ✅ User profile creation")
        print("  ✅ Error handling")

def main():
    """Main function to run instructor registration tests"""
    tester = InstructorRegistrationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()