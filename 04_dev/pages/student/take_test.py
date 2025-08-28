"""
QuizGenius MVP - Test Taking Page

This module provides the test taking interface for students.
Will be implemented in Sprint 4.
"""

import streamlit as st


def show_test_page():
    """Display test taking page"""
    
    st.title("📝 Take Test")
    st.write("Take available tests and demonstrate your knowledge.")
    
    st.info("Test taking functionality will be implemented in Sprint 4.")
    
    # Placeholder interface
    st.subheader("📋 Available Tests")
    st.write("No tests available yet. Check back later!")
    
    # Development status
    st.divider()
    st.subheader("🔧 Implementation Status")
    st.write("**Coming in Sprint 4**: Question Management & Test Taking")
    st.info("📋 Dependencies: Test publishing, question display, answer submission")