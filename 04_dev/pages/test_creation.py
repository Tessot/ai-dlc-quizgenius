"""
Test Creation Page for QuizGenius MVP
Allows instructors to create and configure tests from their questions
Implements Step 4.2.1: Test Creation Interface (US-2.5.1 - 5 points)
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from services.test_creation_service import TestCreationService, TestCreationError
from services.question_storage_service import QuestionStorageService
from utils.session_manager import SessionManager


class TestCreationPage:
    """Test creation page for instructors"""
    
    def __init__(self):
        """Initialize test creation page"""
        self.session_manager = SessionManager()
        
        # Try to initialize services
        try:
            self.test_service = TestCreationService()
            self.question_service = QuestionStorageService()
            self.services_available = True
        except Exception as e:
            st.error(f"Test creation services not available: {e}")
            self.test_service = None
            self.question_service = None
            self.services_available = False
    
    def render(self):
        """Render the test creation page"""
        st.title("📝 Test Creation")
        st.markdown("Create and configure tests from your generated questions.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to create tests.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'instructor':
            st.error("Only instructors can create tests.")
            return
        
        instructor_id = user_data.get('user_id')
        
        # Check services availability
        if not self.services_available:
            st.warning("Test creation services are not available. Please try again later.")
            return
        
        # Initialize session state
        if 'test_creation_step' not in st.session_state:
            st.session_state['test_creation_step'] = 'list'  # list, create, edit, preview
        
        # Render based on current step
        if st.session_state['test_creation_step'] == 'list':
            self._render_test_list(instructor_id)
        elif st.session_state['test_creation_step'] == 'create':
            self._render_test_creation_form(instructor_id)
        elif st.session_state['test_creation_step'] == 'edit':
            self._render_test_edit_form(instructor_id)
        elif st.session_state['test_creation_step'] == 'preview':
            self._render_test_preview(instructor_id)
    
    def _render_test_list(self, instructor_id: str):
        """Render list of existing tests"""
        st.subheader("📋 Your Tests")
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("➕ Create New Test", type="primary", use_container_width=True):
                st.session_state['test_creation_step'] = 'create'
                st.session_state['current_test'] = None
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        with col3:
            if st.button("📊 Analytics", use_container_width=True):
                st.info("Test analytics will be available in a future update.")
        
        # Load tests
        try:
            tests = self.test_service.get_tests_by_instructor(instructor_id)
            
            if not tests:
                self._render_no_tests_state()
                return
            
            # Filter controls
            st.subheader("🔍 Filter Tests")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Status",
                    ["All", "Draft", "Published", "Archived"],
                    key="status_filter"
                )
            
            with col2:
                # Get unique tags
                all_tags = set()
                for test in tests:
                    all_tags.update(test.get('tags', []))
                tag_options = ["All"] + sorted(list(all_tags))
                
                tag_filter = st.selectbox(
                    "Tag",
                    tag_options,
                    key="tag_filter"
                )
            
            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Created Date (Newest)", "Created Date (Oldest)", "Title (A-Z)", "Title (Z-A)", "Status"],
                    key="sort_by"
                )
            
            # Apply filters
            filtered_tests = self._apply_test_filters(tests, status_filter, tag_filter, sort_by)
            
            # Display tests
            st.subheader(f"📝 Tests ({len(filtered_tests)})")
            
            for test in filtered_tests:
                self._render_test_card(test, instructor_id)
                
        except Exception as e:
            st.error(f"Failed to load tests: {str(e)}")
    
    def _render_no_tests_state(self):
        """Render state when no tests exist"""
        st.info("📭 No tests found.")
        st.markdown("""
        **To get started:**
        1. Make sure you have generated some questions
        2. Click "Create New Test" to create your first test
        3. Select questions and configure your test settings
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🤖 Generate Questions", use_container_width=True):
                st.session_state['selected_page'] = 'Question Generation'
                st.rerun()
        with col2:
            if st.button("❓ Manage Questions", use_container_width=True):
                st.session_state['selected_page'] = 'Question Management'
                st.rerun()
    
    def _render_test_creation_form(self, instructor_id: str):
        """Render test creation form"""
        st.subheader("➕ Create New Test")
        
        # Back button
        if st.button("⬅️ Back to Test List"):
            st.session_state['test_creation_step'] = 'list'
            st.rerun()
        
        # Test creation form
        with st.form("test_creation_form"):
            st.markdown("### 📋 Test Metadata")
            
            # Basic information
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input(
                    "Test Title *",
                    placeholder="Enter test title",
                    help="A clear, descriptive title for your test"
                )
                
                time_limit = st.number_input(
                    "Time Limit (minutes) *",
                    min_value=1,
                    max_value=480,
                    value=60,
                    help="Maximum time allowed for the test"
                )
                
                attempts_allowed = st.number_input(
                    "Attempts Allowed *",
                    min_value=1,
                    max_value=10,
                    value=1,
                    help="Number of attempts students can make"
                )
            
            with col2:
                description = st.text_area(
                    "Description",
                    placeholder="Optional description of the test",
                    help="Brief description of what the test covers"
                )
                
                passing_score = st.number_input(
                    "Passing Score (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=70.0,
                    step=5.0,
                    help="Minimum score required to pass"
                )
                
                tags = st.text_input(
                    "Tags",
                    placeholder="tag1, tag2, tag3",
                    help="Comma-separated tags for organization"
                )
            
            # Instructions
            st.markdown("### 📝 Test Instructions")
            instructions = st.text_area(
                "Instructions for Students",
                placeholder="Enter instructions that students will see before starting the test",
                height=100,
                help="Clear instructions help students understand what's expected"
            )
            
            # Test configuration
            st.markdown("### ⚙️ Test Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                randomize_questions = st.checkbox(
                    "Randomize Question Order",
                    help="Present questions in random order for each student"
                )
                
                show_results_immediately = st.checkbox(
                    "Show Results Immediately",
                    value=True,
                    help="Show results to students immediately after submission"
                )
            
            with col2:
                randomize_options = st.checkbox(
                    "Randomize Answer Options",
                    help="Randomize the order of multiple choice options"
                )
            
            # Question selection
            st.markdown("### ❓ Question Selection")
            
            # Load available questions
            try:
                available_questions = self.question_service.get_questions_by_instructor(instructor_id, limit=1000)
                
                if not available_questions:
                    st.warning("No questions available. Please generate some questions first.")
                    st.stop()
                
                # Question selection interface
                selected_questions = self._render_question_selection(available_questions)
                
            except Exception as e:
                st.error(f"Failed to load questions: {str(e)}")
                st.stop()
            
            # Form submission
            submitted = st.form_submit_button("🚀 Create Test", type="primary")
            
            if submitted:
                # Validate form
                if not title.strip():
                    st.error("Test title is required.")
                    return
                
                if not selected_questions:
                    st.error("At least one question must be selected.")
                    return
                
                # Prepare test configuration
                test_config = {
                    'title': title.strip(),
                    'description': description.strip(),
                    'instructor_id': instructor_id,
                    'question_ids': selected_questions,
                    'time_limit': time_limit,
                    'attempts_allowed': attempts_allowed,
                    'randomize_questions': randomize_questions,
                    'randomize_options': randomize_options,
                    'show_results_immediately': show_results_immediately,
                    'passing_score': passing_score,
                    'instructions': instructions.strip(),
                    'tags': [tag.strip() for tag in tags.split(',') if tag.strip()]
                }
                
                # Create test
                try:
                    result = self.test_service.create_test(test_config)
                    
                    if result['success']:
                        st.success(f"✅ Test created successfully!")
                        st.session_state['current_test'] = result['test_id']
                        st.session_state['test_creation_step'] = 'preview'
                        st.rerun()
                    else:
                        st.error("Failed to create test.")
                        
                except TestCreationError as e:
                    st.error(f"Test creation failed: {str(e)}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")
    
    def _render_question_selection(self, available_questions: List[Dict[str, Any]]) -> List[str]:
        """Render question selection interface"""
        if not available_questions:
            return []
        
        # Question selection method
        selection_method = st.radio(
            "Selection Method",
            ["Manual Selection", "Smart Selection", "Filter & Select"],
            horizontal=True,
            help="Choose how to select questions for your test"
        )
        
        if selection_method == "Manual Selection":
            return self._render_manual_question_selection(available_questions)
        elif selection_method == "Smart Selection":
            return self._render_smart_question_selection(available_questions)
        else:
            return self._render_filtered_question_selection(available_questions)
    
    def _render_manual_question_selection(self, questions: List[Dict[str, Any]]) -> List[str]:
        """Render manual question selection"""
        st.markdown("**Select questions individually:**")
        
        selected_questions = []
        
        # Show questions with checkboxes
        for i, question in enumerate(questions):
            question_id = question.get('QuestionID', question.get('question_id'))
            question_text = question.get('QuestionText', question.get('question_text', 'Unknown Question'))
            question_type = question.get('QuestionType', question.get('question_type', 'unknown'))
            
            # Question preview
            with st.expander(f"{question_type.upper()}: {question_text[:80]}...", expanded=False):
                # Checkbox for selection
                selected = st.checkbox(
                    f"Include in test",
                    key=f"select_q_{question_id}",
                    help=f"Select this question for the test"
                )
                
                if selected:
                    selected_questions.append(question_id)
                
                # Question details
                st.markdown(f"**Question:** {question_text}")
                
                if question_type == 'multiple_choice':
                    options = question.get('Options', question.get('options', []))
                    correct = question.get('CorrectAnswer', question.get('correct_answer', ''))
                    
                    for j, option in enumerate(options):
                        prefix = "✅" if option == correct else "  "
                        st.markdown(f"{prefix} **{chr(65+j)}.** {option}")
                else:
                    correct = question.get('CorrectAnswer', question.get('correct_answer', ''))
                    st.markdown(f"**Answer:** {correct}")
                
                # Metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    difficulty = question.get('DifficultyLevel', question.get('difficulty_level', 'Unknown'))
                    st.caption(f"Difficulty: {difficulty}")
                with col2:
                    topic = question.get('Topic', question.get('topic', 'Unknown'))
                    st.caption(f"Topic: {topic}")
                with col3:
                    quality = question.get('QualityScore', question.get('quality_score', 0))
                    st.caption(f"Quality: {quality:.1f}/10")
        
        # Selection summary
        if selected_questions:
            st.success(f"✅ Selected {len(selected_questions)} questions")
        else:
            st.info("No questions selected yet")
        
        return selected_questions
    
    def _render_smart_question_selection(self, questions: List[Dict[str, Any]]) -> List[str]:
        """Render smart question selection"""
        st.markdown("**Smart selection based on criteria:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            num_questions = st.number_input(
                "Number of Questions",
                min_value=1,
                max_value=min(50, len(questions)),
                value=min(10, len(questions)),
                help="How many questions to select"
            )
        
        with col2:
            difficulty_preference = st.selectbox(
                "Difficulty Preference",
                ["Mixed", "Easy", "Medium", "Hard"],
                help="Preferred difficulty level"
            )
        
        with col3:
            quality_threshold = st.slider(
                "Minimum Quality Score",
                min_value=0.0,
                max_value=10.0,
                value=7.0,
                step=0.5,
                help="Minimum quality score for selected questions"
            )
        
        # Smart selection logic
        filtered_questions = []
        
        for question in questions:
            quality = question.get('QualityScore', question.get('quality_score', 0))
            difficulty = question.get('DifficultyLevel', question.get('difficulty_level', 'unknown')).lower()
            
            # Quality filter
            if quality < quality_threshold:
                continue
            
            # Difficulty filter
            if difficulty_preference != "Mixed" and difficulty != difficulty_preference.lower():
                continue
            
            filtered_questions.append(question)
        
        # Sort by quality and select top N
        filtered_questions.sort(key=lambda x: x.get('QualityScore', x.get('quality_score', 0)), reverse=True)
        selected_questions_data = filtered_questions[:num_questions]
        
        # Show selected questions
        if selected_questions_data:
            st.success(f"✅ Smart selection found {len(selected_questions_data)} questions")
            
            with st.expander("📋 Selected Questions Preview", expanded=False):
                for question in selected_questions_data:
                    question_text = question.get('QuestionText', question.get('question_text', 'Unknown'))
                    quality = question.get('QualityScore', question.get('quality_score', 0))
                    st.markdown(f"- {question_text[:100]}... (Quality: {quality:.1f})")
        else:
            st.warning("No questions match the smart selection criteria.")
        
        return [q.get('QuestionID', q.get('question_id')) for q in selected_questions_data]
    
    def _render_filtered_question_selection(self, questions: List[Dict[str, Any]]) -> List[str]:
        """Render filtered question selection"""
        st.markdown("**Filter questions then select:**")
        
        # Filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Type filter
            types = list(set(q.get('QuestionType', q.get('question_type', 'unknown')) for q in questions))
            type_filter = st.multiselect(
                "Question Types",
                types,
                default=types,
                help="Filter by question type"
            )
        
        with col2:
            # Topic filter
            topics = list(set(q.get('Topic', q.get('topic', 'unknown')) for q in questions))
            topic_filter = st.multiselect(
                "Topics",
                topics,
                default=topics,
                help="Filter by topic"
            )
        
        with col3:
            # Difficulty filter
            difficulties = list(set(q.get('DifficultyLevel', q.get('difficulty_level', 'unknown')) for q in questions))
            difficulty_filter = st.multiselect(
                "Difficulty Levels",
                difficulties,
                default=difficulties,
                help="Filter by difficulty"
            )
        
        # Apply filters
        filtered_questions = []
        for question in questions:
            q_type = question.get('QuestionType', question.get('question_type', 'unknown'))
            topic = question.get('Topic', question.get('topic', 'unknown'))
            difficulty = question.get('DifficultyLevel', question.get('difficulty_level', 'unknown'))
            
            if (q_type in type_filter and 
                topic in topic_filter and 
                difficulty in difficulty_filter):
                filtered_questions.append(question)
        
        st.info(f"📊 {len(filtered_questions)} questions match your filters")
        
        if not filtered_questions:
            return []
        
        # Bulk selection options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Select All Filtered"):
                for question in filtered_questions:
                    question_id = question.get('QuestionID', question.get('question_id'))
                    st.session_state[f"select_fq_{question_id}"] = True
                st.rerun()
        
        with col2:
            if st.button("❌ Clear All"):
                for question in filtered_questions:
                    question_id = question.get('QuestionID', question.get('question_id'))
                    if f"select_fq_{question_id}" in st.session_state:
                        del st.session_state[f"select_fq_{question_id}"]
                st.rerun()
        
        with col3:
            selected_count = sum(1 for q in filtered_questions 
                               if st.session_state.get(f"select_fq_{q.get('QuestionID', q.get('question_id'))}", False))
            st.metric("Selected", selected_count)
        
        # Show filtered questions with selection
        selected_questions = []
        
        for question in filtered_questions:
            question_id = question.get('QuestionID', question.get('question_id'))
            question_text = question.get('QuestionText', question.get('question_text', 'Unknown Question'))
            
            selected = st.checkbox(
                f"{question_text[:100]}...",
                key=f"select_fq_{question_id}",
                help="Select this question for the test"
            )
            
            if selected:
                selected_questions.append(question_id)
        
        return selected_questions
    
    def _render_test_preview(self, instructor_id: str):
        """Render test preview"""
        if 'current_test' not in st.session_state:
            st.error("No test selected for preview.")
            return
        
        test_id = st.session_state['current_test']
        
        st.subheader("👀 Test Preview")
        
        # Navigation buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Back to List"):
                st.session_state['test_creation_step'] = 'list'
                st.rerun()
        
        with col2:
            if st.button("✏️ Edit Test"):
                st.session_state['test_creation_step'] = 'edit'
                st.rerun()
        
        with col3:
            if st.button("🚀 Publish Test"):
                st.session_state['test_creation_step'] = 'publish'
                st.rerun()
        
        # Load test preview
        try:
            preview_data = self.test_service.get_test_preview(test_id, instructor_id)
            
            test_data = preview_data['test_data']
            questions = preview_data['questions']
            stats = preview_data['statistics']
            
            # Test information
            st.markdown("### 📋 Test Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Title:** {test_data['title']}")
                st.markdown(f"**Description:** {test_data.get('description', 'No description')}")
                st.markdown(f"**Time Limit:** {test_data['time_limit']} minutes")
                st.markdown(f"**Attempts Allowed:** {test_data['attempts_allowed']}")
                st.markdown(f"**Passing Score:** {test_data['passing_score']}%")
            
            with col2:
                st.markdown(f"**Status:** {test_data['status'].title()}")
                st.markdown(f"**Created:** {test_data['created_at'][:19]}")
                st.markdown(f"**Randomize Questions:** {'Yes' if test_data['randomize_questions'] else 'No'}")
                st.markdown(f"**Randomize Options:** {'Yes' if test_data['randomize_options'] else 'No'}")
                st.markdown(f"**Show Results:** {'Immediately' if test_data['show_results_immediately'] else 'Later'}")
            
            # Test statistics
            st.markdown("### 📊 Test Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Questions", stats['total_questions'])
            
            with col2:
                st.metric("Estimated Time", f"{stats['estimated_time']} min")
            
            with col3:
                st.metric("Topics Covered", len(stats['topics']))
            
            with col4:
                mc_count = stats['question_types'].get('multiple_choice', 0)
                tf_count = stats['question_types'].get('true_false', 0)
                st.metric("MC / TF", f"{mc_count} / {tf_count}")
            
            # Question breakdown
            if stats['question_types']:
                st.markdown("**Question Types:**")
                for q_type, count in stats['question_types'].items():
                    st.markdown(f"- {q_type.replace('_', ' ').title()}: {count}")
            
            if stats['difficulty_distribution']:
                st.markdown("**Difficulty Distribution:**")
                for difficulty, count in stats['difficulty_distribution'].items():
                    st.markdown(f"- {difficulty.title()}: {count}")
            
            # Instructions preview
            if test_data.get('instructions'):
                st.markdown("### 📝 Instructions")
                st.info(test_data['instructions'])
            
            # Questions preview
            st.markdown("### ❓ Questions Preview")
            
            for i, question in enumerate(questions, 1):
                with st.expander(f"Question {i}: {question['question_text'][:80]}...", expanded=False):
                    st.markdown(f"**Question:** {question['question_text']}")
                    
                    if question['question_type'] == 'multiple_choice':
                        for j, option in enumerate(question.get('options', [])):
                            prefix = "✅" if option == question['correct_answer'] else "  "
                            st.markdown(f"{prefix} **{chr(65+j)}.** {option}")
                    else:
                        st.markdown(f"**Answer:** {question['correct_answer']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"Type: {question['question_type'].replace('_', ' ').title()}")
                    with col2:
                        st.caption(f"Difficulty: {question['difficulty_level'].title()}")
                    with col3:
                        st.caption(f"Topic: {question['topic']}")
            
        except Exception as e:
            st.error(f"Failed to load test preview: {str(e)}")
    
    def _render_test_card(self, test: Dict[str, Any], instructor_id: str):
        """Render individual test card"""
        test_id = test['test_id']
        title = test['title']
        status = test['status']
        created_at = test['created_at'][:19]
        question_count = len(test.get('question_ids', []))
        
        # Status color
        status_colors = {
            'draft': '🟡',
            'published': '🟢',
            'archived': '🔴'
        }
        status_icon = status_colors.get(status, '⚪')
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
            
            with col1:
                st.markdown(f"**{title}**")
                st.caption(f"Created: {created_at}")
                
                # Tags
                tags = test.get('tags', [])
                if tags:
                    tag_str = " ".join([f"`{tag}`" for tag in tags[:3]])
                    st.markdown(f"Tags: {tag_str}")
            
            with col2:
                st.markdown(f"{status_icon} **{status.title()}**")
                st.caption(f"{question_count} questions")
            
            with col3:
                time_limit = test.get('time_limit', 0)
                attempts = test.get('attempts_allowed', 1)
                st.markdown(f"⏱️ {time_limit}m")
                st.caption(f"{attempts} attempt{'s' if attempts != 1 else ''}")
            
            with col4:
                # Action buttons
                button_col1, button_col2, button_col3 = st.columns(3)
                
                with button_col1:
                    if st.button("👀", key=f"preview_{test_id}", help="Preview"):
                        st.session_state['current_test'] = test_id
                        st.session_state['test_creation_step'] = 'preview'
                        st.rerun()
                
                with button_col2:
                    if st.button("✏️", key=f"edit_{test_id}", help="Edit"):
                        st.session_state['current_test'] = test_id
                        st.session_state['test_creation_step'] = 'edit'
                        st.rerun()
                
                with button_col3:
                    if status == 'draft':
                        if st.button("🚀", key=f"publish_{test_id}", help="Publish"):
                            self._handle_test_publish(test_id, instructor_id)
                    elif status == 'published':
                        if st.button("📴", key=f"unpublish_{test_id}", help="Unpublish"):
                            self._handle_test_unpublish(test_id, instructor_id)
            
            st.divider()
    
    def _apply_test_filters(self, tests: List[Dict[str, Any]], status_filter: str, 
                          tag_filter: str, sort_by: str) -> List[Dict[str, Any]]:
        """Apply filters and sorting to tests"""
        filtered = tests.copy()
        
        # Status filter
        if status_filter != "All":
            filtered = [t for t in filtered if t.get('status', '').lower() == status_filter.lower()]
        
        # Tag filter
        if tag_filter != "All":
            filtered = [t for t in filtered if tag_filter in t.get('tags', [])]
        
        # Sorting
        if sort_by == "Created Date (Newest)":
            filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == "Created Date (Oldest)":
            filtered.sort(key=lambda x: x.get('created_at', ''))
        elif sort_by == "Title (A-Z)":
            filtered.sort(key=lambda x: x.get('title', '').lower())
        elif sort_by == "Title (Z-A)":
            filtered.sort(key=lambda x: x.get('title', '').lower(), reverse=True)
        elif sort_by == "Status":
            filtered.sort(key=lambda x: x.get('status', ''))
        
        return filtered
    
    def _handle_test_publish(self, test_id: str, instructor_id: str):
        """Handle test publishing"""
        try:
            # This would be handled by the publishing service in Step 4.2.2
            st.success(f"Test {test_id} will be published (Step 4.2.2 functionality)")
        except Exception as e:
            st.error(f"Failed to publish test: {str(e)}")
    
    def _handle_test_unpublish(self, test_id: str, instructor_id: str):
        """Handle test unpublishing"""
        try:
            # This would be handled by the publishing service in Step 4.2.2
            st.success(f"Test {test_id} will be unpublished (Step 4.2.2 functionality)")
        except Exception as e:
            st.error(f"Failed to unpublish test: {str(e)}")


def render_test_creation_page():
    """Render the test creation page"""
    page = TestCreationPage()
    page.render()


if __name__ == "__main__":
    render_test_creation_page()