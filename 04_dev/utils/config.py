"""
QuizGenius MVP - Configuration Management

This module handles application configuration, environment variables,
and configuration validation. Uses AWS CLI credentials when available.
"""

import os
import boto3
from typing import Dict, List, Optional

# Try to load dotenv if available, but don't fail if not installed
try:
    from dotenv import load_dotenv
    # Load .env file from current directory or parent directories
    load_dotenv(dotenv_path='.env', verbose=True)
except ImportError:
    # dotenv not available, just use environment variables
    pass


class Config:
    """Application configuration class"""
    
    # AWS Configuration - Use AWS CLI credentials by default
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # These will be None if using AWS CLI credentials (which is preferred)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    # DynamoDB Configuration
    DYNAMODB_USERS_TABLE = os.getenv('DYNAMODB_USERS_TABLE', 'QuizGenius-Users')
    DYNAMODB_DOCUMENTS_TABLE = os.getenv('DYNAMODB_DOCUMENTS_TABLE', 'QuizGenius-Documents')
    DYNAMODB_QUESTIONS_TABLE = os.getenv('DYNAMODB_QUESTIONS_TABLE', 'QuizGenius-Questions')
    DYNAMODB_TESTS_TABLE = os.getenv('DYNAMODB_TESTS_TABLE', 'QuizGenius-Tests')
    DYNAMODB_TEST_ATTEMPTS_TABLE = os.getenv('DYNAMODB_TEST_ATTEMPTS_TABLE', 'QuizGenius-TestAttempts')
    DYNAMODB_RESULTS_TABLE = os.getenv('DYNAMODB_RESULTS_TABLE', 'QuizGenius-Results')
    
    # AWS Bedrock Configuration
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')
    BEDROCK_DATA_AUTOMATION_MODEL = os.getenv('BEDROCK_DATA_AUTOMATION_MODEL', 'amazon.titan-text-express-v1')
    
    # AWS Cognito Configuration
    COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
    COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
    COGNITO_CLIENT_SECRET = os.getenv('COGNITO_CLIENT_SECRET')
    
    # Application Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def load_environment_config():
    """Load and validate environment configuration"""
    try:
        # Try to load dotenv if available
        from dotenv import load_dotenv
        load_dotenv(dotenv_path='.env', verbose=False)
    except ImportError:
        pass
    
    # Validate required configuration
    required_vars = ['COGNITO_USER_POOL_ID', 'COGNITO_CLIENT_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
    
    return True
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
    STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', 'localhost')
    
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hour
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    ALLOWED_FILE_TYPES = os.getenv('ALLOWED_FILE_TYPES', 'pdf').split(',')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration variables and AWS credentials
        
        Returns:
            bool: True if all required variables are present, False otherwise
        """
        # Test AWS credentials (either from CLI or environment variables)
        try:
            # Try to create a boto3 session to test credentials
            session = boto3.Session(
                aws_access_key_id=cls.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=cls.AWS_SECRET_ACCESS_KEY,
                region_name=cls.AWS_REGION
            )
            
            # Test credentials by trying to get caller identity
            sts = session.client('sts')
            sts.get_caller_identity()
            
            print(f"✅ AWS credentials validated for region: {cls.AWS_REGION}")
            
        except Exception as e:
            print(f"❌ AWS credentials validation failed: {e}")
            print("Please ensure AWS CLI is configured or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            return False
        
        # In production mode, validate Cognito configuration
        if not cls.DEBUG:
            required_vars = [
                'COGNITO_USER_POOL_ID',
                'COGNITO_CLIENT_ID',
            ]
            
            missing_vars = []
            for var in required_vars:
                if not getattr(cls, var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"Missing required environment variables: {missing_vars}")
                return False
        
        return True
    
    @classmethod
    def get_aws_config(cls) -> Dict[str, Optional[str]]:
        """
        Get AWS configuration dictionary
        
        Returns:
            Dict[str, Optional[str]]: AWS configuration
            If AWS_ACCESS_KEY_ID is None, boto3 will use AWS CLI credentials
        """
        config = {'region_name': cls.AWS_REGION}
        
        # Only add credentials if they're explicitly set
        # Otherwise, boto3 will use AWS CLI credentials
        if cls.AWS_ACCESS_KEY_ID and cls.AWS_SECRET_ACCESS_KEY:
            config.update({
                'aws_access_key_id': cls.AWS_ACCESS_KEY_ID,
                'aws_secret_access_key': cls.AWS_SECRET_ACCESS_KEY,
            })
        
        return config
    
    @classmethod
    def get_boto3_session(cls) -> boto3.Session:
        """
        Get a configured boto3 session
        
        Returns:
            boto3.Session: Configured AWS session
        """
        if cls.AWS_ACCESS_KEY_ID and cls.AWS_SECRET_ACCESS_KEY:
            return boto3.Session(
                aws_access_key_id=cls.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=cls.AWS_SECRET_ACCESS_KEY,
                region_name=cls.AWS_REGION
            )
        else:
            # Use AWS CLI credentials
            return boto3.Session(region_name=cls.AWS_REGION)
    
    @classmethod
    def get_dynamodb_tables(cls) -> Dict[str, str]:
        """
        Get DynamoDB table names
        
        Returns:
            Dict[str, str]: Table name mappings
        """
        return {
            'users': cls.DYNAMODB_USERS_TABLE,
            'documents': cls.DYNAMODB_DOCUMENTS_TABLE,
            'questions': cls.DYNAMODB_QUESTIONS_TABLE,
            'tests': cls.DYNAMODB_TESTS_TABLE,
            'test_attempts': cls.DYNAMODB_TEST_ATTEMPTS_TABLE,
            'results': cls.DYNAMODB_RESULTS_TABLE,
        }
    
    @classmethod
    def is_development(cls) -> bool:
        """
        Check if running in development mode
        
        Returns:
            bool: True if in development mode
        """
        return cls.DEBUG


def get_aws_session():
    """Get AWS session for DynamoDB operations"""
    # Create boto3 session with AWS CLI credentials or environment variables
    if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
        return boto3.Session(
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
    else:
        # Use default credentials (AWS CLI, IAM role, etc.)
        return boto3.Session(region_name=Config.AWS_REGION)