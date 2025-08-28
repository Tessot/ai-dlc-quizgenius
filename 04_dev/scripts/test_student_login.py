#!/usr/bin/env python3
"""
Test Student Account Login for QuizGenius MVP
Simple script to test student login functionality
"""

import sys
import os

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService, AuthenticationError

def test_student_login():
    """Test student account login"""
    print("🧪 Testing Student Account Login")
    print("=" * 40)
    
    # Student credentials
    email = "test.student@example.com"
    password = "TestPass123!"
    
    print(f"📝 Testing login with:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    
    try:
        # Initialize auth service
        auth_service = AuthService()
        
        # Attempt login
        result = auth_service.authenticate_user(email=email, password=password)
        
        if result['success']:
            print(f"\n✅ LOGIN SUCCESSFUL!")
            
            # Display user info
            user_info = result.get('user_info', {})
            print(f"   • User Sub: {user_info.get('sub', 'Unknown')}")
            print(f"   • Email: {user_info.get('email', 'Unknown')}")
            print(f"   • Name: {user_info.get('given_name', '')} {user_info.get('family_name', '')}")
            print(f"   • Access Token: {result['access_token'][:20]}...")
            print(f"   • Token Expires In: {result['expires_in']} seconds")
            
            return True
        else:
            print(f"\n❌ LOGIN FAILED: {result}")
            return False
            
    except AuthenticationError as e:
        print(f"\n❌ AUTHENTICATION ERROR: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Main function"""
    success = test_student_login()
    
    print(f"\n" + "=" * 40)
    if success:
        print("🎉 Student account is ready for use!")
        print("\n🚀 You can now login to the app with:")
        print("   Email: test.student@example.com")
        print("   Password: TestPass123!")
    else:
        print("⚠️  Student account login failed")
        print("Check the error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)