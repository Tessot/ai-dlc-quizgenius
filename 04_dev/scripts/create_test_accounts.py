#!/usr/bin/env python3
"""
Create Test Accounts Script for QuizGenius MVP

This script creates test accounts in AWS Cognito and DynamoDB for easy testing.
Creates both instructor and student test accounts with known credentials.
"""

import sys
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService, AuthenticationError
from services.user_service import UserService, UserServiceError
from utils.config import Config, get_aws_session

class TestAccountCreator:
    """Creates and manages test accounts for QuizGenius MVP"""
    
    def __init__(self):
        """Initialize the test account creator"""
        self.auth_service = AuthService()
        self.user_service = UserService()
        
        # Test account credentials
        self.test_accounts = {
            'instructor': {
                'email': 'test.instructor@example.com',
                'password': 'TestPass123!',
                'first_name': 'Test',
                'last_name': 'Instructor',
                'role': 'instructor'
            },
            'student': {
                'email': 'test.student@example.com',
                'password': 'TestPass123!',
                'first_name': 'Test',
                'last_name': 'Student',
                'role': 'student'
            }
        }
    
    def create_test_account(self, account_type):
        """Create a single test account"""
        account_data = self.test_accounts[account_type]
        
        print(f"\n🔧 Creating {account_type} test account...")
        print(f"   Email: {account_data['email']}")
        print(f"   Password: {account_data['password']}")
        
        try:
            # Register user in Cognito
            result = self.auth_service.register_user(
                email=account_data['email'],
                password=account_data['password'],
                first_name=account_data['first_name'],
                last_name=account_data['last_name'],
                role=account_data['role']
            )
            
            if result['success']:
                print(f"   ✅ Cognito registration successful")
                print(f"   • User Sub: {result['user_sub']}")
                
                # If confirmation is required, we'll auto-confirm for test accounts
                if result.get('confirmation_required', False):
                    print(f"   📧 Confirmation required - attempting auto-confirmation...")
                    
                    # For test accounts, we'll try to auto-confirm
                    try:
                        self.auto_confirm_user(account_data['email'])
                        print(f"   ✅ User auto-confirmed successfully")
                    except Exception as e:
                        print(f"   ⚠️  Auto-confirmation failed: {e}")
                        print(f"   📝 Manual confirmation may be required")
                
                # Create user record in DynamoDB
                try:
                    user_data = {
                        'user_id': result['user_sub'],
                        'email': account_data['email'],
                        'first_name': account_data['first_name'],
                        'last_name': account_data['last_name'],
                        'role': account_data['role'],
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
                    
                    # Save to DynamoDB
                    self.user_service.create_user(user_data)
                    print(f"   ✅ DynamoDB record created successfully")
                    
                except Exception as e:
                    print(f"   ⚠️  DynamoDB record creation failed: {e}")
                
                return True, account_data
                
            else:
                print(f"   ❌ Registration failed: {result}")
                return False, None
                
        except AuthenticationError as e:
            if "already exists" in str(e).lower():
                print(f"   ⚠️  Account already exists - this is expected for repeated runs")
                return True, account_data
            else:
                print(f"   ❌ Authentication error: {e}")
                return False, None
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False, None
    
    def auto_confirm_user(self, email):
        """Auto-confirm user for testing purposes"""
        try:
            # Get Cognito client
            session = Config.get_boto3_session()
            cognito_client = session.client('cognito-idp')
            
            # Get user pool ID from config
            user_pool_id = Config.COGNITO_USER_POOL_ID
            
            if not user_pool_id:
                raise Exception("COGNITO_USER_POOL_ID not configured")
            
            # Admin confirm user (requires admin privileges)
            cognito_client.admin_confirm_sign_up(
                UserPoolId=user_pool_id,
                Username=email
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotAuthorizedException':
                print(f"   ⚠️  Admin privileges required for auto-confirmation")
            else:
                raise e
    
    def test_login(self, account_type):
        """Test login functionality for the created account"""
        account_data = self.test_accounts[account_type]
        
        print(f"\n🧪 Testing {account_type} login...")
        print(f"   Email: {account_data['email']}")
        print(f"   Password: {account_data['password']}")
        
        try:
            # Attempt authentication
            result = self.auth_service.authenticate_user(
                email=account_data['email'],
                password=account_data['password']
            )
            
            if result['success']:
                print(f"   ✅ Login successful!")
                print(f"   • Access Token: {result['access_token'][:20]}...")
                print(f"   • User Sub: {result['user_sub']}")
                
                # Test user data retrieval
                try:
                    user_data = self.user_service.get_user_by_email(account_data['email'])
                    if user_data:
                        print(f"   ✅ User data retrieved successfully")
                        print(f"   • Name: {user_data['first_name']} {user_data['last_name']}")
                        print(f"   • Role: {user_data['role']}")
                    else:
                        print(f"   ⚠️  User data not found in DynamoDB")
                except Exception as e:
                    print(f"   ⚠️  User data retrieval failed: {e}")
                
                return True
            else:
                print(f"   ❌ Login failed: {result}")
                return False
                
        except AuthenticationError as e:
            if "not confirmed" in str(e).lower():
                print(f"   ⚠️  User not confirmed - manual confirmation required")
                print(f"   📧 Check email for confirmation code or use AWS Console")
                return False
            else:
                print(f"   ❌ Authentication error: {e}")
                return False
        except Exception as e:
            print(f"   ❌ Unexpected error during login test: {e}")
            return False
    
    def create_all_test_accounts(self):
        """Create all test accounts and test login"""
        print("🚀 Creating QuizGenius Test Accounts")
        print("=" * 60)
        
        success_count = 0
        total_accounts = len(self.test_accounts)
        
        # Create accounts
        for account_type in self.test_accounts.keys():
            success, account_data = self.create_test_account(account_type)
            if success:
                success_count += 1
        
        print(f"\n📊 Account Creation Summary:")
        print(f"   • Created: {success_count}/{total_accounts} accounts")
        
        # Test logins
        print(f"\n🧪 Testing Login Functionality")
        print("-" * 40)
        
        login_success_count = 0
        for account_type in self.test_accounts.keys():
            if self.test_login(account_type):
                login_success_count += 1
        
        print(f"\n📊 Login Test Summary:")
        print(f"   • Successful logins: {login_success_count}/{total_accounts}")
        
        # Final summary
        print(f"\n" + "=" * 60)
        if success_count == total_accounts and login_success_count == total_accounts:
            print("✅ ALL TEST ACCOUNTS CREATED AND VERIFIED!")
            print("\n🎯 Ready to use credentials:")
            for account_type, data in self.test_accounts.items():
                print(f"\n{account_type.title()} Account:")
                print(f"   Email: {data['email']}")
                print(f"   Password: {data['password']}")
        else:
            print("⚠️  Some accounts may need manual confirmation")
            print("📧 Check email or AWS Cognito Console for confirmation")
        
        return success_count == total_accounts and login_success_count == total_accounts

def main():
    """Main function"""
    try:
        # Test AWS credentials first
        print("🔧 Testing AWS credentials...")
        try:
            session = get_aws_session()
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ AWS credentials validated")
            print(f"   Account: {identity.get('Account', 'Unknown')}")
            print(f"   Region: {Config.AWS_REGION}")
        except Exception as e:
            print(f"❌ AWS credentials validation failed: {e}")
            print("Please ensure AWS CLI is configured or set AWS credentials")
            return False
        
        # Create test accounts
        creator = TestAccountCreator()
        success = creator.create_all_test_accounts()
        
        if success:
            print(f"\n🎉 Test accounts ready! Launch the app with:")
            print(f"   streamlit run app.py")
            return True
        else:
            print(f"\n⚠️  Some issues occurred. Check output above.")
            return False
            
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)