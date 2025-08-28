#!/usr/bin/env python3
"""
Create Student Account Script for QuizGenius MVP

This script creates the student test account directly in Cognito
using admin privileges to bypass email verification.
"""

import sys
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config, get_aws_session
from services.user_service import UserService
from services.auth_service import AuthService

def create_cognito_user_admin(email, password, first_name, last_name):
    """Create user directly in Cognito using admin privileges"""
    try:
        session = get_aws_session()
        cognito_client = session.client('cognito-idp')
        
        user_pool_id = Config.COGNITO_USER_POOL_ID
        
        # Create user with admin privileges (no email verification needed)
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'given_name', 'Value': first_name},
                {'Name': 'family_name', 'Value': last_name}
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS',  # Don't send welcome email
            ForceAliasCreation=False
        )
        
        user_sub = None
        for attr in response['User']['Attributes']:
            if attr['Name'] == 'sub':
                user_sub = attr['Value']
                break
        
        print(f"   ✅ User created in Cognito")
        print(f"   • Username: {response['User']['Username']}")
        print(f"   • User Sub: {user_sub}")
        print(f"   • Status: {response['User']['UserStatus']}")
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        print(f"   ✅ Permanent password set")
        
        return True, user_sub
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            print(f"   ⚠️  User already exists")
            # Try to get existing user info
            try:
                user_response = cognito_client.admin_get_user(
                    UserPoolId=user_pool_id,
                    Username=email
                )
                user_sub = None
                for attr in user_response['UserAttributes']:
                    if attr['Name'] == 'sub':
                        user_sub = attr['Value']
                        break
                
                # Set permanent password anyway
                cognito_client.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=email,
                    Password=password,
                    Permanent=True
                )
                print(f"   ✅ Password updated for existing user")
                
                return True, user_sub
            except Exception as inner_e:
                print(f"   ❌ Error handling existing user: {inner_e}")
                return False, None
        else:
            print(f"   ❌ Error creating user: {e}")
            return False, None
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False, None

def create_dynamodb_record(user_sub, email, first_name, last_name, role):
    """Create user record in DynamoDB"""
    try:
        user_service = UserService()
        
        user_data = {
            'user_id': user_sub,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'status': 'active',
            'created_date': datetime.utcnow().isoformat() + 'Z',
            'school': 'Test University',
            'grade_level': 'Undergraduate',
            'subject_interests': ['Computer Science', 'Mathematics']
        }
        
        user_service.create_user(user_data)
        print(f"   ✅ DynamoDB record created")
        return True
        
    except Exception as e:
        print(f"   ⚠️  DynamoDB record creation failed: {e}")
        return False

def test_login(email, password):
    """Test login with the created account"""
    try:
        auth_service = AuthService()
        
        result = auth_service.authenticate_user(email=email, password=password)
        
        if result['success']:
            print(f"   ✅ Login test successful!")
            user_info = result.get('user_info', {})
            print(f"   • User Sub: {user_info.get('sub', 'Unknown')}")
            print(f"   • Email: {user_info.get('email', 'Unknown')}")
            return True
        else:
            print(f"   ❌ Login test failed: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Login test error: {e}")
        return False

def main():
    """Main function to create student account"""
    print("🎓 Creating Student Test Account")
    print("=" * 40)
    
    # Student account details
    student_data = {
        'email': 'test.student@example.com',
        'password': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'Student',
        'role': 'student'
    }
    
    print(f"📝 Creating student account:")
    print(f"   Email: {student_data['email']}")
    print(f"   Password: {student_data['password']}")
    print(f"   Name: {student_data['first_name']} {student_data['last_name']}")
    
    # Create Cognito user
    print(f"\n🔧 Creating user in Cognito...")
    success, user_sub = create_cognito_user_admin(
        student_data['email'],
        student_data['password'],
        student_data['first_name'],
        student_data['last_name']
    )
    
    if not success:
        print(f"❌ Failed to create Cognito user")
        return False
    
    # Create DynamoDB record
    print(f"\n📊 Creating DynamoDB record...")
    db_success = create_dynamodb_record(
        user_sub,
        student_data['email'],
        student_data['first_name'],
        student_data['last_name'],
        student_data['role']
    )
    
    # Test login
    print(f"\n🧪 Testing login...")
    login_success = test_login(student_data['email'], student_data['password'])
    
    # Summary
    print(f"\n" + "=" * 40)
    print(f"📊 Student Account Creation Summary:")
    print(f"   • Cognito User: {'✅ Created' if success else '❌ Failed'}")
    print(f"   • DynamoDB Record: {'✅ Created' if db_success else '❌ Failed'}")
    print(f"   • Login Test: {'✅ Passed' if login_success else '❌ Failed'}")
    
    if success and login_success:
        print(f"\n🎉 Student account ready!")
        print(f"\n🎯 Test Credentials:")
        print(f"   Email: {student_data['email']}")
        print(f"   Password: {student_data['password']}")
        print(f"\n🚀 You can now test both accounts in the app:")
        print(f"   streamlit run app.py")
        return True
    else:
        print(f"\n⚠️  Account creation had issues. Check output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)