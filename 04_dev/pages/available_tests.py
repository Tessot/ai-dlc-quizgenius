#!/usr/bin/env python3
"""
Available Tests Page for QuizGenius MVP
Displays published tests available to students
Implements Step 4.3.1: Available Tests Display (US-3.2.1 - 3 points)
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from services.student_test_service import StudentTestService, StudentTestError, AvailableTest
from utils.session_manager import SessionManager


class AvailableTestsPage:
    """Available tests page for students"""
    
    def __init__(self):
        """Initialize available tests page"""
        self.session_manager = SessionManager()
        
        # Try to initialize services
        try:
            self.student_service = StudentTestService()
            self.services_available = True
        except Exception as e:
            st.error(f"Student services not available: {e}")
            self.student_service = None
            self.services_available = False
    
    def render(self):
        """Render the available tests page"""
        st.title("📚 Available Tests")
        st.markdown("View and access tests published by your instructors.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to view available tests.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'student':
            st.error("Only students can view available tests.")
            return
        
        student_id = user_data.get('user_id')
        
        # Check services availability
        if not self.services_available:
            st.warning("Test services are not available. Please try again later.")
            return
        
        # Initialize session state
        if 'access_code_input' not in st.session_state:
            st.session_state['access_code_input'] = ''
        if 'selected_test' not in st.session_state:
            st.session_state['selected_test'] = None
        
        # Access code input section
        self._render_access_code_section()
        
        # Load and display available tests
        self._render_available_tests(student_id)
    
    def _render_access_code_section(self):
        """Render access code input section"""
        with st.expander("🔑 Enter Access Code (Optional)", expanded=False):
            st.markdown("""
            Some tests require an access code provided by your instructor.
            Enter the code below to access restricted tests.
            """)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                access_code = st.text_input(
                    "Access Code",
                    value=st.session_state.get('access_code_input', ''),
                    placeholder="Enter access code...",
                    help="Access code provided by your instructor"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                if st.button("Apply Code", use_container_width=True):
                    st.session_state['access_code_input'] = access_code
                    st.rerun()
            
            if st.session_state.get('access_code_input'):
                st.success(f"🔑 Using access code: `{st.session_state['access_code_input']}`")
                if st.button("Clear Access Code"):
                    st.session_state['access_code_input'] = ''
                    st.rerun()
    
    def _render_available_tests(self, student_id: str):
        """Render available tests list"""
        try:
            # Get access code from session
            access_code = st.session_state.get('access_code_input') or None
            
            # Load available tests
            with st.spinner("Loading available tests..."):
                available_tests = self.student_service.get_available_tests(student_id, access_code)
            
            if not available_tests:
                self._render_no_tests_state()
                return
            
            # Filter and sort options
            self._render_filter_controls(available_tests)
            
            # Apply filters
            filtered_tests = self._apply_filters(available_tests)
            
            # Display tests
            st.subheader(f"📝 Available Tests ({len(filtered_tests)})")
            
            if not filtered_tests:
                st.info("No tests match your current filters.")
                return
            
            # Group tests by availability
            available_now = [t for t in filtered_tests if t.is_available_now and t.student_can_take]
            available_later = [t for t in filtered_tests if t.is_available_now and not t.student_can_take]
            not_available = [t for t in filtered_tests if not t.is_available_now]
            
            # Display available tests first
            if available_now:
                st.markdown("### 🟢 Ready to Take")
                for test in available_now:
                    self._render_test_card(test, "available")
            
            if available_later:
                st.markdown("### 🟡 Available (Restrictions Apply)")
                for test in available_later:
                    self._render_test_card(test, "restricted")
            
            if not_available:
                st.markdown("### 🔴 Not Currently Available")
                for test in not_available:
                    self._render_test_card(test, "unavailable")
                    
        except StudentTestError as e:
            st.error(f"Failed to load tests: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    def _render_no_tests_state(self):
        """Render state when no tests are available"""
        st.info("📭 No tests are currently available.")
        st.markdown("""
        **Possible reasons:**
        - No tests have been published by your instructors yet
        - Tests may require an access code (check with your instructor)
        - Tests may be scheduled for a future date
        - You may have already completed all available tests
        
        **What you can do:**
        - Check back later for new tests
        - Contact your instructor for access codes
        - Review your completed tests in the Results section
        """)
    
    def _render_filter_controls(self, tests: List[AvailableTest]):
        """Render filter and sort controls"""
        st.subheader("🔍 Filter & Sort")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            availability_filter = st.selectbox(
                "Availability",
                ["All", "Available Now", "Coming Soon", "Completed"],
                key="availability_filter"
            )
        
        with col2:
            # Get unique instructors
            instructors = list(set(test.instructor_name for test in tests))
            instructor_filter = st.selectbox(
                "Instructor",
                ["All"] + sorted(instructors),
                key="instructor_filter"
            )
        
        with col3:
            difficulty_filter = st.selectbox(
                "Difficulty",
                ["All", "Easy", "Medium", "Hard"],
                key="difficulty_filter"
            )
        
        with col4:
            sort_by = st.selectbox(
                "Sort by",
                ["Availability", "Title (A-Z)", "Title (Z-A)", "Due Date", "Instructor"],
                key="sort_by"
            )
    
    def _apply_filters(self, tests: List[AvailableTest]) -> List[AvailableTest]:
        """Apply filters and sorting to tests"""
        filtered = tests.copy()
        
        # Availability filter
        availability_filter = st.session_state.get('availability_filter', 'All')
        if availability_filter == "Available Now":
            filtered = [t for t in filtered if t.is_available_now and t.student_can_take]
        elif availability_filter == "Coming Soon":
            filtered = [t for t in filtered if not t.is_available_now]
        elif availability_filter == "Completed":
            filtered = [t for t in filtered if t.attempts_used > 0]
        
        # Instructor filter
        instructor_filter = st.session_state.get('instructor_filter', 'All')
        if instructor_filter != "All":
            filtered = [t for t in filtered if t.instructor_name == instructor_filter]
        
        # Sorting
        sort_by = st.session_state.get('sort_by', 'Availability')
        if sort_by == "Title (A-Z)":
            filtered.sort(key=lambda x: x.title.lower())
        elif sort_by == "Title (Z-A)":
            filtered.sort(key=lambda x: x.title.lower(), reverse=True)
        elif sort_by == "Due Date":
            filtered.sort(key=lambda x: x.available_until or '9999-12-31')
        elif sort_by == "Instructor":
            filtered.sort(key=lambda x: x.instructor_name)
        else:  # Availability
            filtered.sort(key=lambda x: (not x.is_available_now, not x.student_can_take, x.title))
        
        return filtered
    
    def _render_test_card(self, test: AvailableTest, status: str):
        """Render individual test card"""
        # Status colors and icons
        status_config = {
            "available": {"color": "green", "icon": "🟢", "text": "Ready to Take"},
            "restricted": {"color": "orange", "icon": "🟡", "text": "Restrictions Apply"},
            "unavailable": {"color": "red", "icon": "🔴", "text": "Not Available"}
        }
        
        config = status_config.get(status, status_config["unavailable"])
        
        with st.container():
            # Header row
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{test.title}**")
                if test.description:
                    st.caption(test.description)
            
            with col2:
                st.markdown(f"{config['icon']} **{config['text']}**")
            
            with col3:
                if status == "available":
                    if st.button("Start Test", key=f"start_{test.test_id}", type="primary", use_container_width=True):
                        self._handle_start_test(test)
                elif status == "restricted":
                    if st.button("View Details", key=f"details_{test.test_id}", use_container_width=True):
                        self._show_test_details(test)
                else:
                    st.button("Not Available", key=f"na_{test.test_id}", disabled=True, use_container_width=True)
            
            # Details row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"**Instructor:** {test.instructor_name}")
                st.markdown(f"**Questions:** {test.total_questions}")
            
            with col2:
                st.markdown(f"**Time Limit:** {test.time_limit} minutes")
                st.markdown(f"**Passing Score:** {test.passing_score}%")
            
            with col3:
                st.markdown(f"**Attempts:** {test.attempts_used}/{test.attempts_allowed}")
                if test.best_score is not None:
                    st.markdown(f"**Best Score:** {test.best_score:.1f}%")
            
            with col4:
                # Availability info
                if test.available_from:
                    st.markdown(f"**Available From:** {test.available_from[:16]}")
                if test.available_until:
                    st.markdown(f"**Available Until:** {test.available_until[:16]}")
                if test.requires_access_code:
                    st.markdown("🔑 **Requires Access Code**")
            
            # Restriction messages
            if status == "restricted":
                if test.attempts_used >= test.attempts_allowed:
                    st.warning(f"⚠️ You have used all {test.attempts_allowed} attempts for this test.")
                elif not test.is_available_now:
                    if test.available_from:
                        st.warning(f"⚠️ This test will be available starting {test.available_from[:16]}.")
                    if test.available_until:
                        st.warning(f"⚠️ This test is available until {test.available_until[:16]}.")
            
            st.divider()
    
    def _handle_start_test(self, test: AvailableTest):
        """Handle starting a test"""
        try:
            # Confirm test start
            if f"confirm_start_{test.test_id}" not in st.session_state:
                st.session_state[f"confirm_start_{test.test_id}"] = False
            
            if not st.session_state[f"confirm_start_{test.test_id}"]:
                st.warning(f"⚠️ Are you ready to start '{test.title}'?")
                st.markdown(f"""
                **Test Details:**
                - **Time Limit:** {test.time_limit} minutes
                - **Questions:** {test.total_questions}
                - **Attempts Remaining:** {test.attempts_allowed - test.attempts_used}
                - **Passing Score:** {test.passing_score}%
                
                ⚠️ **Important:** Once you start, the timer will begin immediately.
                """)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Start Test", key=f"confirm_start_{test.test_id}", type="primary"):
                        st.session_state[f"confirm_start_{test.test_id}"] = True
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_start_{test.test_id}"):
                        return
            else:
                # Start the test
                user_data = self.session_manager.get_user_info()
                student_id = user_data.get('user_id')
                access_code = st.session_state.get('access_code_input')
                
                with st.spinner("Starting test..."):
                    result = self.student_service.start_test_attempt(
                        test.test_id, student_id, access_code
                    )
                
                if result['success']:
                    st.success("✅ Test started successfully!")
                    
                    # Store attempt info in session
                    st.session_state['current_attempt'] = {
                        'attempt_id': result['attempt_id'],
                        'test_id': test.test_id,
                        'started_at': result['started_at'],
                        'time_limit_seconds': result['time_limit_seconds']
                    }
                    
                    # Navigate to test taking page
                    st.session_state['selected_page'] = 'Test Taking'
                    st.rerun()
                else:
                    st.error("Failed to start test. Please try again.")
                    
        except StudentTestError as e:
            st.error(f"Cannot start test: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    def _show_test_details(self, test: AvailableTest):
        """Show detailed test information"""
        with st.expander(f"📋 Details: {test.title}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Test Information")
                st.markdown(f"**Title:** {test.title}")
                st.markdown(f"**Instructor:** {test.instructor_name}")
                st.markdown(f"**Description:** {test.description or 'No description provided'}")
                st.markdown(f"**Questions:** {test.total_questions}")
                st.markdown(f"**Time Limit:** {test.time_limit} minutes")
                st.markdown(f"**Passing Score:** {test.passing_score}%")
            
            with col2:
                st.markdown("### Your Progress")
                st.markdown(f"**Attempts Used:** {test.attempts_used}/{test.attempts_allowed}")
                
                if test.last_attempt_score is not None:
                    st.markdown(f"**Last Score:** {test.last_attempt_score:.1f}%")
                
                if test.best_score is not None:
                    st.markdown(f"**Best Score:** {test.best_score:.1f}%")
                    
                    # Show pass/fail status
                    if test.best_score >= test.passing_score:
                        st.success(f"✅ **Status:** Passed ({test.best_score:.1f}%)")
                    else:
                        st.error(f"❌ **Status:** Not Passed ({test.best_score:.1f}%)")
                
                st.markdown("### Availability")
                if test.available_from:
                    st.markdown(f"**Available From:** {test.available_from}")
                if test.available_until:
                    st.markdown(f"**Available Until:** {test.available_until}")
                if test.requires_access_code:
                    st.markdown("🔑 **Requires Access Code**")
            
            # Show why test is not available
            if not test.student_can_take:
                st.markdown("### ⚠️ Why Can't I Take This Test?")
                reasons = []
                
                if not test.is_available_now:
                    if test.available_from:
                        reasons.append(f"Test is not yet available (starts {test.available_from[:16]})")
                    if test.available_until:
                        reasons.append(f"Test is no longer available (ended {test.available_until[:16]})")
                
                if test.attempts_used >= test.attempts_allowed:
                    reasons.append(f"You have used all {test.attempts_allowed} attempts")
                
                if test.requires_access_code and not st.session_state.get('access_code_input'):
                    reasons.append("Test requires an access code")
                
                for reason in reasons:
                    st.markdown(f"- {reason}")


def render_available_tests_page():
    """Render the available tests page"""
    page = AvailableTestsPage()
    page.render()


if __name__ == "__main__":
    render_available_tests_page()