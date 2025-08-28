# QuizGenius MVP - AWS Bedrock Integration Design

## Overview
This document provides detailed integration design for AWS Bedrock services in the QuizGenius MVP Streamlit application, including Data Automation for PDF processing and Foundation Models for question generation.

---

## AWS Bedrock Services Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           QuizGenius Streamlit App                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                        AWS SDK Integration Layer                            │
│  │                                                                             │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  │   boto3 Client  │    │  Credentials    │    │  Error Handler  │         │
│  │  │                 │    │                 │    │                 │         │
│  │  │ • bedrock-agent │    │ • AWS Profile   │    │ • Retry Logic   │         │
│  │  │ • bedrock-runtime│   │ • Environment   │    │ • Rate Limiting │         │
│  │  │ • Configuration │    │ • IAM Roles     │    │ • Logging       │         │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│  └─────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Bedrock Services                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────┐    ┌─────────────────────────────────┐ │
│  │      Bedrock Data Automation        │    │    Bedrock Foundation Models   │ │
│  │                                     │    │                                 │ │
│  │  ┌─────────────────────────────────┐│    │  ┌─────────────────────────────┐│ │
│  │  │    Document Processing          ││    │  │    Question Generation      ││ │
│  │  │                                 ││    │  │                             ││ │
│  │  │ • PDF Text Extraction           ││    │  │ • Claude 3 Haiku/Sonnet    ││ │
│  │  │ • Document Analysis             ││    │  │ • Amazon Titan Text        ││ │
│  │  │ • Content Structure             ││    │  │ • Custom Prompts           ││ │
│  │  │ • Quality Assessment            ││    │  │ • Response Parsing         ││ │
│  │  └─────────────────────────────────┘│    │  └─────────────────────────────┘│ │
│  │                                     │    │                                 │ │
│  │  API Endpoints:                     │    │  API Endpoints:                 │ │
│  │  • StartDocumentAnalysis           │    │  • InvokeModel                  │ │
│  │  • GetDocumentAnalysis             │    │  • InvokeModelWithResponseStream│ │
│  │  • ListDocumentAnalysisJobs        │    │  • ListFoundationModels        │ │
│  └─────────────────────────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Streamlit Authentication System Design

### Session State Management
```python
# Authentication state structure in st.session_state
authentication_state = {
    "authenticated": False,
    "user_role": None,  # "instructor" | "student"
    "user_id": None,
    "username": None,
    "login_time": None,
    "session_timeout": 3600  # 1 hour in seconds
}

# Navigation state
navigation_state = {
    "current_page": "login",
    "previous_page": None,
    "allowed_pages": [],  # Based on user role
    "redirect_after_login": None
}
```

### Authentication Flow (ASCII Diagram)
```
User Access Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Landing   │───►│   Login     │───►│ Role Check  │───►│ Dashboard   │
│   Page      │    │   Form      │    │             │    │   Redirect  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │ Validate    │    │ Set Session │    │ Load User   │
                   │ Credentials │    │ State       │    │ Interface   │
                   └─────────────┘    └─────────────┘    └─────────────┘

Session Management:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Page Access │───►│ Auth Check  │───►│ Allow/Deny  │
│ Request     │    │             │    │ Access      │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │ Session     │    │ Redirect to │
                   │ Validation  │    │ Login       │
                   └─────────────┘    └─────────────┘
```

### Implementation Pattern
```python
# utils/auth.py
import streamlit as st
import json
import hashlib
from datetime import datetime, timedelta

class StreamlitAuth:
    def __init__(self, users_file="data/users.json"):
        self.users_file = users_file
        
    def authenticate_user(self, username, password, role):
        """Authenticate user credentials"""
        users = self.load_users()
        user_key = f"{username}_{role}"
        
        if user_key in users:
            stored_hash = users[user_key]["password_hash"]
            if self.verify_password(password, stored_hash):
                self.set_session_state(username, role, users[user_key])
                return True
        return False
    
    def set_session_state(self, username, role, user_data):
        """Set authentication session state"""
        st.session_state.authenticated = True
        st.session_state.user_role = role
        st.session_state.user_id = user_data["user_id"]
        st.session_state.username = username
        st.session_state.login_time = datetime.now()
        
        # Set allowed pages based on role
        if role == "instructor":
            st.session_state.allowed_pages = [
                "instructor_dashboard", "pdf_upload", "question_generation",
                "question_management", "test_creation", "results_viewing"
            ]
        else:  # student
            st.session_state.allowed_pages = [
                "student_dashboard", "test_taking", "results_viewing"
            ]
    
    def check_authentication(self):
        """Check if user is authenticated and session is valid"""
        if not st.session_state.get("authenticated", False):
            return False
            
        # Check session timeout
        if st.session_state.get("login_time"):
            elapsed = datetime.now() - st.session_state.login_time
            if elapsed.total_seconds() > st.session_state.get("session_timeout", 3600):
                self.logout()
                return False
        
        return True
    
    def logout(self):
        """Clear authentication session state"""
        auth_keys = ["authenticated", "user_role", "user_id", "username", 
                    "login_time", "allowed_pages"]
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]
```

---

## 2. AWS Bedrock Foundation Models Integration

### Question Generation API Integration
```python
# utils/bedrock_client.py
import boto3
import json
import logging
from typing import Dict, List, Optional
from botocore.exceptions import ClientError, BotoCoreError

class BedrockQuestionGenerator:
    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=region_name
        )
        self.logger = logging.getLogger(__name__)
        
    def generate_questions(self, 
                          text_content: str, 
                          num_multiple_choice: int = 5,
                          num_true_false: int = 5,
                          model_id: str = "anthropic.claude-3-haiku-20240307-v1:0") -> Dict:
        """Generate questions using Bedrock Foundation Models"""
        
        try:
            # Generate multiple choice questions
            mc_questions = self._generate_multiple_choice(
                text_content, num_multiple_choice, model_id
            )
            
            # Generate true/false questions
            tf_questions = self._generate_true_false(
                text_content, num_true_false, model_id
            )
            
            return {
                "success": True,
                "multiple_choice": mc_questions,
                "true_false": tf_questions,
                "total_questions": len(mc_questions) + len(tf_questions)
            }
            
        except Exception as e:
            self.logger.error(f"Question generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "multiple_choice": [],
                "true_false": [],
                "total_questions": 0
            }
    
    def _generate_multiple_choice(self, content: str, num_questions: int, model_id: str) -> List[Dict]:
        """Generate multiple choice questions"""
        prompt = self._build_mc_prompt(content, num_questions)
        
        response = self._invoke_model(model_id, prompt)
        if response["success"]:
            return self._parse_mc_response(response["content"])
        return []
    
    def _generate_true_false(self, content: str, num_questions: int, model_id: str) -> List[Dict]:
        """Generate true/false questions"""
        prompt = self._build_tf_prompt(content, num_questions)
        
        response = self._invoke_model(model_id, prompt)
        if response["success"]:
            return self._parse_tf_response(response["content"])
        return []
    
    def _invoke_model(self, model_id: str, prompt: str) -> Dict:
        """Invoke Bedrock model with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Prepare request body based on model
                if "claude" in model_id:
                    body = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 4000,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    }
                elif "titan" in model_id:
                    body = {
                        "inputText": prompt,
                        "textGenerationConfig": {
                            "maxTokenCount": 4000,
                            "temperature": 0.3,
                            "topP": 0.9
                        }
                    }
                
                response = self.bedrock_runtime.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json"
                )
                
                response_body = json.loads(response["body"].read())
                
                # Parse response based on model
                if "claude" in model_id:
                    content = response_body["content"][0]["text"]
                elif "titan" in model_id:
                    content = response_body["results"][0]["outputText"]
                
                return {"success": True, "content": content}
                
            except ClientError as e:
                retry_count += 1
                self.logger.warning(f"Bedrock API error (attempt {retry_count}): {e}")
                if retry_count >= max_retries:
                    return {"success": False, "error": str(e)}
                
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
```

### Prompt Engineering Strategy
```python
# config/prompts.py
class QuestionPrompts:
    
    @staticmethod
    def build_multiple_choice_prompt(content: str, num_questions: int) -> str:
        return f"""
You are an expert educator creating multiple choice questions from educational content.

CONTENT TO ANALYZE:
{content}

INSTRUCTIONS:
1. Create exactly {num_questions} multiple choice questions based on the content
2. Each question should have 4 options (A, B, C, D)
3. Only one option should be correct
4. Questions should test understanding, not just memorization
5. Avoid ambiguous or trick questions
6. Focus on key concepts and important information

OUTPUT FORMAT (JSON):
{{
    "questions": [
        {{
            "question": "Question text here?",
            "options": {{
                "A": "First option",
                "B": "Second option", 
                "C": "Third option",
                "D": "Fourth option"
            }},
            "correct_answer": "A",
            "explanation": "Brief explanation of why this is correct"
        }}
    ]
}}

Generate the questions now:
"""

    @staticmethod
    def build_true_false_prompt(content: str, num_questions: int) -> str:
        return f"""
You are an expert educator creating true/false questions from educational content.

CONTENT TO ANALYZE:
{content}

INSTRUCTIONS:
1. Create exactly {num_questions} true/false questions based on the content
2. Each statement should be clearly true or false based on the content
3. Avoid ambiguous statements that could be interpreted either way
4. Focus on factual information from the content
5. Mix true and false statements roughly equally

OUTPUT FORMAT (JSON):
{{
    "questions": [
        {{
            "statement": "Clear statement about the content",
            "correct_answer": true,
            "explanation": "Brief explanation referencing the content"
        }}
    ]
}}

Generate the questions now:
"""
```

---

## 3. AWS Bedrock Data Automation Integration

### PDF Processing Workflow
```
PDF Processing Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PDF Upload  │───►│ File        │───►│ Bedrock     │───►│ Text        │
│ (Streamlit) │    │ Validation  │    │ Data Auto   │    │ Extraction  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Temp File   │    │ Size/Format │    │ Document    │    │ Structured  │
│ Storage     │    │ Check       │    │ Analysis    │    │ Content     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

Content Processing:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Raw Text    │───►│ Content     │───►│ Quality     │───►│ Ready for   │
│ Output      │    │ Cleaning    │    │ Assessment  │    │ AI Gen      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Text        │    │ Remove      │    │ Length      │    │ Store in    │
│ Extraction  │    │ Headers/    │    │ Check       │    │ Session     │
│             │    │ Footers     │    │ Education   │    │ State       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Data Automation Implementation
```python
# utils/pdf_processor.py
import boto3
import json
import time
import tempfile
import os
from typing import Dict, Optional
from botocore.exceptions import ClientError

class BedrockDataAutomation:
    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name
        self.bedrock_agent = boto3.client(
            service_name="bedrock-agent",
            region_name=region_name
        )
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.temp_bucket = None  # Will be configured
        
    def extract_text_from_pdf(self, pdf_file, filename: str) -> Dict:
        """Extract text from PDF using Bedrock Data Automation"""
        
        try:
            # Step 1: Upload PDF to temporary S3 location
            s3_key = self._upload_to_temp_s3(pdf_file, filename)
            if not s3_key:
                return {"success": False, "error": "Failed to upload PDF"}
            
            # Step 2: Start document analysis job
            job_id = self._start_document_analysis(s3_key)
            if not job_id:
                return {"success": False, "error": "Failed to start analysis"}
            
            # Step 3: Wait for completion and get results
            analysis_result = self._wait_for_analysis_completion(job_id)
            if not analysis_result["success"]:
                return analysis_result
            
            # Step 4: Process and clean extracted text
            processed_text = self._process_extracted_text(analysis_result["data"])
            
            # Step 5: Validate content quality
            quality_check = self._validate_content_quality(processed_text)
            
            # Step 6: Cleanup temporary files
            self._cleanup_temp_s3(s3_key)
            
            return {
                "success": True,
                "extracted_text": processed_text,
                "quality_metrics": quality_check,
                "word_count": len(processed_text.split()),
                "character_count": len(processed_text)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _upload_to_temp_s3(self, pdf_file, filename: str) -> Optional[str]:
        """Upload PDF to temporary S3 location"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(pdf_file.read())
                temp_file_path = temp_file.name
            
            # Generate S3 key
            s3_key = f"temp-pdfs/{int(time.time())}_{filename}"
            
            # Upload to S3 (assuming temp bucket is configured)
            if self.temp_bucket:
                self.s3_client.upload_file(temp_file_path, self.temp_bucket, s3_key)
                os.unlink(temp_file_path)  # Clean up local temp file
                return s3_key
            else:
                # For local development, we might need to handle this differently
                # This is a placeholder for the actual implementation
                return f"local://{temp_file_path}"
                
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            return None
    
    def _start_document_analysis(self, s3_key: str) -> Optional[str]:
        """Start Bedrock Data Automation document analysis"""
        try:
            # This is a placeholder for the actual Bedrock Data Automation API
            # The exact API calls will depend on the specific service endpoints
            
            response = self.bedrock_agent.start_document_analysis_job(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': self.temp_bucket,
                        'Name': s3_key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS', 'LAYOUT'],
                OutputConfig={
                    'S3Bucket': self.temp_bucket,
                    'S3Prefix': f'analysis-output/{s3_key}'
                }
            )
            
            return response.get('JobId')
            
        except ClientError as e:
            print(f"Error starting document analysis: {e}")
            return None
    
    def _wait_for_analysis_completion(self, job_id: str, max_wait_time: int = 300) -> Dict:
        """Wait for document analysis to complete"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.bedrock_agent.get_document_analysis_job(JobId=job_id)
                status = response.get('JobStatus')
                
                if status == 'SUCCEEDED':
                    return {
                        "success": True,
                        "data": response.get('Results', {})
                    }
                elif status == 'FAILED':
                    return {
                        "success": False,
                        "error": f"Analysis job failed: {response.get('StatusMessage', 'Unknown error')}"
                    }
                elif status in ['IN_PROGRESS', 'SUBMITTED']:
                    time.sleep(10)  # Wait 10 seconds before checking again
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Unexpected job status: {status}"
                    }
                    
            except ClientError as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Analysis timeout"}
    
    def _process_extracted_text(self, analysis_data: Dict) -> str:
        """Process and clean extracted text"""
        # This will depend on the actual structure of Bedrock Data Automation response
        # Placeholder implementation
        
        extracted_text = ""
        
        # Extract text from different document elements
        if 'Blocks' in analysis_data:
            for block in analysis_data['Blocks']:
                if block.get('BlockType') == 'LINE':
                    text = block.get('Text', '')
                    if text.strip():
                        extracted_text += text + "\n"
        
        # Clean up the text
        cleaned_text = self._clean_extracted_text(extracted_text)
        
        return cleaned_text
    
    def _clean_extracted_text(self, raw_text: str) -> str:
        """Clean and format extracted text"""
        lines = raw_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Skip likely headers/footers (simple heuristic)
            if len(line) < 10 and (line.isdigit() or 'page' in line.lower()):
                continue
                
            # Skip lines that are mostly special characters
            if len([c for c in line if c.isalnum()]) < len(line) * 0.5:
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _validate_content_quality(self, text: str) -> Dict:
        """Validate extracted content quality"""
        word_count = len(text.split())
        char_count = len(text)
        
        # Basic quality metrics
        quality_score = 0
        issues = []
        
        # Check minimum length
        if word_count < 100:
            issues.append("Content too short for meaningful question generation")
        else:
            quality_score += 25
            
        # Check for educational indicators
        educational_keywords = [
            'chapter', 'section', 'definition', 'example', 'theory',
            'concept', 'principle', 'method', 'process', 'analysis'
        ]
        
        found_keywords = sum(1 for keyword in educational_keywords 
                           if keyword in text.lower())
        
        if found_keywords >= 3:
            quality_score += 25
        elif found_keywords >= 1:
            quality_score += 10
        else:
            issues.append("Limited educational content indicators found")
        
        # Check text structure
        sentences = text.split('.')
        if len(sentences) >= 10:
            quality_score += 25
        elif len(sentences) >= 5:
            quality_score += 15
        else:
            issues.append("Limited sentence structure")
        
        # Check for coherent paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) >= 3:
            quality_score += 25
        elif len(paragraphs) >= 1:
            quality_score += 15
        else:
            issues.append("Poor paragraph structure")
        
        return {
            "quality_score": quality_score,
            "word_count": word_count,
            "character_count": char_count,
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
            "issues": issues,
            "suitable_for_questions": quality_score >= 50
        }
    
    def _cleanup_temp_s3(self, s3_key: str):
        """Clean up temporary S3 files"""
        try:
            if self.temp_bucket and s3_key.startswith('temp-pdfs/'):
                self.s3_client.delete_object(Bucket=self.temp_bucket, Key=s3_key)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp file {s3_key}: {e}")
```

---

## 4. Configuration and Error Handling

### AWS Configuration Management
```python
# config/aws_config.py
import boto3
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

class AWSConfig:
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.profile = os.getenv('AWS_PROFILE', 'default')
        
    def get_bedrock_runtime_client(self):
        """Get Bedrock Runtime client with proper configuration"""
        try:
            session = boto3.Session(profile_name=self.profile)
            return session.client('bedrock-runtime', region_name=self.region)
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise Exception(f"AWS credentials not configured: {e}")
    
    def get_bedrock_agent_client(self):
        """Get Bedrock Agent client for Data Automation"""
        try:
            session = boto3.Session(profile_name=self.profile)
            return session.client('bedrock-agent', region_name=self.region)
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise Exception(f"AWS credentials not configured: {e}")
    
    def validate_configuration(self):
        """Validate AWS configuration"""
        try:
            # Test Bedrock access
            bedrock = self.get_bedrock_runtime_client()
            bedrock.list_foundation_models()
            
            return {"valid": True, "message": "AWS configuration is valid"}
        except Exception as e:
            return {"valid": False, "message": str(e)}

# Environment configuration
AWS_REGION = "us-east-1"
BEDROCK_MODEL_IDS = {
    "claude_haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude_sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "titan_text": "amazon.titan-text-express-v1"
}

# Retry configuration
RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 2,
    "initial_delay": 1
}

# Rate limiting
RATE_LIMITS = {
    "requests_per_minute": 60,
    "tokens_per_minute": 50000
}
```

### Error Handling and Logging
```python
# utils/error_handler.py
import logging
import streamlit as st
from functools import wraps
from typing import Callable, Any

class QuizGeniusLogger:
    def __init__(self):
        self.logger = logging.getLogger('quizgenius')
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with context"""
        self.logger.error(f"{context}: {str(error)}")
    
    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)

def handle_bedrock_errors(func: Callable) -> Callable:
    """Decorator to handle Bedrock API errors"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = str(e)
            
            # Handle specific Bedrock errors
            if "ThrottlingException" in error_message:
                st.error("⚠️ Service is busy. Please try again in a moment.")
            elif "ValidationException" in error_message:
                st.error("❌ Invalid request. Please check your input.")
            elif "AccessDeniedException" in error_message:
                st.error("🔒 Access denied. Please check your AWS permissions.")
            elif "ModelNotReadyException" in error_message:
                st.error("🤖 AI model is not ready. Please try again later.")
            else:
                st.error(f"❌ An error occurred: {error_message}")
            
            # Log the error
            logger = QuizGeniusLogger()
            logger.log_error(e, f"Function: {func.__name__}")
            
            return None
    
    return wrapper

def display_user_friendly_error(error_type: str, details: str = ""):
    """Display user-friendly error messages"""
    error_messages = {
        "pdf_upload": "📄 There was an issue processing your PDF. Please ensure it's a valid text-based PDF file.",
        "question_generation": "🤖 Unable to generate questions at this time. Please try again or check your content.",
        "authentication": "🔐 Login failed. Please check your credentials and try again.",
        "data_save": "💾 Unable to save your data. Please try again.",
        "aws_connection": "☁️ Unable to connect to AWS services. Please check your internet connection."
    }
    
    message = error_messages.get(error_type, "❌ An unexpected error occurred.")
    if details:
        message += f"\n\nDetails: {details}"
    
    st.error(message)
```

---

## 5. Integration Testing Strategy

### Testing Components
```python
# tests/test_bedrock_integration.py
import pytest
import boto3
from moto import mock_bedrock
from utils.bedrock_client import BedrockQuestionGenerator
from utils.pdf_processor import BedrockDataAutomation

class TestBedrockIntegration:
    
    def test_question_generation_success(self):
        """Test successful question generation"""
        generator = BedrockQuestionGenerator()
        
        sample_text = """
        Photosynthesis is the process by which plants convert sunlight into energy.
        This process occurs in the chloroplasts of plant cells and requires carbon dioxide,
        water, and sunlight to produce glucose and oxygen.
        """
        
        # Mock the Bedrock response
        with mock_bedrock():
            result = generator.generate_questions(sample_text, 2, 2)
            
            assert result["success"] == True
            assert len(result["multiple_choice"]) <= 2
            assert len(result["true_false"]) <= 2
    
    def test_pdf_processing_workflow(self):
        """Test PDF processing workflow"""
        processor = BedrockDataAutomation()
        
        # Test with sample PDF content
        # This would require actual PDF file for full testing
        pass
    
    def test_error_handling(self):
        """Test error handling for API failures"""
        generator = BedrockQuestionGenerator()
        
        # Test with invalid content
        result = generator.generate_questions("", 1, 1)
        assert result["success"] == False
        assert "error" in result
```

---

## Summary

This AWS Bedrock integration design provides:

1. **Comprehensive Bedrock Integration** - Both Data Automation and Foundation Models
2. **Streamlit Authentication** - Simple session-based user management
3. **Robust Error Handling** - User-friendly error messages and logging
4. **Configuration Management** - Flexible AWS credential handling
5. **Quality Validation** - Content quality assessment for better question generation
6. **Testing Strategy** - Unit tests for integration components

The design supports all MVP requirements while maintaining simplicity for local development and providing a clear path for AWS deployment.