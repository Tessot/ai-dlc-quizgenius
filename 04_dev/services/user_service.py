"""
User Service for QuizGenius MVP

This module provides user data management functionality using DynamoDB,
including user CRUD operations, profile management, and user queries.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from botocore.exceptions import ClientError
from utils.dynamodb_utils import DynamoDBManager, generate_id, get_current_timestamp
from utils.dynamodb_utils import validate_user_data, handle_dynamodb_error

class UserServiceError(Exception):
    """Custom exception for user service errors"""
    pass

class UserService:
    """Service class for user data operations"""
    
    def __init__(self):
        """Initialize user service"""
        self.db_manager = DynamoDBManager()
        self.users_table = self.db_manager.get_table('users')
    
    def create_user(self, user_data: Dict[str, any]) -> Dict[str, any]:
        """
        Create a new user in DynamoDB
        
        Args:
            user_data: Dictionary containing user information
                Required fields: email, first_name, last_name, role
                Optional fields: user_id, created_date, status
        
        Returns:
            Dict containing created user data
            
        Raises:
            UserServiceError: If user creation fails
        """
        try:
            # Validate user data
            validation_result = validate_user_data(user_data)
            if not validation_result['valid']:
                raise UserServiceError(f"Invalid user data: {', '.join(validation_result['errors'])}")
            
            # Generate user ID if not provided
            if 'user_id' not in user_data or not user_data['user_id']:
                user_data['user_id'] = generate_id('user')
            
            # Set default values
            user_data.setdefault('created_date', get_current_timestamp())
            user_data.setdefault('status', 'active')
            user_data.setdefault('last_login', None)
            user_data.setdefault('login_count', 0)
            
            # Check if user already exists
            if self.get_user_by_email(user_data['email']):
                raise UserServiceError(f"User with email {user_data['email']} already exists")
            
            # Create user in DynamoDB
            self.users_table.put_item(
                Item=user_data,
                ConditionExpression='attribute_not_exists(user_id)'
            )
            
            return {
                'success': True,
                'user_id': user_data['user_id'],
                'user_data': user_data,
                'message': 'User created successfully'
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise UserServiceError(f"User with ID {user_data['user_id']} already exists")
            else:
                error_msg = handle_dynamodb_error(e)
                raise UserServiceError(f"Failed to create user: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error creating user: {str(e)}")
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, any]]:
        """
        Get user by user ID
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User data dictionary or None if not found
            
        Raises:
            UserServiceError: If query fails
        """
        try:
            response = self.users_table.get_item(Key={'user_id': user_id})
            return response.get('Item')
            
        except ClientError as e:
            error_msg = handle_dynamodb_error(e)
            raise UserServiceError(f"Failed to get user by ID: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error getting user: {str(e)}")
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, any]]:
        """
        Get user by email address using GSI
        
        Args:
            email: User's email address
            
        Returns:
            User data dictionary or None if not found
            
        Raises:
            UserServiceError: If query fails
        """
        try:
            response = self.users_table.query(
                IndexName='UsersByEmail-Index',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email},
                Limit=1
            )
            
            items = response.get('Items', [])
            return items[0] if items else None
            
        except ClientError as e:
            error_msg = handle_dynamodb_error(e)
            raise UserServiceError(f"Failed to get user by email: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error getting user by email: {str(e)}")
    
    def update_user(self, user_id: str, updates: Dict[str, any]) -> Dict[str, any]:
        """
        Update user information
        
        Args:
            user_id: User's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            Dict containing update result and updated user data
            
        Raises:
            UserServiceError: If update fails
        """
        try:
            # Validate that user exists
            existing_user = self.get_user_by_id(user_id)
            if not existing_user:
                raise UserServiceError(f"User with ID {user_id} not found")
            
            # Prepare update expression
            update_expression_parts = []
            expression_attribute_names = {}
            expression_attribute_values = {}
            
            # Add updated_date
            updates['updated_date'] = get_current_timestamp()
            
            for key, value in updates.items():
                if key != 'user_id':  # Don't allow updating the primary key
                    attr_name = f"#{key}"
                    attr_value = f":{key}"
                    
                    update_expression_parts.append(f"{attr_name} = {attr_value}")
                    expression_attribute_names[attr_name] = key
                    expression_attribute_values[attr_value] = value
            
            if not update_expression_parts:
                raise UserServiceError("No valid fields to update")
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            # Update user in DynamoDB
            response = self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression='attribute_exists(user_id)',
                ReturnValues='ALL_NEW'
            )
            
            return {
                'success': True,
                'user_data': response['Attributes'],
                'message': 'User updated successfully'
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise UserServiceError(f"User with ID {user_id} not found")
            else:
                error_msg = handle_dynamodb_error(e)
                raise UserServiceError(f"Failed to update user: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error updating user: {str(e)}")
    
    def delete_user(self, user_id: str) -> Dict[str, any]:
        """
        Delete user (soft delete by setting status to 'deleted')
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dict containing deletion result
            
        Raises:
            UserServiceError: If deletion fails
        """
        try:
            # Soft delete by updating status
            result = self.update_user(user_id, {
                'status': 'deleted',
                'deleted_date': get_current_timestamp()
            })
            
            return {
                'success': True,
                'user_id': user_id,
                'message': 'User deleted successfully'
            }
            
        except UserServiceError:
            raise
        except Exception as e:
            raise UserServiceError(f"Unexpected error deleting user: {str(e)}")
    
    def hard_delete_user(self, user_id: str) -> Dict[str, any]:
        """
        Permanently delete user from database
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dict containing deletion result
            
        Raises:
            UserServiceError: If deletion fails
        """
        try:
            # Verify user exists before deletion
            existing_user = self.get_user_by_id(user_id)
            if not existing_user:
                raise UserServiceError(f"User with ID {user_id} not found")
            
            # Delete user from DynamoDB
            self.users_table.delete_item(
                Key={'user_id': user_id},
                ConditionExpression='attribute_exists(user_id)'
            )
            
            return {
                'success': True,
                'user_id': user_id,
                'message': 'User permanently deleted'
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise UserServiceError(f"User with ID {user_id} not found")
            else:
                error_msg = handle_dynamodb_error(e)
                raise UserServiceError(f"Failed to delete user: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error deleting user: {str(e)}")
    
    def get_users_by_role(self, role: str, limit: int = 50) -> List[Dict[str, any]]:
        """
        Get users by role using GSI
        
        Args:
            role: User role (instructor or student)
            limit: Maximum number of users to return
            
        Returns:
            List of user data dictionaries
            
        Raises:
            UserServiceError: If query fails
        """
        try:
            response = self.users_table.query(
                IndexName='UsersByRole-Index',
                KeyConditionExpression='#role = :role',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#role': 'role', '#status': 'status'},
                ExpressionAttributeValues={':role': role, ':status': 'active'},
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            error_msg = handle_dynamodb_error(e)
            raise UserServiceError(f"Failed to get users by role: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error getting users by role: {str(e)}")
    
    def update_last_login(self, user_id: str) -> Dict[str, any]:
        """
        Update user's last login timestamp and increment login count
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dict containing update result
            
        Raises:
            UserServiceError: If update fails
        """
        try:
            response = self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET last_login = :timestamp, login_count = if_not_exists(login_count, :zero) + :one',
                ExpressionAttributeValues={
                    ':timestamp': get_current_timestamp(),
                    ':zero': 0,
                    ':one': 1
                },
                ConditionExpression='attribute_exists(user_id)',
                ReturnValues='UPDATED_NEW'
            )
            
            return {
                'success': True,
                'last_login': response['Attributes']['last_login'],
                'login_count': response['Attributes']['login_count'],
                'message': 'Last login updated successfully'
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise UserServiceError(f"User with ID {user_id} not found")
            else:
                error_msg = handle_dynamodb_error(e)
                raise UserServiceError(f"Failed to update last login: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error updating last login: {str(e)}")
    
    def search_users(self, search_term: str, role: Optional[str] = None, limit: int = 20) -> List[Dict[str, any]]:
        """
        Search users by name or email
        
        Args:
            search_term: Term to search for in names or email
            role: Optional role filter
            limit: Maximum number of results
            
        Returns:
            List of matching user data dictionaries
            
        Raises:
            UserServiceError: If search fails
        """
        try:
            # This is a simple implementation using scan
            # In production, you might want to use ElasticSearch or similar for better search
            
            filter_expression = 'contains(first_name, :term) OR contains(last_name, :term) OR contains(email, :term)'
            expression_values = {':term': search_term.lower()}
            
            if role:
                filter_expression += ' AND #role = :role'
                expression_values[':role'] = role
            
            # Add status filter
            filter_expression += ' AND #status = :status'
            expression_values[':status'] = 'active'
            
            response = self.users_table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeNames={'#role': 'role', '#status': 'status'} if role else {'#status': 'status'},
                ExpressionAttributeValues=expression_values,
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            error_msg = handle_dynamodb_error(e)
            raise UserServiceError(f"Failed to search users: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error searching users: {str(e)}")
    
    def get_user_statistics(self) -> Dict[str, any]:
        """
        Get user statistics (counts by role, status, etc.)
        
        Returns:
            Dict containing user statistics
            
        Raises:
            UserServiceError: If query fails
        """
        try:
            # Get all users (this could be expensive for large datasets)
            response = self.users_table.scan()
            users = response.get('Items', [])
            
            # Calculate statistics
            stats = {
                'total_users': len(users),
                'active_users': len([u for u in users if u.get('status') == 'active']),
                'deleted_users': len([u for u in users if u.get('status') == 'deleted']),
                'instructors': len([u for u in users if u.get('role') == 'instructor']),
                'students': len([u for u in users if u.get('role') == 'student']),
                'active_instructors': len([u for u in users if u.get('role') == 'instructor' and u.get('status') == 'active']),
                'active_students': len([u for u in users if u.get('role') == 'student' and u.get('status') == 'active'])
            }
            
            return stats
            
        except ClientError as e:
            error_msg = handle_dynamodb_error(e)
            raise UserServiceError(f"Failed to get user statistics: {error_msg}")
        except Exception as e:
            raise UserServiceError(f"Unexpected error getting user statistics: {str(e)}")
    
    def delete_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Delete a user by email address (hard delete for testing)
        
        Args:
            email: User's email address
            
        Returns:
            Dict containing deletion result
        """
        try:
            # First, find the user
            user = self.get_user_by_email(email)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Hard delete the user
            result = self.hard_delete_user(user['user_id'])
            return result
            
        except UserServiceError:
            raise
        except Exception as e:
            raise UserServiceError(f"Unexpected error deleting user by email: {str(e)}")

# Utility functions for user data processing
def format_user_for_display(user_data: Dict[str, any]) -> Dict[str, any]:
    """Format user data for display purposes"""
    if not user_data:
        return {}
    
    return {
        'user_id': user_data.get('user_id'),
        'email': user_data.get('email'),
        'full_name': f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
        'first_name': user_data.get('first_name'),
        'last_name': user_data.get('last_name'),
        'role': user_data.get('role'),
        'status': user_data.get('status'),
        'created_date': user_data.get('created_date'),
        'last_login': user_data.get('last_login'),
        'login_count': user_data.get('login_count', 0)
    }

def create_user_from_cognito(cognito_user_info: Dict[str, any]) -> Dict[str, any]:
    """Create user data structure from Cognito user info"""
    return {
        'user_id': generate_id('user'),
        'email': cognito_user_info.get('email'),
        'first_name': cognito_user_info.get('first_name'),
        'last_name': cognito_user_info.get('last_name'),
        'role': cognito_user_info.get('role'),
        'cognito_username': cognito_user_info.get('username'),
        'email_verified': cognito_user_info.get('email_verified', False),
        'created_date': get_current_timestamp(),
        'status': 'active',
        'login_count': 0
    }

def validate_role(role: str) -> bool:
    """Validate user role"""
    return role in ['instructor', 'student']

def validate_status(status: str) -> bool:
    """Validate user status"""
    return status in ['active', 'inactive', 'deleted', 'suspended']