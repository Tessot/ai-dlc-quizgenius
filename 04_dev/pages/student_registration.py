"""
Student Registration Page for QuizGenius MVP

This module provides a dedicated student registration page with
features optimized for student accounts and academic use.
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

def show_student_registration_page():
    """Display the student registration page"""
    
    st.set_page_config(
        page_title="Student Registration - QuizGenius",
        page_icon="👨‍🎓",
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
    st.title("👨‍🎓 Student Registration")
    st.markdown("*Join QuizGenius as a student to take AI-powered quizzes and track your learning progress*")
    st.divider()
    
    # Check if user is already logged in
    session_manager.initialize_session()
    if session_manager.is_authenticated():
        user_info = session_manager.get_user_info()
        st.success(f"✅ You are already logged in as {user_info.get('first_name', 'User')}")
        
        if st.button("🏠 Go to Dashboard"):
            st.switch_page("app.py")
        return
    
    # Registration form with student-specific enhancements
    show_enhanced_student_registration(auth_service, user_service, session_manager)
    
    # Additional information for students
    show_student_benefits()
    
    # Login option
    st.divider()
    st.markdown("### Already have an account?")
    if st.button("🔑 Login Instead", use_container_width=True):
        st.switch_page("app.py")

def show_enhanced_student_registration(auth_service: AuthService, user_service: UserService, session_manager: SessionManager):
    """Show enhanced student registration form"""
    
    st.subheader("📝 Create Your Student Account")
    
    with st.form("student_registration_form", clear_on_submit=False):
        # Personal Information Section
        st.markdown("#### 👤 Personal Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input(
                "First Name *",
                placeholder="Enter your first name",
                help="Your first name"
            )
        
        with col2:
            last_name = st.text_input(
                "Last Name *",
                placeholder="Enter your last name",
                help="Your last name"
            )
        
        # Contact Information Section
        st.markdown("#### 📧 Contact Information")
        
        email = st.text_input(
            "Email Address *",
            placeholder="Enter your email address",
            help="This will be your username for login. Use your school email if you have one."
        )
        
        # Academic Information Section (Optional)
        st.markdown("#### 🎓 Academic Information (Optional)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            school = st.text_input(
                "School/Institution",
                placeholder="e.g., Lincoln High School, State University",
                help="The school or institution you attend"
            )
        
        with col2:
            grade_level = st.selectbox(
                "Grade/Academic Level",
                options=["", "Elementary School", "Middle School", "High School", "Undergraduate", "Graduate", "Other"],
                help="Your current academic level"
            )
        
        # Subject Interests
        st.markdown("#### 📚 Learning Preferences (Optional)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            subject_interests = st.multiselect(
                "Subject Interests",
                options=[
                    "Mathematics", "Science", "English/Literature", "History", 
                    "Computer Science", "Foreign Languages", "Arts", "Social Studies",
                    "Business", "Engineering", "Medicine", "Other"
                ],
                help="Select subjects you're interested in studying"
            )
        
        with col2:
            preferred_quiz_types = st.multiselect(
                "Preferred Quiz Types",
                options=["Multiple Choice", "True/False", "Mixed Format"],
                default=["Multiple Choice", "True/False"],
                help="Types of quizzes you prefer to take"
            )
        
        # Account Security Section
        st.markdown("#### 🔒 Account Security")
        
        password = st.text_input(
            "Password *",
            type="password",
            placeholder="Create a strong password",
            help="Password must be at least 8 characters long with mixed case, numbers"
        )
        
        confirm_password = st.text_input(
            "Confirm Password *",
            type="password",
            placeholder="Confirm your password",
            help="Re-enter your password to confirm"
        )
        
        # Preferences Section
        st.markdown("#### ⚙️ Learning Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email_notifications = st.checkbox(
                "Email Notifications",
                value=True,
                help="Receive notifications about new quizzes and results"
            )
        
        with col2:
            study_reminders = st.checkbox(
                "Study Reminders",
                value=False,
                help="Receive periodic study reminders and tips"
            )
        
        performance_tracking = st.checkbox(
            "Performance Tracking",
            value=True,
            help="Track your quiz performance and learning progress over time"
        )
        
        # Age Verification (for compliance)
        st.markdown("#### 📅 Age Verification")
        
        age_verification = st.checkbox(
            "I am at least 13 years old *",
            help="You must be at least 13 years old to create an account"
        )
        
        # Parent/Guardian Contact (Optional)
        with st.expander("👨‍👩‍👧‍👦 Parent/Guardian Information (Optional - for students under 18)"):
            parent_name = st.text_input(
                "Parent/Guardian Name",
                placeholder="Enter parent or guardian name",
                help="Optional: Parent or guardian contact information"
            )
            
            parent_email = st.text_input(
                "Parent/Guardian Email",
                placeholder="Enter parent or guardian email",
                help="Optional: Parent or guardian email for important notifications"
            )
        
        # Terms and Conditions
        st.markdown("#### 📋 Terms and Conditions")
        
        accept_terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy *",
            help="You must accept the terms to create an account"
        )
        
        accept_student_terms = st.checkbox(
            "I agree to the Student Code of Conduct *",
            help="Additional terms specific to student accounts and academic integrity"
        )
        
        # Submit button
        st.markdown("---")
        register_submitted = st.form_submit_button(
            "👨‍🎓 Create Student Account", 
            use_container_width=True,
            type="primary"
        )
        
        if register_submitted:
            # Validate form
            validation_errors = validate_student_registration(
                first_name, last_name, email, password, confirm_password,
                age_verification, accept_terms, accept_student_terms
            )
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"❌ {error}", icon="⚠️")
            else:
                # Process registration
                handle_student_registration(
                    first_name, last_name, email, password,
                    school, grade_level, subject_interests, preferred_quiz_types,
                    email_notifications, study_reminders, performance_tracking,
                    parent_name, parent_email,
                    auth_service, user_service, session_manager
                )

def validate_student_registration(first_name: str, last_name: str, email: str,
                                password: str, confirm_password: str,
                                age_verification: bool, accept_terms: bool, 
                                accept_student_terms: bool) -> list:
    """Validate student registration form"""
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
    
    # Age verification
    if not age_verification:
        errors.append("You must be at least 13 years old to create an account")
    
    # Terms validation
    if not accept_terms:
        errors.append("You must accept the Terms of Service and Privacy Policy")
    
    if not accept_student_terms:
        errors.append("You must accept the Student Code of Conduct")
    
    return errors

def handle_student_registration(first_name: str, last_name: str, email: str, password: str,
                              school: str, grade_level: str, subject_interests: list,
                              preferred_quiz_types: list, email_notifications: bool,
                              study_reminders: bool, performance_tracking: bool,
                              parent_name: str, parent_email: str,
                              auth_service: AuthService, user_service: UserService, 
                              session_manager: SessionManager):
    """Handle student registration process"""
    
    try:
        with st.spinner("🔄 Creating your student account..."):
            # Register with Cognito
            auth_result = auth_service.register_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role="student"
            )
            
            if auth_result['success']:
                # Create enhanced user profile in DynamoDB
                user_data = {
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'student',
                    'cognito_username': auth_result.get('username', email),
                    'school': school.strip() if school else None,
                    'grade_level': grade_level if grade_level else None,
                    'subject_interests': subject_interests if subject_interests else [],
                    'preferred_quiz_types': preferred_quiz_types if preferred_quiz_types else [],
                    'preferences': {
                        'email_notifications': email_notifications,
                        'study_reminders': study_reminders,
                        'performance_tracking': performance_tracking
                    },
                    'parent_contact': {
                        'name': parent_name.strip() if parent_name else None,
                        'email': parent_email.strip() if parent_email else None
                    } if parent_name or parent_email else None,
                    'student_status': 'active'
                }
                
                user_result = user_service.create_user(user_data)
                
                if user_result['success']:
                    # Success message
                    st.success("✅ Student account created successfully!", icon="🎉")
                    
                    # Show next steps
                    st.info(
                        "📧 **Next Steps:**\n"
                        "1. Check your email to verify your account\n"
                        "2. Click the verification link in the email\n"
                        "3. Return here to log in and start taking quizzes!",
                        icon="📬"
                    )
                    
                    # Show verification reminder
                    st.warning(
                        "⚠️ **Important:** You must verify your email address before you can log in.",
                        icon="📧"
                    )
                    
                    # Show welcome message
                    st.markdown(
                        f"### 🎓 Welcome to QuizGenius, {first_name}!\n"
                        "You're now ready to start your learning journey with AI-powered quizzes."
                    )
                    
                    # Celebration
                    st.balloons()
                    
                    # Auto-redirect option
                    if st.button("🔑 Go to Login Page", use_container_width=True):
                        st.switch_page("app.py")
                        
                else:
                    st.error(f"❌ Failed to create student profile: {user_result.get('message', 'Unknown error')}")
            else:
                st.error(f"❌ Registration failed: {auth_result.get('message', 'Unknown error')}")
                
    except AuthenticationError as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            st.error("❌ An account with this email already exists. Please try logging in instead.")
            if st.button("🔑 Go to Login"):
                st.switch_page("app.py")
        elif "Password does not meet requirements" in error_msg:
            st.error("❌ Password does not meet requirements. Please use a stronger password.")
        elif "Invalid registration parameters" in error_msg:
            st.error("❌ Invalid registration information. Please check your details.")
        else:
            st.error(f"❌ Registration error: {error_msg}")
    except UserServiceError as e:
        st.error(f"❌ User profile creation error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Unexpected registration error: {str(e)}")
        st.exception(e)

def show_student_benefits():
    """Show benefits of student account"""
    
    st.markdown("---")
    st.subheader("🌟 Why Choose QuizGenius for Students?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🎯 Personalized Learning**
        - Take quizzes tailored to your subjects
        - Track your progress over time
        - Get insights into your strengths and areas for improvement
        """)
    
    with col2:
        st.markdown("""
        **📊 Performance Analytics**
        - Detailed results and feedback
        - Progress tracking across different topics
        - Study recommendations based on your performance
        """)
    
    with col3:
        st.markdown("""
        **⚡ Easy to Use**
        - Simple, student-friendly interface
        - Take quizzes anytime, anywhere
        - Immediate results and feedback
        """)
    
    # Feature highlights
    st.markdown("### 🚀 Key Features for Students")
    
    features = [
        "📝 **Take Quizzes**: Access quizzes created by your instructors",
        "📊 **Track Progress**: Monitor your learning progress and performance",
        "🎯 **Personalized Experience**: Customize your learning preferences",
        "📈 **Detailed Results**: Get comprehensive feedback on your performance",
        "🏆 **Achievement Tracking**: See your improvements over time",
        "📱 **Mobile Friendly**: Study and take quizzes on any device"
    ]
    
    for feature in features:
        st.markdown(f"- {feature}")
    
    # Study tips
    st.markdown("### 💡 Study Tips")
    
    with st.expander("📚 How to Get the Most Out of QuizGenius"):
        st.markdown("""
        **Before Taking a Quiz:**
        - Review your course materials
        - Set aside dedicated time without distractions
        - Make sure you have a stable internet connection
        
        **During the Quiz:**
        - Read each question carefully
        - Don't rush - take your time to think
        - Use the navigation to review your answers
        
        **After the Quiz:**
        - Review your results and feedback
        - Note areas where you can improve
        - Use the insights to guide your future study sessions
        """)

if __name__ == "__main__":
    show_student_registration_page()