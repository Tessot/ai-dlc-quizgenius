"""
Authentication Service for QuizGenius MVP

This module provides authentication functionality using AWS Cognito,
including user registration, login, session management, and user profile operations.
"""

import boto3
import hashlib
import hmac
import base64
from typing import Dict, Optional, Tuple, Any
from botocore.exceptions import ClientError
from utils.config import Config, get_aws_session

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

class AuthService:
    """Authentication service using AWS Cognito"""
    
    def __init__(self):
        """Initialize authentication service"""
        self.session = get_aws_session()
        self.cognito_client = self.session.client('cognito-idp')
        self.user_pool_id = Config.COGNITO_USER_POOL_ID
        self.client_id = Config.COGNITO_CLIENT_ID
        self.client_secret = Config.COGNITO_CLIENT_SECRET
        
        if not self.user_pool_id or not self.client_id:
            raise ValueError("Cognito User Pool ID and Client ID must be configured")
    
    def _calculate_secret_hash(self, username: str) -> Optional[str]:
        """Calculate secret hash for Cognito client if client secret is configured"""
        if not self.client_secret:
            return None
            
        message = username + self.client_id
        dig = hmac.new(
            str(self.client_secret).encode('utf-8'),
            msg=str(message).encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def register_user(self, email: str, password: str, first_name: str, 
                     last_name: str, role: str) -> Dict[str, any]:
        """
        Register a new user with Cognito
        
        Args:
            email: User's email address
            password: User's password
            first_name: User's first name
            last_name: User's last name
            role: User's role (instructor or student)
            
        Returns:
            Dict containing registration result
            
        Raises:
            AuthenticationError: If registration fails
        """
        try:
            # Validate inputs
            if not all([email, password, first_name, last_name, role]):
                raise AuthenticationError("All registration fields are required")
            
            if role not in ['instructor', 'student']:
                raise AuthenticationError("Role must be 'instructor' or 'student'")
            
            # Prepare user attributes (store role in DynamoDB, not Cognito)
            user_attributes = [
                {'Name': 'email', 'Value': email},
                {'Name': 'given_name', 'Value': first_name},
                {'Name': 'family_name', 'Value': last_name}
            ]
            
            # Prepare sign up parameters
            signup_params = {
                'ClientId': self.client_id,
                'Username': email,
                'Password': password,
                'UserAttributes': user_attributes
            }
            
            # Add secret hash only if client secret is configured
            if self.client_secret:
                secret_hash = self._calculate_secret_hash(email)
                if secret_hash:
                    signup_params['SecretHash'] = secret_hash
            
            # Register user
            response = self.cognito_client.sign_up(**signup_params)
            
            return {
                'success': True,
                'user_sub': response['UserSub'],
                'username': response.get('Username', email),
                'confirmation_required': not response.get('UserConfirmed', False),
                'message': 'User registered successfully. Please check your email for verification code.'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            # Map common errors to user-friendly messages
            if error_code == 'UsernameExistsException':
                raise AuthenticationError("An account with this email already exists")
            elif error_code == 'InvalidPasswordException':
                raise AuthenticationError(f"Password does not meet requirements: {error_message}")
            elif error_code == 'InvalidParameterException':
                raise AuthenticationError(f"Invalid registration parameters: {error_message}")
            else:
                raise AuthenticationError(f"Registration failed: {error_message}")
        except AuthenticationError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            raise AuthenticationError(f"Unexpected registration error: {str(e)}")
    
    def confirm_registration(self, email: str, confirmation_code: str) -> Dict[str, any]:
        """
        Confirm user registration with verification code
        
        Args:
            email: User's email address
            confirmation_code: Verification code from email
            
        Returns:
            Dict containing confirmation result
            
        Raises:
            AuthenticationError: If confirmation fails
        """
        try:
            # Prepare confirmation parameters
            confirm_params = {
                'ClientId': self.client_id,
                'Username': email,
                'ConfirmationCode': confirmation_code
            }
            
            # Add secret hash if client secret is configured
            secret_hash = self._calculate_secret_hash(email)
            if secret_hash:
                confirm_params['SecretHash'] = secret_hash
            
            # Confirm registration
            self.cognito_client.confirm_sign_up(**confirm_params)
            
            return {
                'success': True,
                'message': 'Email verified successfully. You can now log in.'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'CodeMismatchException':
                raise AuthenticationError("Invalid verification code")
            elif error_code == 'ExpiredCodeException':
                raise AuthenticationError("Verification code has expired")
            elif error_code == 'UserNotFoundException':
                raise AuthenticationError("User not found")
            else:
                raise AuthenticationError(f"Verification failed: {error_message}")
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, any]:
        """
        Authenticate user with email and password
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing authentication tokens and user info
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Prepare authentication parameters
            auth_params = {
                'ClientId': self.client_id,
                'AuthFlow': 'USER_PASSWORD_AUTH',
                'AuthParameters': {
                    'USERNAME': email,
                    'PASSWORD': password
                }
            }
            
            # Add secret hash if client secret is configured
            secret_hash = self._calculate_secret_hash(email)
            if secret_hash:
                auth_params['AuthParameters']['SECRET_HASH'] = secret_hash
            
            # Authenticate user
            response = self.cognito_client.initiate_auth(**auth_params)
            
            # Extract tokens
            auth_result = response['AuthenticationResult']
            
            # Get user attributes
            user_info = self.get_user_info(auth_result['AccessToken'])
            
            return {
                'success': True,
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'refresh_token': auth_result['RefreshToken'],
                'expires_in': auth_result['ExpiresIn'],
                'user_info': user_info,
                'message': 'Authentication successful'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError("Invalid email or password")
            elif error_code == 'UserNotConfirmedException':
                raise AuthenticationError("Please verify your email address before logging in")
            elif error_code == 'UserNotFoundException':
                raise AuthenticationError("User not found")
            elif error_code == 'PasswordResetRequiredException':
                raise AuthenticationError("Password reset required")
            else:
                raise AuthenticationError(f"Authentication failed: {error_message}")
    
    def get_user_info(self, access_token: str) -> Dict[str, any]:
        """
        Get user information from access token
        
        Args:
            access_token: User's access token
            
        Returns:
            Dict containing user information
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            response = self.cognito_client.get_user(AccessToken=access_token)
            
            # Parse user attributes
            user_attributes = {}
            for attr in response['UserAttributes']:
                user_attributes[attr['Name']] = attr['Value']
            
            return {
                'username': response['Username'],
                'email': user_attributes.get('email'),
                'first_name': user_attributes.get('given_name'),
                'last_name': user_attributes.get('family_name'),
                'role': user_attributes.get('custom:role'),
                'email_verified': user_attributes.get('email_verified') == 'true',
                'user_status': response.get('UserStatus')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError("Invalid or expired access token")
            else:
                raise AuthenticationError(f"Failed to get user info: {e.response['Error']['Message']}")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: User's refresh token
            
        Returns:
            Dict containing new tokens
            
        Raises:
            AuthenticationError: If refresh fails
        """
        try:
            # Prepare refresh parameters
            refresh_params = {
                'ClientId': self.client_id,
                'AuthFlow': 'REFRESH_TOKEN_AUTH',
                'AuthParameters': {
                    'REFRESH_TOKEN': refresh_token
                }
            }
            
            # Note: SECRET_HASH is not needed for refresh token flow
            
            # Refresh tokens
            response = self.cognito_client.initiate_auth(**refresh_params)
            auth_result = response['AuthenticationResult']
            
            return {
                'success': True,
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'expires_in': auth_result['ExpiresIn'],
                'message': 'Token refreshed successfully'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError("Invalid or expired refresh token")
            else:
                raise AuthenticationError(f"Token refresh failed: {e.response['Error']['Message']}")
    
    def logout_user(self, access_token: str) -> Dict[str, any]:
        """
        Logout user by revoking access token
        
        Args:
            access_token: User's access token
            
        Returns:
            Dict containing logout result
        """
        try:
            self.cognito_client.global_sign_out(AccessToken=access_token)
            
            return {
                'success': True,
                'message': 'Logged out successfully'
            }
            
        except ClientError as e:
            # Even if logout fails, we consider it successful from client perspective
            return {
                'success': True,
                'message': 'Logged out (token may have been already expired)'
            }
    
    def resend_confirmation_code(self, email: str) -> Dict[str, any]:
        """
        Resend confirmation code for unverified user
        
        Args:
            email: User's email address
            
        Returns:
            Dict containing resend result
            
        Raises:
            AuthenticationError: If resend fails
        """
        try:
            # Prepare resend parameters
            resend_params = {
                'ClientId': self.client_id,
                'Username': email
            }
            
            # Add secret hash if client secret is configured
            secret_hash = self._calculate_secret_hash(email)
            if secret_hash:
                resend_params['SecretHash'] = secret_hash
            
            # Resend confirmation code
            self.cognito_client.resend_confirmation_code(**resend_params)
            
            return {
                'success': True,
                'message': 'Confirmation code sent to your email'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UserNotFoundException':
                raise AuthenticationError("User not found")
            elif error_code == 'InvalidParameterException':
                raise AuthenticationError("User is already confirmed")
            else:
                raise AuthenticationError(f"Failed to resend code: {e.response['Error']['Message']}")
    
    def validate_token(self, access_token: str) -> bool:
        """
        Validate if access token is still valid
        
        Args:
            access_token: User's access token
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            self.cognito_client.get_user(AccessToken=access_token)
            return True
        except ClientError:
            return False
    
    def get_user_pool_info(self) -> Dict[str, Any]:
        """
        Get user pool information for testing/status purposes
        
        Returns:
            Dict containing user pool info and success status
        """
        try:
            response = self.cognito_client.describe_user_pool(
                UserPoolId=self.user_pool_id
            )
            
            return {
                'success': True,
                'user_pool_id': self.user_pool_id,
                'user_pool_name': response['UserPool'].get('Name', 'Unknown'),
                'status': response['UserPool'].get('Status', 'Unknown'),
                'creation_date': str(response['UserPool'].get('CreationDate', '')),
                'estimated_users': response['UserPool'].get('EstimatedNumberOfUsers', 0)
            }
            
        except ClientError as e:
            return {
                'success': False,
                'error': str(e),
                'user_pool_id': self.user_pool_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'user_pool_id': self.user_pool_id
            }

# Utility functions for session management
def create_session_data(auth_result: Dict[str, any]) -> Dict[str, any]:
    """Create session data from authentication result"""
    return {
        'access_token': auth_result['access_token'],
        'id_token': auth_result['id_token'],
        'refresh_token': auth_result['refresh_token'],
        'user_info': auth_result['user_info'],
        'authenticated': True
    }

def clear_session_data() -> Dict[str, any]:
    """Clear session data for logout"""
    return {
        'access_token': None,
        'id_token': None,
        'refresh_token': None,
        'user_info': None,
        'authenticated': False
    }

def get_user_role(session_data: Dict[str, any]) -> Optional[str]:
    """Get user role from session data"""
    if session_data.get('authenticated') and session_data.get('user_info'):
        return session_data['user_info'].get('role')
    return None

def is_instructor(session_data: Dict[str, any]) -> bool:
    """Check if user is an instructor"""
    return get_user_role(session_data) == 'instructor'

def is_student(session_data: Dict[str, any]) -> bool:
    """Check if user is a student"""
    return get_user_role(session_data) == 'student'