"""
Question Review Page for QuizGenius MVP
Allows instructors to review, edit, and manage generated questions
Implements Step 4.1.1: Question Review Interface (US-2.4.1 - 3 points)
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.question_storage_service import QuestionStorageService, QuestionStorageError
from utils.session_manager import SessionManager


class QuestionReviewPage:
    """Question Review page for instructors"""
    
    def __init__(self):
        """Initialize question review page"""
        self.session_manager = SessionManager()
        
        # Try to initialize storage service
        try:
            self.storage_service = QuestionStorageService()
            self.storage_available = True
        except Exception as e:
            st.error(f"Storage service not available: {e}")
            self.storage_service = None
            self.storage_available = False
        
    def render(self):
        """Render the question review page"""
        st.title("📝 Question Review & Management")
        st.markdown("Review, edit, and manage your generated questions before creating tests.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to review questions.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'instructor':
            st.error("Only instructors can review questions.")
            return
            
        # Check storage availability
        if not self.storage_available:
            st.warning("Question storage is not available. Using session data only.")
            self._render_session_questions()
            return
            
        # Main review interface
        self._render_question_management_interface(user_data)
        
    def _render_question_management_interface(self, user_data: Dict[str, Any]):
        """Render the main question management interface"""
        instructor_id = user_data.get('user_id')
        
        # Load questions
        questions = self._load_instructor_questions(instructor_id)
        
        if not questions:
            self._render_no_questions_state()
            return
            
        # Question management controls
        self._render_management_controls(questions)
        
        # Question list
        self._render_question_list(questions, instructor_id)
        
    def _render_session_questions(self):
        """Render questions from session state (fallback)"""
        if 'current_questions' in st.session_state and st.session_state['current_questions']:
            questions = st.session_state['current_questions']
            st.info(f"Showing {len(questions)} questions from your current session.")
            
            # Convert to display format
            display_questions = []
            for i, q in enumerate(questions):
                display_questions.append({
                    'QuestionID': q.question_id,
                    'QuestionText': q.question_text,
                    'QuestionType': q.question_type,
                    'CorrectAnswer': q.correct_answer,
                    'Options': q.options,
                    'DifficultyLevel': q.difficulty_level,
                    'Topic': q.topic,
                    'ConfidenceScore': q.confidence_score,
                    'CreatedAt': q.metadata.get('created_at', datetime.now().isoformat())
                })
            
            self._render_question_list(display_questions, 'session_user')
        else:
            self._render_no_questions_state()
            
    def _load_instructor_questions(self, instructor_id: str) -> List[Dict[str, Any]]:
        """Load questions for the instructor"""
        try:
            questions = self.storage_service.get_questions_by_instructor(instructor_id, limit=100)
            return questions
        except Exception as e:
            st.error(f"Failed to load questions: {str(e)}")
            return []
            
    def _render_no_questions_state(self):
        """Render state when no questions are available"""
        st.info("📭 No questions found.")
        st.markdown("""
        **To get started:**
        1. Upload a PDF document
        2. Generate questions from the content
        3. Return here to review and manage your questions
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Upload PDF", use_container_width=True):
                st.session_state['selected_page'] = 'PDF Upload'
                st.rerun()
        with col2:
            if st.button("🤖 Generate Questions", use_container_width=True):
                st.session_state['selected_page'] = 'Question Generation'
                st.rerun()
                
    def _render_management_controls(self, questions: List[Dict[str, Any]]):
        """Render question management controls"""
        st.subheader("📊 Question Overview")
        
        # Statistics
        total_questions = len(questions)
        mc_questions = len([q for q in questions if q.get('QuestionType') == 'multiple_choice'])
        tf_questions = len([q for q in questions if q.get('QuestionType') == 'true_false'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Questions", total_questions)
        with col2:
            st.metric("Multiple Choice", mc_questions)
        with col3:
            st.metric("True/False", tf_questions)
        with col4:
            avg_quality = sum(q.get('QualityScore', 0) for q in questions) / len(questions) if questions else 0
            st.metric("Avg Quality", f"{avg_quality:.1f}/10")
            
        # Filters and controls
        st.subheader("🔍 Filter & Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            question_type_filter = st.selectbox(
                "Filter by Type",
                ["All", "Multiple Choice", "True/False"],
                key="question_type_filter"
            )
            
        with col2:
            topic_options = ["All"] + list(set(q.get('Topic', 'Unknown') for q in questions))
            topic_filter = st.selectbox(
                "Filter by Topic",
                topic_options,
                key="topic_filter"
            )
            
        with col3:
            sort_by = st.selectbox(
                "Sort by",
                ["Created Date (Newest)", "Created Date (Oldest)", "Quality Score (High)", "Quality Score (Low)", "Question Type"],
                key="sort_by"
            )
            
        # Apply filters
        filtered_questions = self._apply_filters(questions, question_type_filter, topic_filter, sort_by)
        
        # Bulk actions
        if filtered_questions:
            st.markdown("**Bulk Actions:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📋 Select All Visible", use_container_width=True):
                    for q in filtered_questions:
                        st.session_state[f"select_{q['QuestionID']}"] = True
                    st.rerun()
                    
            with col2:
                if st.button("🔄 Clear Selection", use_container_width=True):
                    for q in filtered_questions:
                        if f"select_{q['QuestionID']}" in st.session_state:
                            del st.session_state[f"select_{q['QuestionID']}"]
                    st.rerun()
                    
            with col3:
                selected_count = sum(1 for q in filtered_questions if st.session_state.get(f"select_{q['QuestionID']}", False))
                if selected_count > 0:
                    if st.button(f"🗑️ Delete Selected ({selected_count})", use_container_width=True, type="secondary"):
                        self._handle_bulk_delete(filtered_questions)
                        
        # Store filtered questions for rendering
        st.session_state['filtered_questions'] = filtered_questions
        
    def _apply_filters(self, questions: List[Dict[str, Any]], type_filter: str, 
                      topic_filter: str, sort_by: str) -> List[Dict[str, Any]]:
        """Apply filters and sorting to questions"""
        filtered = questions.copy()
        
        # Type filter
        if type_filter == "Multiple Choice":
            filtered = [q for q in filtered if q.get('QuestionType') == 'multiple_choice']
        elif type_filter == "True/False":
            filtered = [q for q in filtered if q.get('QuestionType') == 'true_false']
            
        # Topic filter
        if topic_filter != "All":
            filtered = [q for q in filtered if q.get('Topic', 'Unknown') == topic_filter]
            
        # Sorting
        if sort_by == "Created Date (Newest)":
            filtered.sort(key=lambda x: x.get('CreatedAt', ''), reverse=True)
        elif sort_by == "Created Date (Oldest)":
            filtered.sort(key=lambda x: x.get('CreatedAt', ''))
        elif sort_by == "Quality Score (High)":
            filtered.sort(key=lambda x: x.get('QualityScore', 0), reverse=True)
        elif sort_by == "Quality Score (Low)":
            filtered.sort(key=lambda x: x.get('QualityScore', 0))
        elif sort_by == "Question Type":
            filtered.sort(key=lambda x: x.get('QuestionType', ''))
            
        return filtered
        
    def _render_question_list(self, questions: List[Dict[str, Any]], instructor_id: str):
        """Render the list of questions"""
        if 'filtered_questions' in st.session_state:
            questions = st.session_state['filtered_questions']
            
        if not questions:
            st.info("No questions match the current filters.")
            return
            
        st.subheader(f"📋 Questions ({len(questions)})")
        
        # Render each question
        for i, question in enumerate(questions):
            self._render_question_card(question, i, instructor_id)
            
    def _render_question_card(self, question: Dict[str, Any], index: int, instructor_id: str):
        """Render a single question card"""
        question_id = question.get('QuestionID', f'q_{index}')
        question_type = question.get('QuestionType', 'unknown')
        
        # Question type icon and color
        if question_type == 'multiple_choice':
            type_icon = "🔤"
            type_label = "Multiple Choice"
            type_color = "blue"
        else:
            type_icon = "✅"
            type_label = "True/False"
            type_color = "green"
            
        # Question card
        with st.expander(
            f"{type_icon} {question.get('QuestionText', 'Unknown Question')[:80]}...",
            expanded=index < 3  # Expand first 3 questions
        ):
            # Question header
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                # Selection checkbox
                selected = st.checkbox(
                    f"Select question",
                    key=f"select_{question_id}",
                    label_visibility="collapsed"
                )
                
            with col2:
                st.markdown(f"**Type:** {type_label}")
                
            with col3:
                difficulty = question.get('DifficultyLevel', 'Unknown').title()
                st.markdown(f"**Difficulty:** {difficulty}")
                
            with col4:
                quality_score = question.get('QualityScore', 0)
                st.markdown(f"**Quality:** {quality_score:.1f}/10")
                
            # Question content
            st.markdown("**Question:**")
            st.markdown(f"*{question.get('QuestionText', 'No question text')}*")
            
            # Answer options
            if question_type == 'multiple_choice':
                st.markdown("**Answer Options:**")
                options = question.get('Options', [])
                correct_answer = question.get('CorrectAnswer', '')
                
                for j, option in enumerate(options):
                    is_correct = option == correct_answer
                    prefix = "✅" if is_correct else "  "
                    st.markdown(f"{prefix} **{chr(65+j)}.** {option}")
                    
            else:  # true_false
                correct_answer = question.get('CorrectAnswer', 'Unknown')
                st.markdown(f"**Correct Answer:** ✅ {correct_answer}")
                
            # Additional metadata
            with st.expander("📊 Question Details", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Question ID:** {question_id}")
                    st.write(f"**Topic:** {question.get('Topic', 'Unknown')}")
                    confidence = question.get('ConfidenceScore', 0)
                    st.write(f"**Confidence:** {confidence:.2f}")
                    
                with col2:
                    created_at = question.get('CreatedAt', 'Unknown')[:19] if question.get('CreatedAt') else 'Unknown'
                    st.write(f"**Created:** {created_at}")
                    document_id = question.get('DocumentID', 'Unknown')
                    st.write(f"**Document:** {document_id[:8]}..." if len(document_id) > 8 else document_id)
                    
                # Processing info if available
                if question.get('ProcessedText'):
                    st.write("**Processing Applied:** ✅ Enhanced")
                    
            # Action buttons
            st.markdown("**Actions:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✏️ Edit", key=f"edit_{question_id}", use_container_width=True):
                    self._handle_edit_question(question)
                    
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{question_id}", use_container_width=True):
                    self._handle_delete_question(question, instructor_id)
                    
            with col3:
                if st.button("📋 Duplicate", key=f"duplicate_{question_id}", use_container_width=True):
                    self._handle_duplicate_question(question)
                    
            with col4:
                if st.button("📤 Export", key=f"export_{question_id}", use_container_width=True):
                    self._handle_export_question(question)
                    
    def _handle_edit_question(self, question: Dict[str, Any]):
        """Handle question editing"""
        st.session_state['edit_question'] = question
        st.session_state['selected_page'] = 'Question Edit'
        st.rerun()
        
    def _handle_delete_question(self, question: Dict[str, Any], instructor_id: str):
        """Handle single question deletion"""
        question_id = question.get('QuestionID')
        
        # Confirmation dialog
        if f"confirm_delete_{question_id}" not in st.session_state:
            st.session_state[f"confirm_delete_{question_id}"] = False
            
        if not st.session_state[f"confirm_delete_{question_id}"]:
            st.warning(f"⚠️ Are you sure you want to delete this question?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete", key=f"confirm_yes_{question_id}"):
                    st.session_state[f"confirm_delete_{question_id}"] = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key=f"confirm_no_{question_id}"):
                    return
        else:
            # Perform deletion
            try:
                if self.storage_available:
                    result = self.storage_service.delete_question(question_id, instructor_id)
                    if result.get('success'):
                        st.success("Question deleted successfully!")
                        # Clean up session state
                        if f"confirm_delete_{question_id}" in st.session_state:
                            del st.session_state[f"confirm_delete_{question_id}"]
                        st.rerun()
                    else:
                        st.error("Failed to delete question.")
                else:
                    # Remove from session questions
                    if 'current_questions' in st.session_state:
                        st.session_state['current_questions'] = [
                            q for q in st.session_state['current_questions'] 
                            if q.question_id != question_id
                        ]
                    st.success("Question removed from session!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error deleting question: {str(e)}")
                
    def _handle_duplicate_question(self, question: Dict[str, Any]):
        """Handle question duplication"""
        st.info("🔄 Question duplication will be available in a future update.")
        
    def _handle_export_question(self, question: Dict[str, Any]):
        """Handle single question export"""
        import json
        
        # Create export data
        export_data = {
            'question_id': question.get('QuestionID'),
            'question_text': question.get('QuestionText'),
            'question_type': question.get('QuestionType'),
            'correct_answer': question.get('CorrectAnswer'),
            'options': question.get('Options', []),
            'difficulty': question.get('DifficultyLevel'),
            'topic': question.get('Topic'),
            'quality_score': question.get('QualityScore'),
            'exported_at': datetime.now().isoformat()
        }
        
        # Create download
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name=f"question_{question.get('QuestionID', 'unknown')}.json",
            mime="application/json",
            key=f"download_{question.get('QuestionID')}"
        )
        
    def _handle_bulk_delete(self, questions: List[Dict[str, Any]]):
        """Handle bulk question deletion"""
        selected_questions = [
            q for q in questions 
            if st.session_state.get(f"select_{q['QuestionID']}", False)
        ]
        
        if not selected_questions:
            st.warning("No questions selected for deletion.")
            return
            
        # Confirmation
        if 'confirm_bulk_delete' not in st.session_state:
            st.session_state['confirm_bulk_delete'] = False
            
        if not st.session_state['confirm_bulk_delete']:
            st.warning(f"⚠️ Are you sure you want to delete {len(selected_questions)} questions?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete All"):
                    st.session_state['confirm_bulk_delete'] = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    return
        else:
            # Perform bulk deletion
            success_count = 0
            error_count = 0
            
            for question in selected_questions:
                try:
                    question_id = question.get('QuestionID')
                    if self.storage_available:
                        user_data = self.session_manager.get_user_info()
                        instructor_id = user_data.get('user_id')
                        result = self.storage_service.delete_question(question_id, instructor_id)
                        if result.get('success'):
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        # Remove from session
                        if 'current_questions' in st.session_state:
                            st.session_state['current_questions'] = [
                                q for q in st.session_state['current_questions'] 
                                if q.question_id != question_id
                            ]
                        success_count += 1
                        
                except Exception as e:
                    error_count += 1
                    
            # Show results
            if success_count > 0:
                st.success(f"Successfully deleted {success_count} questions!")
            if error_count > 0:
                st.error(f"Failed to delete {error_count} questions.")
                
            # Clean up
            st.session_state['confirm_bulk_delete'] = False
            st.rerun()


def render_question_review_page():
    """Render the question review page"""
    page = QuestionReviewPage()
    page.render()


if __name__ == "__main__":
    render_question_review_page()