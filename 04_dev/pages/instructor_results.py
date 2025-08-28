#!/usr/bin/env python3
"""
Instructor Results Dashboard for QuizGenius MVP
Displays test analytics, student performance, and comprehensive results for instructors
Implements Phase 5.3: Instructor Results Interface
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

# Try to import plotly, fall back to basic charts if not available
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from services.instructor_analytics_service import (
    InstructorAnalyticsService, InstructorAnalyticsError, 
    TestSummary, StudentPerformance, QuestionAnalytics, InstructorDashboard
)
from services.test_creation_service import TestCreationService
from utils.session_manager import SessionManager


class InstructorResultsPage:
    """Instructor results dashboard page"""
    
    def __init__(self):
        """Initialize instructor results page"""
        self.session_manager = SessionManager()
        
        # Try to initialize services
        try:
            self.analytics_service = InstructorAnalyticsService()
            self.test_service = TestCreationService()
            self.services_available = True
        except Exception as e:
            st.error(f"Analytics services not available: {e}")
            self.analytics_service = None
            self.test_service = None
            self.services_available = False
    
    def render(self):
        """Render the instructor results dashboard"""
        st.title("📊 Results & Analytics Dashboard")
        st.markdown("Comprehensive analytics and insights for your tests and students.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to view results dashboard.")
            return
            
        # Check user role
        user_data = self.session_manager.get_user_info()
        if not user_data or user_data.get('role') != 'instructor':
            st.error("Only instructors can view the results dashboard.")
            return
        
        instructor_id = user_data.get('user_id')
        
        # Check services availability
        if not self.services_available:
            st.warning("Analytics services are not available. Please try again later.")
            return
        
        # Initialize session state
        if 'selected_view' not in st.session_state:
            st.session_state['selected_view'] = 'Dashboard'
        
        # Render navigation tabs
        self._render_navigation_tabs()
        
        # Render selected view
        selected_view = st.session_state['selected_view']
        
        if selected_view == 'Dashboard':
            self._render_dashboard_overview(instructor_id)
        elif selected_view == 'Test Analytics':
            self._render_test_analytics(instructor_id)
        elif selected_view == 'Student Performance':
            self._render_student_performance(instructor_id)
        elif selected_view == 'Question Analysis':
            self._render_question_analysis(instructor_id)
        elif selected_view == 'Data Export':
            self._render_data_export(instructor_id)
    
    def _render_navigation_tabs(self):
        """Render navigation tabs for different views"""
        tabs = ['Dashboard', 'Test Analytics', 'Student Performance', 'Question Analysis', 'Data Export']
        
        selected_tab = st.selectbox(
            "Select View",
            tabs,
            index=tabs.index(st.session_state['selected_view']),
            key="results_view_selector"
        )
        
        if selected_tab != st.session_state['selected_view']:
            st.session_state['selected_view'] = selected_tab
            st.rerun()
    
    def _render_dashboard_overview(self, instructor_id: str):
        """Render the main dashboard overview"""
        try:
            with st.spinner("Loading dashboard data..."):
                dashboard = self.analytics_service.get_instructor_dashboard(instructor_id)
            
            # Overview metrics
            st.subheader("📈 Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Tests Created", dashboard.total_tests_created)
            
            with col2:
                st.metric("Tests Published", dashboard.total_tests_published)
            
            with col3:
                st.metric("Student Attempts", dashboard.total_student_attempts)
            
            with col4:
                st.metric("Students Reached", dashboard.total_students_reached)
            
            # Average score with trend
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Average Test Score", 
                    f"{dashboard.average_test_score:.1f}%",
                    delta=None
                )
            
            with col2:
                # Performance indicator
                if dashboard.average_test_score >= 80:
                    st.success("🌟 Excellent overall performance!")
                elif dashboard.average_test_score >= 70:
                    st.info("👍 Good overall performance")
                else:
                    st.warning("📚 Students may need additional support")
            
            # Top performing tests
            if dashboard.top_performing_tests:
                st.subheader("🏆 Top Performing Tests")
                
                for test in dashboard.top_performing_tests[:3]:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{test.test_title}**")
                            st.caption(f"Created: {test.created_date[:10]}")
                        
                        with col2:
                            st.metric("Avg Score", f"{test.average_score:.1f}%")
                        
                        with col3:
                            st.metric("Completion", f"{test.completion_rate:.1%}")
                        
                        with col4:
                            st.metric("Students", test.total_students_attempted)
                        
                        st.divider()
            
            # Tests needing attention
            if dashboard.tests_needing_attention:
                st.subheader("⚠️ Tests Needing Attention")
                
                for test in dashboard.tests_needing_attention[:3]:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 2])
                        
                        with col1:
                            st.markdown(f"**{test.test_title}**")
                        
                        with col2:
                            if test.completion_rate < 0.5:
                                st.error(f"Low completion: {test.completion_rate:.1%}")
                            if test.average_score < 60:
                                st.error(f"Low avg score: {test.average_score:.1f}%")
                        
                        with col3:
                            if st.button("View Details", key=f"details_{test.test_id}"):
                                st.session_state['selected_test_id'] = test.test_id
                                st.session_state['selected_view'] = 'Test Analytics'
                                st.rerun()
                        
                        st.divider()
            
            # Recent activity
            if dashboard.recent_activity:
                st.subheader("📅 Recent Activity")
                
                for activity in dashboard.recent_activity[:5]:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{activity['student_name']}** completed **{activity['test_title']}**")
                            st.caption(activity['timestamp'][:16])
                        
                        with col2:
                            st.markdown(f"Score: {activity['score']:.1f}%")
                        
                        with col3:
                            if activity['passed']:
                                st.success("✅ Passed")
                            else:
                                st.error("❌ Failed")
                        
                        st.divider()
            
        except InstructorAnalyticsError as e:
            st.error(f"Failed to load dashboard: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    def _render_test_analytics(self, instructor_id: str):
        """Render test analytics view"""
        st.subheader("📝 Test Analytics")
        
        try:
            # Get instructor's tests
            with st.spinner("Loading test data..."):
                instructor_tests = self.analytics_service._get_instructor_tests(instructor_id)
            
            if not instructor_tests:
                st.info("No tests found. Create and publish tests to see analytics.")
                return
            
            # Test selection
            published_tests = [t for t in instructor_tests if t.get('status') == 'published']
            
            if not published_tests:
                st.info("No published tests found. Publish tests to see analytics.")
                return
            
            test_options = {f"{test['title']} ({test['test_id'][:8]}...)": test['test_id'] 
                          for test in published_tests}
            
            selected_test_display = st.selectbox(
                "Select Test",
                list(test_options.keys()),
                key="analytics_test_selector"
            )
            
            selected_test_id = test_options[selected_test_display]
            
            # Get test summary
            with st.spinner("Loading test analytics..."):
                test_summary = self.analytics_service.get_test_summary(selected_test_id, instructor_id)
            
            if not test_summary:
                st.error("Failed to load test summary.")
                return
            
            # Display test summary
            self._render_test_summary_card(test_summary)
            
            # Performance charts
            self._render_test_performance_charts(selected_test_id, instructor_id)
            
        except Exception as e:
            st.error(f"Failed to load test analytics: {str(e)}")
    
    def _render_test_summary_card(self, test_summary: TestSummary):
        """Render test summary card"""
        st.markdown(f"### 📊 {test_summary.test_title}")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Students Attempted", test_summary.total_students_attempted)
        
        with col2:
            st.metric("Completion Rate", f"{test_summary.completion_rate:.1%}")
        
        with col3:
            st.metric("Average Score", f"{test_summary.average_score:.1f}%")
        
        with col4:
            st.metric("Passing Rate", f"{test_summary.passing_rate:.1%}")
        
        # Additional metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Highest Score", f"{test_summary.highest_score:.1f}%")
        
        with col2:
            st.metric("Lowest Score", f"{test_summary.lowest_score:.1f}%")
        
        with col3:
            st.metric("Median Score", f"{test_summary.median_score:.1f}%")
        
        with col4:
            if test_summary.average_time_taken:
                minutes = int(test_summary.average_time_taken // 60)
                seconds = int(test_summary.average_time_taken % 60)
                st.metric("Avg Time", f"{minutes}m {seconds}s")
            else:
                st.metric("Avg Time", "N/A")
    
    def _render_test_performance_charts(self, test_id: str, instructor_id: str):
        """Render performance charts for a test"""
        try:
            # Get student performances
            performances = self.analytics_service.get_student_performances(test_id, instructor_id)
            
            if not performances:
                st.info("No student performances found for this test.")
                return
            
            # Score distribution chart
            st.subheader("📈 Score Distribution")
            
            scores = [p.score for p in performances]
            
            if PLOTLY_AVAILABLE:
                fig = px.histogram(
                    x=scores,
                    nbins=10,
                    title="Score Distribution",
                    labels={'x': 'Score (%)', 'y': 'Number of Students'}
                )
                
                fig.update_layout(
                    xaxis_title="Score (%)",
                    yaxis_title="Number of Students",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Fallback to basic chart
                df_scores = pd.DataFrame({'Score': scores})
                st.bar_chart(df_scores['Score'].value_counts().sort_index())
            
            # Pass/Fail pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                passed_count = len([p for p in performances if p.passed])
                failed_count = len(performances) - passed_count
                
                if PLOTLY_AVAILABLE:
                    fig = px.pie(
                        values=[passed_count, failed_count],
                        names=['Passed', 'Failed'],
                        title="Pass/Fail Distribution",
                        color_discrete_map={'Passed': 'green', 'Failed': 'red'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Fallback to metrics
                    st.metric("Passed", passed_count)
                    st.metric("Failed", failed_count)
            
            with col2:
                # Time distribution
                times = [p.time_taken for p in performances if p.time_taken]
                
                if times:
                    if PLOTLY_AVAILABLE:
                        fig = px.box(
                            y=times,
                            title="Time Distribution",
                            labels={'y': 'Time (seconds)'}
                        )
                        
                        fig.update_layout(
                            yaxis_title="Time (seconds)",
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        # Fallback to basic stats
                        avg_time = sum(times) / len(times)
                        st.metric("Average Time", f"{avg_time//60:.0f}m {avg_time%60:.0f}s")
                        st.metric("Min Time", f"{min(times)//60:.0f}m {min(times)%60:.0f}s")
                        st.metric("Max Time", f"{max(times)//60:.0f}m {max(times)%60:.0f}s")
                else:
                    st.info("No time data available")
            
        except Exception as e:
            st.error(f"Failed to render performance charts: {str(e)}")
    
    def _render_student_performance(self, instructor_id: str):
        """Render individual student performance view"""
        st.subheader("👥 Student Performance")
        
        try:
            # Get instructor's tests
            instructor_tests = self.analytics_service._get_instructor_tests(instructor_id)
            published_tests = [t for t in instructor_tests if t.get('status') == 'published']
            
            if not published_tests:
                st.info("No published tests found.")
                return
            
            # Test selection
            test_options = {f"{test['title']} ({test['test_id'][:8]}...)": test['test_id'] 
                          for test in published_tests}
            
            selected_test_display = st.selectbox(
                "Select Test",
                list(test_options.keys()),
                key="student_performance_test_selector"
            )
            
            selected_test_id = test_options[selected_test_display]
            
            # Get student performances
            with st.spinner("Loading student performances..."):
                performances = self.analytics_service.get_student_performances(selected_test_id, instructor_id)
            
            if not performances:
                st.info("No student performances found for this test.")
                return
            
            # Display performances table
            st.subheader(f"📊 Results for {selected_test_display}")
            
            # Create DataFrame for display
            df_data = []
            for p in performances:
                df_data.append({
                    'Student': p.student_name,
                    'Email': p.student_email,
                    'Score (%)': f"{p.score:.1f}",
                    'Status': '✅ Passed' if p.passed else '❌ Failed',
                    'Correct': f"{p.correct_answers}/{p.total_questions}",
                    'Time': f"{p.time_taken//60:.0f}m {p.time_taken%60:.0f}s" if p.time_taken else "N/A",
                    'Completed': p.completed_at[:16],
                    'Attempt #': p.attempt_number
                })
            
            df = pd.DataFrame(df_data)
            
            # Display with formatting
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_score = sum(p.score for p in performances) / len(performances)
                st.metric("Class Average", f"{avg_score:.1f}%")
            
            with col2:
                passed_count = len([p for p in performances if p.passed])
                st.metric("Students Passed", f"{passed_count}/{len(performances)}")
            
            with col3:
                if any(p.time_taken for p in performances):
                    avg_time = sum(p.time_taken for p in performances if p.time_taken) / len([p for p in performances if p.time_taken])
                    st.metric("Avg Time", f"{avg_time//60:.0f}m {avg_time%60:.0f}s")
                else:
                    st.metric("Avg Time", "N/A")
            
        except Exception as e:
            st.error(f"Failed to load student performance: {str(e)}")
    
    def _render_question_analysis(self, instructor_id: str):
        """Render question-level analysis"""
        st.subheader("❓ Question Analysis")
        
        try:
            # Get instructor's tests
            instructor_tests = self.analytics_service._get_instructor_tests(instructor_id)
            published_tests = [t for t in instructor_tests if t.get('status') == 'published']
            
            if not published_tests:
                st.info("No published tests found.")
                return
            
            # Test selection
            test_options = {f"{test['title']} ({test['test_id'][:8]}...)": test['test_id'] 
                          for test in published_tests}
            
            selected_test_display = st.selectbox(
                "Select Test",
                list(test_options.keys()),
                key="question_analysis_test_selector"
            )
            
            selected_test_id = test_options[selected_test_display]
            
            # Get question analytics
            with st.spinner("Loading question analytics..."):
                question_analytics = self.analytics_service.get_question_analytics(selected_test_id, instructor_id)
            
            if not question_analytics:
                st.info("No question analytics found for this test.")
                return
            
            # Display question analytics
            st.subheader(f"📊 Question Performance for {selected_test_display}")
            
            for qa in question_analytics:
                with st.container():
                    # Question header
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Question {qa.question_number}** ({qa.question_type.replace('_', ' ').title()})")
                        st.markdown(f"*{qa.question_text}*")
                    
                    with col2:
                        # Accuracy indicator
                        if qa.accuracy_rate >= 0.8:
                            st.success(f"✅ {qa.accuracy_rate:.1%} accuracy")
                        elif qa.accuracy_rate >= 0.6:
                            st.warning(f"⚠️ {qa.accuracy_rate:.1%} accuracy")
                        else:
                            st.error(f"❌ {qa.accuracy_rate:.1%} accuracy")
                    
                    # Question statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Attempts", qa.total_attempts)
                    
                    with col2:
                        st.metric("Correct", qa.correct_attempts)
                    
                    with col3:
                        st.metric("Incorrect", qa.incorrect_attempts)
                    
                    with col4:
                        st.metric("Accuracy", f"{qa.accuracy_rate:.1%}")
                    
                    # Answer details
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Correct Answer:**")
                        st.info(qa.correct_answer)
                    
                    with col2:
                        if qa.most_common_wrong_answer:
                            st.markdown("**Most Common Wrong Answer:**")
                            st.error(qa.most_common_wrong_answer)
                    
                    st.divider()
            
        except Exception as e:
            st.error(f"Failed to load question analysis: {str(e)}")
    
    def _render_data_export(self, instructor_id: str):
        """Render data export functionality"""
        st.subheader("📤 Data Export")
        
        try:
            # Get instructor's tests
            instructor_tests = self.analytics_service._get_instructor_tests(instructor_id)
            published_tests = [t for t in instructor_tests if t.get('status') == 'published']
            
            if not published_tests:
                st.info("No published tests found.")
                return
            
            # Test selection
            test_options = {f"{test['title']} ({test['test_id'][:8]}...)": test['test_id'] 
                          for test in published_tests}
            
            selected_test_display = st.selectbox(
                "Select Test to Export",
                list(test_options.keys()),
                key="export_test_selector"
            )
            
            selected_test_id = test_options[selected_test_display]
            
            # Export format selection
            export_format = st.selectbox(
                "Export Format",
                ["JSON", "CSV"],
                key="export_format_selector"
            )
            
            # Export button
            if st.button("📤 Export Data", type="primary"):
                try:
                    with st.spinner("Preparing export..."):
                        export_data = self.analytics_service.export_test_results(
                            selected_test_id, instructor_id, export_format.lower()
                        )
                    
                    # Display export preview
                    st.success("✅ Export prepared successfully!")
                    
                    # Show summary
                    st.subheader("📊 Export Summary")
                    
                    if export_data['test_summary']:
                        summary = export_data['test_summary']
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Students", summary['total_students_attempted'])
                        
                        with col2:
                            st.metric("Average Score", f"{summary['average_score']:.1f}%")
                        
                        with col3:
                            st.metric("Questions Analyzed", len(export_data['question_analytics']))
                    
                    # Download button
                    export_json = json.dumps(export_data, indent=2)
                    
                    st.download_button(
                        label="💾 Download Export File",
                        data=export_json,
                        file_name=f"test_results_{selected_test_id[:8]}_{export_format.lower()}.json",
                        mime="application/json"
                    )
                    
                    # Show preview
                    with st.expander("👀 Preview Export Data"):
                        st.json(export_data)
                
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
            
        except Exception as e:
            st.error(f"Failed to load export interface: {str(e)}")


def render_instructor_results_page():
    """Render the instructor results page"""
    page = InstructorResultsPage()
    page.render()


if __name__ == "__main__":
    render_instructor_results_page()