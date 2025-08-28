#!/usr/bin/env python3
"""
Check and Create DynamoDB Tables Script
Simple script to check if tables exist and create them if needed
"""

import boto3
import sys
import os
from botocore.exceptions import ClientError

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_and_create_tables():
    """Check if DynamoDB tables exist and create them if needed"""
    
    # Initialize DynamoDB client
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        print("✅ Connected to DynamoDB")
    except Exception as e:
        print(f"❌ Failed to connect to DynamoDB: {e}")
        return False
    
    # Define required tables
    required_tables = [
        'QuizGenius_Users',
        'QuizGenius_Documents', 
        'QuizGenius_Questions',
        'QuizGenius_Tests',
        'QuizGenius_TestAttempts',
        'QuizGenius_Results'
    ]
    
    # Check existing tables
    try:
        existing_tables = list(dynamodb.tables.all())
        existing_table_names = [table.name for table in existing_tables]
        print(f"📋 Found {len(existing_table_names)} existing tables: {existing_table_names}")
    except Exception as e:
        print(f"❌ Failed to list tables: {e}")
        existing_table_names = []
    
    # Check which tables are missing
    missing_tables = [table for table in required_tables if table not in existing_table_names]
    
    if not missing_tables:
        print("✅ All required tables exist!")
        return True
    
    print(f"⚠️ Missing tables: {missing_tables}")
    
    # Create missing tables
    success = True
    for table_name in missing_tables:
        try:
            if table_name == 'QuizGenius_Users':
                create_users_table(dynamodb)
            elif table_name == 'QuizGenius_Documents':
                create_documents_table(dynamodb)
            elif table_name == 'QuizGenius_Questions':
                create_questions_table(dynamodb)
            elif table_name == 'QuizGenius_Tests':
                create_tests_table(dynamodb)
            elif table_name == 'QuizGenius_TestAttempts':
                create_test_attempts_table(dynamodb)
            elif table_name == 'QuizGenius_Results':
                create_results_table(dynamodb)
            
            print(f"✅ Created table: {table_name}")
            
        except Exception as e:
            print(f"❌ Failed to create table {table_name}: {e}")
            success = False
    
    return success

def create_users_table(dynamodb):
    """Create Users table"""
    table = dynamodb.create_table(
        TableName='QuizGenius_Users',
        KeySchema=[
            {'AttributeName': 'UserID', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'UserID', 'AttributeType': 'S'},
            {'AttributeName': 'Role', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'UsersByRole-Index',
                'KeySchema': [
                    {'AttributeName': 'Role', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'BillingMode': 'PAY_PER_REQUEST'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()

def create_documents_table(dynamodb):
    """Create Documents table"""
    table = dynamodb.create_table(
        TableName='QuizGenius_Documents',
        KeySchema=[
            {'AttributeName': 'DocumentID', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'DocumentID', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()

def create_questions_table(dynamodb):
    """Create Questions table"""
    table = dynamodb.create_table(
        TableName='QuizGenius_Questions',
        KeySchema=[
            {'AttributeName': 'QuestionID', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'QuestionID', 'AttributeType': 'S'},
            {'AttributeName': 'CreatedBy', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'QuestionsByCreator-Index',
                'KeySchema': [
                    {'AttributeName': 'CreatedBy', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'BillingMode': 'PAY_PER_REQUEST'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()

def create_tests_table(dynamodb):
    """Create Tests table"""
    table = dynamodb.create_table(
        TableName='QuizGenius_Tests',
        KeySchema=[
            {'AttributeName': 'TestID', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'TestID', 'AttributeType': 'S'},
            {'AttributeName': 'Status', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'TestsByStatus-Index',
                'KeySchema': [
                    {'AttributeName': 'Status', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'BillingMode': 'PAY_PER_REQUEST'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()

def create_test_attempts_table(dynamodb):
    """Create TestAttempts table"""
    table = dynamodb.create_table(
        TableName='QuizGenius_TestAttempts',
        KeySchema=[
            {'AttributeName': 'AttemptID', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'AttemptID', 'AttributeType': 'S'},
            {'AttributeName': 'StudentID', 'AttributeType': 'S'},
            {'AttributeName': 'TestID', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'AttemptsByStudent-Index',
                'KeySchema': [
                    {'AttributeName': 'StudentID', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'BillingMode': 'PAY_PER_REQUEST'
            },
            {
                'IndexName': 'AttemptsByTest-Index',
                'KeySchema': [
                    {'AttributeName': 'TestID', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'BillingMode': 'PAY_PER_REQUEST'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()

def create_results_table(dynamodb):
    """Create Results table"""
    table = dynamodb.create_table(
        TableName='QuizGenius_Results',
        KeySchema=[
            {'AttributeName': 'ResultID', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'ResultID', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()

if __name__ == "__main__":
    print("🔍 Checking DynamoDB tables...")
    success = check_and_create_tables()
    if success:
        print("✅ All tables are ready!")
    else:
        print("❌ Some tables could not be created")
        sys.exit(1)