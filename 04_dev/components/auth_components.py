"""
Authentication Components for QuizGenius MVP

This module provides Streamlit components for user authentication,
including login and registration forms with proper validation and error handling.
"""

import streamlit as st
from typing import Dict, Any, Optional
from services.auth_service import AuthService, AuthenticationError
from services.user_service import UserService, UserServiceError
from utils.session_manager import SessionManager

class AuthComponents:
    """Authentication UI components for Streamlit"""
    
    def __init__(self):
        """Initialize authentication components"""
        pass
    
    def show_login_form(self, auth_service: AuthService, user_service: UserService, session_manager: SessionManager):
        """
        Display login form
        
        Args:
            auth_service: Authentication service instance
            user_service: User service instance
            session_manager: Session manager instance
        """
        st.subheader("🔑 Login to Your Account")
        
        with st.form("login_form", clear_on_submit=False):
            # Login form fields
            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
                help="The email address you used to register"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Your account password"
            )
            
            # Remember me option
            remember_me = st.checkbox("Remember me", help="Keep me logged in")
            
            # Submit button
            login_submitted = st.form_submit_button("🔑 Login", use_container_width=True)
            
            if login_submitted:
                if not email or not password:
                    st.error("❌ Please enter both email and password", icon="⚠️")
                else:
                    self._handle_login(email, password, remember_me, auth_service, user_service, session_manager)
        
        # Additional options
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Forgot Password?", help="Reset your password"):
                st.info("Password reset functionality will be implemented in a future update")
        
        with col2:
            if st.button("❓ Need Help?", help="Get help with login"):
                st.info("Contact support for assistance with login issues")
    
    def show_registration_form(self, auth_service: AuthService, user_service: UserService, session_manager: SessionManager):
        """
        Display registration form
        
        Args:
            auth_service: Authentication service instance
            user_service: User service instance
            session_manager: Session manager instance
        """
        st.subheader("📝 Create New Account")
        
        with st.form("registration_form", clear_on_submit=False):
            # Personal information
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
            
            # Account information
            email = st.text_input(
                "Email Address *",
                placeholder="Enter your email address",
                help="This will be your username for login"
            )
            
            # Role selection
            role = st.selectbox(
                "Account Type *",
                options=["", "instructor", "student"],
                format_func=lambda x: {
                    "": "Select your role...",
                    "instructor": "👨‍🏫 Instructor (Create and manage tests)",
                    "student": "👨‍🎓 Student (Take tests and view results)"
                }.get(x, x),
                help="Choose whether you are an instructor or student"
            )
            
            # Password fields
            password = st.text_input(
                "Password *",
                type="password",
                placeholder="Create a strong password",
                help="Password must be at least 8 characters long"
            )
            
            confirm_password = st.text_input(
                "Confirm Password *",
                type="password",
                placeholder="Confirm your password",
                help="Re-enter your password to confirm"
            )
            
            # Terms and conditions
            accept_terms = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy *",
                help="You must accept the terms to create an account"
            )
            
            # Submit button
            register_submitted = st.form_submit_button("📝 Create Account", use_container_width=True)
            
            if register_submitted:
                validation_errors = self._validate_registration_form(
                    first_name, last_name, email, role, password, confirm_password, accept_terms
                )
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(f"❌ {error}", icon="⚠️")
                else:
                    self._handle_registration(
                        first_name, last_name, email, role, password,
                        auth_service, user_service, session_manager
                    )
        
        # Additional information
        st.divider()
        st.info("📋 **Note:** All fields marked with * are required")
    
    def _validate_registration_form(self, first_name: str, last_name: str, email: str, 
                                  role: str, password: str, confirm_password: str, 
                                  accept_terms: bool) -> list:
        """
        Validate registration form data
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Required field validation
        if not first_name.strip():
            errors.append("First name is required")
        
        if not last_name.strip():
            errors.append("Last name is required")
        
        if not email.strip():
            errors.append("Email address is required")
        elif "@" not in email or "." not in email:
            errors.append("Please enter a valid email address")
        
        if not role:
            errors.append("Please select your account type")
        
        if not password:
            errors.append("Password is required")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not confirm_password:
            errors.append("Please confirm your password")
        elif password != confirm_password:
            errors.append("Passwords do not match")
        
        if not accept_terms:
            errors.append("You must accept the Terms of Service and Privacy Policy")
        
        return errors
    
    def _handle_login(self, email: str, password: str, remember_me: bool,
                     auth_service: AuthService, user_service: UserService, 
                     session_manager: SessionManager):
        """
        Handle user login process
        
        Args:
            email: User email
            password: User password
            remember_me: Whether to remember the user
            auth_service: Authentication service instance
            user_service: User service instance
            session_manager: Session manager instance
        """
        try:
            with st.spinner("🔄 Logging in..."):
                # Authenticate with Cognito
                auth_result = auth_service.authenticate_user(email, password)
                
                if auth_result['success']:
                    # Get user information from DynamoDB
                    user_data = user_service.get_user_by_email(email)
                    
                    if user_data:
                        # Update last login
                        user_service.update_last_login(user_data['user_id'])
                        
                        # Set up session
                        session_manager.login_user(user_data, auth_result, remember_me)
                        
                        # Role-based success message and redirection
                        role = user_data.get('role', 'user')
                        if role == 'instructor':
                            st.success(f"✅ Welcome back, {user_data['first_name']}! Redirecting to Instructor Dashboard...", icon="👨‍🏫")
                        elif role == 'student':
                            st.success(f"✅ Welcome back, {user_data['first_name']}! Redirecting to Student Dashboard...", icon="👨‍🎓")
                        else:
                            st.success(f"✅ Welcome back, {user_data['first_name']}!", icon="🎉")
                        
                        st.balloons()
                        
                        # Rerun to refresh the app and trigger role-based redirection
                        st.rerun()
                    else:
                        st.error("❌ User profile not found. Please contact support.", icon="⚠️")
                else:
                    st.error(f"❌ Login failed: {auth_result.get('message', 'Unknown error')}", icon="🔒")
                    
        except AuthenticationError as e:
            error_msg = str(e)
            if "NotAuthorizedException" in error_msg:
                st.error("❌ Invalid email or password. Please try again.", icon="🔒")
            elif "UserNotConfirmedException" in error_msg:
                st.error("❌ Please verify your email address before logging in.", icon="📧")
            elif "UserNotFoundException" in error_msg:
                st.error("❌ Account not found. Please check your email or register.", icon="👤")
            else:
                st.error(f"❌ Login error: {error_msg}", icon="⚠️")
        except Exception as e:
            st.error(f"❌ Unexpected login error: {str(e)}", icon="🚨")
    
    def _handle_registration(self, first_name: str, last_name: str, email: str, 
                           role: str, password: str, auth_service: AuthService, 
                           user_service: UserService, session_manager: SessionManager):
        """
        Handle user registration process
        
        Args:
            first_name: User's first name
            last_name: User's last name
            email: User's email
            role: User's role (instructor/student)
            password: User's password
            auth_service: Authentication service instance
            user_service: User service instance
            session_manager: Session manager instance
        """
        try:
            with st.spinner("🔄 Creating your account..."):
                # Register with Cognito
                auth_result = auth_service.register_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role
                )
                
                if auth_result['success']:
                    # Create user profile in DynamoDB
                    user_data = {
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': role,
                        'cognito_username': auth_result.get('username', email)
                    }
                    
                    user_result = user_service.create_user(user_data)
                    
                    if user_result['success']:
                        st.success("✅ Account created successfully!", icon="🎉")
                        st.info("📧 Please check your email to verify your account before logging in.", icon="📬")
                        
                        # Show confirmation message
                        st.balloons()
                        
                        # Clear the form by rerunning
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create user profile: {user_result.get('message', 'Unknown error')}", icon="⚠️")
                else:
                    st.error(f"❌ Registration failed: {auth_result.get('message', 'Unknown error')}", icon="📝")
                    
        except AuthenticationError as e:
            error_msg = str(e)
            if "UsernameExistsException" in error_msg:
                st.error("❌ An account with this email already exists. Please try logging in.", icon="👤")
            elif "InvalidPasswordException" in error_msg:
                st.error("❌ Password does not meet requirements. Please use a stronger password.", icon="🔒")
            elif "InvalidParameterException" in error_msg:
                st.error("❌ Invalid registration information. Please check your details.", icon="📝")
            else:
                st.error(f"❌ Registration error: {error_msg}", icon="⚠️")
        except UserServiceError as e:
            st.error(f"❌ User profile creation error: {str(e)}", icon="👤")
        except Exception as e:
            st.error(f"❌ Unexpected registration error: {str(e)}", icon="🚨")

    def show_email_verification_form(self, auth_service: AuthService):
        """
        Display email verification form
        
        Args:
            auth_service: Authentication service instance
        """
        st.subheader("📧 Verify Your Email")
        st.info("Please enter the verification code sent to your email address.")
        
        with st.form("verification_form"):
            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
                help="The email address you registered with"
            )
            
            verification_code = st.text_input(
                "Verification Code",
                placeholder="Enter the 6-digit code",
                help="Check your email for the verification code"
            )
            
            verify_submitted = st.form_submit_button("✅ Verify Email", use_container_width=True)
            
            if verify_submitted:
                if not email or not verification_code:
                    st.error("❌ Please enter both email and verification code", icon="⚠️")
                else:
                    self._handle_email_verification(email, verification_code, auth_service)
        
        # Resend code option
        st.divider()
        
        if st.button("🔄 Resend Verification Code", help="Send a new verification code"):
            st.info("Resend verification functionality will be implemented in a future update")
    
    def _handle_email_verification(self, email: str, verification_code: str, auth_service: AuthService):
        """
        Handle email verification process
        
        Args:
            email: User's email address
            verification_code: Verification code from email
            auth_service: Authentication service instance
        """
        try:
            with st.spinner("🔄 Verifying email..."):
                result = auth_service.confirm_user_registration(email, verification_code)
                
                if result['success']:
                    st.success("✅ Email verified successfully! You can now log in.", icon="🎉")
                    st.balloons()
                else:
                    st.error(f"❌ Verification failed: {result.get('message', 'Unknown error')}", icon="📧")
                    
        except AuthenticationError as e:
            error_msg = str(e)
            if "CodeMismatchException" in error_msg:
                st.error("❌ Invalid verification code. Please check and try again.", icon="🔢")
            elif "ExpiredCodeException" in error_msg:
                st.error("❌ Verification code has expired. Please request a new one.", icon="⏰")
            else:
                st.error(f"❌ Verification error: {error_msg}", icon="⚠️")
        except Exception as e:
            st.error(f"❌ Unexpected verification error: {str(e)}", icon="🚨")