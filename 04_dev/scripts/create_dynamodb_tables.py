#!/usr/bin/env python3
"""
DynamoDB Tables Creation Script for QuizGenius MVP

This script creates all required DynamoDB tables with their Global Secondary Indexes (GSI)
as defined in the architecture specification.

Tables created:
- Users: User profiles with role-based access
- Documents: PDF metadata and processing status
- Questions: Generated questions with creator tracking
- Tests: Test configurations and status
- TestAttempts: Student test attempts with tracking
- Results: Test results and scoring data
"""

import boto3
import json
import time
import sys
import os
from botocore.exceptions import ClientError

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import get_aws_session

def create_users_table(dynamodb):
    """Create Users table with GSI for role-based queries"""
    table_name = 'QuizGenius_Users'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'role',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UsersByRole-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'role',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'UsersByEmail-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'email',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"❌ Error creating {table_name}: {e}")
            raise

def create_documents_table(dynamodb):
    """Create Documents table for PDF metadata"""
    table_name = 'QuizGenius_Documents'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'document_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'document_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'uploaded_by',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'upload_date',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'DocumentsByUploader-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'uploaded_by',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'upload_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"❌ Error creating {table_name}: {e}")
            raise

def create_questions_table(dynamodb):
    """Create Questions table with GSI for creator tracking"""
    table_name = 'QuizGenius_Questions'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'question_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'question_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_by',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'document_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_date',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'QuestionsByCreator-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'created_by',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'QuestionsByDocument-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'document_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"❌ Error creating {table_name}: {e}")
            raise

def create_tests_table(dynamodb):
    """Create Tests table with GSI for status tracking"""
    table_name = 'QuizGenius_Tests'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'test_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'test_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_by',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_date',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'TestsByStatus-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'TestsByCreator-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'created_by',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"❌ Error creating {table_name}: {e}")
            raise

def create_test_attempts_table(dynamodb):
    """Create TestAttempts table with GSI for student and test tracking"""
    table_name = 'QuizGenius_TestAttempts'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'attempt_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'attempt_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'student_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'test_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'attempt_date',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'AttemptsByStudent-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'student_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'attempt_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'AttemptsByTest-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'test_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'attempt_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'StudentTestIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'student_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'test_id',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"❌ Error creating {table_name}: {e}")
            raise

def create_results_table(dynamodb):
    """Create Results table for test scoring data"""
    table_name = 'QuizGenius_Results'
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'result_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'result_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'attempt_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'student_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'test_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'ResultsByAttempt-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'attempt_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'ResultsByStudent-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'student_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'ResultsByTest-Index',
                    'KeySchema': [
                        {
                            'AttributeName': 'test_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"❌ Error creating {table_name}: {e}")
            raise

def wait_for_table_creation(tables):
    """Wait for all tables to become active"""
    print("\n⏳ Waiting for tables to become active...")
    
    for table in tables:
        table.wait_until_exists()
        print(f"✅ Table {table.name} is now active")

def main():
    """Main function to create all DynamoDB tables"""
    print("🚀 Starting DynamoDB table creation for QuizGenius MVP")
    print("=" * 60)
    
    try:
        # Get AWS session
        session = get_aws_session()
        dynamodb = session.resource('dynamodb')
        
        # Create all tables
        tables = []
        
        print("\n📋 Creating tables...")
        tables.append(create_users_table(dynamodb))
        tables.append(create_documents_table(dynamodb))
        tables.append(create_questions_table(dynamodb))
        tables.append(create_tests_table(dynamodb))
        tables.append(create_test_attempts_table(dynamodb))
        tables.append(create_results_table(dynamodb))
        
        # Wait for tables to become active
        wait_for_table_creation(tables)
        
        print("\n" + "=" * 60)
        print("✅ All DynamoDB tables created successfully!")
        print("\nTables created:")
        for table in tables:
            print(f"  • {table.name}")
        
        print("\n📊 Table summary:")
        for table in tables:
            table.reload()
            print(f"  • {table.name}: {table.table_status}")
            
    except Exception as e:
        print(f"\n❌ Error during table creation: {e}")
        raise

if __name__ == "__main__":
    main()