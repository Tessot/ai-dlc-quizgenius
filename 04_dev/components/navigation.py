"""
Navigation Components for QuizGenius MVP

This module provides navigation components for the Streamlit application,
including sidebar navigation and page routing based on user roles.
"""

import streamlit as st
from typing import Dict, List, Optional

class NavigationManager:
    """Navigation manager for the Streamlit application"""
    
    def __init__(self):
        """Initialize navigation manager"""
        self.instructor_pages = [
            {"name": "Dashboard", "icon": "📊", "description": "Overview and quick actions"},
            {"name": "PDF Upload", "icon": "📤", "description": "Upload PDF documents"},
            {"name": "Content Preview", "icon": "👀", "description": "Preview extracted PDF content"},
            {"name": "Question Generation", "icon": "🤖", "description": "Generate questions from PDF content"},
            {"name": "Question Management", "icon": "❓", "description": "Review and edit questions"},
            {"name": "Test Creation", "icon": "📝", "description": "Create tests from questions"},
            {"name": "Test Publishing", "icon": "🚀", "description": "Publish tests to students"},
            {"name": "Results & Analytics", "icon": "📈", "description": "View test results and analytics"},
            {"name": "Profile", "icon": "👤", "description": "Manage your profile"},
            {"name": "System Status", "icon": "🔧", "description": "Check system status"}
        ]
        
        self.student_pages = [
            {"name": "Dashboard", "icon": "📊", "description": "Overview and quick actions"},
            {"name": "Available Tests", "icon": "📝", "description": "Browse and take tests"},
            {"name": "Test Taking", "icon": "✏️", "description": "Take an active test"},
            {"name": "Test Results", "icon": "📈", "description": "View your test results"},
            {"name": "Profile", "icon": "👤", "description": "Manage your profile"},
            {"name": "System Status", "icon": "🔧", "description": "Check system status"}
        ]
    
    def show_sidebar(self, user_role: str) -> str:
        """
        Display navigation sidebar
        
        Args:
            user_role: Current user's role (instructor/student)
            
        Returns:
            Selected page name
        """
        with st.sidebar:
            st.title("🧠 QuizGenius")
            st.markdown(f"**{user_role.title()} Portal**")
            st.divider()
            
            # Get pages based on user role
            pages = self._get_pages_for_role(user_role)
            
            # Create navigation menu
            selected_page = self._create_navigation_menu(pages)
            
            st.divider()
            
            # Show user info and actions
            self._show_sidebar_footer(user_role)
            
            return selected_page
    
    def _get_pages_for_role(self, user_role: str) -> List[Dict]:
        """
        Get available pages for user role
        
        Args:
            user_role: User's role
            
        Returns:
            List of available pages
        """
        if user_role == "instructor":
            return self.instructor_pages
        elif user_role == "student":
            return self.student_pages
        else:
            return [{"name": "Dashboard", "icon": "📊", "description": "Dashboard"}]
    
    def _create_navigation_menu(self, pages: List[Dict]) -> str:
        """
        Create navigation menu from pages
        
        Args:
            pages: List of page configurations
            
        Returns:
            Selected page name
        """
        # Initialize session state for selected page
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = pages[0]['name']
        
        st.subheader("📋 Navigation")
        
        # Create radio buttons for navigation
        page_options = [f"{page['icon']} {page['name']}" for page in pages]
        page_names = [page['name'] for page in pages]
        
        # Find current selection index
        try:
            current_index = page_names.index(st.session_state.selected_page)
        except ValueError:
            current_index = 0
            st.session_state.selected_page = page_names[0]
        
        # Show navigation options
        selected_option = st.radio(
            "Select a page:",
            options=page_options,
            index=current_index,
            label_visibility="collapsed"
        )
        
        # Extract page name from selection
        selected_page_name = selected_option.split(" ", 1)[1]  # Remove icon
        st.session_state.selected_page = selected_page_name
        
        # Show page description
        selected_page_info = next((p for p in pages if p['name'] == selected_page_name), None)
        if selected_page_info:
            st.caption(selected_page_info['description'])
        
        return selected_page_name
    
    def _show_sidebar_footer(self, user_role: str):
        """
        Show sidebar footer with user info and actions
        
        Args:
            user_role: Current user's role
        """
        st.subheader("ℹ️ Information")
        
        # Show current sprint info
        st.info("**Current Sprint:** Sprint 4 - Question Management & Test Taking ✅ COMPLETE", icon="🚀")
        
        # Show role-specific tips
        if user_role == "instructor":
            st.success("💡 **Tip:** Create tests from your generated questions and publish them to students!", icon="💡")
        elif user_role == "student":
            st.success("💡 **Tip:** Browse 'Available Tests' to start taking quizzes!", icon="💡")
        
        # Show version info
        st.caption("QuizGenius MVP v4.3.0")
        st.caption("Sprint 4 Complete - Full Test Taking System")
    
    def get_breadcrumb(self, current_page: str, user_role: str) -> str:
        """
        Generate breadcrumb navigation
        
        Args:
            current_page: Current page name
            user_role: User's role
            
        Returns:
            Breadcrumb string
        """
        role_title = user_role.title()
        return f"🏠 Home > {role_title} Portal > {current_page}"
    
    def get_instructor_pages(self) -> List[Dict]:
        """
        Get instructor pages
        
        Returns:
            List of instructor pages
        """
        return self.instructor_pages
    
    def get_student_pages(self) -> List[Dict]:
        """
        Get student pages
        
        Returns:
            List of student pages
        """
        return self.student_pages
    
    def generate_breadcrumb(self, current_page: str, user_role: str) -> str:
        """
        Generate breadcrumb navigation (alias for get_breadcrumb)
        
        Args:
            current_page: Current page name
            user_role: User's role
            
        Returns:
            Breadcrumb string
        """
        return self.get_breadcrumb(current_page, user_role)
    
    def show_page_header(self, page_name: str, user_role: str):
        """
        Show standardized page header
        
        Args:
            page_name: Name of the current page
            user_role: User's role
        """
        # Show breadcrumb
        breadcrumb = self.get_breadcrumb(page_name, user_role)
        st.caption(breadcrumb)
        
        # Show page title with icon
        pages = self._get_pages_for_role(user_role)
        page_info = next((p for p in pages if p['name'] == page_name), None)
        
        if page_info:
            st.title(f"{page_info['icon']} {page_name}")
            st.markdown(f"*{page_info['description']}*")
        else:
            st.title(page_name)
        
        st.divider()
    
    def show_coming_soon_message(self, feature_name: str, sprint_number: int):
        """
        Show coming soon message for future features
        
        Args:
            feature_name: Name of the feature
            sprint_number: Sprint when feature will be available
        """
        st.info(
            f"🚧 **{feature_name}** will be available in Sprint {sprint_number}. "
            f"Stay tuned for updates!",
            icon="🔮"
        )
        
        # Show development roadmap
        with st.expander("📅 Development Roadmap"):
            st.markdown("""
            **Sprint 1**: Foundation & Infrastructure ✅ COMPLETE
            - ✅ User authentication and registration
            - ✅ Basic application structure
            - ✅ AWS services integration
            
            **Sprint 2**: Authentication & AI Integration ✅ COMPLETE
            - ✅ Complete user registration and login
            - ✅ AI question generation from PDFs
            
            **Sprint 3**: PDF Processing & Question Generation ✅ COMPLETE
            - ✅ PDF upload and processing
            - ✅ Question generation and management
            
            **Sprint 4**: Question Management & Test Taking ✅ COMPLETE
            - ✅ Test creation and publishing
            - ✅ Student test-taking interface
            - ✅ Question management and editing
            
            **Sprint 5**: Auto-Grading & Results (Next)
            - 🔄 Automatic grading system
            - 🔄 Results and analytics
            """)
    
    def show_feature_status(self, features: Dict[str, str]):
        """
        Show status of various features
        
        Args:
            features: Dictionary of feature names and their status
        """
        st.subheader("🔧 Feature Status")
        
        status_icons = {
            "complete": "✅",
            "in_progress": "🔄",
            "planned": "📅",
            "not_started": "⏳"
        }
        
        for feature, status in features.items():
            icon = status_icons.get(status, "❓")
            st.markdown(f"{icon} **{feature}**: {status.replace('_', ' ').title()}")

class PageRouter:
    """Handle page routing and state management"""
    
    def __init__(self):
        """Initialize page router"""
        pass
    
    def navigate_to(self, page_name: str):
        """
        Navigate to a specific page
        
        Args:
            page_name: Name of the page to navigate to
        """
        st.session_state.selected_page = page_name
        st.rerun()
    
    def get_current_page(self) -> str:
        """
        Get the current page name
        
        Returns:
            Current page name
        """
        return st.session_state.get('selected_page', 'Dashboard')
    
    def is_current_page(self, page_name: str) -> bool:
        """
        Check if given page is the current page
        
        Args:
            page_name: Page name to check
            
        Returns:
            True if it's the current page
        """
        return self.get_current_page() == page_name