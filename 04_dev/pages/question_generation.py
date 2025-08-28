"""
Question Generation Page for QuizGenius MVP
Handles AI-powered question generation from PDF content with progress tracking
"""

import streamlit as st
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from services.question_generation_service import QuestionGenerationService, QuestionGenerationRequest
from utils.session_manager import SessionManager


class QuestionGenerationPage:
    """Question Generation page for instructors"""
    
    def __init__(self):
        """Initialize question generation page"""
        self.question_service = QuestionGenerationService()
        self.session_manager = SessionManager()
        
    def render(self):
        """Render the question generation page"""
        st.title("🤖 Generate Quiz Questions")
        st.markdown("Use AI to automatically generate quiz questions from your PDF content.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to generate questions.")
            return
            
        # Check if we have content to work with
        if not self._has_content_for_generation():
            st.warning("No content available for question generation. Please upload a PDF first.")
            if st.button("📄 Upload PDF"):
                st.session_state['page'] = 'pdf_upload'
                st.rerun()
            return
            
        # Get content data
        extracted_text = st.session_state.get('extracted_text', '')
        document_data = st.session_state.get('current_document', {})
        validation_result = st.session_state.get('validation_result')
        
        # Render generation interface
        self._render_document_summary(document_data)
        self._render_generation_controls()
        self._render_generated_questions()
        
    def _has_content_for_generation(self) -> bool:
        """Check if there's content available for question generation"""
        return (
            'extracted_text' in st.session_state and 
            st.session_state['extracted_text'] and
            'current_document' in st.session_state
        )
        
    def _render_document_summary(self, document_data: Dict[str, Any]):
        """Render document summary"""
        if not document_data:
            return
            
        st.subheader("📄 Source Document")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("File", document_data.get('filename', 'Unknown'))
        with col2:
            st.metric("Words", document_data.get('word_count', 0))
        with col3:
            st.metric("Quality", f"{document_data.get('quality_score', 0):.1f}/10")
        with col4:
            suitable = "✅ Yes" if document_data.get('is_suitable', False) else "❌ No"
            st.metric("Suitable", suitable)
            
        if not document_data.get('is_suitable', False):
            st.warning("⚠️ This document may not be ideal for question generation. Consider uploading a different document for better results.")
            
    def _render_generation_controls(self):
        """Render question generation controls"""
        st.subheader("⚙️ Generation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Question types
            st.write("**Question Types:**")
            generate_mc = st.checkbox("Multiple Choice Questions", value=True)
            generate_tf = st.checkbox("True/False Questions", value=True)
            
            if not generate_mc and not generate_tf:
                st.error("Please select at least one question type.")
                return
                
        with col2:
            # Question quantities
            st.write("**Quantities:**")
            if generate_mc:
                mc_count = st.number_input(
                    "Multiple Choice Questions",
                    min_value=1, max_value=20, value=5,
                    help="Number of multiple choice questions to generate"
                )
            else:
                mc_count = 0
                
            if generate_tf:
                tf_count = st.number_input(
                    "True/False Questions", 
                    min_value=1, max_value=20, value=5,
                    help="Number of true/false questions to generate"
                )
            else:
                tf_count = 0
                
        # Advanced settings
        with st.expander("🔧 Advanced Settings", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                difficulty = st.selectbox(
                    "Difficulty Level",
                    ["beginner", "intermediate", "advanced"],
                    index=1,
                    help="Target difficulty level for generated questions"
                )
                
            with col2:
                topic_focus = st.text_input(
                    "Topic Focus (Optional)",
                    placeholder="e.g., machine learning, photosynthesis",
                    help="Focus questions on specific topics (leave blank for general)"
                )
                
        # Generation button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Generate Questions", type="primary", use_container_width=True):
                self._generate_questions(
                    mc_count=mc_count,
                    tf_count=tf_count,
                    difficulty=difficulty,
                    topic_focus=topic_focus.strip() if topic_focus.strip() else None
                )
                
    def _generate_questions(self, mc_count: int, tf_count: int, 
                          difficulty: str, topic_focus: Optional[str]):
        """Generate questions using the AI service"""
        try:
            # Get content and user data
            extracted_text = st.session_state['extracted_text']
            user_data = self.session_manager.get_user_info()
            document_data = st.session_state.get('current_document', {})
            
            # Create progress indicators
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
            # Step 1: Prepare generation request
            status_text.text("📋 Preparing generation request...")
            progress_bar.progress(10)
            
            generation_request = QuestionGenerationRequest(
                content=extracted_text,
                question_types=[],
                num_questions=mc_count + tf_count,
                difficulty_level=difficulty,
                topics=[topic_focus] if topic_focus else [],
                user_id=user_data.get('user_id'),
                document_id=document_data.get('document_id')
            )
            
            # Add question types based on counts
            if mc_count > 0:
                generation_request.question_types.append('multiple_choice')
            if tf_count > 0:
                generation_request.question_types.append('true_false')
                
            # Step 2: Generate questions
            status_text.text("🤖 Generating questions with AI...")
            progress_bar.progress(30)
            
            # Generate multiple choice questions
            generated_questions = []
            
            if mc_count > 0:
                status_text.text("🤖 Generating multiple choice questions...")
                progress_bar.progress(50)
                
                mc_request = QuestionGenerationRequest(
                    content=extracted_text,
                    question_types=['multiple_choice'],
                    num_questions=mc_count,
                    difficulty_level=difficulty,
                    topics=[topic_focus] if topic_focus else [],
                    user_id=user_data.get('user_id'),
                    document_id=document_data.get('document_id')
                )
                
                mc_result = self.question_service.generate_questions(mc_request)
                if mc_result.success:
                    generated_questions.extend(mc_result.generated_questions)
                else:
                    error_msg = mc_result.errors[0] if mc_result.errors else "Unknown error"
                    st.error(f"Failed to generate multiple choice questions: {error_msg}")
                    
            if tf_count > 0:
                status_text.text("🤖 Generating true/false questions...")
                progress_bar.progress(75)
                
                tf_request = QuestionGenerationRequest(
                    content=extracted_text,
                    question_types=['true_false'],
                    num_questions=tf_count,
                    difficulty_level=difficulty,
                    topics=[topic_focus] if topic_focus else [],
                    user_id=user_data.get('user_id'),
                    document_id=document_data.get('document_id')
                )
                
                tf_result = self.question_service.generate_questions(tf_request)
                if tf_result.success:
                    generated_questions.extend(tf_result.generated_questions)
                else:
                    error_msg = tf_result.errors[0] if tf_result.errors else "Unknown error"
                    st.error(f"Failed to generate true/false questions: {error_msg}")
                    
            # Step 3: Process and store results
            status_text.text("💾 Processing generated questions...")
            progress_bar.progress(90)
            
            if generated_questions:
                # Store questions in session
                generation_session = {
                    'session_id': str(uuid.uuid4()),
                    'timestamp': datetime.now().isoformat(),
                    'document_id': document_data.get('document_id'),
                    'questions': generated_questions,
                    'settings': {
                        'mc_count': mc_count,
                        'tf_count': tf_count,
                        'difficulty': difficulty,
                        'topic_focus': topic_focus
                    },
                    'statistics': {
                        'total_requested': mc_count + tf_count,
                        'total_generated': len(generated_questions),
                        'mc_generated': len([q for q in generated_questions if q.question_type == 'multiple_choice']),
                        'tf_generated': len([q for q in generated_questions if q.question_type == 'true_false'])
                    }
                }
                
                # Store in session state
                if 'question_sessions' not in st.session_state:
                    st.session_state['question_sessions'] = []
                st.session_state['question_sessions'].append(generation_session)
                st.session_state['current_questions'] = generated_questions
                
                # Complete
                status_text.text("✅ Questions generated successfully!")
                progress_bar.progress(100)
                
                # Clear progress indicators after a moment
                import time
                time.sleep(1)
                progress_container.empty()
                
                # Show success message
                st.success(f"🎉 Successfully generated {len(generated_questions)} questions!")
                
                # Auto-scroll to results
                st.rerun()
                
            else:
                st.error("No questions were generated. Please try again with different settings.")
                
        except Exception as e:
            st.error(f"Error generating questions: {str(e)}")
            
    def _render_generated_questions(self):
        """Render generated questions"""
        if 'current_questions' not in st.session_state or not st.session_state['current_questions']:
            return
            
        questions = st.session_state['current_questions']
        
        st.subheader(f"📝 Generated Questions ({len(questions)})")
        
        # Statistics
        mc_count = len([q for q in questions if q.question_type == 'multiple_choice'])
        tf_count = len([q for q in questions if q.question_type == 'true_false'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Questions", len(questions))
        with col2:
            st.metric("Multiple Choice", mc_count)
        with col3:
            st.metric("True/False", tf_count)
        with col4:
            avg_confidence = sum(q.confidence_score for q in questions) / len(questions) if questions else 0
            st.metric("Avg Confidence", f"{avg_confidence:.1f}")
            
        # Display questions
        for i, question in enumerate(questions, 1):
            self._render_question_card(question, i)
            
        # Action buttons
        st.markdown("---")
        self._render_question_actions()
        
    def _render_question_card(self, question, index: int):
        """Render a single question card"""
        # Question type icon
        type_icon = "🔤" if question.question_type == 'multiple_choice' else "✅"
        type_label = "Multiple Choice" if question.question_type == 'multiple_choice' else "True/False"
        
        with st.expander(f"{type_icon} Question {index}: {question.question_text[:60]}...", expanded=index <= 3):
            # Question header
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**Type:** {type_label}")
            with col2:
                st.write(f"**Difficulty:** {question.difficulty_level.title()}")
            with col3:
                st.write(f"**Confidence:** {question.confidence_score:.1f}")
                
            # Question text
            st.write("**Question:**")
            st.write(question.question_text)
            
            # Answer options
            if question.question_type == 'multiple_choice':
                st.write("**Answer Options:**")
                for j, option in enumerate(question.options, 1):
                    is_correct = option == question.correct_answer
                    prefix = "✅" if is_correct else "  "
                    st.write(f"{prefix} {chr(64+j)}. {option}")
                    
            else:  # true_false
                st.write("**Correct Answer:**")
                answer_text = "True" if question.correct_answer.lower() == 'true' else "False"
                st.write(f"✅ {answer_text}")
                
            # Additional info
            explanation = question.metadata.get('explanation', '')
            if explanation:
                st.write("**Explanation:**")
                st.write(explanation)
                
            # Question metadata
            with st.expander("📊 Question Details", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Question ID:** {question.question_id}")
                    created_at = question.metadata.get('created_at', 'Unknown')
                    st.write(f"**Generated:** {created_at}")
                with col2:
                    if question.topic:
                        st.write(f"**Topic:** {question.topic}")
                    if question.source_content:
                        st.write(f"**Source Text:** {question.source_content[:100]}...")
                        
    def _render_question_actions(self):
        """Render action buttons for generated questions"""
        st.subheader("🚀 Next Steps")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Generate More", use_container_width=True):
                # Clear current questions to show generation controls again
                if 'current_questions' in st.session_state:
                    del st.session_state['current_questions']
                st.rerun()
                
        with col2:
            if st.button("📝 Review & Edit", use_container_width=True):
                st.session_state['page'] = 'question_review'
                st.rerun()
                
        with col3:
            if st.button("💾 Save Questions", use_container_width=True):
                self._save_questions()
                
        with col4:
            if st.button("🧪 Create Test", type="primary", use_container_width=True):
                st.session_state['page'] = 'test_creation'
                st.rerun()
                
        # Export options
        with st.expander("📤 Export Options", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Export as Text", use_container_width=True):
                    self._export_questions_text()
            with col2:
                if st.button("📊 Export as JSON", use_container_width=True):
                    self._export_questions_json()
                    
    def _save_questions(self):
        """Save questions (placeholder for future DynamoDB integration)"""
        if 'current_questions' not in st.session_state:
            st.error("No questions to save.")
            return
            
        # For now, just show success message
        # In later phases, this will save to DynamoDB
        questions = st.session_state['current_questions']
        st.success(f"✅ {len(questions)} questions saved successfully!")
        st.info("💡 Questions are temporarily stored in your session. Full persistence will be available in the next phase.")
        
    def _export_questions_text(self):
        """Export questions as text format"""
        if 'current_questions' not in st.session_state:
            return
            
        questions = st.session_state['current_questions']
        text_content = self._format_questions_as_text(questions)
        
        st.download_button(
            label="📄 Download Text File",
            data=text_content,
            file_name=f"quiz_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
    def _export_questions_json(self):
        """Export questions as JSON format"""
        if 'current_questions' not in st.session_state:
            return
            
        import json
        questions = st.session_state['current_questions']
        
        # Convert questions to dict format
        questions_data = []
        for q in questions:
            question_dict = {
                'id': q.question_id,
                'type': q.question_type,
                'question': q.question_text,
                'correct_answer': q.correct_answer,
                'answer_options': q.options,
                'difficulty': q.difficulty,
                'confidence': q.confidence_score,
                'explanation': q.metadata.get('explanation', ''),
                'topic': q.topic,
                'created_at': q.metadata.get('created_at', datetime.now().isoformat())
            }
            questions_data.append(question_dict)
            
        json_content = json.dumps(questions_data, indent=2)
        
        st.download_button(
            label="📊 Download JSON File",
            data=json_content,
            file_name=f"quiz_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
    def _format_questions_as_text(self, questions) -> str:
        """Format questions as text"""
        content = f"Quiz Questions - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 60 + "\n\n"
        
        for i, q in enumerate(questions, 1):
            content += f"Question {i}: {q.question_text}\n"
            content += f"Type: {q.question_type.replace('_', ' ').title()}\n"
            content += f"Difficulty: {q.difficulty.title()}\n"
            
            if q.question_type == 'multiple_choice':
                content += "Options:\n"
                for j, option in enumerate(q.options, 1):
                    marker = "✓" if option == q.correct_answer else " "
                    content += f"  {chr(64+j)}. [{marker}] {option}\n"
            else:
                content += f"Correct Answer: {q.correct_answer}\n"
                
            explanation = q.metadata.get('explanation', '')
            if explanation:
                content += f"Explanation: {explanation}\n"
                
            content += f"Confidence: {q.confidence_score:.1f}\n"
            content += "-" * 40 + "\n\n"
            
        return content


def render_question_generation_page():
    """Render the question generation page"""
    page = QuestionGenerationPage()
    page.render()


if __name__ == "__main__":
    render_question_generation_page()