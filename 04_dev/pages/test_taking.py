#!/usr/bin/env python3
"""
Test Taking Interface for QuizGenius MVP
Provides the interface for students to take tests
Implements Steps 4.3.2-4.3.5: Test Taking Interface, Question Answering, Navigation, and Submission
"""

import streamlit as st
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

from services.student_test_service import StudentTestService, StudentTestError, TestAttempt
from services.test_creation_service import TestCreationService
from utils.session_manager import SessionManager


class TestTakingPage:
    """Test taking interface for students"""
    
    def __init__(self):
        """Initialize test taking page"""
        self.session_manager = SessionManager()
        
        # Try to initialize services
        try:
            self.student_service = StudentTestService()
            self.test_service = TestCreationService()
            self.services_available = True
        except Exception as e:
            st.error(f"Test services not available: {e}")
            self.student_service = None
            self.test_service = None
            self.services_available = False
    
    def render(self):
        """Render the test taking page"""
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to take tests.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'student':
            st.error("Only students can take tests.")
            return
        
        student_id = user_data.get('user_id')
        
        # Check services availability
        if not self.services_available:
            st.warning("Test services are not available. Please try again later.")
            return
        
        # Check if there's an active attempt
        if 'current_attempt' not in st.session_state:
            st.warning("No active test attempt found.")
            st.markdown("Please start a test from the Available Tests page.")
            if st.button("Go to Available Tests"):
                st.session_state['selected_page'] = 'Available Tests'
                st.rerun()
            return
        
        # Load current attempt
        attempt_info = st.session_state['current_attempt']
        attempt_id = attempt_info['attempt_id']
        
        try:
            # Get current attempt from database
            attempt = self.student_service.get_test_attempt(attempt_id, student_id)
            if not attempt:
                st.error("Test attempt not found.")
                return
            
            # Check if attempt is still active
            if attempt.status != 'in_progress':
                st.warning(f"This test attempt is {attempt.status}.")
                if attempt.status == 'submitted':
                    st.success("Your test has been submitted successfully!")
                    if st.button("View Results"):
                        st.session_state['selected_page'] = 'Test Results'
                        st.rerun()
                return
            
            # Render test taking interface
            self._render_test_interface(attempt, student_id)
            
        except StudentTestError as e:
            st.error(f"Error loading test: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    def _render_test_interface(self, attempt: TestAttempt, student_id: str):
        """Render the main test taking interface"""
        # Get test data
        test_data = self.test_service.get_test_by_id(attempt.test_id)
        if not test_data:
            st.error("Test data not found.")
            return
        
        # Initialize session state for answers
        if 'test_answers' not in st.session_state:
            st.session_state['test_answers'] = attempt.answers.copy()
        
        # Render test header
        self._render_test_header(test_data, attempt)
        
        # Render timer
        self._render_timer(attempt)
        
        # Get test questions
        try:
            questions = self.student_service.get_test_questions(
                attempt.test_id, student_id, attempt.attempt_id
            )
        except:
            # Fallback to mock questions if service not fully implemented
            questions = self._get_mock_questions(test_data)
        
        if not questions:
            st.error("No questions found for this test.")
            return
        
        # Render navigation
        current_question = self._render_question_navigation(questions, attempt.current_question)
        
        # Render current question
        self._render_question(questions[current_question], current_question)
        
        # Render action buttons
        self._render_action_buttons(attempt, student_id, questions, current_question)
    
    def _render_test_header(self, test_data: Dict[str, Any], attempt: TestAttempt):
        """Render test header with basic information"""
        st.title(f"📝 {test_data['title']}")
        
        if test_data.get('description'):
            st.markdown(f"*{test_data['description']}*")
        
        # Test info bar
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Questions", len(test_data.get('question_ids', [])))
        
        with col2:
            st.metric("Time Limit", f"{test_data.get('time_limit', 0)} min")
        
        with col3:
            st.metric("Passing Score", f"{test_data.get('passing_score', 0)}%")
        
        with col4:
            answered = len([a for a in st.session_state.get('test_answers', {}).values() if a])
            total = len(test_data.get('question_ids', []))
            st.metric("Progress", f"{answered}/{total}")
        
        st.divider()
    
    def _render_timer(self, attempt: TestAttempt):
        """Render countdown timer"""
        if attempt.time_remaining is None:
            return
        
        # Calculate time remaining
        started_time = datetime.fromisoformat(attempt.started_at.replace('Z', '+00:00'))
        elapsed_seconds = (datetime.now() - started_time).total_seconds()
        time_remaining = max(0, attempt.time_remaining - elapsed_seconds)
        
        # Convert to minutes and seconds
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        
        # Color coding based on time remaining
        if time_remaining > 300:  # More than 5 minutes
            color = "green"
        elif time_remaining > 60:  # More than 1 minute
            color = "orange"
        else:  # Less than 1 minute
            color = "red"
        
        # Display timer
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(
                f"<div style='text-align: center; font-size: 24px; color: {color}; font-weight: bold;'>"
                f"⏰ Time Remaining: {minutes:02d}:{seconds:02d}"
                f"</div>",
                unsafe_allow_html=True
            )
        
        # Auto-submit warning
        if time_remaining <= 60:
            st.error("⚠️ Less than 1 minute remaining! Your test will be auto-submitted when time expires.")
        elif time_remaining <= 300:
            st.warning("⚠️ Less than 5 minutes remaining!")
        
        # Auto-refresh every 30 seconds to update timer
        if time_remaining > 0:
            time.sleep(1)  # Small delay to prevent too frequent updates
            st.rerun()
        else:
            # Time expired - auto submit
            st.error("⏰ Time expired! Submitting your test automatically...")
            self._auto_submit_test(attempt, student_id)
    
    def _render_question_navigation(self, questions: List[Dict[str, Any]], current_q: int) -> int:
        """Render question navigation and return current question index"""
        st.subheader("📋 Question Navigation")
        
        # Question grid
        cols_per_row = 10
        num_questions = len(questions)
        
        for row_start in range(0, num_questions, cols_per_row):
            cols = st.columns(cols_per_row)
            
            for i in range(cols_per_row):
                q_index = row_start + i
                if q_index >= num_questions:
                    break
                
                with cols[i]:
                    # Determine button style based on answer status
                    answer_key = f"question_{q_index}"
                    has_answer = bool(st.session_state.get('test_answers', {}).get(answer_key))
                    is_current = q_index == current_q
                    
                    if is_current:
                        button_type = "primary"
                        label = f"**{q_index + 1}**"
                    elif has_answer:
                        button_type = "secondary"
                        label = f"✓ {q_index + 1}"
                    else:
                        button_type = None
                        label = str(q_index + 1)
                    
                    if st.button(
                        label, 
                        key=f"nav_q_{q_index}",
                        type=button_type,
                        use_container_width=True
                    ):
                        st.session_state['current_question_index'] = q_index
                        st.rerun()
        
        # Get current question index from session state or use provided
        return st.session_state.get('current_question_index', current_q)
    
    def _render_question(self, question: Dict[str, Any], question_index: int):
        """Render individual question"""
        st.subheader(f"Question {question_index + 1}")
        
        # Question text
        st.markdown(f"### {question['question_text']}")
        
        # Answer input based on question type
        answer_key = f"question_{question_index}"
        current_answer = st.session_state.get('test_answers', {}).get(answer_key, '')
        
        if question['question_type'] == 'multiple_choice':
            self._render_multiple_choice_question(question, answer_key, current_answer)
        elif question['question_type'] == 'true_false':
            self._render_true_false_question(question, answer_key, current_answer)
        else:
            st.error(f"Unsupported question type: {question['question_type']}")
        
        # Save answer button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("💾 Save Answer", key=f"save_{question_index}", use_container_width=True):
                self._save_current_answer(answer_key)
    
    def _render_multiple_choice_question(self, question: Dict[str, Any], answer_key: str, current_answer: str):
        """Render multiple choice question"""
        options = question.get('options', [])
        
        # Find current selection index
        try:
            current_index = options.index(current_answer) if current_answer in options else None
        except ValueError:
            current_index = None
        
        # Radio buttons for options
        selected_option = st.radio(
            "Select your answer:",
            options,
            index=current_index,
            key=f"radio_{answer_key}"
        )
        
        # Update session state
        if selected_option:
            if 'test_answers' not in st.session_state:
                st.session_state['test_answers'] = {}
            st.session_state['test_answers'][answer_key] = selected_option
    
    def _render_true_false_question(self, question: Dict[str, Any], answer_key: str, current_answer: str):
        """Render true/false question"""
        # Radio buttons for True/False
        options = ['True', 'False']
        current_index = None
        
        if current_answer in options:
            current_index = options.index(current_answer)
        
        selected_option = st.radio(
            "Select your answer:",
            options,
            index=current_index,
            key=f"tf_radio_{answer_key}"
        )
        
        # Update session state
        if selected_option:
            if 'test_answers' not in st.session_state:
                st.session_state['test_answers'] = {}
            st.session_state['test_answers'][answer_key] = selected_option
    
    def _save_current_answer(self, answer_key: str):
        """Save current answer to database"""
        try:
            # Get current attempt info
            attempt_info = st.session_state['current_attempt']
            attempt_id = attempt_info['attempt_id']
            
            user_data = self.session_manager.get_user_info()
            student_id = user_data.get('user_id')
            
            # Update attempt with current answers
            updates = {
                'answers': st.session_state.get('test_answers', {})
            }
            
            result = self.student_service.update_test_attempt(
                attempt_id, student_id, updates
            )
            
            if result['success']:
                st.success("✅ Answer saved!")
            else:
                st.error("Failed to save answer.")
                
        except Exception as e:
            st.error(f"Error saving answer: {str(e)}")
    
    def _render_action_buttons(self, attempt: TestAttempt, student_id: str, 
                             questions: List[Dict[str, Any]], current_question: int):
        """Render navigation and action buttons"""
        st.divider()
        
        # Navigation buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        
        with col1:
            if current_question > 0:
                if st.button("⬅️ Previous", use_container_width=True):
                    st.session_state['current_question_index'] = current_question - 1
                    st.rerun()
            else:
                st.button("⬅️ Previous", disabled=True, use_container_width=True)
        
        with col2:
            if current_question < len(questions) - 1:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state['current_question_index'] = current_question + 1
                    st.rerun()
            else:
                st.button("Next ➡️", disabled=True, use_container_width=True)
        
        with col3:
            if st.button("💾 Save All", use_container_width=True):
                self._save_all_answers(attempt, student_id)
        
        with col4:
            if st.button("📋 Review", use_container_width=True):
                self._show_review_modal(questions)
        
        with col5:
            if st.button("📤 Submit Test", type="primary", use_container_width=True):
                self._handle_test_submission(attempt, student_id, questions)
    
    def _save_all_answers(self, attempt: TestAttempt, student_id: str):
        """Save all current answers"""
        try:
            updates = {
                'answers': st.session_state.get('test_answers', {}),
                'current_question': st.session_state.get('current_question_index', 0)
            }
            
            result = self.student_service.update_test_attempt(
                attempt.attempt_id, student_id, updates
            )
            
            if result['success']:
                st.success("✅ All answers saved!")
            else:
                st.error("Failed to save answers.")
                
        except Exception as e:
            st.error(f"Error saving answers: {str(e)}")
    
    def _show_review_modal(self, questions: List[Dict[str, Any]]):
        """Show test review modal"""
        with st.expander("📋 Test Review", expanded=True):
            st.markdown("### Answer Summary")
            
            answers = st.session_state.get('test_answers', {})
            answered_count = 0
            
            for i, question in enumerate(questions):
                answer_key = f"question_{i}"
                answer = answers.get(answer_key, '')
                
                if answer:
                    answered_count += 1
                    status = "✅"
                else:
                    status = "❌"
                
                st.markdown(f"{status} **Question {i + 1}:** {answer or 'Not answered'}")
            
            # Summary
            total_questions = len(questions)
            unanswered = total_questions - answered_count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Questions", total_questions)
            with col2:
                st.metric("Answered", answered_count)
            with col3:
                st.metric("Unanswered", unanswered)
            
            if unanswered > 0:
                st.warning(f"⚠️ You have {unanswered} unanswered questions.")
                st.markdown("**Unanswered questions will be marked as incorrect.**")
    
    def _handle_test_submission(self, attempt: TestAttempt, student_id: str, questions: List[Dict[str, Any]]):
        """Handle test submission with confirmation"""
        answers = st.session_state.get('test_answers', {})
        total_questions = len(questions)
        answered_count = len([a for a in answers.values() if a])
        unanswered_count = total_questions - answered_count
        
        # Show submission confirmation
        if 'confirm_submission' not in st.session_state:
            st.session_state['confirm_submission'] = False
        
        if not st.session_state['confirm_submission']:
            st.warning("⚠️ Are you sure you want to submit your test?")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Submission Summary")
                st.markdown(f"- **Total Questions:** {total_questions}")
                st.markdown(f"- **Answered:** {answered_count}")
                st.markdown(f"- **Unanswered:** {unanswered_count}")
                
                if unanswered_count > 0:
                    st.error(f"⚠️ {unanswered_count} questions will be marked as incorrect!")
            
            with col2:
                st.markdown("### ⚠️ Important")
                st.markdown("""
                - Once submitted, you cannot change your answers
                - Unanswered questions will be marked as incorrect
                - Your score will be calculated immediately
                - This action cannot be undone
                """)
            
            # Confirmation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Submit Test", type="primary", use_container_width=True):
                    st.session_state['confirm_submission'] = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    return
        else:
            # Actually submit the test
            try:
                with st.spinner("Submitting your test..."):
                    result = self.student_service.submit_test_attempt(
                        attempt.attempt_id, student_id, answers
                    )
                
                if result['success']:
                    st.success("🎉 Test submitted successfully!")
                    
                    # Show grading results if available
                    if result.get('graded'):
                        st.success(f"✅ Auto-graded: {result['score']:.1f}% ({result['correct_answers']}/{result['total_questions']} correct)")
                        if result.get('passed'):
                            st.balloons()
                    
                    # Clear session state
                    if 'current_attempt' in st.session_state:
                        del st.session_state['current_attempt']
                    if 'test_answers' in st.session_state:
                        del st.session_state['test_answers']
                    if 'current_question_index' in st.session_state:
                        del st.session_state['current_question_index']
                    
                    # Navigate to results with specific attempt
                    st.session_state['show_result_for_attempt'] = attempt.attempt_id
                    st.markdown("Redirecting to results...")
                    time.sleep(2)
                    st.session_state['selected_page'] = 'Test Results'
                    st.rerun()
                else:
                    st.error("Failed to submit test. Please try again.")
                    
            except Exception as e:
                st.error(f"Error submitting test: {str(e)}")
    
    def _auto_submit_test(self, attempt: TestAttempt, student_id: str):
        """Auto-submit test when time expires"""
        try:
            answers = st.session_state.get('test_answers', {})
            
            result = self.student_service.submit_test_attempt(
                attempt.attempt_id, student_id, answers
            )
            
            if result['success']:
                st.success("⏰ Test auto-submitted due to time expiration.")
                
                # Clear session state
                if 'current_attempt' in st.session_state:
                    del st.session_state['current_attempt']
                if 'test_answers' in st.session_state:
                    del st.session_state['test_answers']
                
                # Navigate to results
                time.sleep(2)
                st.session_state['selected_page'] = 'Test Results'
                st.rerun()
            else:
                st.error("Failed to auto-submit test.")
                
        except Exception as e:
            st.error(f"Error auto-submitting test: {str(e)}")
    
    def _get_mock_questions(self, test_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock questions for testing"""
        questions = []
        question_ids = test_data.get('question_ids', [])
        
        for i, question_id in enumerate(question_ids):
            if i % 2 == 0:  # Multiple choice
                question = {
                    'question_number': i + 1,
                    'question_id': question_id,
                    'question_text': f'Sample multiple choice question {i + 1}: What is the correct answer?',
                    'question_type': 'multiple_choice',
                    'options': [
                        f'Option A for question {i + 1}',
                        f'Option B for question {i + 1}',
                        f'Option C for question {i + 1}',
                        f'Option D for question {i + 1}'
                    ]
                }
            else:  # True/False
                question = {
                    'question_number': i + 1,
                    'question_id': question_id,
                    'question_text': f'Sample true/false question {i + 1}: This statement is correct.',
                    'question_type': 'true_false',
                    'options': ['True', 'False']
                }
            
            questions.append(question)
        
        return questions


def render_test_taking_page():
    """Render the test taking page"""
    page = TestTakingPage()
    page.render()


if __name__ == "__main__":
    render_test_taking_page()