#!/usr/bin/env python3
"""
DynamoDB Tables Deletion Script for QuizGenius MVP

This script deletes all QuizGenius DynamoDB tables for testing and cleanup purposes.
USE WITH CAUTION - This will permanently delete all data!

Tables deleted:
- QuizGenius_Users
- QuizGenius_Documents  
- QuizGenius_Questions
- QuizGenius_Tests
- QuizGenius_TestAttempts
- QuizGenius_Results
"""

import boto3
import time
from botocore.exceptions import ClientError
from utils.config import get_aws_session

def delete_table(dynamodb, table_name):
    """Delete a single DynamoDB table"""
    try:
        table = dynamodb.Table(table_name)
        table.delete()
        print(f"🗑️  Deleting table: {table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  Table {table_name} does not exist")
            return None
        else:
            print(f"❌ Error deleting {table_name}: {e}")
            raise

def wait_for_table_deletion(tables):
    """Wait for all tables to be deleted"""
    print("\n⏳ Waiting for tables to be deleted...")
    
    for table in tables:
        if table:  # Only wait for tables that existed
            try:
                table.wait_until_not_exists()
                print(f"✅ Table {table.name} has been deleted")
            except Exception as e:
                print(f"⚠️  Error waiting for {table.name} deletion: {e}")

def main():
    """Main function to delete all DynamoDB tables"""
    print("🚨 DANGER: DynamoDB table deletion for QuizGenius MVP")
    print("=" * 60)
    print("⚠️  This will permanently delete ALL data in the following tables:")
    
    table_names = [
        'QuizGenius_Users',
        'QuizGenius_Documents',
        'QuizGenius_Questions', 
        'QuizGenius_Tests',
        'QuizGenius_TestAttempts',
        'QuizGenius_Results'
    ]
    
    for name in table_names:
        print(f"  • {name}")
    
    print("\n❓ Are you sure you want to continue? (type 'DELETE' to confirm)")
    confirmation = input("Confirmation: ")
    
    if confirmation != 'DELETE':
        print("❌ Deletion cancelled")
        return
    
    try:
        # Get AWS session
        session = get_aws_session()
        dynamodb = session.resource('dynamodb')
        
        # Delete all tables
        tables = []
        
        print("\n🗑️  Deleting tables...")
        for table_name in table_names:
            table = delete_table(dynamodb, table_name)
            if table:
                tables.append(table)
        
        # Wait for tables to be deleted
        if tables:
            wait_for_table_deletion(tables)
        
        print("\n" + "=" * 60)
        print("✅ All DynamoDB tables deleted successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during table deletion: {e}")
        raise

if __name__ == "__main__":
    main()