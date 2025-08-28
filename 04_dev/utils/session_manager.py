"""
Session Manager for QuizGenius MVP

This module provides session management functionality for the Streamlit application,
including user authentication state, session persistence, and user data management.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

class SessionManager:
    """Manage user sessions and authentication state"""
    
    def __init__(self):
        """Initialize session manager"""
        self.session_keys = {
            'authenticated': 'user_authenticated',
            'user_info': 'user_info',
            'auth_tokens': 'auth_tokens',
            'login_time': 'login_time',
            'remember_me': 'remember_me',
            'session_id': 'session_id'
        }
    
    def initialize_session(self):
        """Initialize session state variables"""
        # Initialize authentication state
        if self.session_keys['authenticated'] not in st.session_state:
            st.session_state[self.session_keys['authenticated']] = False
        
        # Initialize user info
        if self.session_keys['user_info'] not in st.session_state:
            st.session_state[self.session_keys['user_info']] = {}
        
        # Initialize auth tokens
        if self.session_keys['auth_tokens'] not in st.session_state:
            st.session_state[self.session_keys['auth_tokens']] = {}
        
        # Initialize login time
        if self.session_keys['login_time'] not in st.session_state:
            st.session_state[self.session_keys['login_time']] = None
        
        # Initialize remember me
        if self.session_keys['remember_me'] not in st.session_state:
            st.session_state[self.session_keys['remember_me']] = False
        
        # Initialize session ID
        if self.session_keys['session_id'] not in st.session_state:
            st.session_state[self.session_keys['session_id']] = self._generate_session_id()
        
        # Initialize page state
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'Dashboard'
        
        # Initialize error messages
        if 'error_messages' not in st.session_state:
            st.session_state.error_messages = []
        
        # Initialize success messages
        if 'success_messages' not in st.session_state:
            st.session_state.success_messages = []
    
    def login_user(self, user_data: Dict[str, Any], auth_result: Dict[str, Any], remember_me: bool = False):
        """
        Log in a user and set up session
        
        Args:
            user_data: User information from database
            auth_result: Authentication result from Cognito
            remember_me: Whether to remember the user
        """
        # Set authentication state
        st.session_state[self.session_keys['authenticated']] = True
        
        # Store user information
        st.session_state[self.session_keys['user_info']] = {
            'user_id': user_data.get('user_id'),
            'email': user_data.get('email'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'role': user_data.get('role'),
            'status': user_data.get('status'),
            'created_date': user_data.get('created_date'),
            'last_login': user_data.get('last_login'),
            'login_count': user_data.get('login_count', 0)
        }
        
        # Store authentication tokens
        st.session_state[self.session_keys['auth_tokens']] = {
            'access_token': auth_result.get('access_token'),
            'id_token': auth_result.get('id_token'),
            'refresh_token': auth_result.get('refresh_token'),
            'token_type': auth_result.get('token_type', 'Bearer')
        }
        
        # Set login time
        st.session_state[self.session_keys['login_time']] = datetime.now().isoformat()
        
        # Set remember me preference
        st.session_state[self.session_keys['remember_me']] = remember_me
        
        # Reset page to dashboard
        st.session_state.selected_page = 'Dashboard'
        
        # Clear any error messages
        st.session_state.error_messages = []
        
        # Add success message
        st.session_state.success_messages = [f"Welcome back, {user_data.get('first_name', 'User')}!"]
    
    def logout(self):
        """Log out the current user and clear session"""
        # Clear authentication state
        st.session_state[self.session_keys['authenticated']] = False
        
        # Clear user information
        st.session_state[self.session_keys['user_info']] = {}
        
        # Clear authentication tokens
        st.session_state[self.session_keys['auth_tokens']] = {}
        
        # Clear login time
        st.session_state[self.session_keys['login_time']] = None
        
        # Clear remember me
        st.session_state[self.session_keys['remember_me']] = False
        
        # Reset page selection
        st.session_state.selected_page = 'Dashboard'
        
        # Clear messages
        st.session_state.error_messages = []
        st.session_state.success_messages = ["You have been logged out successfully."]
        
        # Generate new session ID
        st.session_state[self.session_keys['session_id']] = self._generate_session_id()
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated
        
        Returns:
            True if user is authenticated, False otherwise
        """
        authenticated = st.session_state.get(self.session_keys['authenticated'], False)
        
        if authenticated:
            # Check if session has expired
            if self._is_session_expired():
                self.logout()
                return False
        
        return authenticated
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information
        
        Returns:
            User information dictionary
        """
        return st.session_state.get(self.session_keys['user_info'], {})
    
    def update_user_info(self, updated_info: Dict[str, Any]):
        """
        Update user information in session
        
        Args:
            updated_info: Updated user information
        """
        current_info = self.get_user_info()
        current_info.update(updated_info)
        st.session_state[self.session_keys['user_info']] = current_info
    
    def get_auth_tokens(self) -> Dict[str, Any]:
        """
        Get authentication tokens
        
        Returns:
            Authentication tokens dictionary
        """
        return st.session_state.get(self.session_keys['auth_tokens'], {})
    
    def get_user_role(self) -> str:
        """
        Get current user's role
        
        Returns:
            User role (instructor/student) or empty string
        """
        user_info = self.get_user_info()
        return user_info.get('role', '')
    
    def get_user_id(self) -> Optional[str]:
        """
        Get current user's ID
        
        Returns:
            User ID or None
        """
        user_info = self.get_user_info()
        return user_info.get('user_id')
    
    def get_session_duration(self) -> Optional[timedelta]:
        """
        Get current session duration
        
        Returns:
            Session duration or None if not logged in
        """
        login_time_str = st.session_state.get(self.session_keys['login_time'])
        
        if login_time_str:
            try:
                login_time = datetime.fromisoformat(login_time_str)
                return datetime.now() - login_time
            except ValueError:
                return None
        
        return None
    
    def _is_session_expired(self) -> bool:
        """
        Check if current session has expired
        
        Returns:
            True if session has expired, False otherwise
        """
        login_time_str = st.session_state.get(self.session_keys['login_time'])
        remember_me = st.session_state.get(self.session_keys['remember_me'], False)
        
        if not login_time_str:
            return True
        
        try:
            login_time = datetime.fromisoformat(login_time_str)
            current_time = datetime.now()
            
            # Set session timeout based on remember me preference
            if remember_me:
                timeout_hours = 24 * 7  # 7 days
            else:
                timeout_hours = 8  # 8 hours
            
            timeout_duration = timedelta(hours=timeout_hours)
            
            return (current_time - login_time) > timeout_duration
            
        except ValueError:
            return True
    
    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID
        
        Returns:
            Unique session ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get comprehensive session information
        
        Returns:
            Session information dictionary
        """
        return {
            'session_id': st.session_state.get(self.session_keys['session_id']),
            'authenticated': self.is_authenticated(),
            'user_info': self.get_user_info(),
            'login_time': st.session_state.get(self.session_keys['login_time']),
            'session_duration': str(self.get_session_duration()) if self.get_session_duration() else None,
            'remember_me': st.session_state.get(self.session_keys['remember_me'], False),
            'current_page': st.session_state.get('selected_page', 'Dashboard')
        }
    
    def add_error_message(self, message: str):
        """
        Add an error message to display
        
        Args:
            message: Error message to add
        """
        if 'error_messages' not in st.session_state:
            st.session_state.error_messages = []
        
        st.session_state.error_messages.append(message)
    
    def add_success_message(self, message: str):
        """
        Add a success message to display
        
        Args:
            message: Success message to add
        """
        if 'success_messages' not in st.session_state:
            st.session_state.success_messages = []
        
        st.session_state.success_messages.append(message)
    
    def get_and_clear_messages(self) -> Dict[str, list]:
        """
        Get and clear all pending messages
        
        Returns:
            Dictionary with error and success messages
        """
        messages = {
            'errors': st.session_state.get('error_messages', []),
            'success': st.session_state.get('success_messages', [])
        }
        
        # Clear messages after retrieving them
        st.session_state.error_messages = []
        st.session_state.success_messages = []
        
        return messages
    
    def clear_session_data(self):
        """Clear all session data (for testing or reset purposes)"""
        for key in self.session_keys.values():
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear other session variables
        session_vars_to_clear = [
            'selected_page', 'error_messages', 'success_messages'
        ]
        
        for var in session_vars_to_clear:
            if var in st.session_state:
                del st.session_state[var]
    
    def export_session_data(self) -> str:
        """
        Export session data as JSON (for debugging)
        
        Returns:
            JSON string of session data
        """
        session_data = {}
        
        for key, session_key in self.session_keys.items():
            session_data[key] = st.session_state.get(session_key)
        
        # Add other relevant session data
        session_data['selected_page'] = st.session_state.get('selected_page')
        session_data['error_messages'] = st.session_state.get('error_messages', [])
        session_data['success_messages'] = st.session_state.get('success_messages', [])
        
        return json.dumps(session_data, indent=2, default=str)