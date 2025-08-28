#!/usr/bin/env python3
"""
AWS Cognito User Pool Deletion Script for QuizGenius MVP

This script deletes the Cognito User Pool for cleanup purposes.
USE WITH CAUTION - This will permanently delete all user data!
"""

import boto3
from botocore.exceptions import ClientError
from utils.config import get_aws_session, Config

def delete_user_pool(cognito_client, user_pool_id):
    """Delete Cognito User Pool"""
    
    try:
        cognito_client.delete_user_pool(UserPoolId=user_pool_id)
        print(f"✅ Deleted User Pool: {user_pool_id}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  User Pool {user_pool_id} does not exist")
            return True
        else:
            print(f"❌ Error deleting User Pool: {e}")
            return False

def main():
    """Main function to delete Cognito User Pool"""
    print("🚨 DANGER: Cognito User Pool deletion for QuizGenius MVP")
    print("=" * 60)
    
    # Get user pool ID from config
    user_pool_id = Config.COGNITO_USER_POOL_ID
    
    if not user_pool_id:
        print("❌ No User Pool ID found in configuration")
        return
    
    print(f"⚠️  This will permanently delete User Pool: {user_pool_id}")
    print("\n❓ Are you sure you want to continue? (type 'DELETE' to confirm)")
    confirmation = input("Confirmation: ")
    
    if confirmation != 'DELETE':
        print("❌ Deletion cancelled")
        return
    
    try:
        # Get AWS session
        session = get_aws_session()
        cognito_client = session.client('cognito-idp')
        
        # Delete User Pool
        if delete_user_pool(cognito_client, user_pool_id):
            print("\n✅ User Pool deleted successfully!")
        else:
            print("\n❌ Failed to delete User Pool")
            
    except Exception as e:
        print(f"\n❌ Error during deletion: {e}")
        raise

if __name__ == "__main__":
    main()