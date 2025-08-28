#!/usr/bin/env python3
"""
Manual Test Account Creation Guide for QuizGenius MVP

This script provides instructions for manually creating test accounts
when AWS Cognito email limits are reached.
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

def get_cognito_info():
    """Get Cognito User Pool information"""
    try:
        session = get_aws_session()
        cognito_client = session.client('cognito-idp')
        
        user_pool_id = Config.COGNITO_USER_POOL_ID
        if not user_pool_id:
            print("❌ COGNITO_USER_POOL_ID not configured")
            return None
            
        # Get user pool details
        response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
        user_pool = response['UserPool']
        
        return {
            'user_pool_id': user_pool_id,
            'user_pool_name': user_pool.get('Name', 'Unknown'),
            'client_id': Config.COGNITO_CLIENT_ID
        }
        
    except Exception as e:
        print(f"❌ Error getting Cognito info: {e}")
        return None

def create_user_in_dynamodb(user_data):
    """Create user record in DynamoDB"""
    try:
        user_service = UserService()
        user_service.create_user(user_data)
        print(f"   ✅ DynamoDB record created for {user_data['email']}")
        return True
    except Exception as e:
        print(f"   ⚠️  DynamoDB record creation failed: {e}")
        return False

def main():
    """Main function to provide manual account creation instructions"""
    print("🔧 QuizGenius Test Account Creation Guide")
    print("=" * 60)
    
    # Test AWS credentials
    try:
        session = get_aws_session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials validated")
        print(f"   Account: {identity.get('Account', 'Unknown')}")
        print(f"   Region: {Config.AWS_REGION}")
    except Exception as e:
        print(f"❌ AWS credentials validation failed: {e}")
        return False
    
    # Get Cognito information
    cognito_info = get_cognito_info()
    if not cognito_info:
        return False
    
    print(f"\n📋 Cognito User Pool Information:")
    print(f"   User Pool ID: {cognito_info['user_pool_id']}")
    print(f"   User Pool Name: {cognito_info['user_pool_name']}")
    print(f"   Client ID: {cognito_info['client_id']}")
    
    # Test account credentials
    test_accounts = {
        'instructor': {
            'email': 'test.instructor@example.com',
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'Instructor',
            'role': 'instructor',
            'user_id': 'test-instructor-001'
        },
        'student': {
            'email': 'test.student@example.com',
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'Student',
            'role': 'student',
            'user_id': 'test-student-001'
        }
    }
    
    print(f"\n🎯 Test Account Credentials:")
    print(f"=" * 40)
    for account_type, data in test_accounts.items():
        print(f"\n{account_type.title()} Account:")
        print(f"   Email: {data['email']}")
        print(f"   Password: {data['password']}")
        print(f"   Name: {data['first_name']} {data['last_name']}")
        print(f"   Role: {data['role']}")
    
    print(f"\n📝 Manual Account Creation Steps:")
    print(f"=" * 40)
    print(f"1. Open AWS Console and navigate to Cognito")
    print(f"2. Go to User Pools → {cognito_info['user_pool_name']}")
    print(f"3. Click 'Users' tab")
    print(f"4. Click 'Create user' button")
    print(f"5. For each account above:")
    print(f"   • Username: Use the email address")
    print(f"   • Email: Use the email address")
    print(f"   • Temporary password: {test_accounts['instructor']['password']}")
    print(f"   • Uncheck 'Send an invitation to this new user'")
    print(f"   • Check 'Mark phone number as verified' (if available)")
    print(f"   • Check 'Mark email as verified'")
    print(f"6. After creating, click on each user and set permanent password")
    print(f"7. Set password to: {test_accounts['instructor']['password']}")
    
    print(f"\n🔧 Creating DynamoDB Records:")
    print(f"=" * 40)
    
    # Create DynamoDB records for the test accounts
    for account_type, data in test_accounts.items():
        print(f"\n📝 Creating {account_type} DynamoDB record...")
        
        user_data = {
            'user_id': data['user_id'],
            'email': data['email'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'role': data['role'],
            'status': 'active',
            'created_date': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add role-specific data
        if account_type == 'instructor':
            user_data.update({
                'institution': 'Test University',
                'department': 'Computer Science'
            })
        else:  # student
            user_data.update({
                'school': 'Test University',
                'grade_level': 'Undergraduate',
                'subject_interests': ['Computer Science', 'Mathematics']
            })
        
        create_user_in_dynamodb(user_data)
    
    print(f"\n🚀 Alternative: Use App Registration")
    print(f"=" * 40)
    print(f"If manual Cognito creation is complex, you can:")
    print(f"1. Launch the app: streamlit run app.py")
    print(f"2. Click 'Register as Instructor' and use:")
    print(f"   Email: {test_accounts['instructor']['email']}")
    print(f"   Password: {test_accounts['instructor']['password']}")
    print(f"3. Click 'Register as Student' and use:")
    print(f"   Email: {test_accounts['student']['email']}")
    print(f"   Password: {test_accounts['student']['password']}")
    print(f"4. If email verification is required, check AWS Cognito console")
    print(f"   and manually verify the users")
    
    print(f"\n✅ Setup Complete!")
    print(f"Once accounts are created, launch the app with:")
    print(f"   streamlit run app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)