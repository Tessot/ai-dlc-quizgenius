#!/usr/bin/env python3
"""
DynamoDB Setup Testing Script for QuizGenius MVP

This script tests the DynamoDB table creation and validates:
- All tables exist and are active
- Table schemas match specifications
- Global Secondary Indexes are properly configured
- Basic CRUD operations work correctly
"""

import sys
import json
from datetime import datetime
from utils.dynamodb_utils import DynamoDBManager, generate_id, get_current_timestamp
from utils.config import get_aws_session

def test_table_existence():
    """Test that all required tables exist"""
    print("🔍 Testing table existence...")
    
    db_manager = DynamoDBManager()
    table_status = db_manager.list_all_tables()
    
    all_exist = True
    for table_key, status in table_status.items():
        if status == 'ACTIVE':
            print(f"  ✅ {table_key}: {status}")
        elif status == 'NOT_EXISTS':
            print(f"  ❌ {table_key}: {status}")
            all_exist = False
        else:
            print(f"  ⚠️  {table_key}: {status}")
    
    return all_exist

def test_table_schemas():
    """Test that table schemas match specifications"""
    print("\n🔍 Testing table schemas...")
    
    db_manager = DynamoDBManager()
    
    # Expected schema configurations
    expected_schemas = {
        'users': {
            'key_schema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            'gsi_count': 2,  # UsersByRole-Index, UsersByEmail-Index
            'gsi_names': ['UsersByRole-Index', 'UsersByEmail-Index']
        },
        'documents': {
            'key_schema': [{'AttributeName': 'document_id', 'KeyType': 'HASH'}],
            'gsi_count': 1,  # DocumentsByUploader-Index
            'gsi_names': ['DocumentsByUploader-Index']
        },
        'questions': {
            'key_schema': [{'AttributeName': 'question_id', 'KeyType': 'HASH'}],
            'gsi_count': 2,  # QuestionsByCreator-Index, QuestionsByDocument-Index
            'gsi_names': ['QuestionsByCreator-Index', 'QuestionsByDocument-Index']
        },
        'tests': {
            'key_schema': [{'AttributeName': 'test_id', 'KeyType': 'HASH'}],
            'gsi_count': 2,  # TestsByStatus-Index, TestsByCreator-Index
            'gsi_names': ['TestsByStatus-Index', 'TestsByCreator-Index']
        },
        'test_attempts': {
            'key_schema': [{'AttributeName': 'attempt_id', 'KeyType': 'HASH'}],
            'gsi_count': 2,  # AttemptsByStudent-Index, AttemptsByTest-Index
            'gsi_names': ['AttemptsByStudent-Index', 'AttemptsByTest-Index']
        },
        'results': {
            'key_schema': [{'AttributeName': 'result_id', 'KeyType': 'HASH'}],
            'gsi_count': 3,  # ResultsByAttempt-Index, ResultsByStudent-Index, ResultsByTest-Index
            'gsi_names': ['ResultsByAttempt-Index', 'ResultsByStudent-Index', 'ResultsByTest-Index']
        }
    }
    
    all_valid = True
    
    for table_key, expected in expected_schemas.items():
        schema_info = db_manager.validate_table_schema(table_key)
        
        if 'error' in schema_info:
            print(f"  ❌ {table_key}: {schema_info['error']}")
            all_valid = False
            continue
        
        # Check key schema
        if schema_info['key_schema'] == expected['key_schema']:
            print(f"  ✅ {table_key}: Key schema correct")
        else:
            print(f"  ❌ {table_key}: Key schema mismatch")
            all_valid = False
        
        # Check GSI count
        gsi_list = schema_info.get('global_secondary_indexes', [])
        if len(gsi_list) == expected['gsi_count']:
            print(f"  ✅ {table_key}: GSI count correct ({len(gsi_list)})")
        else:
            print(f"  ❌ {table_key}: GSI count mismatch (expected {expected['gsi_count']}, got {len(gsi_list)})")
            all_valid = False
        
        # Check GSI names
        actual_gsi_names = [gsi['IndexName'] for gsi in gsi_list]
        missing_gsi = set(expected['gsi_names']) - set(actual_gsi_names)
        if not missing_gsi:
            print(f"  ✅ {table_key}: All GSIs present")
        else:
            print(f"  ❌ {table_key}: Missing GSIs: {missing_gsi}")
            all_valid = False
    
    return all_valid

def test_basic_crud_operations():
    """Test basic CRUD operations on each table"""
    print("\n🔍 Testing basic CRUD operations...")
    
    db_manager = DynamoDBManager()
    test_results = {}
    
    # Test Users table
    try:
        users_table = db_manager.get_table('users')
        test_user = {
            'user_id': f'test-user-{generate_id()}',
            'email': 'test@example.com',
            'role': 'student',
            'first_name': 'Test',
            'last_name': 'User',
            'created_date': get_current_timestamp(),
            'status': 'active'
        }
        
        # Create
        users_table.put_item(Item=test_user)
        
        # Read
        response = users_table.get_item(Key={'user_id': test_user['user_id']})
        if 'Item' in response:
            print("  ✅ Users table: CRUD operations working")
            test_results['users'] = True
            
            # Clean up
            users_table.delete_item(Key={'user_id': test_user['user_id']})
        else:
            print("  ❌ Users table: Read operation failed")
            test_results['users'] = False
            
    except Exception as e:
        print(f"  ❌ Users table: CRUD test failed - {e}")
        test_results['users'] = False
    
    # Test Documents table
    try:
        docs_table = db_manager.get_table('documents')
        test_doc = {
            'document_id': f'test-doc-{generate_id()}',
            'filename': 'test.pdf',
            'uploaded_by': 'test-user',
            'upload_date': get_current_timestamp(),
            'file_size': 1024,
            'processing_status': 'pending'
        }
        
        # Create and Read
        docs_table.put_item(Item=test_doc)
        response = docs_table.get_item(Key={'document_id': test_doc['document_id']})
        
        if 'Item' in response:
            print("  ✅ Documents table: CRUD operations working")
            test_results['documents'] = True
            docs_table.delete_item(Key={'document_id': test_doc['document_id']})
        else:
            print("  ❌ Documents table: Read operation failed")
            test_results['documents'] = False
            
    except Exception as e:
        print(f"  ❌ Documents table: CRUD test failed - {e}")
        test_results['documents'] = False
    
    # Test Questions table
    try:
        questions_table = db_manager.get_table('questions')
        test_question = {
            'question_id': f'test-q-{generate_id()}',
            'document_id': 'test-doc',
            'created_by': 'test-user',
            'created_date': get_current_timestamp(),
            'question_type': 'multiple_choice',
            'question_text': 'Test question?',
            'options': ['A', 'B', 'C', 'D'],
            'correct_answer': 0
        }
        
        questions_table.put_item(Item=test_question)
        response = questions_table.get_item(Key={'question_id': test_question['question_id']})
        
        if 'Item' in response:
            print("  ✅ Questions table: CRUD operations working")
            test_results['questions'] = True
            questions_table.delete_item(Key={'question_id': test_question['question_id']})
        else:
            print("  ❌ Questions table: Read operation failed")
            test_results['questions'] = False
            
    except Exception as e:
        print(f"  ❌ Questions table: CRUD test failed - {e}")
        test_results['questions'] = False
    
    # Test remaining tables with minimal data
    remaining_tables = ['tests', 'test_attempts', 'results']
    for table_key in remaining_tables:
        try:
            table = db_manager.get_table(table_key)
            # Just test table access
            table.table_status
            print(f"  ✅ {table_key.title()} table: Access working")
            test_results[table_key] = True
        except Exception as e:
            print(f"  ❌ {table_key.title()} table: Access failed - {e}")
            test_results[table_key] = False
    
    return all(test_results.values())

def test_gsi_queries():
    """Test Global Secondary Index queries"""
    print("\n🔍 Testing GSI queries...")
    
    db_manager = DynamoDBManager()
    
    try:
        # Test Users GSI query
        users_table = db_manager.get_table('users')
        
        # Query by role (if data exists)
        response = users_table.query(
            IndexName='UsersByRole-Index',
            KeyConditionExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'instructor'},
            Limit=1
        )
        
        print("  ✅ Users GSI query: Working")
        
        # Test other GSI access
        for table_key in ['documents', 'questions', 'tests', 'test_attempts', 'results']:
            table = db_manager.get_table(table_key)
            # Just verify GSI exists by accessing table metadata
            gsi_list = table.global_secondary_indexes or []
            if gsi_list:
                print(f"  ✅ {table_key.title()} GSI: Accessible")
            else:
                print(f"  ⚠️  {table_key.title()} GSI: No indexes found")
        
        return True
        
    except Exception as e:
        print(f"  ❌ GSI query test failed: {e}")
        return False

def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "=" * 60)
    print("📊 DynamoDB Setup Test Report")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! DynamoDB setup is complete and working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the setup and fix any issues.")
        return False

def main():
    """Main function to run all DynamoDB tests"""
    print("🧪 DynamoDB Setup Testing for QuizGenius MVP")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results['table_existence'] = test_table_existence()
    test_results['table_schemas'] = test_table_schemas()
    test_results['crud_operations'] = test_basic_crud_operations()
    test_results['gsi_queries'] = test_gsi_queries()
    
    # Generate report
    success = generate_test_report(test_results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()