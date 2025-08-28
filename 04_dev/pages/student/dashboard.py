"""
QuizGenius MVP - Student Dashboard

This module provides the main dashboard interface for students.
"""

import streamlit as st


def show_dashboard():
    """Display student dashboard"""
    
    st.title("🎓 Student Dashboard")
    st.write("Welcome to your QuizGenius student dashboard!")
    
    # Dashboard overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Available Tests", "0", "0")
    
    with col2:
        st.metric("Tests Completed", "0", "0")
    
    with col3:
        st.metric("Average Score", "0%", "0%")
    
    with col4:
        st.metric("Total Time Spent", "0 min", "0 min")
    
    st.divider()
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.button("📝 Take Available Test", disabled=True, use_container_width=True)
        st.button("📈 View My Results", disabled=True, use_container_width=True)
    
    with col2:
        st.button("📊 View Progress", disabled=True, use_container_width=True)
        st.button("🎯 Practice Mode", disabled=True, use_container_width=True)
    
    st.divider()
    
    # Available tests placeholder
    st.subheader("📝 Available Tests")
    st.info("No tests available yet. Check back later!")
    
    # Recent results placeholder
    st.subheader("📈 Recent Results")
    st.info("No test results yet. Take your first test to see results here!")
    
    # Development status
    st.divider()
    st.subheader("🔧 Development Status")
    st.write("**Sprint 1, Phase 1.1**: Project Setup & Infrastructure")
    st.success("✅ Project structure created")
    st.success("✅ Basic navigation implemented")
    st.info("🔄 Next: AWS infrastructure setup")