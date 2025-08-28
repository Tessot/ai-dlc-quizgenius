"""
QuizGenius MVP - Test Creation Page

This module provides the test creation interface for instructors.
Will be implemented in Sprint 4.
"""

import streamlit as st


def show_create_test_page():
    """Display test creation page"""
    
    st.title("📝 Create Test")
    st.write("Create and publish tests from your generated questions.")
    
    st.info("Test creation functionality will be implemented in Sprint 4.")
    
    # Placeholder interface
    st.subheader("🎯 Test Configuration")
    st.text_input("Test Title", disabled=True, placeholder="Enter test title")
    st.text_area("Test Description", disabled=True, placeholder="Enter test description")
    st.number_input("Time Limit (minutes)", disabled=True, min_value=1, value=30)
    
    st.button("📋 Select Questions", disabled=True)
    st.button("🚀 Publish Test", disabled=True)
    
    # Development status
    st.divider()
    st.subheader("🔧 Implementation Status")
    st.write("**Coming in Sprint 4**: Question Management & Test Taking")
    st.info("📋 Dependencies: Question management, test data storage")