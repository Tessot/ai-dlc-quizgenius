"""
PDF Upload Page for QuizGenius MVP
Handles PDF file upload with validation and processing status tracking
"""

import streamlit as st
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from services.bedrock_service import BedrockService
from services.content_validation_service import ContentValidationService
from utils.session_manager import SessionManager
from utils.config import Config


class PDFUploadPage:
    """PDF Upload page for instructors"""
    
    def __init__(self):
        """Initialize PDF upload page"""
        self.config = Config()
        self.bedrock_service = BedrockService()
        self.content_validator = ContentValidationService()
        self.session_manager = SessionManager()
        
        # File upload constraints
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = ['.pdf']
        
    def render(self):
        """Render the PDF upload page"""
        st.title("📄 Upload PDF Document")
        st.markdown("Upload your lecture materials to generate quiz questions automatically.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to upload PDFs.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'instructor':
            st.error("Only instructors can upload PDFs.")
            return
            
        # Main upload interface
        self._render_upload_interface()
        
        # Display upload history
        self._render_upload_history()
        
    def _render_upload_interface(self):
        """Render the main upload interface"""
        st.subheader("Upload New PDF")
        
        # File upload component
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a text-based PDF document (max 10MB)"
        )
        
        if uploaded_file is not None:
            # Validate file
            validation_result = self._validate_uploaded_file(uploaded_file)
            
            if validation_result['valid']:
                # Show file details
                self._display_file_details(uploaded_file)
                
                # Upload button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🚀 Process PDF", type="primary", use_container_width=True):
                        self._process_uploaded_file(uploaded_file)
            else:
                # Show validation errors
                for error in validation_result['errors']:
                    st.error(error)
                    
    def _validate_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """Validate uploaded file"""
        errors = []
        
        # Check file size
        if uploaded_file.size > self.max_file_size:
            errors.append(f"File size ({uploaded_file.size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (10MB)")
            
        # Check file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in self.allowed_extensions:
            errors.append(f"File type '{file_extension}' not supported. Please upload a PDF file.")
            
        # Check file name
        if not uploaded_file.name or len(uploaded_file.name.strip()) == 0:
            errors.append("File must have a valid name")
            
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
        
    def _display_file_details(self, uploaded_file):
        """Display details about the uploaded file"""
        st.success("✅ File validation passed")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024 / 1024:.1f} MB")
        with col3:
            st.metric("File Type", "PDF")
            
    def _process_uploaded_file(self, uploaded_file):
        """Process the uploaded PDF file"""
        try:
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Save file temporarily
            status_text.text("📁 Saving file...")
            progress_bar.progress(20)
            
            upload_id = str(uuid.uuid4())
            temp_file_path = self._save_temp_file(uploaded_file, upload_id)
            
            # Step 2: Extract text from PDF
            status_text.text("📖 Extracting text from PDF...")
            progress_bar.progress(40)
            
            # Read PDF content
            with open(temp_file_path, 'rb') as f:
                pdf_content = f.read()
            extraction_result = self.bedrock_service.extract_text_from_pdf(pdf_content, uploaded_file.name)
            
            if not extraction_result['success']:
                st.error(f"Failed to extract text: {extraction_result['error']}")
                self._cleanup_temp_file(temp_file_path)
                return
                
            extracted_text = extraction_result['extracted_text']
            
            # Step 3: Validate content quality
            status_text.text("🔍 Validating content quality...")
            progress_bar.progress(60)
            
            validation_result = self.content_validator.validate_content(extracted_text)
            
            # Step 4: Store document metadata
            status_text.text("💾 Storing document information...")
            progress_bar.progress(80)
            
            document_data = self._store_document_metadata(
                uploaded_file, upload_id, extracted_text, validation_result
            )
            
            # Step 5: Complete processing
            status_text.text("✅ Processing complete!")
            progress_bar.progress(100)
            
            # Store in session for next steps
            st.session_state['current_document'] = document_data
            st.session_state['extracted_text'] = extracted_text
            st.session_state['validation_result'] = validation_result
            
            # Show results
            self._display_processing_results(document_data, validation_result)
            
            # Cleanup
            self._cleanup_temp_file(temp_file_path)
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            if 'temp_file_path' in locals():
                self._cleanup_temp_file(temp_file_path)
                
    def _save_temp_file(self, uploaded_file, upload_id: str) -> str:
        """Save uploaded file temporarily"""
        # Create temp directory if it doesn't exist
        temp_dir = "/tmp/quizgenius_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1]
        temp_filename = f"upload_{upload_id}{file_extension}"
        temp_file_path = os.path.join(temp_dir, temp_filename)
        
        # Save file
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        return temp_file_path
        
    def _store_document_metadata(self, uploaded_file, upload_id: str, 
                               extracted_text: str, validation_result) -> Dict[str, Any]:
        """Store document metadata"""
        user_data = self.session_manager.get_user_info()
        
        document_data = {
            'document_id': upload_id,
            'filename': uploaded_file.name,
            'file_size': uploaded_file.size,
            'upload_timestamp': datetime.now().isoformat(),
            'instructor_id': user_data.get('user_id'),
            'instructor_email': user_data.get('email'),
            'text_length': len(extracted_text),
            'word_count': len(extracted_text.split()),
            'quality_score': validation_result.quality_score,
            'is_suitable': validation_result.is_suitable,
            'content_type': validation_result.metadata['detailed_analysis']['content_type'],
            'processing_status': 'completed'
        }
        
        # Store in session state for now (will be stored in DynamoDB in later phases)
        if 'uploaded_documents' not in st.session_state:
            st.session_state['uploaded_documents'] = []
        st.session_state['uploaded_documents'].append(document_data)
        
        return document_data
        
    def _display_processing_results(self, document_data: Dict[str, Any], validation_result):
        """Display processing results"""
        st.success("🎉 PDF processed successfully!")
        
        # Document summary
        st.subheader("📊 Document Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Word Count", document_data['word_count'])
        with col2:
            st.metric("Quality Score", f"{document_data['quality_score']:.1f}/10")
        with col3:
            st.metric("Content Type", document_data['content_type'].replace('_', ' ').title())
        with col4:
            suitable_text = "✅ Yes" if document_data['is_suitable'] else "❌ No"
            st.metric("Suitable for Questions", suitable_text)
            
        # Content quality feedback
        if validation_result.issues:
            st.subheader("⚠️ Content Issues")
            for issue in validation_result.issues:
                st.warning(issue)
                
        if validation_result.recommendations:
            st.subheader("💡 Recommendations")
            for rec in validation_result.recommendations:
                st.info(rec)
                
        # Next steps
        st.subheader("🚀 Next Steps")
        if document_data['is_suitable']:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👀 Preview Content", use_container_width=True):
                    st.session_state['show_content_preview'] = True
                    st.rerun()
            with col2:
                if st.button("🤖 Generate Questions", type="primary", use_container_width=True):
                    st.session_state['page'] = 'question_generation'
                    st.rerun()
        else:
            st.warning("This document may not be suitable for question generation. Please review the issues above and consider uploading a different document.")
            
    def _render_upload_history(self):
        """Render upload history"""
        if 'uploaded_documents' in st.session_state and st.session_state['uploaded_documents']:
            st.subheader("📚 Recent Uploads")
            
            for doc in reversed(st.session_state['uploaded_documents'][-5:]):  # Show last 5
                with st.expander(f"📄 {doc['filename']} - {doc['upload_timestamp'][:19]}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Size:** {doc['file_size'] / 1024 / 1024:.1f} MB")
                        st.write(f"**Words:** {doc['word_count']}")
                    with col2:
                        st.write(f"**Quality:** {doc['quality_score']:.1f}/10")
                        st.write(f"**Type:** {doc['content_type'].replace('_', ' ').title()}")
                    with col3:
                        suitable = "✅ Yes" if doc['is_suitable'] else "❌ No"
                        st.write(f"**Suitable:** {suitable}")
                        
                        if doc['is_suitable']:
                            if st.button(f"🤖 Generate Questions", key=f"gen_{doc['document_id']}"):
                                st.session_state['current_document'] = doc
                                st.session_state['page'] = 'question_generation'
                                st.rerun()
                                
    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            st.warning(f"Could not clean up temporary file: {e}")


def render_pdf_upload_page():
    """Render the PDF upload page"""
    page = PDFUploadPage()
    page.render()


if __name__ == "__main__":
    render_pdf_upload_page()