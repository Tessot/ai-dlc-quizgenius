"""
QuizGenius MVP - Instructor Dashboard

This module provides the main dashboard interface for instructors.
"""

import streamlit as st


def show_dashboard():
    """Display instructor dashboard"""
    
    st.title("📚 Instructor Dashboard")
    st.write("Welcome to your QuizGenius instructor dashboard!")
    
    # Dashboard overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("PDFs Uploaded", "0", "0")
    
    with col2:
        st.metric("Questions Generated", "0", "0")
    
    with col3:
        st.metric("Tests Created", "0", "0")
    
    with col4:
        st.metric("Students Tested", "0", "0")
    
    st.divider()
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Upload New PDF", use_container_width=True):
            st.session_state.current_page = 'upload_pdf'
            st.rerun()
        
        if st.button("❓ Manage Questions", use_container_width=True):
            st.session_state.current_page = 'manage_questions'
            st.rerun()
    
    with col2:
        if st.button("📝 Create New Test", use_container_width=True):
            st.session_state.current_page = 'create_test'
            st.rerun()
        
        st.button("📊 View Analytics", disabled=True, use_container_width=True)
    
    st.divider()
    
    # Recent activity placeholder
    st.subheader("📈 Recent Activity")
    st.info("No recent activity. Start by uploading a PDF to generate questions!")
    
    # Development status
    st.divider()
    st.subheader("🔧 Development Status")
    st.write("**Sprint 1, Phase 1.1**: Project Setup & Infrastructure")
    st.success("✅ Project structure created")
    st.success("✅ Basic navigation implemented")
    st.info("🔄 Next: AWS infrastructure setup")