"""
Test Publishing Page for QuizGenius MVP
Allows instructors to publish and manage test availability
Implements Step 4.2.2: Test Publishing (US-2.5.2 - 3 points)
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from services.test_publishing_service import TestPublishingService, TestPublishingError
from services.test_creation_service import TestCreationService
from utils.session_manager import SessionManager


class TestPublishingPage:
    """Test publishing page for instructors"""
    
    def __init__(self):
        """Initialize test publishing page"""
        self.session_manager = SessionManager()
        
        # Try to initialize services
        try:
            self.publishing_service = TestPublishingService()
            self.test_service = TestCreationService()
            self.services_available = True
        except Exception as e:
            st.error(f"Publishing services not available: {e}")
            self.publishing_service = None
            self.test_service = None
            self.services_available = False
    
    def render(self):
        """Render the test publishing page"""
        st.title("🚀 Test Publishing")
        st.markdown("Publish tests to make them available to students.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to publish tests.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'instructor':
            st.error("Only instructors can publish tests.")
            return
        
        instructor_id = user_data.get('user_id')
        
        # Check services availability
        if not self.services_available:
            st.warning("Publishing services are not available. Please try again later.")
            return
        
        # Initialize session state
        if 'publishing_view' not in st.session_state:
            st.session_state['publishing_view'] = 'list'  # list, publish, settings
        
        # Render based on current view
        if st.session_state['publishing_view'] == 'list':
            self._render_test_list(instructor_id)
        elif st.session_state['publishing_view'] == 'publish':
            self._render_publishing_interface(instructor_id)
        elif st.session_state['publishing_view'] == 'settings':
            self._render_publication_settings(instructor_id)
    
    def _render_test_list(self, instructor_id: str):
        """Render list of tests with publishing status"""
        st.subheader("📋 Test Publishing Dashboard")
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("📊 Analytics", use_container_width=True):
                st.info("Publishing analytics will be available in a future update.")
        
        with col3:
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state['publishing_view'] = 'settings'
                st.rerun()
        
        # Load tests
        try:
            all_tests = self.test_service.get_tests_by_instructor(instructor_id)
            
            if not all_tests:
                self._render_no_tests_state()
                return
            
            # Separate tests by status
            draft_tests = [t for t in all_tests if t.get('status') == 'draft']
            published_tests = [t for t in all_tests if t.get('status') == 'published']
            archived_tests = [t for t in all_tests if t.get('status') == 'archived']
            
            # Publishing overview
            self._render_publishing_overview(draft_tests, published_tests, archived_tests)
            
            # Test status tabs
            tab1, tab2, tab3 = st.tabs([
                f"📝 Draft Tests ({len(draft_tests)})",
                f"🚀 Published Tests ({len(published_tests)})",
                f"📦 Archived Tests ({len(archived_tests)})"
            ])
            
            with tab1:
                self._render_draft_tests(draft_tests, instructor_id)
            
            with tab2:
                self._render_published_tests(published_tests, instructor_id)
            
            with tab3:
                self._render_archived_tests(archived_tests, instructor_id)
                
        except Exception as e:
            st.error(f"Failed to load tests: {str(e)}")
    
    def _render_no_tests_state(self):
        """Render state when no tests exist"""
        st.info("📭 No tests found.")
        st.markdown("""
        **To get started:**
        1. Create some tests first
        2. Return here to publish them
        3. Students will be able to access published tests
        """)
        
        if st.button("➕ Create Test", use_container_width=True):
            st.session_state['selected_page'] = 'Test Creation'
            st.rerun()
    
    def _render_publishing_overview(self, draft_tests: List[Dict], 
                                  published_tests: List[Dict], archived_tests: List[Dict]):
        """Render publishing overview statistics"""
        st.subheader("📊 Publishing Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tests", len(draft_tests) + len(published_tests) + len(archived_tests))
        
        with col2:
            st.metric("Draft Tests", len(draft_tests))
        
        with col3:
            st.metric("Published Tests", len(published_tests))
        
        with col4:
            # Calculate total student access
            available_tests = sum(1 for test in published_tests 
                                if test.get('publication_info', {}).get('student_access', True))
            st.metric("Available to Students", available_tests)
    
    def _render_draft_tests(self, draft_tests: List[Dict], instructor_id: str):
        """Render draft tests ready for publishing"""
        if not draft_tests:
            st.info("No draft tests available. Create some tests to publish them.")
            return
        
        st.markdown("**Tests ready for publishing:**")
        
        for test in draft_tests:
            self._render_draft_test_card(test, instructor_id)
    
    def _render_published_tests(self, published_tests: List[Dict], instructor_id: str):
        """Render published tests with management options"""
        if not published_tests:
            st.info("No published tests. Publish some draft tests to make them available to students.")
            return
        
        st.markdown("**Currently published tests:**")
        
        for test in published_tests:
            self._render_published_test_card(test, instructor_id)
    
    def _render_archived_tests(self, archived_tests: List[Dict], instructor_id: str):
        """Render archived tests"""
        if not archived_tests:
            st.info("No archived tests.")
            return
        
        st.markdown("**Archived tests:**")
        
        for test in archived_tests:
            self._render_archived_test_card(test, instructor_id)
    
    def _render_draft_test_card(self, test: Dict[str, Any], instructor_id: str):
        """Render individual draft test card"""
        test_id = test['test_id']
        title = test['title']
        question_count = len(test.get('question_ids', []))
        created_at = test['created_at'][:19]
        
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 2])
            
            with col1:
                st.markdown(f"**{title}**")
                st.caption(f"Created: {created_at}")
                st.caption(f"{question_count} questions")
            
            with col2:
                # Validation status
                try:
                    validation = self.publishing_service._validate_test_for_publication(test)
                    if validation['valid']:
                        st.success("✅ Ready")
                    else:
                        st.warning(f"⚠️ {len(validation['errors'])} issues")
                        with st.expander("Issues", expanded=False):
                            for error in validation['errors']:
                                st.markdown(f"- {error}")
                except:
                    st.info("❓ Unknown")
            
            with col3:
                # Action buttons
                button_col1, button_col2 = st.columns(2)
                
                with button_col1:
                    if st.button("🚀 Publish", key=f"publish_{test_id}", use_container_width=True):
                        st.session_state['current_test'] = test_id
                        st.session_state['publishing_view'] = 'publish'
                        st.rerun()
                
                with button_col2:
                    if st.button("👀 Preview", key=f"preview_{test_id}", use_container_width=True):
                        st.session_state['current_test'] = test_id
                        st.session_state['selected_page'] = 'Test Creation'
                        st.session_state['test_creation_step'] = 'preview'
                        st.rerun()
            
            st.divider()
    
    def _render_published_test_card(self, test: Dict[str, Any], instructor_id: str):
        """Render individual published test card"""
        test_id = test['test_id']
        title = test['title']
        question_count = len(test.get('question_ids', []))
        published_at = test.get('published_at', 'Unknown')[:19]
        
        # Get publication status
        try:
            pub_status = self.publishing_service.get_publication_status(test_id, instructor_id)
            availability = pub_status['availability_status']
            attempt_stats = pub_status['attempt_statistics']
        except:
            availability = {'status': 'unknown', 'available_now': False}
            attempt_stats = {'total_attempts': 0}
        
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 2])
            
            with col1:
                st.markdown(f"**{title}**")
                st.caption(f"Published: {published_at}")
                st.caption(f"{question_count} questions")
            
            with col2:
                # Availability status
                if availability['available_now']:
                    st.success("🟢 Available")
                else:
                    st.warning(f"🟡 {availability['status'].title()}")
                
                st.caption(f"{attempt_stats['total_attempts']} attempts")
            
            with col3:
                # Action buttons
                button_col1, button_col2 = st.columns(2)
                
                with button_col1:
                    if st.button("📴 Unpublish", key=f"unpublish_{test_id}", use_container_width=True):
                        self._handle_unpublish_test(test_id, instructor_id)
                
                with button_col2:
                    if st.button("⚙️ Settings", key=f"settings_{test_id}", use_container_width=True):
                        st.session_state['current_test'] = test_id
                        st.session_state['publishing_view'] = 'settings'
                        st.rerun()
            
            # Publication details
            with st.expander("📊 Publication Details", expanded=False):
                pub_info = test.get('publication_info', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Publication ID:** {pub_info.get('publication_id', 'N/A')}")
                    st.markdown(f"**Student Access:** {'Yes' if pub_info.get('student_access', True) else 'No'}")
                    
                with col2:
                    st.markdown(f"**Availability:** {availability['message']}")
                    max_students = pub_info.get('max_students')
                    st.markdown(f"**Max Students:** {max_students if max_students else 'Unlimited'}")
            
            st.divider()
    
    def _render_archived_test_card(self, test: Dict[str, Any], instructor_id: str):
        """Render individual archived test card"""
        test_id = test['test_id']
        title = test['title']
        question_count = len(test.get('question_ids', []))
        
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 2])
            
            with col1:
                st.markdown(f"**{title}**")
                st.caption(f"{question_count} questions")
            
            with col2:
                st.info("📦 Archived")
            
            with col3:
                if st.button("🔄 Restore", key=f"restore_{test_id}", use_container_width=True):
                    self._handle_restore_test(test_id, instructor_id)
            
            st.divider()
    
    def _render_publishing_interface(self, instructor_id: str):
        """Render test publishing interface"""
        if 'current_test' not in st.session_state:
            st.error("No test selected for publishing.")
            return
        
        test_id = st.session_state['current_test']
        
        st.subheader("🚀 Publish Test")
        
        # Back button
        if st.button("⬅️ Back to Test List"):
            st.session_state['publishing_view'] = 'list'
            st.rerun()
        
        # Load test data
        try:
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data:
                st.error("Test not found.")
                return
            
            # Test information
            st.markdown("### 📋 Test Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Title:** {test_data['title']}")
                st.markdown(f"**Questions:** {len(test_data.get('question_ids', []))}")
                st.markdown(f"**Time Limit:** {test_data.get('time_limit', 0)} minutes")
            
            with col2:
                st.markdown(f"**Passing Score:** {test_data.get('passing_score', 0)}%")
                st.markdown(f"**Attempts Allowed:** {test_data.get('attempts_allowed', 1)}")
                st.markdown(f"**Status:** {test_data.get('status', 'unknown').title()}")
            
            # Validation check
            validation = self.publishing_service._validate_test_for_publication(test_data)
            
            if not validation['valid']:
                st.error("❌ Test is not ready for publication")
                st.markdown("**Issues to resolve:**")
                for error in validation['errors']:
                    st.markdown(f"- {error}")
                
                if st.button("✏️ Edit Test"):
                    st.session_state['selected_page'] = 'Test Creation'
                    st.session_state['test_creation_step'] = 'edit'
                    st.rerun()
                
                return
            
            st.success("✅ Test is ready for publication")
            
            # Publication configuration
            st.markdown("### ⚙️ Publication Settings")
            
            with st.form("publication_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    student_access = st.checkbox(
                        "Enable Student Access",
                        value=True,
                        help="Allow students to access this test"
                    )
                    
                    availability_start = st.date_input(
                        "Available From (Optional)",
                        value=None,
                        help="Test will be available starting from this date"
                    )
                    
                    max_students = st.number_input(
                        "Maximum Students (Optional)",
                        min_value=1,
                        max_value=1000,
                        value=None,
                        help="Limit the number of students who can take this test"
                    )
                
                with col2:
                    immediate_publish = st.checkbox(
                        "Publish Immediately",
                        value=True,
                        help="Make test available to students immediately"
                    )
                    
                    availability_end = st.date_input(
                        "Available Until (Optional)",
                        value=None,
                        help="Test will be unavailable after this date"
                    )
                    
                    publication_notes = st.text_area(
                        "Publication Notes (Optional)",
                        placeholder="Internal notes about this publication",
                        help="Notes for your reference (not visible to students)"
                    )
                
                # Publication confirmation
                st.markdown("### 🚀 Publish Test")
                
                st.info("**Publishing will:**")
                st.markdown("""
                - Make the test available to students
                - Allow students to take the test based on your settings
                - Enable test attempt tracking and grading
                - Send notifications to students (if enabled)
                """)
                
                publish_button = st.form_submit_button(
                    "🚀 Publish Test",
                    type="primary",
                    use_container_width=True
                )
                
                if publish_button:
                    # Prepare publication configuration
                    pub_config = {
                        'student_access': student_access,
                        'availability_start': availability_start.isoformat() if availability_start else None,
                        'availability_end': availability_end.isoformat() if availability_end else None,
                        'max_students': max_students,
                        'notes': publication_notes.strip()
                    }
                    
                    # Publish test
                    try:
                        result = self.publishing_service.publish_test(test_id, instructor_id, pub_config)
                        
                        if result['success']:
                            st.success("🎉 Test published successfully!")
                            
                            # Show publication details
                            st.markdown("**Publication Details:**")
                            st.markdown(f"- Publication ID: `{result['publication_id']}`")
                            st.markdown(f"- Published at: {result['published_at'][:19]}")
                            st.markdown(f"- Status: {result['status'].title()}")
                            
                            # Auto-redirect after success
                            st.session_state['publishing_view'] = 'list'
                            st.rerun()
                        else:
                            st.error(f"❌ Publication failed: {result.get('error', 'Unknown error')}")
                            
                    except TestPublishingError as e:
                        st.error(f"❌ Publication failed: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {str(e)}")
            
        except Exception as e:
            st.error(f"Failed to load test data: {str(e)}")
    
    def _render_publication_settings(self, instructor_id: str):
        """Render publication settings interface"""
        st.subheader("⚙️ Publication Settings")
        
        # Back button
        if st.button("⬅️ Back to Test List"):
            st.session_state['publishing_view'] = 'list'
            st.rerun()
        
        if 'current_test' not in st.session_state:
            st.error("No test selected for settings.")
            return
        
        test_id = st.session_state['current_test']
        
        try:
            # Get current publication status
            pub_status = self.publishing_service.get_publication_status(test_id, instructor_id)
            
            if not pub_status['is_published']:
                st.warning("This test is not currently published.")
                return
            
            test_data = self.test_service.get_test_by_id(test_id)
            pub_info = pub_status['publication_info']
            
            # Test information
            st.markdown("### 📋 Test Information")
            st.markdown(f"**Title:** {test_data['title']}")
            st.markdown(f"**Publication ID:** {pub_info.get('publication_id', 'N/A')}")
            st.markdown(f"**Published:** {pub_info.get('published_at', 'Unknown')[:19]}")
            
            # Current settings
            st.markdown("### 📊 Current Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                availability = pub_status['availability_status']
                if availability['available_now']:
                    st.success(f"🟢 {availability['message']}")
                else:
                    st.warning(f"🟡 {availability['message']}")
            
            with col2:
                attempt_stats = pub_status['attempt_statistics']
                st.info(f"📊 {attempt_stats['total_attempts']} total attempts")
            
            # Settings form
            st.markdown("### ⚙️ Update Settings")
            
            with st.form("settings_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_student_access = st.checkbox(
                        "Student Access",
                        value=pub_info.get('student_access', True),
                        help="Enable or disable student access"
                    )
                    
                    current_start = pub_info.get('availability_start')
                    new_availability_start = st.date_input(
                        "Available From",
                        value=datetime.fromisoformat(current_start).date() if current_start else None,
                        help="When the test becomes available"
                    )
                
                with col2:
                    current_end = pub_info.get('availability_end')
                    new_availability_end = st.date_input(
                        "Available Until",
                        value=datetime.fromisoformat(current_end).date() if current_end else None,
                        help="When the test becomes unavailable"
                    )
                    
                    new_max_students = st.number_input(
                        "Maximum Students",
                        min_value=1,
                        max_value=1000,
                        value=pub_info.get('max_students'),
                        help="Maximum number of students allowed"
                    )
                
                new_notes = st.text_area(
                    "Publication Notes",
                    value=pub_info.get('publication_notes', ''),
                    help="Internal notes about this publication"
                )
                
                update_button = st.form_submit_button(
                    "💾 Update Settings",
                    type="primary",
                    use_container_width=True
                )
                
                if update_button:
                    # Prepare settings update
                    new_settings = {
                        'student_access': new_student_access,
                        'availability_start': new_availability_start.isoformat() if new_availability_start else None,
                        'availability_end': new_availability_end.isoformat() if new_availability_end else None,
                        'max_students': new_max_students,
                        'publication_notes': new_notes.strip()
                    }
                    
                    try:
                        result = self.publishing_service.update_publication_settings(
                            test_id, instructor_id, new_settings
                        )
                        
                        if result['success']:
                            st.success("✅ Settings updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update settings")
                            
                    except TestPublishingError as e:
                        st.error(f"❌ Update failed: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {str(e)}")
            
        except Exception as e:
            st.error(f"Failed to load publication settings: {str(e)}")
    
    def _handle_unpublish_test(self, test_id: str, instructor_id: str):
        """Handle test unpublishing"""
        # Confirmation dialog
        if f"confirm_unpublish_{test_id}" not in st.session_state:
            st.session_state[f"confirm_unpublish_{test_id}"] = False
        
        if not st.session_state[f"confirm_unpublish_{test_id}"]:
            st.warning("⚠️ Are you sure you want to unpublish this test?")
            st.markdown("This will make the test unavailable to students.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Unpublish", key=f"confirm_unpublish_yes_{test_id}"):
                    st.session_state[f"confirm_unpublish_{test_id}"] = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key=f"confirm_unpublish_no_{test_id}"):
                    return
        else:
            # Perform unpublishing
            try:
                reason = st.text_input(
                    "Reason for unpublishing (optional):",
                    key=f"unpublish_reason_{test_id}",
                    placeholder="e.g., Found errors, Need updates, etc."
                )
                
                if st.button("📴 Unpublish Now", key=f"unpublish_now_{test_id}"):
                    result = self.publishing_service.unpublish_test(test_id, instructor_id, reason)
                    
                    if result['success']:
                        st.success("✅ Test unpublished successfully!")
                        
                        # Show unpublish details
                        if result.get('had_attempts'):
                            st.warning(f"⚠️ Test had {result['attempt_count']} student attempts")
                        
                        # Clean up session state
                        if f"confirm_unpublish_{test_id}" in st.session_state:
                            del st.session_state[f"confirm_unpublish_{test_id}"]
                        
                        st.rerun()
                    else:
                        st.error(f"❌ Unpublish failed: {result.get('error', 'Unknown error')}")
                        
            except TestPublishingError as e:
                st.error(f"❌ Unpublish failed: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
    
    def _handle_restore_test(self, test_id: str, instructor_id: str):
        """Handle test restoration from archive"""
        try:
            # Update test status back to draft
            result = self.test_service.update_test(
                test_id, 
                {'status': 'draft'}, 
                instructor_id
            )
            
            if result['success']:
                st.success("✅ Test restored to draft status!")
                st.rerun()
            else:
                st.error("❌ Failed to restore test")
                
        except Exception as e:
            st.error(f"❌ Restore failed: {str(e)}")


def render_test_publishing_page():
    """Render the test publishing page"""
    page = TestPublishingPage()
    page.render()


if __name__ == "__main__":
    render_test_publishing_page()