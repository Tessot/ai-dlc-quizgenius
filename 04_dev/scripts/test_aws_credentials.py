#!/usr/bin/env python3
"""
QuizGenius MVP - AWS Credentials Test Script

This script tests AWS credentials and service access.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from utils.config import Config


def test_aws_credentials():
    """Test AWS credentials and basic service access"""
    
    print("🔐 Testing AWS Credentials...")
    print("=" * 50)
    
    try:
        # Get boto3 session using our config
        session = Config.get_boto3_session()
        
        # Test STS (Security Token Service) to verify credentials
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"✅ AWS Credentials Valid")
        print(f"   Account ID: {identity.get('Account', 'N/A')}")
        print(f"   User ARN: {identity.get('Arn', 'N/A')}")
        print(f"   Region: {Config.AWS_REGION}")
        
        return True
        
    except NoCredentialsError:
        print("❌ No AWS credentials found!")
        print("   Please run 'aws configure' or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return False
        
    except ClientError as e:
        print(f"❌ AWS credentials error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_service_access():
    """Test access to required AWS services"""
    
    print("\n🔧 Testing AWS Service Access...")
    print("=" * 50)
    
    session = Config.get_boto3_session()
    services_to_test = [
        ('DynamoDB', 'dynamodb'),
        ('Bedrock Runtime', 'bedrock-runtime'),
        ('Cognito Identity Provider', 'cognito-idp'),
    ]
    
    results = []
    
    for service_name, service_code in services_to_test:
        try:
            client = session.client(service_code)
            
            # Test basic service access (this might fail due to permissions, but at least we can create the client)
            if service_code == 'dynamodb':
                # Try to list tables (might be empty, but should not fail with credentials)
                client.list_tables()
                print(f"✅ {service_name} - Access confirmed")
                
            elif service_code == 'bedrock-runtime':
                # For Bedrock, we can't easily test without making a real call
                # Just confirm we can create the client
                print(f"✅ {service_name} - Client created (access depends on region/permissions)")
                
            elif service_code == 'cognito-idp':
                # Try to list user pools (might be empty)
                client.list_user_pools(MaxResults=1)
                print(f"✅ {service_name} - Access confirmed")
            
            results.append((service_name, True))
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                print(f"⚠️  {service_name} - Access denied (check permissions)")
                results.append((service_name, 'permissions'))
            else:
                print(f"❌ {service_name} - Error: {error_code}")
                results.append((service_name, False))
                
        except Exception as e:
            print(f"❌ {service_name} - Unexpected error: {e}")
            results.append((service_name, False))
    
    return results


def main():
    """Run AWS credentials and service tests"""
    
    print("🚀 QuizGenius MVP - AWS Credentials Test")
    print("=" * 50)
    
    # Test basic credentials
    if not test_aws_credentials():
        print("\n❌ AWS credentials test failed. Please configure AWS CLI or environment variables.")
        return 1
    
    # Test service access
    service_results = test_service_access()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    credentials_ok = True
    services_ok = True
    
    for service_name, result in service_results:
        if result is True:
            print(f"  ✅ {service_name}")
        elif result == 'permissions':
            print(f"  ⚠️  {service_name} (permissions may need adjustment)")
        else:
            print(f"  ❌ {service_name}")
            services_ok = False
    
    if credentials_ok and services_ok:
        print("\n🎉 AWS setup looks good! Ready for development.")
        return 0
    elif credentials_ok:
        print("\n⚠️  AWS credentials work, but some services may need permission adjustments.")
        print("This is normal - we'll set up the specific resources as needed.")
        return 0
    else:
        print("\n❌ AWS setup needs attention.")
        return 1


if __name__ == "__main__":
    exit(main())