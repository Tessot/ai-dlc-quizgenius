#!/usr/bin/env python3
"""
Test Results Page for QuizGenius MVP
Displays test results and detailed answer review for students
Implements Phase 5.2: Student Results Interface
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from services.auto_grading_service import AutoGradingService, AutoGradingError, TestResult, QuestionResult
from services.student_test_service import StudentTestService
from utils.session_manager import SessionManager


class TestResultsPage:
    """Test results page for students"""
    
    def __init__(self):
        """Initialize test results page"""
        self.session_manager = SessionManager()
        
        # Try to initialize services
        try:
            self.grading_service = AutoGradingService()
            self.student_service = StudentTestService()
            self.services_available = True
        except Exception as e:
            st.error(f"Results services not available: {e}")
            self.grading_service = None
            self.student_service = None
            self.services_available = False
    
    def render(self):
        """Render the test results page"""
        st.title("📊 Test Results")
        st.markdown("View your test results and detailed answer review.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to view test results.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'student':
            st.error("Only students can view test results.")
            return
        
        student_id = user_data.get('user_id')
        
        # Check services availability
        if not self.services_available:
            st.warning("Results services are not available. Please try again later.")
            return
        
        # Check if there's a specific result to show (from recent submission)
        if 'show_result_for_attempt' in st.session_state:
            attempt_id = st.session_state['show_result_for_attempt']
            del st.session_state['show_result_for_attempt']  # Clear it
            self._render_specific_result(attempt_id, student_id)
        else:
            # Show all results
            self._render_all_results(student_id)
    
    def _render_specific_result(self, attempt_id: str, student_id: str):
        """Render a specific test result (immediate results after submission)"""
        try:
            # Get the specific result
            result = self.grading_service.get_test_results(attempt_id, student_id)
            
            if not result:
                st.error("Test results not found.")
                return
            
            # Show immediate results
            st.success("🎉 Test submitted and graded successfully!")
            
            # Render the result
            self._render_test_result_card(result, expanded=True, show_details=True)
            
            # Navigation options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Take Another Test", use_container_width=True):
                    st.session_state['selected_page'] = 'Available Tests'
                    st.rerun()
            
            with col2:
                if st.button("📊 View All Results", use_container_width=True):
                    st.rerun()  # This will show all results
                    
        except AutoGradingError as e:
            st.error(f"Failed to load test result: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    def _render_all_results(self, student_id: str):
        """Render all test results for the student"""
        try:
            # Load all results
            with st.spinner("Loading your test results..."):
                results = self.grading_service.get_student_results(student_id)
            
            if not results:
                self._render_no_results_state()
                return
            
            # Show summary statistics
            self._render_results_summary(results)
            
            # Filter and sort options
            self._render_filter_controls(results)
            
            # Apply filters
            filtered_results = self._apply_filters(results)
            
            # Display results
            st.subheader(f"📝 Your Test Results ({len(filtered_results)})")
            
            if not filtered_results:
                st.info("No results match your current filters.")
                return
            
            # Group results by status
            passed_results = [r for r in filtered_results if r.passed]
            failed_results = [r for r in filtered_results if not r.passed]
            
            # Display passed tests first
            if passed_results:
                st.markdown("### ✅ Passed Tests")
                for result in passed_results:
                    self._render_test_result_card(result, "passed")
            
            if failed_results:
                st.markdown("### ❌ Failed Tests")
                for result in failed_results:
                    self._render_test_result_card(result, "failed")
                    
        except AutoGradingError as e:
            st.error(f"Failed to load test results: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    def _render_no_results_state(self):
        """Render state when no results are available"""
        st.info("📭 You haven't completed any tests yet.")
        st.markdown("""
        **Get started:**
        - Browse available tests in the 'Available Tests' section
        - Complete a test to see your results here
        - Results include your score, time taken, and detailed answer review
        
        **What you'll see:**
        - Overall score and pass/fail status
        - Question-by-question breakdown
        - Time taken and performance analytics
        - Historical results and progress tracking
        """)
        
        if st.button("📝 Browse Available Tests", use_container_width=True):
            st.session_state['selected_page'] = 'Available Tests'
            st.rerun()
    
    def _render_results_summary(self, results: List[TestResult]):
        """Render summary statistics"""
        st.subheader("📈 Performance Summary")
        
        # Calculate statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests
        
        if total_tests > 0:
            avg_score = sum(r.percentage_score for r in results) / total_tests
            best_score = max(r.percentage_score for r in results)
            total_time = sum(r.time_taken for r in results if r.time_taken)
        else:
            avg_score = best_score = total_time = 0
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Tests Taken", total_tests)
        
        with col2:
            st.metric("Tests Passed", passed_tests, delta=f"{passed_tests - failed_tests:+d}")
        
        with col3:
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col4:
            st.metric("Best Score", f"{best_score:.1f}%")
        
        # Performance chart
        if total_tests > 1:
            with st.expander("📊 Score Trend", expanded=False):
                # Create a simple chart of scores over time
                chart_data = []
                for i, result in enumerate(reversed(results)):  # Chronological order
                    chart_data.append({
                        'Test': i + 1,
                        'Score': result.percentage_score,
                        'Passed': result.passed
                    })
                
                df = pd.DataFrame(chart_data)
                st.line_chart(df.set_index('Test')['Score'])
    
    def _render_filter_controls(self, results: List[TestResult]):
        """Render filter and sort controls"""
        st.subheader("🔍 Filter & Sort")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "Passed", "Failed"],
                key="results_status_filter"
            )
        
        with col2:
            # Get unique test names (would need test titles from test service)
            test_filter = st.selectbox(
                "Test",
                ["All Tests"],  # Could expand this with actual test names
                key="results_test_filter"
            )
        
        with col3:
            date_filter = st.selectbox(
                "Date Range",
                ["All Time", "Last Week", "Last Month", "Last 3 Months"],
                key="results_date_filter"
            )
        
        with col4:
            sort_by = st.selectbox(
                "Sort by",
                ["Most Recent", "Oldest First", "Highest Score", "Lowest Score"],
                key="results_sort_by"
            )
    
    def _apply_filters(self, results: List[TestResult]) -> List[TestResult]:
        """Apply filters and sorting to results"""
        filtered = results.copy()
        
        # Status filter
        status_filter = st.session_state.get('results_status_filter', 'All')
        if status_filter == "Passed":
            filtered = [r for r in filtered if r.passed]
        elif status_filter == "Failed":
            filtered = [r for r in filtered if not r.passed]
        
        # Date filter
        date_filter = st.session_state.get('results_date_filter', 'All Time')
        if date_filter != "All Time":
            now = datetime.now()
            if date_filter == "Last Week":
                cutoff = now - timedelta(weeks=1)
            elif date_filter == "Last Month":
                cutoff = now - timedelta(days=30)
            elif date_filter == "Last 3 Months":
                cutoff = now - timedelta(days=90)
            else:
                cutoff = None
            
            if cutoff:
                filtered = [r for r in filtered 
                          if datetime.fromisoformat(r.graded_at.replace('Z', '+00:00')) >= cutoff]
        
        # Sorting
        sort_by = st.session_state.get('results_sort_by', 'Most Recent')
        if sort_by == "Most Recent":
            filtered.sort(key=lambda x: x.graded_at, reverse=True)
        elif sort_by == "Oldest First":
            filtered.sort(key=lambda x: x.graded_at)
        elif sort_by == "Highest Score":
            filtered.sort(key=lambda x: x.percentage_score, reverse=True)
        elif sort_by == "Lowest Score":
            filtered.sort(key=lambda x: x.percentage_score)
        
        return filtered
    
    def _render_test_result_card(self, result: TestResult, status: str = None, 
                                expanded: bool = False, show_details: bool = False):
        """Render individual test result card"""
        # Determine status if not provided
        if status is None:
            status = "passed" if result.passed else "failed"
        
        # Status colors and icons
        status_config = {
            "passed": {"color": "green", "icon": "✅", "text": "Passed"},
            "failed": {"color": "red", "icon": "❌", "text": "Failed"}
        }
        
        config = status_config.get(status, status_config["failed"])
        
        with st.container():
            # Header row
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**Test ID: {result.test_id[:8]}...** (Attempt: {result.attempt_id[:8]}...)")
                st.caption(f"Completed: {result.graded_at[:16]}")
            
            with col2:
                st.markdown(f"{config['icon']} **{config['text']}**")
                st.markdown(f"**Score: {result.percentage_score:.1f}%**")
            
            with col3:
                if st.button("📋 View Details", key=f"details_{result.result_id}", use_container_width=True):
                    self._show_detailed_results(result)
            
            # Summary row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"**Questions:** {result.correct_answers}/{result.total_questions}")
                if result.unanswered_questions > 0:
                    st.markdown(f"**Unanswered:** {result.unanswered_questions}")
            
            with col2:
                st.markdown(f"**Points:** {result.total_points_earned:.1f}/{result.total_points_possible:.1f}")
                st.markdown(f"**Passing:** {result.passing_score}%")
            
            with col3:
                if result.time_taken:
                    minutes = result.time_taken // 60
                    seconds = result.time_taken % 60
                    st.markdown(f"**Time:** {minutes}m {seconds}s")
                else:
                    st.markdown("**Time:** Not recorded")
            
            with col4:
                # Performance indicator
                if result.percentage_score >= 90:
                    st.markdown("🌟 **Excellent**")
                elif result.percentage_score >= 80:
                    st.markdown("👍 **Good**")
                elif result.percentage_score >= result.passing_score:
                    st.markdown("✅ **Satisfactory**")
                else:
                    st.markdown("📚 **Needs Improvement**")
            
            # Show detailed breakdown if requested
            if show_details or expanded:
                self._render_question_breakdown(result)
            
            st.divider()
    
    def _show_detailed_results(self, result: TestResult):
        """Show detailed results in an expander"""
        with st.expander(f"📋 Detailed Results: {result.result_id[:8]}...", expanded=True):
            self._render_question_breakdown(result)
    
    def _render_question_breakdown(self, result: TestResult):
        """Render question-by-question breakdown"""
        st.markdown("### 📝 Question-by-Question Review")
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Correct", result.correct_answers, delta=f"{result.correct_answers - result.incorrect_answers:+d}")
        with col2:
            st.metric("Incorrect", result.incorrect_answers)
        with col3:
            st.metric("Unanswered", result.unanswered_questions)
        
        # Question details
        for qr in result.question_results:
            self._render_question_result(qr)
    
    def _render_question_result(self, qr: QuestionResult):
        """Render individual question result"""
        # Status icon and color
        if qr.is_correct:
            icon = "✅"
            color = "green"
        elif qr.student_answer:
            icon = "❌"
            color = "red"
        else:
            icon = "⚪"
            color = "gray"
        
        with st.container():
            # Question header
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"{icon} **Question {qr.question_number}** ({qr.question_type.replace('_', ' ').title()})")
                st.markdown(f"*{qr.question_text}*")
            
            with col2:
                st.markdown(f"**Points:** {qr.points_earned:.1f}/{qr.points_possible:.1f}")
            
            # Answer comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Your Answer:**")
                if qr.student_answer:
                    if qr.is_correct:
                        st.success(qr.student_answer)
                    else:
                        st.error(qr.student_answer)
                else:
                    st.warning("Not answered")
            
            with col2:
                st.markdown("**Correct Answer:**")
                st.info(qr.correct_answer)
            
            st.markdown("---")


def render_test_results_page():
    """Render the test results page"""
    page = TestResultsPage()
    page.render()


if __name__ == "__main__":
    render_test_results_page()