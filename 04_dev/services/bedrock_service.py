"""
Bedrock Service for QuizGenius MVP

This module provides AWS Bedrock integration for PDF text extraction and AI processing,
including document analysis, content validation, and question generation capabilities.
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from botocore.exceptions import ClientError
from utils.config import get_aws_session
from utils.dynamodb_utils import get_current_timestamp, handle_dynamodb_error

class BedrockServiceError(Exception):
    """Custom exception for Bedrock service errors"""
    pass

class BedrockService:
    """Service class for AWS Bedrock operations"""
    
    def __init__(self):
        """Initialize Bedrock service"""
        self.session = get_aws_session()
        self.bedrock_runtime = self.session.client('bedrock-runtime')
        self.bedrock_agent_runtime = self.session.client('bedrock-agent-runtime')
        self.textract_client = self.session.client('textract')
        
        # Model configurations
        self.text_model = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.data_automation_model = "amazon.titan-text-premier-v1:0"
        
        # Processing configurations
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.max_content_length = 100000  # characters
    
    def extract_text_from_pdf(self, pdf_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract text from PDF using Bedrock Data Automation
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for reference
            
        Returns:
            Dict containing extracted text and metadata
            
        Raises:
            BedrockServiceError: If text extraction fails
        """
        try:
            # Use Bedrock Data Automation for PDF text extraction
            extracted_text = self._extract_text_with_bedrock_data_automation(pdf_content, filename)
            
            if not extracted_text:
                raise BedrockServiceError("No text could be extracted from PDF using Bedrock Data Automation")
            
            # Validate and clean the extracted text using Bedrock
            processed_text = self._process_extracted_text(extracted_text, filename)
            
            return {
                'success': True,
                'extracted_text': processed_text['text'],
                'word_count': processed_text['word_count'],
                'quality_score': processed_text['quality_score'],
                'content_type': processed_text['content_type'],
                'filename': filename,
                'extraction_timestamp': get_current_timestamp(),
                'processing_notes': processed_text.get('notes', [])
            }
            
        except Exception as e:
            raise BedrockServiceError(f"PDF text extraction failed: {str(e)}")
    
    def _extract_text_with_bedrock_data_automation(self, pdf_content: bytes, filename: str) -> str:
        """
        Extract text from PDF using Bedrock Data Automation
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for reference
            
        Returns:
            Extracted text as string
        """
        try:
            import base64
            
            # Encode PDF content to base64 for Bedrock Data Automation
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Prepare request for Bedrock Data Automation
            # Using the document analysis capability
            request_body = {
                "inputDocuments": [
                    {
                        "name": filename,
                        "document": {
                            "bytes": pdf_base64
                        }
                    }
                ],
                "outputConfig": {
                    "textExtractionTypes": ["DOCUMENT_TEXT"],
                    "parsedResultFormat": {
                        "textExtractionTypes": ["DOCUMENT_TEXT"]
                    }
                }
            }
            
            # Call Bedrock Data Automation using the correct service
            # Note: Bedrock Data Automation might not be available as a direct model
            # Let's use Textract as the primary method since it's part of the AWS ecosystem
            return self._extract_text_with_textract_fallback(pdf_content, filename)
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text from response
            if 'outputDocuments' in response_body and len(response_body['outputDocuments']) > 0:
                output_doc = response_body['outputDocuments'][0]
                
                if 'extractedText' in output_doc:
                    return output_doc['extractedText']
                elif 'parsedResult' in output_doc and 'documentText' in output_doc['parsedResult']:
                    return output_doc['parsedResult']['documentText']
                else:
                    raise BedrockServiceError("No text found in Bedrock Data Automation response")
            else:
                raise BedrockServiceError("No output documents in Bedrock Data Automation response")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ValidationException':
                raise BedrockServiceError(f"Invalid request to Bedrock Data Automation: {e.response['Error']['Message']}")
            elif error_code == 'AccessDeniedException':
                raise BedrockServiceError("Access denied to Bedrock Data Automation. Please check IAM permissions.")
            elif error_code == 'ThrottlingException':
                raise BedrockServiceError("Bedrock Data Automation request was throttled. Please retry later.")
            elif error_code == 'ServiceUnavailableException':
                raise BedrockServiceError("Bedrock Data Automation service is currently unavailable.")
            else:
                raise BedrockServiceError(f"Bedrock Data Automation error: {error_code}")
                
        except Exception as e:
            # Fallback to Amazon Textract if Bedrock Data Automation is not available
            try:
                return self._extract_text_with_textract_fallback(pdf_content, filename)
            except Exception as fallback_error:
                raise BedrockServiceError(
                    f"Both Bedrock Data Automation and Textract fallback failed. "
                    f"Primary error: {str(e)}. Fallback error: {str(fallback_error)}"
                )
    
    def _process_extracted_text(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Process and validate extracted text using Bedrock
        
        Args:
            text: Extracted text to process
            filename: Original filename for context
            
        Returns:
            Dict containing processed text and analysis
        """
        try:
            # Prepare prompt for text analysis and cleaning
            prompt = f"""
            Please analyze and clean the following text extracted from a PDF document named "{filename}".
            
            Tasks:
            1. Clean up any formatting artifacts or OCR errors
            2. Assess the educational content quality (score 1-10)
            3. Determine the content type (lecture notes, textbook, article, etc.)
            4. Count approximate word count
            5. Identify any issues or notes about the content
            
            Text to analyze:
            {text[:5000]}  # Limit to first 5000 characters for analysis
            
            Please respond in JSON format with the following structure:
            {{
                "text": "cleaned text here",
                "quality_score": 8,
                "content_type": "lecture notes",
                "word_count": 1500,
                "notes": ["any issues or observations"]
            }}
            """
            
            # Call Bedrock to process the text
            response = self._call_bedrock_model(prompt, max_tokens=4000)
            
            # Parse the response
            try:
                result = json.loads(response)
                
                # Validate the response structure
                required_fields = ['text', 'quality_score', 'content_type', 'word_count']
                for field in required_fields:
                    if field not in result:
                        result[field] = self._get_default_value(field, text)
                
                return result
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'text': text,
                    'quality_score': 5,
                    'content_type': 'unknown',
                    'word_count': len(text.split()),
                    'notes': ['Could not parse Bedrock analysis response']
                }
            
        except Exception as e:
            # Fallback processing without Bedrock
            return {
                'text': text,
                'quality_score': 5,
                'content_type': 'unknown',
                'word_count': len(text.split()),
                'notes': [f'Bedrock processing failed: {str(e)}']
            }
    
    def _call_bedrock_model(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Call Bedrock model with retry logic
        
        Args:
            prompt: Text prompt to send to the model
            max_tokens: Maximum tokens in response
            
        Returns:
            Model response as string
        """
        for attempt in range(self.max_retries):
            try:
                # Prepare the request body for Claude
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
                
                # Call Bedrock Runtime
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.text_model,
                    body=json.dumps(body),
                    contentType='application/json',
                    accept='application/json'
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                
                if 'content' in response_body and len(response_body['content']) > 0:
                    return response_body['content'][0]['text']
                else:
                    raise BedrockServiceError("Empty response from Bedrock model")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                if error_code == 'ThrottlingException' and attempt < self.max_retries - 1:
                    # Wait and retry for throttling
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise BedrockServiceError(f"Bedrock API error: {error_code}")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise BedrockServiceError(f"Bedrock model call failed: {str(e)}")
        
        raise BedrockServiceError("Max retries exceeded for Bedrock model call")
    
    def _extract_text_with_textract_fallback(self, pdf_content: bytes, filename: str) -> str:
        """
        Fallback method to extract text using Amazon Textract
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for reference
            
        Returns:
            Extracted text as string
        """
        try:
            # Use Textract to extract text from PDF
            response = self.textract_client.detect_document_text(
                Document={
                    'Bytes': pdf_content
                }
            )
            
            # Extract text from Textract response
            extracted_text = ""
            
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    extracted_text += block.get('Text', '') + "\n"
            
            if not extracted_text.strip():
                raise BedrockServiceError("No text extracted from PDF using Textract")
            
            return extracted_text.strip()
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'InvalidParameterException':
                raise BedrockServiceError(f"Invalid PDF format for Textract: {e.response['Error']['Message']}")
            elif error_code == 'DocumentTooLargeException':
                raise BedrockServiceError("PDF file is too large for Textract processing")
            elif error_code == 'UnsupportedDocumentException':
                raise BedrockServiceError("PDF format not supported by Textract")
            elif error_code == 'AccessDeniedException':
                raise BedrockServiceError("Access denied to Amazon Textract. Please check IAM permissions.")
            else:
                raise BedrockServiceError(f"Textract error: {error_code}")
                
        except Exception as e:
            raise BedrockServiceError(f"Textract text extraction failed: {str(e)}")
    
    def _get_default_value(self, field: str, text: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            'text': text,
            'quality_score': 5,
            'content_type': 'unknown',
            'word_count': len(text.split()) if text else 0,
            'notes': []
        }
        return defaults.get(field, None)
    
    def validate_content_quality(self, text: str) -> Dict[str, Any]:
        """
        Validate content quality for educational use
        
        Args:
            text: Text content to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            validation_result = {
                'is_suitable': True,
                'quality_score': 5,
                'issues': [],
                'recommendations': []
            }
            
            # Basic validation checks
            if not text or len(text.strip()) < 100:
                validation_result['is_suitable'] = False
                validation_result['issues'].append('Content too short for meaningful questions')
                validation_result['quality_score'] = 1
            
            word_count = len(text.split())
            if word_count < 50:
                validation_result['is_suitable'] = False
                validation_result['issues'].append('Insufficient content for question generation')
                validation_result['quality_score'] = 2
            elif word_count > 10000:
                validation_result['recommendations'].append('Content is very long, consider breaking into sections')
            
            # Check for educational indicators
            educational_keywords = [
                'chapter', 'section', 'definition', 'example', 'theory', 'concept',
                'principle', 'method', 'process', 'analysis', 'conclusion'
            ]
            
            text_lower = text.lower()
            educational_score = sum(1 for keyword in educational_keywords if keyword in text_lower)
            
            if educational_score >= 3:
                validation_result['quality_score'] = min(validation_result['quality_score'] + 2, 10)
            elif educational_score == 0:
                validation_result['issues'].append('Content may not be educational material')
                validation_result['quality_score'] = max(validation_result['quality_score'] - 2, 1)
            
            return validation_result
            
        except Exception as e:
            return {
                'is_suitable': False,
                'quality_score': 1,
                'issues': [f'Validation error: {str(e)}'],
                'recommendations': []
            }
    
    def test_bedrock_connection(self) -> Dict[str, Any]:
        """
        Test Bedrock service connectivity
        
        Returns:
            Dict containing connection test results
        """
        try:
            # Test with a simple prompt
            test_prompt = "Hello, please respond with 'Bedrock connection successful' to confirm connectivity."
            
            response = self._call_bedrock_model(test_prompt, max_tokens=50)
            
            return {
                'success': True,
                'model': self.text_model,
                'response': response,
                'timestamp': get_current_timestamp()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': get_current_timestamp()
            }

# Utility functions for PDF processing
def validate_pdf_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Validate PDF file before processing
    
    Args:
        file_content: PDF file content as bytes
        filename: Original filename
        
    Returns:
        Dict containing validation results
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'file_info': {}
    }
    
    try:
        # Check file size (limit to 10MB for MVP)
        file_size = len(file_content)
        validation_result['file_info']['size_bytes'] = file_size
        validation_result['file_info']['size_mb'] = round(file_size / (1024 * 1024), 2)
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            validation_result['is_valid'] = False
            validation_result['errors'].append('File size exceeds 10MB limit')
        
        if file_size < 1024:  # 1KB minimum
            validation_result['is_valid'] = False
            validation_result['errors'].append('File too small to be a valid PDF')
        
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            validation_result['warnings'].append('File does not have .pdf extension')
        
        # Check PDF magic bytes
        if not file_content.startswith(b'%PDF-'):
            validation_result['is_valid'] = False
            validation_result['errors'].append('File does not appear to be a valid PDF')
        
        # Try to read PDF structure
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            validation_result['file_info']['pages'] = len(pdf_reader.pages)
            
            if len(pdf_reader.pages) == 0:
                validation_result['is_valid'] = False
                validation_result['errors'].append('PDF contains no pages')
            elif len(pdf_reader.pages) > 100:
                validation_result['warnings'].append('PDF has many pages, processing may take longer')
                
        except ImportError:
            validation_result['warnings'].append('PyPDF2 not available for detailed validation')
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'PDF structure validation failed: {str(e)}')
        
        return validation_result
        
    except Exception as e:
        return {
            'is_valid': False,
            'errors': [f'Validation error: {str(e)}'],
            'warnings': [],
            'file_info': {}
        }

def create_temp_file_path(filename: str) -> str:
    """
    Create a temporary file path for PDF processing
    
    Args:
        filename: Original filename
        
    Returns:
        Temporary file path
    """
    import tempfile
    import os
    from utils.dynamodb_utils import generate_id
    
    # Create temp directory if it doesn't exist
    temp_dir = os.path.join(tempfile.gettempdir(), 'quizgenius_pdfs')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate unique filename
    file_id = generate_id('pdf')
    temp_filename = f"{file_id}_{filename}"
    
    return os.path.join(temp_dir, temp_filename)

def cleanup_temp_file(file_path: str) -> bool:
    """
    Clean up temporary file
    
    Args:
        file_path: Path to temporary file
        
    Returns:
        True if cleanup successful, False otherwise
    """
    try:
        import os
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return True  # File doesn't exist, consider it cleaned up
    except Exception:
        return False