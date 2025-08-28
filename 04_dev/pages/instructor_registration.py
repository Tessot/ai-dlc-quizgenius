"""
Instructor Registration Page for QuizGenius MVP

This module provides a dedicated instructor registration page with
enhanced features specific to instructor accounts.
"""

import streamlit as st
import sys
import os

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService, AuthenticationError
from services.user_service import UserService, UserServiceError
from components.auth_components import AuthComponents
from utils.session_manager import SessionManager
from utils.config import load_environment_config

def show_instructor_registration_page():
    """Display the instructor registration page"""
    
    st.set_page_config(
        page_title="Instructor Registration - QuizGenius",
        page_icon="👨‍🏫",
        layout="wide"
    )
    
    # Load configuration and initialize services
    try:
        load_environment_config()
        auth_service = AuthService()
        user_service = UserService()
        session_manager = SessionManager()
        auth_components = AuthComponents()
    except Exception as e:
        st.error(f"❌ Service initialization error: {str(e)}")
        st.stop()
    
    # Header
    st.title("👨‍🏫 Instructor Registration")
    st.markdown("*Join QuizGenius as an instructor to create AI-powered quizzes from your PDF materials*")
    st.divider()
    
    # Check if user is already logged in
    session_manager.initialize_session()
    if session_manager.is_authenticated():
        user_info = session_manager.get_user_info()
        st.success(f"✅ You are already logged in as {user_info.get('first_name', 'User')}")
        
        if st.button("🏠 Go to Dashboard"):
            st.switch_page("app.py")
        return
    
    # Registration form with instructor-specific enhancements
    show_enhanced_instructor_registration(auth_service, user_service, session_manager)
    
    # Additional information for instructors
    show_instructor_benefits()
    
    # Login option
    st.divider()
    st.markdown("### Already have an account?")
    if st.button("🔑 Login Instead", use_container_width=True):
        st.switch_page("app.py")

def show_enhanced_instructor_registration(auth_service: AuthService, user_service: UserService, session_manager: SessionManager):
    """Show enhanced instructor registration form"""
    
    st.subheader("📝 Create Your Instructor Account")
    
    with st.form("instructor_registration_form", clear_on_submit=False):
        # Personal Information Section
        st.markdown("#### 👤 Personal Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input(
                "First Name *",
                placeholder="Enter your first name",
                help="Your first name as you'd like it to appear to students"
            )
        
        with col2:
            last_name = st.text_input(
                "Last Name *",
                placeholder="Enter your last name",
                help="Your last name as you'd like it to appear to students"
            )
        
        # Contact Information Section
        st.markdown("#### 📧 Contact Information")
        
        email = st.text_input(
            "Email Address *",
            placeholder="Enter your professional email address",
            help="This will be your username for login. Use your institutional email if available."
        )
        
        # Institution Information (Optional)
        st.markdown("#### 🏫 Institution Information (Optional)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            institution = st.text_input(
                "Institution/Organization",
                placeholder="e.g., University of Example",
                help="The institution or organization you're affiliated with"
            )
        
        with col2:
            department = st.text_input(
                "Department/Subject Area",
                placeholder="e.g., Computer Science, Mathematics",
                help="Your department or primary subject area"
            )
        
        # Account Security Section
        st.markdown("#### 🔒 Account Security")
        
        password = st.text_input(
            "Password *",
            type="password",
            placeholder="Create a strong password",
            help="Password must be at least 8 characters long with mixed case, numbers, and symbols"
        )
        
        confirm_password = st.text_input(
            "Confirm Password *",
            type="password",
            placeholder="Confirm your password",
            help="Re-enter your password to confirm"
        )
        
        # Preferences Section
        st.markdown("#### ⚙️ Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email_notifications = st.checkbox(
                "Email Notifications",
                value=True,
                help="Receive notifications about student test completions and system updates"
            )
        
        with col2:
            newsletter = st.checkbox(
                "Educational Newsletter",
                value=False,
                help="Receive tips and best practices for online assessment"
            )
        
        # Terms and Conditions
        st.markdown("#### 📋 Terms and Conditions")
        
        accept_terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy *",
            help="You must accept the terms to create an account"
        )
        
        accept_instructor_terms = st.checkbox(
            "I agree to the Instructor Code of Conduct *",
            help="Additional terms specific to instructor accounts"
        )
        
        # Submit button
        st.markdown("---")
        register_submitted = st.form_submit_button(
            "👨‍🏫 Create Instructor Account", 
            use_container_width=True,
            type="primary"
        )
        
        if register_submitted:
            # Validate form
            validation_errors = validate_instructor_registration(
                first_name, last_name, email, password, confirm_password,
                accept_terms, accept_instructor_terms
            )
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"❌ {error}", icon="⚠️")
            else:
                # Process registration
                handle_instructor_registration(
                    first_name, last_name, email, password,
                    institution, department, email_notifications, newsletter,
                    auth_service, user_service, session_manager
                )

def validate_instructor_registration(first_name: str, last_name: str, email: str,
                                   password: str, confirm_password: str,
                                   accept_terms: bool, accept_instructor_terms: bool) -> list:
    """Validate instructor registration form"""
    errors = []
    
    # Required field validation
    if not first_name.strip():
        errors.append("First name is required")
    elif len(first_name.strip()) < 2:
        errors.append("First name must be at least 2 characters long")
    
    if not last_name.strip():
        errors.append("Last name is required")
    elif len(last_name.strip()) < 2:
        errors.append("Last name must be at least 2 characters long")
    
    if not email.strip():
        errors.append("Email address is required")
    elif "@" not in email or "." not in email:
        errors.append("Please enter a valid email address")
    elif len(email) > 100:
        errors.append("Email address is too long")
    
    # Password validation
    if not password:
        errors.append("Password is required")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    elif not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    elif not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    elif not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if not confirm_password:
        errors.append("Please confirm your password")
    elif password != confirm_password:
        errors.append("Passwords do not match")
    
    # Terms validation
    if not accept_terms:
        errors.append("You must accept the Terms of Service and Privacy Policy")
    
    if not accept_instructor_terms:
        errors.append("You must accept the Instructor Code of Conduct")
    
    return errors

def handle_instructor_registration(first_name: str, last_name: str, email: str, password: str,
                                 institution: str, department: str, email_notifications: bool,
                                 newsletter: bool, auth_service: AuthService,
                                 user_service: UserService, session_manager: SessionManager):
    """Handle instructor registration process"""
    
    try:
        with st.spinner("🔄 Creating your instructor account..."):
            # Register with Cognito
            auth_result = auth_service.register_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role="instructor"
            )
            
            if auth_result['success']:
                # Create enhanced user profile in DynamoDB
                user_data = {
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'instructor',
                    'cognito_username': auth_result.get('username', email),
                    'institution': institution.strip() if institution else None,
                    'department': department.strip() if department else None,
                    'preferences': {
                        'email_notifications': email_notifications,
                        'newsletter': newsletter
                    },
                    'instructor_status': 'pending_verification'  # Can be used for approval workflow
                }
                
                user_result = user_service.create_user(user_data)
                
                if user_result['success']:
                    # Success message
                    st.success("✅ Instructor account created successfully!", icon="🎉")
                    
                    # Show next steps
                    st.info(
                        "📧 **Next Steps:**\n"
                        "1. Check your email to verify your account\n"
                        "2. Click the verification link in the email\n"
                        "3. Return here to log in and start creating quizzes!",
                        icon="📬"
                    )
                    
                    # Show verification reminder
                    st.warning(
                        "⚠️ **Important:** You must verify your email address before you can log in.",
                        icon="📧"
                    )
                    
                    # Celebration
                    st.balloons()
                    
                    # Auto-redirect option
                    if st.button("🔑 Go to Login Page", use_container_width=True):
                        st.switch_page("app.py")
                        
                else:
                    st.error(f"❌ Failed to create instructor profile: {user_result.get('message', 'Unknown error')}")
            else:
                st.error(f"❌ Registration failed: {auth_result.get('message', 'Unknown error')}")
                
    except AuthenticationError as e:
        error_msg = str(e)
        if "UsernameExistsException" in error_msg:
            st.error("❌ An account with this email already exists. Please try logging in instead.")
            if st.button("🔑 Go to Login"):
                st.switch_page("app.py")
        elif "InvalidPasswordException" in error_msg:
            st.error("❌ Password does not meet AWS Cognito requirements. Please use a stronger password.")
        elif "InvalidParameterException" in error_msg:
            st.error("❌ Invalid registration information. Please check your details.")
        else:
            st.error(f"❌ Registration error: {error_msg}")
    except UserServiceError as e:
        st.error(f"❌ User profile creation error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Unexpected registration error: {str(e)}")
        st.exception(e)

def show_instructor_benefits():
    """Show benefits of instructor account"""
    
    st.markdown("---")
    st.subheader("🌟 Why Choose QuizGenius for Instructors?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🤖 AI-Powered Question Generation**
        - Automatically generate multiple choice and true/false questions
        - Extract key concepts from your PDF materials
        - Save hours of manual question writing
        """)
    
    with col2:
        st.markdown("""
        **📊 Comprehensive Analytics**
        - Track student performance and progress
        - Identify knowledge gaps and learning patterns
        - Export results for gradebook integration
        """)
    
    with col3:
        st.markdown("""
        **⚡ Easy to Use**
        - Simple PDF upload process
        - Intuitive question review and editing
        - One-click test publishing
        """)
    
    # Feature highlights
    st.markdown("### 🚀 Key Features")
    
    features = [
        "📄 **PDF Processing**: Upload lecture notes, textbooks, or any educational PDF",
        "❓ **Smart Questions**: AI generates relevant questions from your content",
        "✏️ **Easy Editing**: Review and modify questions before publishing",
        "📝 **Test Creation**: Combine questions into comprehensive tests",
        "👥 **Student Management**: Track student progress and performance",
        "📈 **Analytics Dashboard**: Detailed insights into test results"
    ]
    
    for feature in features:
        st.markdown(f"- {feature}")

if __name__ == "__main__":
    show_instructor_registration_page()