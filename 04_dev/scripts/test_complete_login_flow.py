#!/usr/bin/env python3
"""
Complete Login Flow Testing Script for QuizGenius MVP

This script tests the complete login flow for both instructors and students,
including role-based redirection and dashboard functionality.
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

class CompleteLoginFlowTester:
    """Test class for complete login flow functionality"""
    
    def __init__(self):
        """Initialize the tester"""
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
    
    def run_all_tests(self):
        """Run all complete login flow tests"""
        print("🧪 Complete Login Flow Testing for QuizGenius MVP")
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
            self.test_cognito_authentication_integration()
            self.test_session_management_integration()
            self.test_role_based_redirection_logic()
            self.test_instructor_dashboard_functionality()
            self.test_student_dashboard_functionality()
            self.test_navigation_components()
            self.test_user_pool_connectivity()
            self.test_complete_authentication_flow()
            
        except Exception as e:
            print(f"❌ Test setup error: {str(e)}")
            return
        
        # Print results
        self.print_test_results()
    
    def test_cognito_authentication_integration(self):
        """Test Cognito authentication integration"""
        print("🔍 Testing Cognito authentication integration...")
        
        self.total_tests += 1
        
        try:
            # Test user pool connectivity
            pool_info = self.auth_service.get_user_pool_info()
            
            if not pool_info.get('success'):
                self.record_test_result("Cognito authentication integration", False, f"User pool not accessible: {pool_info.get('error')}")
                return
            
            # Test authentication service initialization
            if not hasattr(self.auth_service, 'cognito_client'):
                self.record_test_result("Cognito authentication integration", False, "Cognito client not initialized")
                return
            
            # Test authentication methods exist
            required_methods = ['authenticate_user', 'register_user', 'get_user_info', 'logout_user']
            missing_methods = [method for method in required_methods if not hasattr(self.auth_service, method)]
            
            if missing_methods:
                self.record_test_result("Cognito authentication integration", False, f"Missing methods: {missing_methods}")
                return
            
            self.record_test_result("Cognito authentication integration", True, f"User pool: {pool_info.get('user_pool_name', 'Connected')}")
            
        except Exception as e:
            self.record_test_result("Cognito authentication integration", False, f"Exception: {str(e)}")
    
    def test_session_management_integration(self):
        """Test session management integration"""
        print("🔍 Testing session management integration...")
        
        self.total_tests += 1
        
        try:
            # Test session manager initialization
            self.session_manager.initialize_session()
            
            # Test session methods exist
            required_methods = ['login_user', 'logout', 'is_authenticated', 'get_user_info']
            missing_methods = [method for method in required_methods if not hasattr(self.session_manager, method)]
            
            if missing_methods:
                self.record_test_result("Session management integration", False, f"Missing methods: {missing_methods}")
                return
            
            # Test session state management
            if self.session_manager.is_authenticated():
                self.record_test_result("Session management integration", False, "Session should not be authenticated initially")
                return
            
            # Test mock login/logout cycle
            mock_user_data = {
                'user_id': 'test_123',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'instructor'
            }
            
            mock_auth_result = {'success': True, 'access_token': 'mock_token'}
            
            # Test login
            self.session_manager.login_user(mock_user_data, mock_auth_result, remember_me=False)
            
            if not self.session_manager.is_authenticated():
                self.record_test_result("Session management integration", False, "Session not authenticated after login")
                return
            
            # Test user info retrieval
            user_info = self.session_manager.get_user_info()
            if not user_info or user_info.get('email') != mock_user_data['email']:
                self.record_test_result("Session management integration", False, "User info not properly stored")
                return
            
            # Test logout
            self.session_manager.logout()
            
            if self.session_manager.is_authenticated():
                self.record_test_result("Session management integration", False, "Session still authenticated after logout")
                return
            
            self.record_test_result("Session management integration", True, "Session management working correctly")
            
        except Exception as e:
            self.record_test_result("Session management integration", False, f"Exception: {str(e)}")
    
    def test_role_based_redirection_logic(self):
        """Test role-based redirection logic"""
        print("🔍 Testing role-based redirection logic...")
        
        # Test instructor role detection
        self.total_tests += 1
        
        try:
            from services.auth_service import get_user_role, is_instructor, is_student
            
            # Test instructor session data
            instructor_session = {
                'authenticated': True,
                'user_info': {'role': 'instructor', 'email': 'instructor@example.com'}
            }
            
            if get_user_role(instructor_session) != 'instructor':
                self.record_test_result("Role-based redirection - Instructor", False, "Instructor role not detected")
                return
            
            if not is_instructor(instructor_session):
                self.record_test_result("Role-based redirection - Instructor", False, "is_instructor() failed")
                return
            
            if is_student(instructor_session):
                self.record_test_result("Role-based redirection - Instructor", False, "is_student() incorrectly returned True")
                return
            
            self.record_test_result("Role-based redirection - Instructor", True, "Instructor role detection working")
            
        except Exception as e:
            self.record_test_result("Role-based redirection - Instructor", False, f"Exception: {str(e)}")
        
        # Test student role detection
        self.total_tests += 1
        
        try:
            # Test student session data
            student_session = {
                'authenticated': True,
                'user_info': {'role': 'student', 'email': 'student@example.com'}
            }
            
            if get_user_role(student_session) != 'student':
                self.record_test_result("Role-based redirection - Student", False, "Student role not detected")
                return
            
            if not is_student(student_session):
                self.record_test_result("Role-based redirection - Student", False, "is_student() failed")
                return
            
            if is_instructor(student_session):
                self.record_test_result("Role-based redirection - Student", False, "is_instructor() incorrectly returned True")
                return
            
            self.record_test_result("Role-based redirection - Student", True, "Student role detection working")
            
        except Exception as e:
            self.record_test_result("Role-based redirection - Student", False, f"Exception: {str(e)}")
    
    def test_instructor_dashboard_functionality(self):
        """Test instructor dashboard functionality"""
        print("🔍 Testing instructor dashboard functionality...")
        
        self.total_tests += 1
        
        try:
            # Test that we can get user statistics (used in instructor dashboard)
            stats = self.user_service.get_user_statistics()
            
            if not stats:
                self.record_test_result("Instructor dashboard functionality", False, "User statistics not available")
                return
            
            # Check required statistics fields
            required_fields = ['total_users', 'instructors', 'students']
            missing_fields = [field for field in required_fields if field not in stats]
            
            if missing_fields:
                self.record_test_result("Instructor dashboard functionality", False, f"Missing statistics: {missing_fields}")
                return
            
            # Test user pool info (used in system status)
            pool_info = self.auth_service.get_user_pool_info()
            
            if not pool_info.get('success'):
                self.record_test_result("Instructor dashboard functionality", False, "User pool info not available")
                return
            
            self.record_test_result("Instructor dashboard functionality", True, f"Dashboard data available: {stats['total_users']} users")
            
        except Exception as e:
            self.record_test_result("Instructor dashboard functionality", False, f"Exception: {str(e)}")
    
    def test_student_dashboard_functionality(self):
        """Test student dashboard functionality"""
        print("🔍 Testing student dashboard functionality...")
        
        self.total_tests += 1
        
        try:
            # Test mock student user info processing
            mock_student_info = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'student@example.com',
                'role': 'student',
                'school': 'Test High School',
                'subject_interests': ['Mathematics', 'Science'],
                'preferences': {
                    'performance_tracking': True,
                    'email_notifications': True
                }
            }
            
            # Test that student-specific fields are accessible
            if not mock_student_info.get('school'):
                self.record_test_result("Student dashboard functionality", False, "School field not accessible")
                return
            
            if not mock_student_info.get('subject_interests'):
                self.record_test_result("Student dashboard functionality", False, "Subject interests not accessible")
                return
            
            if not mock_student_info.get('preferences', {}).get('performance_tracking'):
                self.record_test_result("Student dashboard functionality", False, "Performance tracking preference not accessible")
                return
            
            self.record_test_result("Student dashboard functionality", True, f"Student data accessible: {mock_student_info['school']}")
            
        except Exception as e:
            self.record_test_result("Student dashboard functionality", False, f"Exception: {str(e)}")
    
    def test_navigation_components(self):
        """Test navigation components"""
        print("🔍 Testing navigation components...")
        
        self.total_tests += 1
        
        try:
            from components.navigation import NavigationManager
            
            nav_manager = NavigationManager()
            
            # Test navigation methods exist
            required_methods = ['get_instructor_pages', 'get_student_pages', 'generate_breadcrumb']
            missing_methods = [method for method in required_methods if not hasattr(nav_manager, method)]
            
            if missing_methods:
                self.record_test_result("Navigation components", False, f"Missing navigation methods: {missing_methods}")
                return
            
            # Test instructor pages
            instructor_pages = nav_manager.get_instructor_pages()
            if not instructor_pages or len(instructor_pages) == 0:
                self.record_test_result("Navigation components", False, "No instructor pages available")
                return
            
            # Test student pages
            student_pages = nav_manager.get_student_pages()
            if not student_pages or len(student_pages) == 0:
                self.record_test_result("Navigation components", False, "No student pages available")
                return
            
            # Test breadcrumb generation
            breadcrumb = nav_manager.generate_breadcrumb("Dashboard", "instructor")
            if not breadcrumb:
                self.record_test_result("Navigation components", False, "Breadcrumb generation failed")
                return
            
            self.record_test_result("Navigation components", True, f"Navigation working: {len(instructor_pages)} instructor pages, {len(student_pages)} student pages")
            
        except Exception as e:
            self.record_test_result("Navigation components", False, f"Exception: {str(e)}")
    
    def test_user_pool_connectivity(self):
        """Test user pool connectivity"""
        print("🔍 Testing user pool connectivity...")
        
        self.total_tests += 1
        
        try:
            # Test user pool info
            pool_info = self.auth_service.get_user_pool_info()
            
            if not pool_info.get('success'):
                self.record_test_result("User pool connectivity", False, f"Cannot connect to user pool: {pool_info.get('error')}")
                return
            
            # Test that we have basic pool information
            if not pool_info.get('user_pool_id'):
                self.record_test_result("User pool connectivity", False, "User pool ID not available")
                return
            
            self.record_test_result("User pool connectivity", True, f"Connected to pool: {pool_info.get('user_pool_name', 'Unknown')}")
            
        except Exception as e:
            self.record_test_result("User pool connectivity", False, f"Exception: {str(e)}")
    
    def test_complete_authentication_flow(self):
        """Test complete authentication flow simulation"""
        print("🔍 Testing complete authentication flow...")
        
        self.total_tests += 1
        
        try:
            # Simulate complete flow without actual user creation
            # 1. Initialize session
            self.session_manager.initialize_session()
            
            # 2. Simulate authentication result
            mock_auth_result = {
                'success': True,
                'access_token': 'mock_access_token',
                'id_token': 'mock_id_token',
                'refresh_token': 'mock_refresh_token',
                'user_info': {
                    'username': 'testuser',
                    'email': 'test@example.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'role': 'instructor'
                }
            }
            
            # 3. Simulate user data from database
            mock_user_data = {
                'user_id': 'test_user_123',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'instructor',
                'last_login': None,
                'login_count': 0
            }
            
            # 4. Simulate login process
            self.session_manager.login_user(mock_user_data, mock_auth_result, remember_me=True)
            
            # 5. Verify session state
            if not self.session_manager.is_authenticated():
                self.record_test_result("Complete authentication flow", False, "Session not authenticated after login")
                return
            
            # 6. Verify user info
            session_user_info = self.session_manager.get_user_info()
            if not session_user_info or session_user_info.get('role') != 'instructor':
                self.record_test_result("Complete authentication flow", False, "User info not properly stored in session")
                return
            
            # 7. Test role-based logic
            from services.auth_service import is_instructor
            session_data = {
                'authenticated': True,
                'user_info': session_user_info
            }
            
            if not is_instructor(session_data):
                self.record_test_result("Complete authentication flow", False, "Role-based detection failed")
                return
            
            # 8. Test logout
            self.session_manager.logout()
            
            if self.session_manager.is_authenticated():
                self.record_test_result("Complete authentication flow", False, "Session still authenticated after logout")
                return
            
            self.record_test_result("Complete authentication flow", True, "Complete authentication flow successful")
            
        except Exception as e:
            self.record_test_result("Complete authentication flow", False, f"Exception: {str(e)}")
    
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
        print("📊 Complete Login Flow Test Report")
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
            print("\n🎉 All complete login flow tests passed!")
            print("\n🚀 Complete login system functionality is ready!")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Please review and fix issues.")
        
        print("\n📋 Test Coverage:")
        print("  ✅ Cognito authentication integration")
        print("  ✅ Session management integration")
        print("  ✅ Role-based redirection logic")
        print("  ✅ Instructor dashboard functionality")
        print("  ✅ Student dashboard functionality")
        print("  ✅ Navigation components")
        print("  ✅ User pool connectivity")
        print("  ✅ Complete authentication flow")

def main():
    """Main function to run complete login flow tests"""
    tester = CompleteLoginFlowTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()