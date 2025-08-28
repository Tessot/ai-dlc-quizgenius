# QuizGenius MVP - Streamlit Integration Patterns

## Overview
This document provides detailed integration patterns for the QuizGenius MVP Streamlit application, including page structure, navigation, component reusability, and user interaction patterns.

---

## 1. Streamlit Page Structure and Navigation

### Application Entry Point
```python
# app.py - Main application entry point
import streamlit as st
from utils.auth import StreamlitAuth
from utils.session_manager import SessionManager

def main():
    """Main application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="QuizGenius MVP",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session manager
    session_manager = SessionManager()
    session_manager.initialize_session()
    
    # Check authentication
    auth = StreamlitAuth()
    
    if not auth.check_authentication():
        # Show login page
        show_login_page()
    else:
        # Show main application based on user role
        show_main_application()

def show_login_page():
    """Display login interface"""
    st.title("🎓 QuizGenius MVP")
    st.markdown("### Welcome to QuizGenius - AI-Powered Assessment Tool")
    
    # Login form
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👨‍🏫 Instructor Login")
            instructor_username = st.text_input("Username", key="inst_user")
            instructor_password = st.text_input("Password", type="password", key="inst_pass")
            instructor_login = st.form_submit_button("Login as Instructor")
            
        with col2:
            st.subheader("👨‍🎓 Student Login")
            student_username = st.text_input("Username", key="stud_user")
            student_password = st.text_input("Password", type="password", key="stud_pass")
            student_login = st.form_submit_button("Login as Student")
    
    # Handle login attempts
    auth = StreamlitAuth()
    
    if instructor_login and instructor_username and instructor_password:
        if auth.authenticate_user(instructor_username, instructor_password, "instructor"):
            st.success("✅ Instructor login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid instructor credentials")
    
    if student_login and student_username and student_password:
        if auth.authenticate_user(student_username, student_password, "student"):
            st.success("✅ Student login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid student credentials")

def show_main_application():
    """Display main application interface"""
    
    # Sidebar navigation
    with st.sidebar:
        show_navigation_sidebar()
    
    # Main content area
    show_main_content()

if __name__ == "__main__":
    main()
```

### Navigation Sidebar Pattern
```python
# utils/navigation.py
import streamlit as st
from typing import Dict, List

class NavigationManager:
    
    def __init__(self):
        self.instructor_pages = {
            "dashboard": {"title": "📊 Dashboard", "icon": "📊"},
            "pdf_upload": {"title": "📄 Upload PDF", "icon": "📄"},
            "question_generation": {"title": "🤖 Generate Questions", "icon": "🤖"},
            "question_management": {"title": "✏️ Manage Questions", "icon": "✏️"},
            "test_creation": {"title": "📝 Create Tests", "icon": "📝"},
            "results_viewing": {"title": "📈 View Results", "icon": "📈"}
        }
        
        self.student_pages = {
            "dashboard": {"title": "🏠 Dashboard", "icon": "🏠"},
            "test_taking": {"title": "📝 Take Tests", "icon": "📝"},
            "results_viewing": {"title": "📊 My Results", "icon": "📊"}
        }
    
    def show_navigation_sidebar(self):
        """Display navigation sidebar based on user role"""
        
        # User info section
        self._show_user_info()
        
        st.sidebar.markdown("---")
        
        # Navigation menu
        user_role = st.session_state.get("user_role")
        
        if user_role == "instructor":
            self._show_instructor_navigation()
        elif user_role == "student":
            self._show_student_navigation()
        
        st.sidebar.markdown("---")
        
        # Logout button
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            self._handle_logout()
    
    def _show_user_info(self):
        """Display user information in sidebar"""
        username = st.session_state.get("username", "Unknown")
        user_role = st.session_state.get("user_role", "").title()
        
        st.sidebar.markdown(f"**👤 {username}**")
        st.sidebar.markdown(f"*{user_role}*")
    
    def _show_instructor_navigation(self):
        """Show instructor navigation menu"""
        st.sidebar.markdown("### 📚 Instructor Menu")
        
        current_page = st.session_state.get("current_page", "dashboard")
        
        for page_key, page_info in self.instructor_pages.items():
            if st.sidebar.button(
                page_info["title"], 
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if current_page == page_key else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
    
    def _show_student_navigation(self):
        """Show student navigation menu"""
        st.sidebar.markdown("### 🎓 Student Menu")
        
        current_page = st.session_state.get("current_page", "dashboard")
        
        for page_key, page_info in self.student_pages.items():
            if st.sidebar.button(
                page_info["title"], 
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if current_page == page_key else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
    
    def _handle_logout(self):
        """Handle user logout"""
        from utils.auth import StreamlitAuth
        auth = StreamlitAuth()
        auth.logout()
        st.rerun()
```

### Page Router Pattern
```python
# utils/page_router.py
import streamlit as st
from pages import (
    instructor_dashboard, student_dashboard, pdf_upload,
    question_generation, question_management, test_creation,
    test_taking, results_viewing
)

class PageRouter:
    
    def __init__(self):
        self.instructor_routes = {
            "dashboard": instructor_dashboard.show_page,
            "pdf_upload": pdf_upload.show_page,
            "question_generation": question_generation.show_page,
            "question_management": question_management.show_page,
            "test_creation": test_creation.show_page,
            "results_viewing": results_viewing.show_instructor_results
        }
        
        self.student_routes = {
            "dashboard": student_dashboard.show_page,
            "test_taking": test_taking.show_page,
            "results_viewing": results_viewing.show_student_results
        }
    
    def route_to_page(self):
        """Route to appropriate page based on current state"""
        current_page = st.session_state.get("current_page", "dashboard")
        user_role = st.session_state.get("user_role")
        
        if user_role == "instructor":
            if current_page in self.instructor_routes:
                self.instructor_routes[current_page]()
            else:
                st.error(f"Page '{current_page}' not found for instructors")
                
        elif user_role == "student":
            if current_page in self.student_routes:
                self.student_routes[current_page]()
            else:
                st.error(f"Page '{current_page}' not found for students")
        
        else:
            st.error("Invalid user role")
```

---

## 2. Session State Management Patterns

### Session State Structure
```python
# utils/session_manager.py
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

class SessionManager:
    
    def __init__(self):
        self.default_state = {
            # Authentication
            "authenticated": False,
            "user_role": None,
            "user_id": None,
            "username": None,
            "login_time": None,
            
            # Navigation
            "current_page": "dashboard",
            "previous_page": None,
            "page_history": [],
            
            # Instructor workflow
            "uploaded_pdf": None,
            "extracted_text": None,
            "generated_questions": [],
            "current_test": None,
            "editing_question_id": None,
            
            # Student workflow
            "current_test_session": None,
            "question_responses": {},
            "test_start_time": None,
            "current_question_index": 0,
            "test_completed": False,
            
            # UI state
            "show_success_message": False,
            "success_message": "",
            "show_error_message": False,
            "error_message": "",
            "processing": False,
            "processing_message": ""
        }
    
    def initialize_session(self):
        """Initialize session state with default values"""
        for key, value in self.default_state.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def clear_session(self):
        """Clear all session state"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        self.initialize_session()
    
    def set_page(self, page_name: str):
        """Set current page and update history"""
        if st.session_state.current_page != page_name:
            st.session_state.previous_page = st.session_state.current_page
            st.session_state.page_history.append(st.session_state.current_page)
            st.session_state.current_page = page_name
            
            # Keep history limited
            if len(st.session_state.page_history) > 10:
                st.session_state.page_history = st.session_state.page_history[-10:]
    
    def show_success_message(self, message: str):
        """Display success message"""
        st.session_state.show_success_message = True
        st.session_state.success_message = message
    
    def show_error_message(self, message: str):
        """Display error message"""
        st.session_state.show_error_message = True
        st.session_state.error_message = message
    
    def clear_messages(self):
        """Clear all messages"""
        st.session_state.show_success_message = False
        st.session_state.success_message = ""
        st.session_state.show_error_message = False
        st.session_state.error_message = ""
    
    def set_processing(self, processing: bool, message: str = ""):
        """Set processing state"""
        st.session_state.processing = processing
        st.session_state.processing_message = message
    
    def get_user_context(self) -> Dict[str, Any]:
        """Get current user context"""
        return {
            "user_id": st.session_state.get("user_id"),
            "username": st.session_state.get("username"),
            "user_role": st.session_state.get("user_role"),
            "authenticated": st.session_state.get("authenticated", False)
        }
```

### State Persistence Pattern
```python
# utils/state_persistence.py
import json
import os
from typing import Dict, Any
from datetime import datetime

class StatePersistence:
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def save_user_session(self, user_id: str, session_data: Dict[str, Any]):
        """Save user session data"""
        session_file = os.path.join(self.data_dir, f"session_{user_id}.json")
        
        # Add timestamp
        session_data["last_saved"] = datetime.now().isoformat()
        
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving session: {e}")
    
    def load_user_session(self, user_id: str) -> Dict[str, Any]:
        """Load user session data"""
        session_file = os.path.join(self.data_dir, f"session_{user_id}.json")
        
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading session: {e}")
        
        return {}
    
    def clear_user_session(self, user_id: str):
        """Clear user session data"""
        session_file = os.path.join(self.data_dir, f"session_{user_id}.json")
        
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except Exception as e:
                print(f"Error clearing session: {e}")
```

---

## 3. File Upload and Processing Patterns

### PDF Upload Component
```python
# components/pdf_upload.py
import streamlit as st
from utils.pdf_processor import BedrockDataAutomation
from utils.session_manager import SessionManager

class PDFUploadComponent:
    
    def __init__(self):
        self.processor = BedrockDataAutomation()
        self.session_manager = SessionManager()
    
    def show_upload_interface(self):
        """Display PDF upload interface"""
        
        st.subheader("📄 Upload PDF Document")
        st.markdown("Upload a text-based PDF to generate quiz questions.")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a text-based PDF document (max 10MB)"
        )
        
        if uploaded_file is not None:
            self._handle_file_upload(uploaded_file)
    
    def _handle_file_upload(self, uploaded_file):
        """Handle PDF file upload and processing"""
        
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.1f} KB",
            "File type": uploaded_file.type
        }
        
        with st.expander("📋 File Details", expanded=True):
            for key, value in file_details.items():
                st.write(f"**{key}:** {value}")
        
        # Validation
        if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
            st.error("❌ File too large. Please upload a file smaller than 10MB.")
            return
        
        if uploaded_file.type != "application/pdf":
            st.error("❌ Invalid file type. Please upload a PDF file.")
            return
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Process PDF", use_container_width=True, type="primary"):
                self._process_pdf(uploaded_file)
    
    def _process_pdf(self, uploaded_file):
        """Process uploaded PDF"""
        
        # Show processing indicator
        with st.spinner("🔄 Processing PDF... This may take a moment."):
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Upload validation
            status_text.text("📤 Validating upload...")
            progress_bar.progress(20)
            
            # Step 2: Text extraction
            status_text.text("📖 Extracting text from PDF...")
            progress_bar.progress(40)
            
            result = self.processor.extract_text_from_pdf(uploaded_file, uploaded_file.name)
            
            if not result["success"]:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ PDF processing failed: {result['error']}")
                return
            
            # Step 3: Content validation
            status_text.text("✅ Validating content quality...")
            progress_bar.progress(80)
            
            # Step 4: Complete
            status_text.text("✅ Processing complete!")
            progress_bar.progress(100)
            
            # Store results in session state
            st.session_state.uploaded_pdf = uploaded_file.name
            st.session_state.extracted_text = result["extracted_text"]
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Show results
            self._show_processing_results(result)
    
    def _show_processing_results(self, result):
        """Display PDF processing results"""
        
        st.success("✅ PDF processed successfully!")
        
        # Content preview
        with st.expander("📖 Extracted Content Preview", expanded=False):
            preview_text = result["extracted_text"][:1000]
            if len(result["extracted_text"]) > 1000:
                preview_text += "..."
            
            st.text_area(
                "Content Preview",
                preview_text,
                height=200,
                disabled=True
            )
        
        # Quality metrics
        quality_metrics = result.get("quality_metrics", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Word Count", result.get("word_count", 0))
        
        with col2:
            st.metric("Characters", result.get("character_count", 0))
        
        with col3:
            quality_score = quality_metrics.get("quality_score", 0)
            st.metric("Quality Score", f"{quality_score}%")
        
        with col4:
            suitable = quality_metrics.get("suitable_for_questions", False)
            st.metric("Suitable for Questions", "✅ Yes" if suitable else "❌ No")
        
        # Quality issues (if any)
        issues = quality_metrics.get("issues", [])
        if issues:
            with st.expander("⚠️ Content Quality Issues", expanded=False):
                for issue in issues:
                    st.warning(f"• {issue}")
        
        # Next steps
        if quality_metrics.get("suitable_for_questions", False):
            st.info("🎯 Content is ready for question generation! Navigate to 'Generate Questions' to continue.")
        else:
            st.warning("⚠️ Content quality may affect question generation. Consider uploading a different PDF.")
```

### Progress Tracking Pattern
```python
# components/progress_tracker.py
import streamlit as st
import time
from typing import List, Callable

class ProgressTracker:
    
    def __init__(self):
        self.progress_bar = None
        self.status_text = None
        self.current_step = 0
        self.total_steps = 0
    
    def start_progress(self, steps: List[str]):
        """Start progress tracking"""
        self.total_steps = len(steps)
        self.current_step = 0
        
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        
        return self
    
    def update_step(self, step_name: str, delay: float = 0.5):
        """Update progress to next step"""
        self.current_step += 1
        progress = self.current_step / self.total_steps
        
        self.progress_bar.progress(progress)
        self.status_text.text(f"🔄 {step_name}...")
        
        if delay > 0:
            time.sleep(delay)
    
    def complete(self, success_message: str = "✅ Process completed!"):
        """Complete progress tracking"""
        self.progress_bar.progress(1.0)
        self.status_text.text(success_message)
        
        time.sleep(1)
        
        # Clean up
        self.progress_bar.empty()
        self.status_text.empty()
    
    def error(self, error_message: str):
        """Handle error during progress"""
        self.status_text.text(f"❌ {error_message}")
        time.sleep(2)
        
        # Clean up
        self.progress_bar.empty()
        self.status_text.empty()

# Usage example
def process_with_progress(operation: Callable, steps: List[str]):
    """Execute operation with progress tracking"""
    
    tracker = ProgressTracker()
    tracker.start_progress(steps)
    
    try:
        for i, step in enumerate(steps):
            tracker.update_step(step)
            
            # Execute step operation
            if hasattr(operation, f'step_{i+1}'):
                getattr(operation, f'step_{i+1}')()
        
        tracker.complete()
        return True
        
    except Exception as e:
        tracker.error(str(e))
        return False
```

---

## 4. Form Handling and Data Persistence Patterns

### Form Component Pattern
```python
# components/form_components.py
import streamlit as st
from typing import Dict, Any, Optional, List

class FormComponent:
    
    def __init__(self, form_key: str):
        self.form_key = form_key
        self.form_data = {}
    
    def create_question_form(self, question_data: Optional[Dict] = None) -> Optional[Dict]:
        """Create question editing form"""
        
        with st.form(key=self.form_key):
            st.subheader("✏️ Edit Question")
            
            # Question text
            question_text = st.text_area(
                "Question Text",
                value=question_data.get("question", "") if question_data else "",
                height=100,
                help="Enter the question text"
            )
            
            # Question type
            question_type = st.selectbox(
                "Question Type",
                options=["multiple_choice", "true_false"],
                index=0 if not question_data else 
                      (0 if question_data.get("type") == "multiple_choice" else 1),
                help="Select the type of question"
            )
            
            # Dynamic form based on question type
            if question_type == "multiple_choice":
                form_data = self._create_multiple_choice_form(question_data)
            else:
                form_data = self._create_true_false_form(question_data)
            
            # Form buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                save_button = st.form_submit_button("💾 Save", type="primary")
            
            with col2:
                preview_button = st.form_submit_button("👁️ Preview")
            
            with col3:
                cancel_button = st.form_submit_button("❌ Cancel")
            
            # Handle form submission
            if save_button and question_text.strip():
                form_data.update({
                    "question": question_text,
                    "type": question_type
                })
                return {"action": "save", "data": form_data}
            
            elif preview_button and question_text.strip():
                form_data.update({
                    "question": question_text,
                    "type": question_type
                })
                return {"action": "preview", "data": form_data}
            
            elif cancel_button:
                return {"action": "cancel", "data": None}
            
            elif save_button and not question_text.strip():
                st.error("❌ Question text is required")
        
        return None
    
    def _create_multiple_choice_form(self, question_data: Optional[Dict]) -> Dict:
        """Create multiple choice specific form fields"""
        
        st.markdown("#### Answer Options")
        
        options = {}
        correct_answer = None
        
        # Get existing data
        existing_options = question_data.get("options", {}) if question_data else {}
        existing_correct = question_data.get("correct_answer", "A") if question_data else "A"
        
        # Create option inputs
        for option_key in ["A", "B", "C", "D"]:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                option_text = st.text_input(
                    f"Option {option_key}",
                    value=existing_options.get(option_key, ""),
                    key=f"{self.form_key}_option_{option_key}"
                )
                options[option_key] = option_text
            
            with col2:
                is_correct = st.checkbox(
                    "Correct",
                    value=(existing_correct == option_key),
                    key=f"{self.form_key}_correct_{option_key}"
                )
                if is_correct:
                    correct_answer = option_key
        
        # Explanation
        explanation = st.text_area(
            "Explanation (Optional)",
            value=question_data.get("explanation", "") if question_data else "",
            height=80,
            help="Explain why this answer is correct"
        )
        
        return {
            "options": options,
            "correct_answer": correct_answer,
            "explanation": explanation
        }
    
    def _create_true_false_form(self, question_data: Optional[Dict]) -> Dict:
        """Create true/false specific form fields"""
        
        st.markdown("#### Answer")
        
        # Get existing data
        existing_answer = question_data.get("correct_answer", True) if question_data else True
        
        correct_answer = st.radio(
            "Correct Answer",
            options=[True, False],
            format_func=lambda x: "True" if x else "False",
            index=0 if existing_answer else 1,
            key=f"{self.form_key}_tf_answer"
        )
        
        # Explanation
        explanation = st.text_area(
            "Explanation (Optional)",
            value=question_data.get("explanation", "") if question_data else "",
            height=80,
            help="Explain why this answer is correct"
        )
        
        return {
            "correct_answer": correct_answer,
            "explanation": explanation
        }

class TestCreationForm:
    
    def __init__(self):
        self.form_key = "test_creation_form"
    
    def show_test_creation_form(self, available_questions: List[Dict]) -> Optional[Dict]:
        """Show test creation form"""
        
        with st.form(key=self.form_key):
            st.subheader("📝 Create New Test")
            
            # Test metadata
            test_title = st.text_input(
                "Test Title",
                placeholder="Enter test title...",
                help="Give your test a descriptive title"
            )
            
            test_description = st.text_area(
                "Test Description (Optional)",
                placeholder="Describe what this test covers...",
                height=100
            )
            
            # Question selection
            st.markdown("#### Select Questions")
            
            if not available_questions:
                st.warning("⚠️ No questions available. Please generate questions first.")
                return None
            
            selected_questions = []
            
            # Group questions by type
            mc_questions = [q for q in available_questions if q.get("type") == "multiple_choice"]
            tf_questions = [q for q in available_questions if q.get("type") == "true_false"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Multiple Choice Questions**")
                for i, question in enumerate(mc_questions):
                    if st.checkbox(
                        f"Q{i+1}: {question['question'][:50]}...",
                        key=f"mc_q_{i}",
                        value=False
                    ):
                        selected_questions.append(question)
            
            with col2:
                st.markdown("**True/False Questions**")
                for i, question in enumerate(tf_questions):
                    if st.checkbox(
                        f"Q{i+1}: {question['statement'][:50]}...",
                        key=f"tf_q_{i}",
                        value=False
                    ):
                        selected_questions.append(question)
            
            # Test settings
            st.markdown("#### Test Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                time_limit = st.number_input(
                    "Time Limit (minutes)",
                    min_value=0,
                    max_value=180,
                    value=30,
                    help="Set to 0 for no time limit"
                )
            
            with col2:
                shuffle_questions = st.checkbox(
                    "Shuffle Questions",
                    value=True,
                    help="Randomize question order for each student"
                )
            
            # Submit button
            submitted = st.form_submit_button("🚀 Create Test", type="primary")
            
            if submitted:
                if not test_title.strip():
                    st.error("❌ Test title is required")
                    return None
                
                if not selected_questions:
                    st.error("❌ Please select at least one question")
                    return None
                
                return {
                    "title": test_title,
                    "description": test_description,
                    "questions": selected_questions,
                    "time_limit": time_limit if time_limit > 0 else None,
                    "shuffle_questions": shuffle_questions,
                    "created_by": st.session_state.get("user_id"),
                    "status": "draft"
                }
        
        return None
```

### Data Persistence Pattern
```python
# utils/data_persistence.py
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class DataManager:
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.data_dir,
            os.path.join(self.data_dir, "users"),
            os.path.join(self.data_dir, "questions"),
            os.path.join(self.data_dir, "tests"),
            os.path.join(self.data_dir, "results"),
            os.path.join(self.data_dir, "uploads")
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def save_questions(self, user_id: str, questions: List[Dict]) -> bool:
        """Save generated questions"""
        try:
            # Add metadata to each question
            for question in questions:
                if "id" not in question:
                    question["id"] = str(uuid.uuid4())
                question["created_by"] = user_id
                question["created_at"] = datetime.now().isoformat()
            
            # Save to file
            filename = f"questions_{user_id}_{int(datetime.now().timestamp())}.json"
            filepath = os.path.join(self.data_dir, "questions", filename)
            
            with open(filepath, 'w') as f:
                json.dump(questions, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving questions: {e}")
            return False
    
    def load_user_questions(self, user_id: str) -> List[Dict]:
        """Load all questions for a user"""
        questions = []
        questions_dir = os.path.join(self.data_dir, "questions")
        
        try:
            for filename in os.listdir(questions_dir):
                if filename.startswith(f"questions_{user_id}_") and filename.endswith(".json"):
                    filepath = os.path.join(questions_dir, filename)
                    
                    with open(filepath, 'r') as f:
                        file_questions = json.load(f)
                        questions.extend(file_questions)
            
            # Sort by creation date (newest first)
            questions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
        except Exception as e:
            print(f"Error loading questions: {e}")
        
        return questions
    
    def save_test(self, test_data: Dict) -> Optional[str]:
        """Save test configuration"""
        try:
            # Generate test ID
            test_id = str(uuid.uuid4())
            test_data["id"] = test_id
            test_data["created_at"] = datetime.now().isoformat()
            
            # Save to file
            filename = f"test_{test_id}.json"
            filepath = os.path.join(self.data_dir, "tests", filename)
            
            with open(filepath, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            return test_id
            
        except Exception as e:
            print(f"Error saving test: {e}")
            return None
    
    def load_available_tests(self) -> List[Dict]:
        """Load all available tests"""
        tests = []
        tests_dir = os.path.join(self.data_dir, "tests")
        
        try:
            for filename in os.listdir(tests_dir):
                if filename.startswith("test_") and filename.endswith(".json"):
                    filepath = os.path.join(tests_dir, filename)
                    
                    with open(filepath, 'r') as f:
                        test_data = json.load(f)
                        
                        # Only include published tests for students
                        if test_data.get("status") == "published":
                            tests.append(test_data)
            
            # Sort by creation date (newest first)
            tests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
        except Exception as e:
            print(f"Error loading tests: {e}")
        
        return tests
    
    def save_test_result(self, result_data: Dict) -> bool:
        """Save test result"""
        try:
            # Generate result ID
            result_id = str(uuid.uuid4())
            result_data["id"] = result_id
            result_data["completed_at"] = datetime.now().isoformat()
            
            # Save to file
            filename = f"result_{result_id}.json"
            filepath = os.path.join(self.data_dir, "results", filename)
            
            with open(filepath, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving result: {e}")
            return False
    
    def load_user_results(self, user_id: str) -> List[Dict]:
        """Load test results for a user"""
        results = []
        results_dir = os.path.join(self.data_dir, "results")
        
        try:
            for filename in os.listdir(results_dir):
                if filename.startswith("result_") and filename.endswith(".json"):
                    filepath = os.path.join(results_dir, filename)
                    
                    with open(filepath, 'r') as f:
                        result_data = json.load(f)
                        
                        if result_data.get("student_id") == user_id:
                            results.append(result_data)
            
            # Sort by completion date (newest first)
            results.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
            
        except Exception as e:
            print(f"Error loading results: {e}")
        
        return results
```

---

## 5. Component Reusability Patterns

### Reusable UI Components
```python
# components/ui_components.py
import streamlit as st
from typing import List, Dict, Optional, Callable

class UIComponents:
    
    @staticmethod
    def show_question_card(question: Dict, show_answer: bool = False, 
                          edit_callback: Optional[Callable] = None,
                          delete_callback: Optional[Callable] = None):
        """Display a question card with optional actions"""
        
        with st.container():
            # Question header
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                question_type = question.get("type", "unknown")
                type_emoji = "🔤" if question_type == "multiple_choice" else "✅"
                st.markdown(f"**{type_emoji} {question_type.replace('_', ' ').title()}**")
            
            with col2:
                if edit_callback and st.button("✏️ Edit", key=f"edit_{question.get('id')}"):
                    edit_callback(question)
            
            with col3:
                if delete_callback and st.button("🗑️ Delete", key=f"delete_{question.get('id')}"):
                    delete_callback(question)
            
            # Question content
            if question_type == "multiple_choice":
                st.markdown(f"**Q:** {question.get('question', '')}")
                
                options = question.get("options", {})
                correct_answer = question.get("correct_answer", "")
                
                for option_key, option_text in options.items():
                    if show_answer and option_key == correct_answer:
                        st.markdown(f"✅ **{option_key}.** {option_text}")
                    else:
                        st.markdown(f"   **{option_key}.** {option_text}")
            
            else:  # true_false
                st.markdown(f"**Statement:** {question.get('statement', '')}")
                
                if show_answer:
                    correct = question.get("correct_answer", True)
                    st.markdown(f"**Answer:** {'✅ True' if correct else '❌ False'}")
            
            # Explanation
            if show_answer and question.get("explanation"):
                with st.expander("💡 Explanation"):
                    st.markdown(question["explanation"])
            
            st.markdown("---")
    
    @staticmethod
    def show_test_card(test: Dict, take_test_callback: Optional[Callable] = None,
                      view_results_callback: Optional[Callable] = None):
        """Display a test card"""
        
        with st.container():
            # Test header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 📝 {test.get('title', 'Untitled Test')}")
                
                if test.get("description"):
                    st.markdown(test["description"])
            
            with col2:
                if take_test_callback:
                    if st.button("🚀 Take Test", key=f"take_{test.get('id')}", type="primary"):
                        take_test_callback(test)
                
                if view_results_callback:
                    if st.button("📊 View Results", key=f"results_{test.get('id')}"):
                        view_results_callback(test)
            
            # Test metadata
            col1, col2, col3 = st.columns(3)
            
            with col1:
                question_count = len(test.get("questions", []))
                st.metric("Questions", question_count)
            
            with col2:
                time_limit = test.get("time_limit")
                if time_limit:
                    st.metric("Time Limit", f"{time_limit} min")
                else:
                    st.metric("Time Limit", "No limit")
            
            with col3:
                created_at = test.get("created_at", "")
                if created_at:
                    from datetime import datetime
                    try:
                        date = datetime.fromisoformat(created_at).strftime("%Y-%m-%d")
                        st.metric("Created", date)
                    except:
                        st.metric("Created", "Unknown")
            
            st.markdown("---")
    
    @staticmethod
    def show_result_summary(result: Dict):
        """Display test result summary"""
        
        with st.container():
            # Score display
            score = result.get("score", 0)
            total_questions = result.get("total_questions", 0)
            percentage = result.get("percentage", 0)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Score", f"{score}/{total_questions}")
            
            with col2:
                st.metric("Percentage", f"{percentage:.1f}%")
            
            with col3:
                time_taken = result.get("time_taken_minutes", 0)
                st.metric("Time Taken", f"{time_taken:.1f} min")
            
            with col4:
                completed_at = result.get("completed_at", "")
                if completed_at:
                    from datetime import datetime
                    try:
                        date = datetime.fromisoformat(completed_at).strftime("%Y-%m-%d")
                        st.metric("Completed", date)
                    except:
                        st.metric("Completed", "Unknown")
            
            # Performance indicator
            if percentage >= 80:
                st.success(f"🎉 Excellent! You scored {percentage:.1f}%")
            elif percentage >= 60:
                st.info(f"👍 Good job! You scored {percentage:.1f}%")
            else:
                st.warning(f"📚 Keep studying! You scored {percentage:.1f}%")
    
    @staticmethod
    def show_loading_spinner(message: str = "Loading..."):
        """Show loading spinner with message"""
        with st.spinner(message):
            return st.empty()  # Return placeholder for cleanup
    
    @staticmethod
    def show_confirmation_dialog(message: str, confirm_key: str) -> bool:
        """Show confirmation dialog"""
        st.warning(message)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Confirm", key=f"{confirm_key}_confirm", type="primary"):
                return True
        
        with col2:
            if st.button("❌ Cancel", key=f"{confirm_key}_cancel"):
                return False
        
        return False
```

---

## Summary

This Streamlit integration patterns document provides:

1. **Complete Page Structure** - Navigation, routing, and session management
2. **File Upload Patterns** - PDF processing with progress tracking
3. **Form Handling** - Reusable form components for questions and tests
4. **Data Persistence** - Local JSON-based data storage patterns
5. **UI Components** - Reusable cards and display components
6. **State Management** - Session state patterns and persistence
7. **Progress Tracking** - User feedback during long operations
8. **Error Handling** - User-friendly error display patterns

The patterns support rapid development while maintaining code reusability and user experience consistency across the entire QuizGenius MVP application.