"""
Question Edit Page for QuizGenius MVP
Allows instructors to edit individual questions with real-time preview
Implements Step 4.1.2: Question Editing (US-2.4.2 - 5 points)
"""

import streamlit as st
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.question_storage_service import QuestionStorageService, QuestionStorageError
from services.question_processor import QuestionProcessor, ProcessedQuestion
from utils.session_manager import SessionManager


class QuestionEditPage:
    """Question editing page for instructors"""
    
    def __init__(self):
        """Initialize question edit page"""
        self.session_manager = SessionManager()
        
        # Try to initialize services
        try:
            self.storage_service = QuestionStorageService()
            self.processor = QuestionProcessor()
            self.storage_available = True
        except Exception as e:
            st.error(f"Services not available: {e}")
            self.storage_service = None
            self.processor = None
            self.storage_available = False
        
    def render(self):
        """Render the question edit page"""
        st.title("✏️ Edit Question")
        st.markdown("Modify question content with real-time preview and validation.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to edit questions.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'instructor':
            st.error("Only instructors can edit questions.")
            return
            
        # Get question to edit
        question_data = self._get_question_to_edit()
        
        if not question_data:
            self._render_no_question_state()
            return
            
        # Main editing interface
        self._render_editing_interface(question_data, user_data)
        
    def _get_question_to_edit(self) -> Optional[Dict[str, Any]]:
        """Get the question to edit from session state or URL params"""
        # Check if question was passed from question review page
        if 'edit_question' in st.session_state:
            return st.session_state['edit_question']
            
        # Check URL parameters (if implemented)
        query_params = st.experimental_get_query_params()
        if 'question_id' in query_params:
            question_id = query_params['question_id'][0]
            return self._load_question_by_id(question_id)
            
        return None
        
    def _load_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Load question by ID from storage"""
        if not self.storage_available:
            return None
            
        try:
            question = self.storage_service.get_question(question_id)
            return question
        except Exception as e:
            st.error(f"Failed to load question: {str(e)}")
            return None
            
    def _render_no_question_state(self):
        """Render state when no question is selected for editing"""
        st.info("📝 No question selected for editing.")
        st.markdown("""
        **To edit a question:**
        1. Go to Question Management
        2. Find the question you want to edit
        3. Click the "Edit" button
        """)
        
        if st.button("📋 Go to Question Management", use_container_width=True):
            st.session_state['selected_page'] = 'Question Management'
            st.rerun()
            
    def _render_editing_interface(self, question_data: Dict[str, Any], user_data: Dict[str, Any]):
        """Render the main editing interface"""
        st.subheader("📝 Question Editor")
        
        # Initialize editing state
        if 'editing_question' not in st.session_state:
            st.session_state['editing_question'] = question_data.copy()
            st.session_state['original_question'] = question_data.copy()
            st.session_state['has_changes'] = False
            
        # Create two columns: editor and preview
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self._render_question_editor()
            
        with col2:
            self._render_question_preview()
            
        # Action buttons
        self._render_action_buttons(user_data)
        
    def _render_question_editor(self):
        """Render the question editing form"""
        st.markdown("### ✏️ Edit Question")
        
        current_question = st.session_state['editing_question']
        question_type = current_question.get('QuestionType', 'multiple_choice')
        
        # Question text editing
        st.markdown("**Question Text:**")
        new_question_text = st.text_area(
            "Question Text",
            value=current_question.get('QuestionText', ''),
            height=100,
            key="edit_question_text",
            label_visibility="collapsed",
            help="Enter the main question text"
        )
        
        # Update question text if changed
        if new_question_text != current_question.get('QuestionText', ''):
            st.session_state['editing_question']['QuestionText'] = new_question_text
            st.session_state['has_changes'] = True
            
        # Question type selection (allow changing type)
        st.markdown("**Question Type:**")
        new_question_type = st.selectbox(
            "Question Type",
            options=['multiple_choice', 'true_false'],
            index=0 if question_type == 'multiple_choice' else 1,
            format_func=lambda x: "Multiple Choice" if x == 'multiple_choice' else "True/False",
            key="edit_question_type",
            label_visibility="collapsed"
        )
        
        # Update question type if changed
        if new_question_type != question_type:
            st.session_state['editing_question']['QuestionType'] = new_question_type
            st.session_state['has_changes'] = True
            # Reset answers when type changes
            if new_question_type == 'multiple_choice':
                st.session_state['editing_question']['Options'] = ['', '', '', '']
                st.session_state['editing_question']['CorrectAnswer'] = ''
            else:
                st.session_state['editing_question']['CorrectAnswer'] = 'True'
                if 'Options' in st.session_state['editing_question']:
                    del st.session_state['editing_question']['Options']
            
        # Render type-specific editors
        if new_question_type == 'multiple_choice':
            self._render_multiple_choice_editor()
        else:
            self._render_true_false_editor()
            
        # Additional metadata editing
        self._render_metadata_editor()
        
    def _render_multiple_choice_editor(self):
        """Render multiple choice specific editing components"""
        st.markdown("**Answer Options:**")
        
        current_question = st.session_state['editing_question']
        options = current_question.get('Options', ['', '', '', ''])
        correct_answer = current_question.get('CorrectAnswer', '')
        
        # Ensure we have at least 4 options
        while len(options) < 4:
            options.append('')
            
        new_options = []
        
        # Edit each option
        for i in range(4):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                option_value = st.text_input(
                    f"Option {chr(65+i)}",
                    value=options[i] if i < len(options) else '',
                    key=f"edit_option_{i}",
                    placeholder=f"Enter option {chr(65+i)}"
                )
                new_options.append(option_value)
                
            with col2:
                # Correct answer selection
                is_correct = st.checkbox(
                    "Correct",
                    value=options[i] == correct_answer if i < len(options) else False,
                    key=f"edit_correct_{i}",
                    help=f"Mark option {chr(65+i)} as correct"
                )
                
                if is_correct:
                    st.session_state['editing_question']['CorrectAnswer'] = option_value
                    
        # Update options if changed
        if new_options != options:
            st.session_state['editing_question']['Options'] = new_options
            st.session_state['has_changes'] = True
            
        # Validation
        self._validate_multiple_choice_options(new_options)
        
    def _render_true_false_editor(self):
        """Render true/false specific editing components"""
        st.markdown("**Correct Answer:**")
        
        current_question = st.session_state['editing_question']
        current_answer = current_question.get('CorrectAnswer', 'True')
        
        # Convert to boolean for radio button
        current_bool = current_answer in ['True', True, 'true', 1]
        
        answer_choice = st.radio(
            "Select the correct answer:",
            options=[True, False],
            index=0 if current_bool else 1,
            format_func=lambda x: "True" if x else "False",
            key="edit_tf_answer",
            horizontal=True
        )
        
        # Update answer if changed
        new_answer = 'True' if answer_choice else 'False'
        if new_answer != str(current_answer):
            st.session_state['editing_question']['CorrectAnswer'] = new_answer
            st.session_state['has_changes'] = True
            
    def _render_metadata_editor(self):
        """Render metadata editing components"""
        st.markdown("**Additional Settings:**")
        
        current_question = st.session_state['editing_question']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Difficulty level
            current_difficulty = current_question.get('DifficultyLevel', 'medium')
            new_difficulty = st.selectbox(
                "Difficulty Level",
                options=['easy', 'medium', 'hard'],
                index=['easy', 'medium', 'hard'].index(current_difficulty) if current_difficulty in ['easy', 'medium', 'hard'] else 1,
                key="edit_difficulty"
            )
            
            if new_difficulty != current_difficulty:
                st.session_state['editing_question']['DifficultyLevel'] = new_difficulty
                st.session_state['has_changes'] = True
                
        with col2:
            # Topic
            current_topic = current_question.get('Topic', '')
            new_topic = st.text_input(
                "Topic",
                value=current_topic,
                key="edit_topic",
                placeholder="Enter question topic"
            )
            
            if new_topic != current_topic:
                st.session_state['editing_question']['Topic'] = new_topic
                st.session_state['has_changes'] = True
                
    def _validate_multiple_choice_options(self, options: List[str]):
        """Validate multiple choice options"""
        # Check for empty options
        empty_options = [i for i, opt in enumerate(options) if not opt.strip()]
        if empty_options:
            st.warning(f"⚠️ Empty options: {', '.join([chr(65+i) for i in empty_options])}")
            
        # Check for duplicate options
        non_empty_options = [opt.strip() for opt in options if opt.strip()]
        if len(non_empty_options) != len(set(non_empty_options)):
            st.warning("⚠️ Duplicate options detected")
            
        # Check if correct answer is set
        correct_answer = st.session_state['editing_question'].get('CorrectAnswer', '')
        if correct_answer not in options:
            st.warning("⚠️ No correct answer selected")
            
    def _render_question_preview(self):
        """Render real-time question preview"""
        st.markdown("### 👁️ Live Preview")
        
        current_question = st.session_state['editing_question']
        question_text = current_question.get('QuestionText', '')
        question_type = current_question.get('QuestionType', 'multiple_choice')
        
        if not question_text.strip():
            st.info("📝 Question preview will appear here as you type...")
            return
            
        # Preview container
        with st.container():
            st.markdown("---")
            
            # Question type indicator
            if question_type == 'multiple_choice':
                st.markdown("🔤 **Multiple Choice Question**")
            else:
                st.markdown("✅ **True/False Question**")
                
            # Question text
            st.markdown(f"**Question:** {question_text}")
            
            # Answer options preview
            if question_type == 'multiple_choice':
                options = current_question.get('Options', [])
                correct_answer = current_question.get('CorrectAnswer', '')
                
                st.markdown("**Options:**")
                for i, option in enumerate(options):
                    if option.strip():
                        is_correct = option == correct_answer
                        prefix = "✅" if is_correct else "  "
                        st.markdown(f"{prefix} **{chr(65+i)}.** {option}")
                        
            else:
                correct_answer = current_question.get('CorrectAnswer', 'True')
                st.markdown(f"**Correct Answer:** ✅ {correct_answer}")
                
            # Metadata preview
            difficulty = current_question.get('DifficultyLevel', 'medium')
            topic = current_question.get('Topic', 'General')
            
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"**Difficulty:** {difficulty.title()}")
            with col2:
                st.caption(f"**Topic:** {topic}")
                
            st.markdown("---")
            
        # Quality assessment
        self._render_quality_assessment()
        
    def _render_quality_assessment(self):
        """Render real-time quality assessment"""
        st.markdown("**📊 Quality Assessment**")
        
        current_question = st.session_state['editing_question']
        
        # Basic quality checks
        quality_score = 0
        issues = []
        suggestions = []
        
        # Question text quality
        question_text = current_question.get('QuestionText', '').strip()
        if len(question_text) < 10:
            issues.append("Question text is too short")
        elif len(question_text) > 200:
            issues.append("Question text is very long")
        else:
            quality_score += 2
            
        # Question type specific checks
        question_type = current_question.get('QuestionType', 'multiple_choice')
        
        if question_type == 'multiple_choice':
            options = current_question.get('Options', [])
            non_empty_options = [opt for opt in options if opt.strip()]
            
            if len(non_empty_options) < 2:
                issues.append("Need at least 2 answer options")
            elif len(non_empty_options) < 4:
                suggestions.append("Consider adding more answer options")
                quality_score += 1
            else:
                quality_score += 2
                
            # Check correct answer
            correct_answer = current_question.get('CorrectAnswer', '')
            if correct_answer not in options or not correct_answer.strip():
                issues.append("No correct answer selected")
            else:
                quality_score += 2
                
        else:  # true_false
            correct_answer = current_question.get('CorrectAnswer', '')
            if correct_answer in ['True', 'False']:
                quality_score += 2
            else:
                issues.append("Invalid true/false answer")
                
        # Topic and difficulty
        if current_question.get('Topic', '').strip():
            quality_score += 1
        else:
            suggestions.append("Add a topic for better organization")
            
        # Display assessment
        max_score = 7
        quality_percentage = (quality_score / max_score) * 100
        
        # Quality indicator
        if quality_percentage >= 80:
            st.success(f"✅ Quality Score: {quality_score}/{max_score} ({quality_percentage:.0f}%)")
        elif quality_percentage >= 60:
            st.warning(f"⚠️ Quality Score: {quality_score}/{max_score} ({quality_percentage:.0f}%)")
        else:
            st.error(f"❌ Quality Score: {quality_score}/{max_score} ({quality_percentage:.0f}%)")
            
        # Show issues and suggestions
        if issues:
            st.error("**Issues to fix:**")
            for issue in issues:
                st.error(f"• {issue}")
                
        if suggestions:
            st.info("**Suggestions:**")
            for suggestion in suggestions:
                st.info(f"• {suggestion}")
                
    def _render_action_buttons(self, user_data: Dict[str, Any]):
        """Render action buttons for save, cancel, etc."""
        st.markdown("---")
        st.subheader("💾 Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Save button
            save_disabled = not st.session_state.get('has_changes', False)
            if st.button("💾 Save Changes", 
                        disabled=save_disabled, 
                        use_container_width=True,
                        type="primary"):
                self._save_question(user_data)
                
        with col2:
            # Cancel button
            if st.button("❌ Cancel", use_container_width=True):
                self._cancel_editing()
                
        with col3:
            # Reset button
            reset_disabled = not st.session_state.get('has_changes', False)
            if st.button("🔄 Reset", 
                        disabled=reset_disabled, 
                        use_container_width=True):
                self._reset_changes()
                
        with col4:
            # Preview test button
            if st.button("🧪 Test Question", use_container_width=True):
                self._test_question()
                
        # Show changes indicator
        if st.session_state.get('has_changes', False):
            st.info("📝 You have unsaved changes")
        else:
            st.success("✅ No unsaved changes")
            
    def _save_question(self, user_data: Dict[str, Any]):
        """Save the edited question"""
        try:
            current_question = st.session_state['editing_question']
            
            # Validate question before saving
            validation_result = self._validate_question(current_question)
            if not validation_result['valid']:
                st.error(f"Cannot save question: {validation_result['message']}")
                return
                
            # Update metadata
            current_question['UpdatedAt'] = datetime.now().isoformat()
            current_question['UpdatedBy'] = user_data.get('user_id')
            
            # Save to storage if available
            if self.storage_available:
                try:
                    # Prepare updates (exclude ID and creation fields)
                    updates = {k: v for k, v in current_question.items() 
                              if k not in ['QuestionID', 'CreatedAt', 'created_by']}
                    updates['UpdatedBy'] = user_data.get('user_id')
                    
                    result = self.storage_service.update_question(
                        current_question['QuestionID'],
                        updates
                    )
                    
                    if result.get('success'):
                        st.success("✅ Question saved successfully!")
                        st.session_state['has_changes'] = False
                        st.session_state['original_question'] = current_question.copy()
                        
                        # Optionally redirect back to question management
                        if st.button("📋 Back to Question Management"):
                            st.session_state['selected_page'] = 'Question Management'
                            # Clean up edit session
                            if 'edit_question' in st.session_state:
                                del st.session_state['edit_question']
                            if 'editing_question' in st.session_state:
                                del st.session_state['editing_question']
                            st.rerun()
                    else:
                        st.error("Failed to save question to database")
                        
                except Exception as e:
                    st.error(f"Error saving question: {str(e)}")
                    
            else:
                # Update in session state
                if 'current_questions' in st.session_state:
                    questions = st.session_state['current_questions']
                    for i, q in enumerate(questions):
                        if q.question_id == current_question['QuestionID']:
                            # Update the question object
                            questions[i].question_text = current_question['QuestionText']
                            questions[i].question_type = current_question['QuestionType']
                            questions[i].correct_answer = current_question['CorrectAnswer']
                            if 'Options' in current_question:
                                questions[i].options = current_question['Options']
                            questions[i].difficulty_level = current_question.get('DifficultyLevel', 'medium')
                            questions[i].topic = current_question.get('Topic', '')
                            break
                            
                st.success("✅ Question updated in session!")
                st.session_state['has_changes'] = False
                
        except Exception as e:
            st.error(f"Error saving question: {str(e)}")
            
    def _validate_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Validate question data before saving"""
        # Check required fields
        if not question.get('QuestionText', '').strip():
            return {'valid': False, 'message': 'Question text is required'}
            
        question_type = question.get('QuestionType', '')
        if question_type not in ['multiple_choice', 'true_false']:
            return {'valid': False, 'message': 'Invalid question type'}
            
        # Type-specific validation
        if question_type == 'multiple_choice':
            options = question.get('Options', [])
            non_empty_options = [opt for opt in options if opt.strip()]
            
            if len(non_empty_options) < 2:
                return {'valid': False, 'message': 'Multiple choice questions need at least 2 options'}
                
            correct_answer = question.get('CorrectAnswer', '')
            if not correct_answer.strip() or correct_answer not in options:
                return {'valid': False, 'message': 'Valid correct answer must be selected'}
                
        else:  # true_false
            correct_answer = question.get('CorrectAnswer', '')
            if correct_answer not in ['True', 'False']:
                return {'valid': False, 'message': 'True/False answer must be True or False'}
                
        return {'valid': True, 'message': 'Question is valid'}
        
    def _cancel_editing(self):
        """Cancel editing and return to question management"""
        # Clean up session state
        if 'edit_question' in st.session_state:
            del st.session_state['edit_question']
        if 'editing_question' in st.session_state:
            del st.session_state['editing_question']
        if 'original_question' in st.session_state:
            del st.session_state['original_question']
        if 'has_changes' in st.session_state:
            del st.session_state['has_changes']
            
        # Navigate back
        st.session_state['selected_page'] = 'Question Management'
        st.rerun()
        
    def _reset_changes(self):
        """Reset changes to original question"""
        if 'original_question' in st.session_state:
            st.session_state['editing_question'] = st.session_state['original_question'].copy()
            st.session_state['has_changes'] = False
            st.rerun()
            
    def _test_question(self):
        """Test the question in a modal or expandable section"""
        st.markdown("### 🧪 Question Test")
        
        current_question = st.session_state['editing_question']
        question_type = current_question.get('QuestionType', 'multiple_choice')
        
        with st.expander("📝 Take Test Question", expanded=True):
            st.markdown(f"**Question:** {current_question.get('QuestionText', '')}")
            
            if question_type == 'multiple_choice':
                options = current_question.get('Options', [])
                non_empty_options = [(i, opt) for i, opt in enumerate(options) if opt.strip()]
                
                if non_empty_options:
                    selected_option = st.radio(
                        "Select your answer:",
                        options=[f"{chr(65+i)}. {opt}" for i, opt in non_empty_options],
                        key="test_question_answer"
                    )
                    
                    if st.button("Check Answer"):
                        # Extract the option text
                        selected_text = selected_option.split('. ', 1)[1]
                        correct_answer = current_question.get('CorrectAnswer', '')
                        
                        if selected_text == correct_answer:
                            st.success("✅ Correct!")
                        else:
                            st.error(f"❌ Incorrect. The correct answer is: {correct_answer}")
                            
            else:  # true_false
                test_answer = st.radio(
                    "Select your answer:",
                    options=['True', 'False'],
                    key="test_tf_answer"
                )
                
                if st.button("Check Answer"):
                    correct_answer = current_question.get('CorrectAnswer', 'True')
                    
                    if test_answer == correct_answer:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Incorrect. The correct answer is: {correct_answer}")


def render_question_edit_page():
    """Render the question edit page"""
    page = QuestionEditPage()
    page.render()


if __name__ == "__main__":
    render_question_edit_page()