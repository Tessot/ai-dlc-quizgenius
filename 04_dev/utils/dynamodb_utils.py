"""
DynamoDB Utility Functions for QuizGenius MVP

This module provides utility functions for managing DynamoDB operations,
including table management, data validation, and common query patterns.
"""

import boto3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError
from .config import get_aws_session

class DynamoDBManager:
    """Manager class for DynamoDB operations"""
    
    def __init__(self):
        """Initialize DynamoDB manager with AWS session"""
        self.session = get_aws_session()
        self.dynamodb = self.session.resource('dynamodb')
        self.client = self.session.client('dynamodb')
        
        # Table name mappings
        self.tables = {
            'users': 'QuizGenius_Users',
            'documents': 'QuizGenius_Documents',
            'questions': 'QuizGenius_Questions',
            'tests': 'QuizGenius_Tests',
            'test_attempts': 'QuizGenius_TestAttempts',
            'results': 'QuizGenius_Results'
        }
    
    def get_table(self, table_key: str):
        """Get a DynamoDB table resource"""
        if table_key not in self.tables:
            raise ValueError(f"Unknown table key: {table_key}")
        
        table_name = self.tables[table_key]
        return self.dynamodb.Table(table_name)
    
    def table_exists(self, table_key: str) -> bool:
        """Check if a table exists"""
        try:
            table = self.get_table(table_key)
            table.load()
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise
    
    def get_table_status(self, table_key: str) -> str:
        """Get the status of a table"""
        try:
            table = self.get_table(table_key)
            table.reload()
            return table.table_status
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return 'NOT_EXISTS'
            raise
    
    def list_all_tables(self) -> Dict[str, str]:
        """List all QuizGenius tables and their status"""
        table_status = {}
        
        for key, name in self.tables.items():
            try:
                table = self.dynamodb.Table(name)
                table.reload()
                table_status[key] = table.table_status
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    table_status[key] = 'NOT_EXISTS'
                else:
                    table_status[key] = f'ERROR: {e.response["Error"]["Code"]}'
        
        return table_status
    
    def get_table_item_count(self, table_key: str) -> int:
        """Get approximate item count for a table"""
        try:
            table = self.get_table(table_key)
            table.reload()
            return table.item_count
        except ClientError:
            return 0
    
    def validate_table_schema(self, table_key: str) -> Dict[str, Any]:
        """Validate table schema matches expected structure"""
        try:
            table = self.get_table(table_key)
            table.reload()
            
            schema_info = {
                'table_name': table.table_name,
                'key_schema': table.key_schema,
                'attribute_definitions': table.attribute_definitions,
                'global_secondary_indexes': table.global_secondary_indexes or [],
                'billing_mode': table.billing_mode_summary,
                'table_status': table.table_status,
                'item_count': table.item_count
            }
            
            return schema_info
            
        except ClientError as e:
            return {'error': str(e)}

def generate_id(prefix: str = '') -> str:
    """Generate a unique ID with optional prefix"""
    import uuid
    unique_id = str(uuid.uuid4())
    return f"{prefix}-{unique_id}" if prefix else unique_id

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat() + 'Z'

def validate_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user data structure"""
    # user_id is not required as it will be generated if not provided
    required_fields = ['email', 'role', 'first_name', 'last_name']
    errors = []
    
    for field in required_fields:
        if field not in user_data or not user_data[field]:
            errors.append(f"Missing required field: {field}")
    
    if user_data.get('role') not in ['instructor', 'student']:
        errors.append("Role must be 'instructor' or 'student'")
    
    # Basic email validation
    email = user_data.get('email', '')
    if '@' not in email or '.' not in email:
        errors.append("Invalid email format")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_question_data(question_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate question data structure"""
    required_fields = ['question_id', 'question_type', 'question_text', 'correct_answer']
    errors = []
    
    for field in required_fields:
        if field not in question_data or question_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    question_type = question_data.get('question_type')
    if question_type not in ['multiple_choice', 'true_false']:
        errors.append("Question type must be 'multiple_choice' or 'true_false'")
    
    # Validate multiple choice questions
    if question_type == 'multiple_choice':
        options = question_data.get('options', [])
        if not isinstance(options, list) or len(options) < 2:
            errors.append("Multiple choice questions must have at least 2 options")
        
        correct_answer = question_data.get('correct_answer')
        if not isinstance(correct_answer, int) or correct_answer < 0 or correct_answer >= len(options):
            errors.append("Correct answer must be a valid option index")
    
    # Validate true/false questions
    if question_type == 'true_false':
        correct_answer = question_data.get('correct_answer')
        if not isinstance(correct_answer, bool):
            errors.append("True/false questions must have boolean correct answer")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_test_data(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate test data structure"""
    required_fields = ['test_id', 'title', 'created_by', 'question_ids']
    errors = []
    
    for field in required_fields:
        if field not in test_data or not test_data[field]:
            errors.append(f"Missing required field: {field}")
    
    question_ids = test_data.get('question_ids', [])
    if not isinstance(question_ids, list) or len(question_ids) == 0:
        errors.append("Test must have at least one question")
    
    status = test_data.get('status', 'draft')
    if status not in ['draft', 'published', 'archived']:
        errors.append("Status must be 'draft', 'published', or 'archived'")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def format_dynamodb_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Format item for DynamoDB storage (handle special types)"""
    formatted_item = {}
    
    for key, value in item.items():
        if isinstance(value, datetime):
            formatted_item[key] = value.isoformat() + 'Z'
        elif isinstance(value, (list, dict)):
            formatted_item[key] = value  # DynamoDB handles these natively
        else:
            formatted_item[key] = value
    
    return formatted_item

def parse_dynamodb_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Parse item from DynamoDB (handle special types)"""
    # DynamoDB items are already in the correct format
    # This function can be extended for custom parsing if needed
    return item

# Query helper functions
def build_key_condition(partition_key: str, partition_value: str, 
                       sort_key: str = None, sort_value: str = None) -> Dict[str, Any]:
    """Build key condition expression for DynamoDB queries"""
    from boto3.dynamodb.conditions import Key
    
    condition = Key(partition_key).eq(partition_value)
    
    if sort_key and sort_value:
        condition = condition & Key(sort_key).eq(sort_value)
    
    return condition

def build_filter_expression(filters: Dict[str, Any]) -> Any:
    """Build filter expression for DynamoDB queries"""
    from boto3.dynamodb.conditions import Attr
    
    if not filters:
        return None
    
    filter_expr = None
    
    for key, value in filters.items():
        condition = Attr(key).eq(value)
        
        if filter_expr is None:
            filter_expr = condition
        else:
            filter_expr = filter_expr & condition
    
    return filter_expr

# Batch operation helpers
def batch_write_items(table, items: List[Dict[str, Any]], batch_size: int = 25):
    """Write items to DynamoDB in batches"""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        with table.batch_writer() as writer:
            for item in batch:
                writer.put_item(Item=format_dynamodb_item(item))

def batch_get_items(table, keys: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get multiple items from DynamoDB"""
    response = table.batch_get_item(RequestItems={
        table.table_name: {
            'Keys': keys
        }
    })
    
    return response.get('Responses', {}).get(table.table_name, [])

# Error handling helpers
def handle_dynamodb_error(error: ClientError) -> str:
    """Convert DynamoDB errors to user-friendly messages"""
    error_code = error.response['Error']['Code']
    
    error_messages = {
        'ResourceNotFoundException': 'Table or item not found',
        'ConditionalCheckFailedException': 'Item already exists or condition not met',
        'ValidationException': 'Invalid data format',
        'ProvisionedThroughputExceededException': 'Request rate too high, please retry',
        'ItemCollectionSizeLimitExceededException': 'Item collection too large',
        'TransactionConflictException': 'Transaction conflict, please retry',
        'RequestLimitExceeded': 'Request limit exceeded, please retry'
    }
    
    return error_messages.get(error_code, f"Database error: {error_code}")