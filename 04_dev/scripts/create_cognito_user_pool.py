#!/usr/bin/env python3
"""
AWS Cognito User Pool Creation Script for QuizGenius MVP

This script creates and configures a Cognito User Pool for user authentication
with email verification, password policies, and custom attributes.
"""

import boto3
import json
import sys
import os
from botocore.exceptions import ClientError

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import get_aws_session

def create_user_pool(cognito_client):
    """Create Cognito User Pool with required configuration"""
    
    try:
        response = cognito_client.create_user_pool(
            PoolName='QuizGenius-UserPool',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False,
                    'TemporaryPasswordValidityDays': 7
                }
            },
            AutoVerifiedAttributes=['email'],
            UsernameAttributes=['email'],
            Schema=[
                {
                    'Name': 'email',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                },
                {
                    'Name': 'given_name',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                },
                {
                    'Name': 'family_name',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                },
                {
                    'Name': 'custom:role',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True,
                    'DeveloperOnlyAttribute': False,
                    'StringAttributeConstraints': {
                        'MinLength': '1',
                        'MaxLength': '20'
                    }
                }
            ],
            VerificationMessageTemplate={
                'DefaultEmailOption': 'CONFIRM_WITH_CODE',
                'EmailMessage': 'Welcome to QuizGenius! Your verification code is {####}',
                'EmailSubject': 'QuizGenius - Verify your email address'
            },
            EmailConfiguration={
                'EmailSendingAccount': 'COGNITO_DEFAULT'
            },
            AdminCreateUserConfig={
                'AllowAdminCreateUserOnly': False,
                'InviteMessageTemplate': {
                    'EmailMessage': 'Welcome to QuizGenius! Your username is {username} and temporary password is {####}',
                    'EmailSubject': 'Welcome to QuizGenius'
                }
            },
            UserPoolTags={
                'Project': 'QuizGenius',
                'Environment': 'Development',
                'Purpose': 'MVP-Authentication'
            }
        )
        
        user_pool_id = response['UserPool']['Id']
        print(f"✅ Created User Pool: {user_pool_id}")
        return user_pool_id
        
    except ClientError as e:
        print(f"❌ Error creating User Pool: {e}")
        raise

def create_user_pool_client(cognito_client, user_pool_id):
    """Create User Pool Client for application integration"""
    
    try:
        response = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='QuizGenius-WebApp',
            GenerateSecret=False,  # For web apps, typically no secret
            RefreshTokenValidity=30,  # 30 days
            AccessTokenValidity=60,   # 60 minutes
            IdTokenValidity=60,       # 60 minutes
            TokenValidityUnits={
                'AccessToken': 'minutes',
                'IdToken': 'minutes',
                'RefreshToken': 'days'
            },
            ExplicitAuthFlows=[
                'ALLOW_USER_SRP_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH',
                'ALLOW_USER_PASSWORD_AUTH'  # For development/testing
            ],
            PreventUserExistenceErrors='ENABLED',
            EnableTokenRevocation=True,
            SupportedIdentityProviders=['COGNITO']
        )
        
        client_id = response['UserPoolClient']['ClientId']
        print(f"✅ Created User Pool Client: {client_id}")
        return client_id
        
    except ClientError as e:
        print(f"❌ Error creating User Pool Client: {e}")
        raise

def update_environment_config(user_pool_id, client_id):
    """Update .env file with Cognito configuration"""
    
    env_file_path = '.env'
    
    # Read existing .env file
    env_vars = {}
    try:
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    except FileNotFoundError:
        print("⚠️  .env file not found, creating new one")
    
    # Update Cognito configuration
    env_vars['COGNITO_USER_POOL_ID'] = user_pool_id
    env_vars['COGNITO_CLIENT_ID'] = client_id
    
    # Write updated .env file
    with open(env_file_path, 'w') as f:
        f.write("# QuizGenius MVP Environment Configuration\n")
        f.write("# Generated by create_cognito_user_pool.py\n\n")
        
        f.write("# AWS Configuration\n")
        f.write(f"AWS_REGION={env_vars.get('AWS_REGION', 'us-east-1')}\n")
        f.write("# AWS_ACCESS_KEY_ID=your_access_key_here\n")
        f.write("# AWS_SECRET_ACCESS_KEY=your_secret_key_here\n\n")
        
        f.write("# AWS Cognito Configuration\n")
        f.write(f"COGNITO_USER_POOL_ID={user_pool_id}\n")
        f.write(f"COGNITO_CLIENT_ID={client_id}\n\n")
        
        f.write("# Application Configuration\n")
        f.write(f"DEBUG={env_vars.get('DEBUG', 'True')}\n")
        f.write(f"LOG_LEVEL={env_vars.get('LOG_LEVEL', 'INFO')}\n")
        f.write(f"SECRET_KEY={env_vars.get('SECRET_KEY', 'default-secret-key-change-in-production')}\n\n")
        
        f.write("# File Upload Configuration\n")
        f.write(f"MAX_FILE_SIZE_MB={env_vars.get('MAX_FILE_SIZE_MB', '10')}\n")
        f.write(f"ALLOWED_FILE_TYPES={env_vars.get('ALLOWED_FILE_TYPES', 'pdf')}\n")
    
    print(f"✅ Updated .env file with Cognito configuration")

def test_user_pool_configuration(cognito_client, user_pool_id, client_id):
    """Test the created User Pool configuration"""
    
    try:
        # Test User Pool description
        pool_response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
        pool_info = pool_response['UserPool']
        
        print("\n📋 User Pool Configuration:")
        print(f"  • Pool Name: {pool_info['Name']}")
        print(f"  • Pool ID: {pool_info['Id']}")
        print(f"  • Status: {pool_info.get('Status', 'ACTIVE')}")
        print(f"  • Auto Verified Attributes: {pool_info.get('AutoVerifiedAttributes', [])}")
        print(f"  • Username Attributes: {pool_info.get('UsernameAttributes', [])}")
        
        # Test User Pool Client description
        client_response = cognito_client.describe_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_id
        )
        client_info = client_response['UserPoolClient']
        
        print("\n📋 User Pool Client Configuration:")
        print(f"  • Client Name: {client_info['ClientName']}")
        print(f"  • Client ID: {client_info['ClientId']}")
        print(f"  • Auth Flows: {client_info.get('ExplicitAuthFlows', [])}")
        print(f"  • Token Validity: Access={client_info.get('AccessTokenValidity')}min, ID={client_info.get('IdTokenValidity')}min")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error testing User Pool configuration: {e}")
        return False

def main():
    """Main function to create Cognito User Pool"""
    print("🚀 Creating AWS Cognito User Pool for QuizGenius MVP")
    print("=" * 60)
    
    try:
        # Get AWS session
        session = get_aws_session()
        cognito_client = session.client('cognito-idp')
        
        # Create User Pool
        print("\n👥 Creating User Pool...")
        user_pool_id = create_user_pool(cognito_client)
        
        # Create User Pool Client
        print("\n📱 Creating User Pool Client...")
        client_id = create_user_pool_client(cognito_client, user_pool_id)
        
        # Update environment configuration
        print("\n⚙️  Updating environment configuration...")
        update_environment_config(user_pool_id, client_id)
        
        # Test configuration
        print("\n🧪 Testing User Pool configuration...")
        if test_user_pool_configuration(cognito_client, user_pool_id, client_id):
            print("\n" + "=" * 60)
            print("✅ Cognito User Pool created and configured successfully!")
            print("\n📝 Configuration Summary:")
            print(f"  • User Pool ID: {user_pool_id}")
            print(f"  • Client ID: {client_id}")
            print(f"  • Configuration saved to .env file")
            print("\n🔐 Features enabled:")
            print("  • Email-based authentication")
            print("  • Email verification required")
            print("  • Custom role attribute")
            print("  • Password policy enforced")
            print("  • Token-based sessions")
        else:
            print("\n⚠️  User Pool created but configuration test failed")
            
    except Exception as e:
        print(f"\n❌ Error during Cognito setup: {e}")
        raise

if __name__ == "__main__":
    main()