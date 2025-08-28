"""
QuizGenius MVP - Main Streamlit Application Entry Point

This is the main entry point for the QuizGenius MVP Streamlit application.
It handles routing, authentication, and the main application flow.
"""

import streamlit as st
from utils.config import Config
from components.auth import AuthComponent
from components.navigation import NavigationComponent


def main():
    """Main application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="QuizGenius MVP",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load and validate configuration
    if not Config.validate():
        st.error("Configuration validation failed.")
        st.error("Please ensure AWS CLI is configured (`aws configure`) or set AWS credentials in .env file.")
        st.info("Run `python scripts/test_aws_credentials.py` to test your AWS setup.")
        st.stop()
    
    # Initialize session state
    initialize_session_state()
    
    # Authentication check
    auth = AuthComponent()
    if not st.session_state.authenticated:
        auth.show_login_page()
        return
    
    # Show navigation
    nav = NavigationComponent()
    nav.show_navigation()
    
    # Route to appropriate interface based on user role
    if st.session_state.user_role == 'instructor':
        show_instructor_interface()
    elif st.session_state.user_role == 'student':
        show_student_interface()
    else:
        st.error("Invalid user role. Please contact support.")


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    
    # Authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    # Navigation state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    
    # Application state
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = None


def show_instructor_interface():
    """Display instructor interface based on current page"""
    
    page = st.session_state.get('current_page', 'dashboard')
    
    if page == 'dashboard':
        from pages.instructor.dashboard import show_dashboard
        show_dashboard()
    elif page == 'upload_pdf':
        from pages.instructor.upload_pdf import show_upload_page
        show_upload_page()
    elif page == 'manage_questions':
        from pages.instructor.manage_questions import show_questions_page
        show_questions_page()
    elif page == 'create_test':
        from pages.instructor.create_test import show_create_test_page
        show_create_test_page()
    else:
        st.error(f"Unknown page: {page}")


def show_student_interface():
    """Display student interface based on current page"""
    
    page = st.session_state.get('current_page', 'dashboard')
    
    if page == 'dashboard':
        from pages.student.dashboard import show_dashboard
        show_dashboard()
    elif page == 'take_test':
        from pages.student.take_test import show_test_page
        show_test_page()
    elif page == 'view_results':
        from pages.student.view_results import show_results_page
        show_results_page()
    else:
        st.error(f"Unknown page: {page}")


if __name__ == "__main__":
    main()