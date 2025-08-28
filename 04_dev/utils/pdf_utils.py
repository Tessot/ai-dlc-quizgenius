"""
PDF Processing Utilities for QuizGenius MVP

This module provides utility functions for PDF file handling, validation,
and processing operations.
"""

import os
import tempfile
import mimetypes
from typing import Dict, List, Any, Optional, Tuple, BinaryIO
from utils.dynamodb_utils import generate_id, get_current_timestamp

class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors"""
    pass

class PDFProcessor:
    """Utility class for PDF processing operations"""
    
    def __init__(self):
        """Initialize PDF processor"""
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.min_file_size = 500  # 500 bytes (more reasonable for test PDFs)
        self.allowed_extensions = ['.pdf']
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'quizgenius_pdfs')
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def validate_upload(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate uploaded PDF file
        
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
            'file_info': {
                'filename': filename,
                'size_bytes': len(file_content),
                'size_mb': round(len(file_content) / (1024 * 1024), 2),
                'timestamp': get_current_timestamp()
            }
        }
        
        try:
            # File size validation
            file_size = len(file_content)
            
            if file_size > self.max_file_size:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f'File size ({validation_result["file_info"]["size_mb"]}MB) exceeds maximum allowed size (10MB)'
                )
            
            if file_size < self.min_file_size:
                validation_result['is_valid'] = False
                validation_result['errors'].append('File is too small to be a valid PDF')
            
            # File extension validation
            file_ext = os.path.splitext(filename.lower())[1]
            if file_ext not in self.allowed_extensions:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f'Invalid file extension. Only PDF files are allowed.')
            
            # MIME type validation
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type and mime_type != 'application/pdf':
                validation_result['warnings'].append(f'MIME type {mime_type} may not be PDF')
            
            # PDF magic bytes validation
            if not file_content.startswith(b'%PDF-'):
                validation_result['is_valid'] = False
                validation_result['errors'].append('File does not appear to be a valid PDF document')
            
            # Try to extract basic PDF information (optional)
            try:
                pdf_info = self._extract_basic_pdf_info(file_content)
                validation_result['file_info'].update(pdf_info)
                
                if pdf_info.get('pages', 0) == 0:
                    validation_result['warnings'].append('Could not determine page count')
                elif pdf_info.get('pages', 0) > 50:
                    validation_result['warnings'].append(
                        f'PDF has {pdf_info["pages"]} pages. Processing may take longer.'
                    )
                    
            except Exception as e:
                validation_result['warnings'].append(f'Could not extract PDF metadata: {str(e)}')
            
            return validation_result
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f'Validation failed: {str(e)}'],
                'warnings': [],
                'file_info': validation_result['file_info']
            }
    
    def _extract_basic_pdf_info(self, file_content: bytes) -> Dict[str, Any]:
        """
        Extract basic information from PDF without external dependencies
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Dict containing basic PDF information
        """
        try:
            # Basic PDF structure analysis without PyPDF2
            info = {
                'has_pdf_header': file_content.startswith(b'%PDF-'),
                'file_size': len(file_content)
            }
            
            # Try to estimate page count by counting page objects
            # This is a rough estimation and may not be accurate for all PDFs
            try:
                content_str = file_content.decode('latin-1', errors='ignore')
                page_count = content_str.count('/Type /Page')
                if page_count > 0:
                    info['estimated_pages'] = page_count
                else:
                    # Alternative method: count page references
                    page_count = content_str.count('endobj')
                    info['estimated_pages'] = max(1, page_count // 4)  # Rough estimate
            except:
                info['estimated_pages'] = 1  # Default assumption
            
            # Check for encryption indicators
            content_str = file_content.decode('latin-1', errors='ignore')
            info['possibly_encrypted'] = '/Encrypt' in content_str
            
            return info
            
        except Exception as e:
            # Return minimal info if extraction fails
            return {
                'has_pdf_header': file_content.startswith(b'%PDF-') if file_content else False,
                'file_size': len(file_content) if file_content else 0,
                'estimated_pages': 1,
                'extraction_error': str(e)
            }
    
    def save_temp_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded file to temporary location
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Path to temporary file
        """
        try:
            # Generate unique filename
            file_id = generate_id('pdf')
            safe_filename = self._sanitize_filename(filename)
            temp_filename = f"{file_id}_{safe_filename}"
            temp_path = os.path.join(self.temp_dir, temp_filename)
            
            # Write file to temp location
            with open(temp_path, 'wb') as temp_file:
                temp_file.write(file_content)
            
            return temp_path
            
        except Exception as e:
            raise PDFProcessingError(f"Failed to save temporary file: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        import re
        
        # Remove or replace unsafe characters
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Limit length
        if len(safe_filename) > 100:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:95] + ext
        
        return safe_filename
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Remove temporary file
        
        Args:
            file_path: Path to temporary file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception:
            return False
    
    def cleanup_old_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files
        
        Args:
            max_age_hours: Maximum age of files to keep (in hours)
            
        Returns:
            Number of files cleaned up
        """
        import time
        
        cleaned_count = 0
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception:
                            continue
            
            return cleaned_count
            
        except Exception:
            return 0
    
    def get_temp_dir_info(self) -> Dict[str, Any]:
        """
        Get information about temporary directory
        
        Returns:
            Dict containing directory information
        """
        try:
            file_count = 0
            total_size = 0
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    file_count += 1
                    total_size += os.path.getsize(file_path)
            
            return {
                'temp_dir': self.temp_dir,
                'file_count': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'exists': os.path.exists(self.temp_dir)
            }
            
        except Exception as e:
            return {
                'temp_dir': self.temp_dir,
                'error': str(e),
                'exists': os.path.exists(self.temp_dir)
            }

class FileUploadHandler:
    """Handler for file upload operations"""
    
    def __init__(self):
        """Initialize file upload handler"""
        self.pdf_processor = PDFProcessor()
        self.upload_history = []
    
    def handle_upload(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Handle complete file upload process
        
        Args:
            file_content: Uploaded file content
            filename: Original filename
            
        Returns:
            Dict containing upload results
        """
        upload_result = {
            'success': False,
            'upload_id': generate_id('upload'),
            'filename': filename,
            'timestamp': get_current_timestamp(),
            'temp_path': None,
            'validation': None,
            'errors': []
        }
        
        try:
            # Validate the uploaded file
            validation = self.pdf_processor.validate_upload(file_content, filename)
            upload_result['validation'] = validation
            
            if not validation['is_valid']:
                upload_result['errors'] = validation['errors']
                return upload_result
            
            # Save to temporary location
            temp_path = self.pdf_processor.save_temp_file(file_content, filename)
            upload_result['temp_path'] = temp_path
            upload_result['success'] = True
            
            # Add to upload history
            self.upload_history.append({
                'upload_id': upload_result['upload_id'],
                'filename': filename,
                'temp_path': temp_path,
                'timestamp': upload_result['timestamp'],
                'file_info': validation['file_info']
            })
            
            return upload_result
            
        except Exception as e:
            upload_result['errors'].append(f"Upload processing failed: {str(e)}")
            return upload_result
    
    def get_upload_by_id(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """
        Get upload information by ID
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            Upload information or None if not found
        """
        for upload in self.upload_history:
            if upload['upload_id'] == upload_id:
                return upload
        return None
    
    def cleanup_upload(self, upload_id: str) -> bool:
        """
        Clean up upload and remove from history
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            True if successful, False otherwise
        """
        upload = self.get_upload_by_id(upload_id)
        if not upload:
            return False
        
        try:
            # Remove temporary file
            if upload.get('temp_path'):
                self.pdf_processor.cleanup_temp_file(upload['temp_path'])
            
            # Remove from history
            self.upload_history = [u for u in self.upload_history if u['upload_id'] != upload_id]
            
            return True
            
        except Exception:
            return False

# Utility functions
def extract_text_from_pdf_file(file_path: str) -> str:
    """
    Extract text from PDF file using Bedrock Data Automation
    Note: This function requires a BedrockService instance for actual extraction
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text
    """
    try:
        with open(file_path, 'rb') as file:
            pdf_content = file.read()
        
        # This would require BedrockService integration
        # For now, return a placeholder
        raise PDFProcessingError(
            "Text extraction requires BedrockService integration. "
            "Use BedrockService.extract_text_from_pdf() instead."
        )
            
    except Exception as e:
        raise PDFProcessingError(f"Text extraction failed: {str(e)}")

def get_pdf_basic_info(file_path: str) -> Dict[str, Any]:
    """
    Get basic PDF information without external dependencies
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Dict containing basic PDF information
    """
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
        
        processor = PDFProcessor()
        return processor._extract_basic_pdf_info(content)
            
    except Exception as e:
        return {'error': str(e)}

def validate_pdf_file_path(file_path: str) -> Dict[str, Any]:
    """
    Validate PDF file at given path
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Validation results
    """
    try:
        if not os.path.exists(file_path):
            return {
                'is_valid': False,
                'errors': ['File does not exist'],
                'warnings': [],
                'file_info': {}
            }
        
        with open(file_path, 'rb') as file:
            content = file.read()
        
        processor = PDFProcessor()
        filename = os.path.basename(file_path)
        return processor.validate_upload(content, filename)
            
    except Exception as e:
        return {
            'is_valid': False,
            'errors': [f'Validation failed: {str(e)}'],
            'warnings': [],
            'file_info': {}
        }