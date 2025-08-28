#!/usr/bin/env python3
"""
Setup Test User Passwords for QuizGenius MVP

This script helps set permanent passwords for test users in Cognito
and tests the login functionality.
"""

import sys
import os
import boto3
from botocore.exceptions import ClientError

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config, get_aws_session
from services.auth_service import AuthService, AuthenticationError

def set_permanent_password(username, password):
    """Set permanent password for a Cognito user"""
    try:
        session = get_aws_session()
        cognito_client = session.client('cognito-idp')
        
        user_pool_id = Config.COGNITO_USER_POOL_ID
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True
        )
        
        print(f"   ✅ Permanent password set for {username}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            print(f"   ⚠️  Admin privileges required to set password")
        else:
            print(f"   ❌ Error setting password: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_login(email, password):
    """Test login with the given credentials"""
    try:
        auth_service = AuthService()
        
        result = auth_service.authenticate_user(
            email=email,
            password=password
        )
        
        if result['success']:
            print(f"   ✅ Login successful!")
            user_info = result.get('user_info', {})
            print(f"   • User Sub: {user_info.get('sub', 'Unknown')}")
            print(f"   • Access Token: {result['access_token'][:20]}...")
            return True
        else:
            print(f"   ❌ Login failed: {result}")
            return False
            
    except AuthenticationError as e:
        if "password" in str(e).lower():
            print(f"   ⚠️  Password needs to be changed: {e}")
            return False
        else:
            print(f"   ❌ Authentication error: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Setting up Test User Passwords")
    print("=" * 50)
    
    # Test credentials
    test_users = [
        {
            'email': 'test.instructor@example.com',
            'password': 'TestPass123!',
            'username': '7be006f9-3211-4b03-aaa0-4822fe86b3c5',  # From your Cognito output
            'role': 'instructor'
        },
        {
            'email': 'test.student@example.com',
            'password': 'TestPass123!',
            'username': 'test.student@example.com',  # Assuming email as username
            'role': 'student'
        }
    ]
    
    # Set permanent passwords
    print("\n🔑 Setting permanent passwords...")
    for user in test_users:
        print(f"\n📝 Setting password for {user['role']}: {user['email']}")
        set_permanent_password(user['username'], user['password'])
    
    # Test logins
    print(f"\n🧪 Testing login functionality...")
    success_count = 0
    
    for user in test_users:
        print(f"\n🔐 Testing {user['role']} login:")
        print(f"   Email: {user['email']}")
        print(f"   Password: {user['password']}")
        
        if test_login(user['email'], user['password']):
            success_count += 1
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"📊 Setup Summary:")
    print(f"   • Users processed: {len(test_users)}")
    print(f"   • Successful logins: {success_count}/{len(test_users)}")
    
    if success_count == len(test_users):
        print(f"\n🎉 All test accounts are ready!")
        print(f"\n🚀 Launch the app with:")
        print(f"   streamlit run app.py")
        print(f"\n🎯 Test Credentials:")
        for user in test_users:
            print(f"   {user['role'].title()}: {user['email']} / {user['password']}")
    else:
        print(f"\n⚠️  Some accounts may need manual setup in AWS Console")
        print(f"📋 Manual steps:")
        print(f"1. Go to AWS Cognito Console")
        print(f"2. Navigate to User Pools → QuizGenius-UserPool")
        print(f"3. Click on 'Users' tab")
        print(f"4. For each user with FORCE_CHANGE_PASSWORD status:")
        print(f"   • Click on the user")
        print(f"   • Click 'Actions' → 'Set password'")
        print(f"   • Set password to: TestPass123!")
        print(f"   • Check 'Set as permanent password'")
        print(f"   • Click 'Set password'")
    
    return success_count == len(test_users)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)