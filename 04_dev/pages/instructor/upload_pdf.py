"""
QuizGenius MVP - PDF Upload Page

This module provides the PDF upload interface for instructors.
Will be implemented in Sprint 3.
"""

import streamlit as st


def show_upload_page():
    """Display PDF upload page"""
    
    st.title("📄 Upload PDF")
    st.write("Upload your lecture materials to generate quiz questions.")
    
    st.info("PDF upload functionality will be implemented in Sprint 3.")
    
    # Placeholder interface
    st.subheader("📁 File Upload")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        disabled=True,
        help="PDF upload will be enabled in Sprint 3"
    )
    
    st.button("🚀 Process PDF", disabled=True)
    
    # Development status
    st.divider()
    st.subheader("🔧 Implementation Status")
    st.write("**Coming in Sprint 3**: PDF Processing & Question Generation")
    st.info("📋 Dependencies: AWS Bedrock integration, PDF processing service")