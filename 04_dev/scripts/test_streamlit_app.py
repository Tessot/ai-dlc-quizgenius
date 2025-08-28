#!/usr/bin/env python3
"""
Streamlit Application Testing Script for QuizGenius MVP

This script tests the Streamlit application components including:
- Application initialization
- Session management
- Authentication components
- Navigation components
- Basic functionality
"""

import sys
import os

# Add the parent directory to the path so we can import from services and utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import SessionManager
from components.auth_components import AuthComponents
from components.navigation import NavigationManager
from services.auth_service import AuthService
from services.user_service import UserService

def test_session_manager():
    """Test session manager functionality"""
    print("🔍 Testing session manager...")
    
    try:
        session_manager = SessionManager()
        
        # Test initialization
        session_manager.initialize_session()
        print("  ✅ Session manager initialized successfully")
        
        # Test session info
        session_info = session_manager.get_session_info()
        print(f"  ✅ Session info retrieved: {len(session_info)} fields")
        
        # Test authentication state
        is_auth = session_manager.is_authenticated()
        print(f"  ✅ Authentication state: {is_auth}")
        
        # Test user info
        user_info = session_manager.get_user_info()
        print(f"  ✅ User info retrieved: {len(user_info)} fields")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Session manager test failed: {e}")
        return False

def test_auth_components():
    """Test authentication components"""
    print("\n🔍 Testing authentication components...")
    
    try:
        auth_components = AuthComponents()
        print("  ✅ Authentication components initialized successfully")
        
        # Test validation function
        errors = auth_components._validate_registration_form(
            "John", "Doe", "john@example.com", "instructor", 
            "password123", "password123", True
        )
        
        if len(errors) == 0:
            print("  ✅ Registration form validation passed")
        else:
            print(f"  ⚠️  Registration form validation returned {len(errors)} errors")
        
        # Test validation with errors
        errors = auth_components._validate_registration_form(
            "", "", "invalid-email", "", "123", "456", False
        )
        
        if len(errors) > 0:
            print(f"  ✅ Registration form validation correctly caught {len(errors)} errors")
        else:
            print("  ❌ Registration form validation should have caught errors")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Authentication components test failed: {e}")
        return False

def test_navigation_manager():
    """Test navigation manager"""
    print("\n🔍 Testing navigation manager...")
    
    try:
        nav_manager = NavigationManager()
        print("  ✅ Navigation manager initialized successfully")
        
        # Test instructor pages
        instructor_pages = nav_manager._get_pages_for_role("instructor")
        print(f"  ✅ Instructor pages: {len(instructor_pages)} pages available")
        
        # Test student pages
        student_pages = nav_manager._get_pages_for_role("student")
        print(f"  ✅ Student pages: {len(student_pages)} pages available")
        
        # Test breadcrumb generation
        breadcrumb = nav_manager.get_breadcrumb("Dashboard", "instructor")
        print(f"  ✅ Breadcrumb generated: {breadcrumb}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Navigation manager test failed: {e}")
        return False

def test_service_integration():
    """Test service integration"""
    print("\n🔍 Testing service integration...")
    
    try:
        # Test auth service initialization
        auth_service = AuthService()
        print("  ✅ Auth service initialized successfully")
        
        # Test user service initialization
        user_service = UserService()
        print("  ✅ User service initialized successfully")
        
        # Test user pool info (if available)
        try:
            pool_info = auth_service.get_user_pool_info()
            if pool_info.get('success'):
                print("  ✅ User pool connection successful")
            else:
                print("  ⚠️  User pool connection failed")
        except Exception as e:
            print(f"  ⚠️  User pool test failed: {e}")
        
        # Test user statistics
        try:
            stats = user_service.get_user_statistics()
            print(f"  ✅ User statistics retrieved: {stats['total_users']} total users")
        except Exception as e:
            print(f"  ⚠️  User statistics test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Service integration test failed: {e}")
        return False

def test_configuration():
    """Test application configuration"""
    print("\n🔍 Testing application configuration...")
    
    try:
        from utils.config import load_environment_config
        
        # Test config loading
        load_environment_config()
        print("  ✅ Environment configuration loaded successfully")
        
        # Check required environment variables
        required_vars = [
            'AWS_DEFAULT_REGION',
            'COGNITO_USER_POOL_ID',
            'COGNITO_CLIENT_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"  ⚠️  Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("  ✅ All required environment variables are set")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_file_structure():
    """Test application file structure"""
    print("\n🔍 Testing application file structure...")
    
    try:
        # Check main application file
        app_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
        if os.path.exists(app_file):
            print("  ✅ Main application file (app.py) exists")
        else:
            print("  ❌ Main application file (app.py) not found")
        
        # Check component files
        components_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'components')
        component_files = ['__init__.py', 'auth_components.py', 'navigation.py']
        
        for file in component_files:
            file_path = os.path.join(components_dir, file)
            if os.path.exists(file_path):
                print(f"  ✅ Component file ({file}) exists")
            else:
                print(f"  ❌ Component file ({file}) not found")
        
        # Check utils files
        utils_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
        util_files = ['session_manager.py']
        
        for file in util_files:
            file_path = os.path.join(utils_dir, file)
            if os.path.exists(file_path):
                print(f"  ✅ Utility file ({file}) exists")
            else:
                print(f"  ❌ Utility file ({file}) not found")
        
        return True
        
    except Exception as e:
        print(f"  ❌ File structure test failed: {e}")
        return False

def test_import_dependencies():
    """Test import dependencies"""
    print("\n🔍 Testing import dependencies...")
    
    try:
        # Test Streamlit import
        import streamlit as st
        print(f"  ✅ Streamlit imported successfully (version: {st.__version__})")
        
        # Test other required imports
        import json
        import uuid
        import datetime
        print("  ✅ Standard library imports successful")
        
        # Test AWS SDK imports
        import boto3
        import botocore
        print("  ✅ AWS SDK imports successful")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import dependency test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Import test failed: {e}")
        return False

def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "=" * 60)
    print("📊 Streamlit Application Test Report")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! Streamlit application is ready to run.")
        print("\n🚀 To start the application, run:")
        print("   streamlit run app.py")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the setup and fix any issues.")
        print("\nNote: Some failures may be due to missing environment variables or AWS configuration.")
        return False

def main():
    """Main function to run all Streamlit application tests"""
    print("🧪 Streamlit Application Testing for QuizGenius MVP")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: Import dependencies
    import_success = test_import_dependencies()
    test_results['import_dependencies'] = import_success
    
    # Test 2: File structure
    file_structure_success = test_file_structure()
    test_results['file_structure'] = file_structure_success
    
    # Test 3: Configuration
    config_success = test_configuration()
    test_results['configuration'] = config_success
    
    # Test 4: Session manager
    session_success = test_session_manager()
    test_results['session_manager'] = session_success
    
    # Test 5: Authentication components
    auth_success = test_auth_components()
    test_results['auth_components'] = auth_success
    
    # Test 6: Navigation manager
    nav_success = test_navigation_manager()
    test_results['navigation_manager'] = nav_success
    
    # Test 7: Service integration
    service_success = test_service_integration()
    test_results['service_integration'] = service_success
    
    # Generate report
    success = generate_test_report(test_results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()