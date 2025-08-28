"""
QuizGenius MVP - Question Management Page

This module provides the question management interface for instructors.
Will be implemented in Sprint 4.
"""

import streamlit as st


def show_questions_page():
    """Display question management page"""
    
    st.title("❓ Manage Questions")
    st.write("Review, edit, and organize your generated questions.")
    
    st.info("Question management functionality will be implemented in Sprint 4.")
    
    # Placeholder interface
    st.subheader("📝 Generated Questions")
    st.write("No questions available yet. Upload a PDF to generate questions.")
    
    # Development status
    st.divider()
    st.subheader("🔧 Implementation Status")
    st.write("**Coming in Sprint 4**: Question Management & Test Taking")
    st.info("📋 Dependencies: Question generation, data storage")