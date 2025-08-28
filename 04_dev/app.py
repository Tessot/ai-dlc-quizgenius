"""
QuizGenius MVP - Main Streamlit Application

This is the main entry point for the QuizGenius MVP application.
It provides a web interface for instructors and students to interact
with the quiz generation and testing system.
"""

import streamlit as st
import sys
import os
from typing import Dict, Any, Optional

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our services and utilities
from services.auth_service import AuthService
from services.user_service import UserService, UserServiceError
from utils.config import load_environment_config
from components.auth_components import AuthComponents
from components.navigation import NavigationManager
from utils.session_manager import SessionManager

# Page configuration
st.set_page_config(
    page_title="QuizGenius MVP",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class QuizGeniusApp:
    """Main application class for QuizGenius MVP"""
    
    def __init__(self):
        """Initialize the application"""
        self.load_config()
        self.initialize_services()
        self.session_manager = SessionManager()
        self.auth_components = AuthComponents()
        self.navigation = NavigationManager()
    
    def load_config(self):
        """Load application configuration"""
        try:
            load_environment_config()
            st.success("✅ Configuration loaded successfully", icon="⚙️")
        except Exception as e:
            st.error(f"❌ Configuration error: {str(e)}", icon="⚠️")
            st.stop()
    
    def initialize_services(self):
        """Initialize application services"""
        try:
            self.auth_service = AuthService()
            self.user_service = UserService()
            st.success("✅ Services initialized successfully", icon="🔧")
        except Exception as e:
            st.error(f"❌ Service initialization error: {str(e)}", icon="⚠️")
            st.stop()
    
    def run(self):
        """Main application entry point"""
        try:
            # Initialize session state
            self.session_manager.initialize_session()
            
            # Show header
            self.show_header()
            
            # Handle authentication
            if not self.session_manager.is_authenticated():
                self.show_authentication_page()
            else:
                self.show_main_application()
                
        except Exception as e:
            st.error(f"❌ Application error: {str(e)}", icon="🚨")
            st.exception(e)
    
    def show_header(self):
        """Display application header"""
        st.title("🧠 QuizGenius MVP")
        st.markdown("*AI-Powered Quiz Generation from PDF Documents*")
        
        # Show user info if authenticated
        if self.session_manager.is_authenticated():
            user_info = self.session_manager.get_user_info()
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**Welcome, {user_info.get('first_name', 'User')}!** ({user_info.get('role', 'Unknown').title()})")
            
            with col2:
                if st.button("🔄 Refresh", help="Refresh the application"):
                    st.rerun()
            
            with col3:
                if st.button("🚪 Logout", help="Logout from the application"):
                    self.session_manager.logout()
                    st.rerun()
        
        st.divider()
    
    def show_authentication_page(self):
        """Display authentication page"""
        st.header("🔐 Authentication")
        
        # Create tabs for login and registration
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            self.auth_components.show_login_form(
                self.auth_service, 
                self.user_service,
                self.session_manager
            )
        
        with register_tab:
            # Role-based registration options
            st.subheader("📝 Create New Account")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("👨‍🏫 Register as Instructor", use_container_width=True, help="Create an instructor account to generate and manage quizzes"):
                    st.switch_page("pages/instructor_registration.py")
            
            with col2:
                if st.button("👨‍🎓 Register as Student", use_container_width=True, help="Create a student account to take quizzes and track progress"):
                    st.switch_page("pages/student_registration.py")
            
            st.divider()
            
            # Show general registration form as fallback
            with st.expander("📋 General Registration Form"):
                self.auth_components.show_registration_form(
                    self.auth_service,
                    self.user_service,
                    self.session_manager
                )
    
    def show_main_application(self):
        """Display main application interface"""
        user_info = self.session_manager.get_user_info()
        user_role = user_info.get('role', 'unknown')
        
        # Show navigation sidebar
        selected_page = self.navigation.show_sidebar(user_role)
        
        # Show main content based on selected page
        if selected_page == "Dashboard":
            self.show_dashboard(user_role)
        elif selected_page == "PDF Upload" and user_role == "instructor":
            self.show_pdf_upload_page()
        elif selected_page == "Content Preview" and user_role == "instructor":
            self.show_content_preview_page()
        elif selected_page == "Question Generation" and user_role == "instructor":
            self.show_question_generation_page()
        elif selected_page == "Question Management" and user_role == "instructor":
            self.show_question_management_page()
        elif selected_page == "Question Edit" and user_role == "instructor":
            self.show_question_edit_page()
        elif selected_page == "Test Creation" and user_role == "instructor":
            self.show_test_creation_page()
        elif selected_page == "Test Publishing" and user_role == "instructor":
            self.show_test_publishing_page()
        elif selected_page == "Results & Analytics" and user_role == "instructor":
            self.show_instructor_results_page()
        elif selected_page == "Available Tests" and user_role == "student":
            self.show_available_tests_page()
        elif selected_page == "Test Taking" and user_role == "student":
            self.show_test_taking_page()
        elif selected_page == "Test Results" and user_role == "student":
            self.show_test_results_page()
        elif selected_page == "Profile":
            self.show_profile_page()
        elif selected_page == "System Status":
            self.show_system_status_page()
        else:
            st.error("❌ Page not found or access denied", icon="🚫")
    
    def show_dashboard(self, user_role: str):
        """Display user dashboard"""
        st.header(f"📊 {user_role.title()} Dashboard")
        
        if user_role == "instructor":
            self.show_instructor_dashboard()
        elif user_role == "student":
            self.show_student_dashboard()
        else:
            st.error("❌ Unknown user role", icon="⚠️")
    
    def show_instructor_dashboard(self):
        """Display instructor dashboard"""
        st.subheader("👨‍🏫 Instructor Overview")
        
        # Get user info for personalized dashboard
        user_info = self.session_manager.get_user_info()
        
        # Welcome message
        st.markdown(f"**Welcome back, {user_info.get('first_name', 'Instructor')}!**")
        
        # Get user statistics
        try:
            stats = self.user_service.get_user_statistics()
            
            # Dashboard metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 PDFs Processed", "0", help="Total PDFs uploaded and processed")
            
            with col2:
                st.metric("❓ Questions Generated", "0", help="Total questions generated from PDFs")
            
            with col3:
                st.metric("📝 Tests Created", "0", help="Total tests created")
            
            with col4:
                st.metric("👥 Total Students", stats.get('students', 0), help="Total students in the system")
            
        except Exception as e:
            st.error(f"Error loading dashboard metrics: {str(e)}")
        
        st.divider()
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Upload PDF", use_container_width=True, help="Upload a new PDF document"):
                st.session_state['selected_page'] = 'PDF Upload'
                st.rerun()
        
        with col2:
            if st.button("❓ Manage Questions", use_container_width=True, help="Review and edit generated questions"):
                st.session_state['selected_page'] = 'Question Management'
                st.rerun()
        
        with col3:
            if st.button("📈 View Analytics", use_container_width=True, help="View test results and analytics"):
                st.session_state['selected_page'] = 'Results & Analytics'
                st.rerun()
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        
        # Show user's recent login info
        if user_info.get('last_login'):
            st.info(f"Last login: {user_info.get('last_login')}")
        else:
            st.info("Welcome! This is your first time logging in.")
        
        # System status
        st.subheader("🔧 System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                # Test DynamoDB connection
                stats = self.user_service.get_user_statistics()
                st.success(f"✅ Database: Connected ({stats['total_users']} users)")
            except Exception as e:
                st.error(f"❌ Database: Error - {str(e)}")
        
        with col2:
            try:
                # Test Cognito connection
                pool_info = self.auth_service.get_user_pool_info()
                if pool_info.get('success'):
                    st.success("✅ Authentication: Connected")
                else:
                    st.error("❌ Authentication: Error")
            except Exception as e:
                st.error(f"❌ Authentication: Error - {str(e)}")
    
    def show_student_dashboard(self):
        """Display student dashboard"""
        st.subheader("👨‍🎓 Student Overview")
        
        # Get user info for personalized dashboard
        user_info = self.session_manager.get_user_info()
        
        # Welcome message
        st.markdown(f"**Welcome back, {user_info.get('first_name', 'Student')}!**")
        
        # Show student-specific information
        if user_info.get('school'):
            st.markdown(f"*{user_info.get('school')}*")
        
        # Dashboard metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Tests Available", "0", help="Tests available to take")
        
        with col2:
            st.metric("✅ Tests Completed", "0", help="Tests you have completed")
        
        with col3:
            st.metric("📊 Average Score", "0%", help="Your average test score")
        
        with col4:
            st.metric("🏆 Best Score", "0%", help="Your highest test score")
        
        st.divider()
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 Browse Tests", use_container_width=True, help="Browse and take available tests"):
                st.session_state['selected_page'] = 'Available Tests'
                st.rerun()
        
        with col2:
            if st.button("📊 View Results", use_container_width=True, help="View your test results"):
                st.session_state['selected_page'] = 'Test Results'
                st.rerun()
        
        # Learning preferences
        if user_info.get('subject_interests'):
            st.subheader("📚 Your Interests")
            interests = user_info.get('subject_interests', [])
            if interests:
                st.write(", ".join(interests))
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        
        # Show user's recent login info
        if user_info.get('last_login'):
            st.info(f"Last login: {user_info.get('last_login')}")
        else:
            st.info("Welcome! This is your first time logging in.")
        
        # Study tips
        st.subheader("💡 Study Tips")
        
        tips = [
            "📖 Review your course materials before taking quizzes",
            "⏰ Set aside dedicated time for studying without distractions",
            "🎯 Focus on understanding concepts rather than memorizing",
            "📝 Take notes while studying to reinforce learning",
            "🔄 Review your quiz results to identify areas for improvement"
        ]
        
        for tip in tips:
            st.markdown(f"- {tip}")
        
        # Performance tracking
        if user_info.get('preferences', {}).get('performance_tracking'):
            st.subheader("📈 Performance Tracking")
            st.info("Performance tracking is enabled. Your quiz results will be tracked to help you improve.")
    
    def show_pdf_upload_page(self):
        """Display PDF upload page"""
        from pages.pdf_upload import render_pdf_upload_page
        render_pdf_upload_page()
    
    def show_content_preview_page(self):
        """Display PDF content preview page"""
        from pages.pdf_content_preview import render_pdf_content_preview_page
        render_pdf_content_preview_page()
    
    def show_question_generation_page(self):
        """Display question generation page"""
        from pages.question_generation import render_question_generation_page
        render_question_generation_page()
    
    def show_question_management_page(self):
        """Display question management page"""
        from pages.question_review import render_question_review_page
        render_question_review_page()
    
    def show_question_edit_page(self):
        """Display question edit page"""
        from pages.question_edit import render_question_edit_page
        render_question_edit_page()
    
    def show_test_creation_page(self):
        """Display test creation page"""
        from pages.test_creation import render_test_creation_page
        render_test_creation_page()
    
    def show_test_publishing_page(self):
        """Display test publishing page"""
        from pages.test_publishing import render_test_publishing_page
        render_test_publishing_page()
    
    def show_instructor_results_page(self):
        """Display instructor results and analytics page"""
        from pages.instructor_results import render_instructor_results_page
        render_instructor_results_page()
    
    def show_available_tests_page(self):
        """Display available tests page"""
        from pages.available_tests import render_available_tests_page
        render_available_tests_page()
    
    def show_test_taking_page(self):
        """Display test taking page"""
        from pages.test_taking import render_test_taking_page
        render_test_taking_page()
    
    def show_test_results_page(self):
        """Display test results page"""
        from pages.test_results import render_test_results_page
        render_test_results_page()
    
    def show_profile_page(self):
        """Display user profile page"""
        st.header("👤 User Profile")
        
        user_info = self.session_manager.get_user_info()
        
        # Display user information
        st.subheader("📋 Profile Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("First Name", value=user_info.get('first_name', ''), disabled=True)
            st.text_input("Email", value=user_info.get('email', ''), disabled=True)
        
        with col2:
            st.text_input("Last Name", value=user_info.get('last_name', ''), disabled=True)
            st.text_input("Role", value=user_info.get('role', '').title(), disabled=True)
        
        st.divider()
        
        # Profile actions
        st.subheader("⚙️ Profile Actions")
        
        if st.button("🔄 Refresh Profile", help="Refresh profile information"):
            # Refresh user info from database
            try:
                user_id = user_info.get('user_id')
                if user_id:
                    updated_user = self.user_service.get_user_by_id(user_id)
                    if updated_user:
                        self.session_manager.update_user_info(updated_user)
                        st.success("✅ Profile refreshed successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Could not refresh profile")
                else:
                    st.error("❌ User ID not found")
            except Exception as e:
                st.error(f"❌ Error refreshing profile: {str(e)}")
    
    def show_system_status_page(self):
        """Display system status page"""
        st.header("🔧 System Status")
        
        # Service status checks
        st.subheader("📊 Service Status")
        
        # Check DynamoDB
        try:
            stats = self.user_service.get_user_statistics()
            st.success(f"✅ DynamoDB: Connected ({stats['total_users']} users)", icon="🗄️")
        except Exception as e:
            st.error(f"❌ DynamoDB: Error - {str(e)}", icon="🗄️")
        
        # Check Cognito
        try:
            # Simple test of auth service
            test_result = self.auth_service.get_user_pool_info()
            if test_result.get('success'):
                st.success("✅ AWS Cognito: Connected", icon="🔐")
            else:
                st.error("❌ AWS Cognito: Error", icon="🔐")
        except Exception as e:
            st.error(f"❌ AWS Cognito: Error - {str(e)}", icon="🔐")
        
        # Check Bedrock (placeholder)
        st.info("🤖 AWS Bedrock: Status check will be implemented", icon="🤖")
        
        st.divider()
        
        # System information
        st.subheader("ℹ️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text(f"Python Version: {sys.version.split()[0]}")
            st.text(f"Streamlit Version: {st.__version__}")
        
        with col2:
            st.text(f"Environment: Development")
            st.text(f"Region: {os.getenv('AWS_DEFAULT_REGION', 'Not Set')}")

def main():
    """Main function to run the application"""
    try:
        app = QuizGeniusApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Critical application error: {str(e)}", icon="🚨")
        st.exception(e)

if __name__ == "__main__":
    main()