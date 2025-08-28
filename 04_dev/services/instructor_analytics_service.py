#!/usr/bin/env python3
"""
Instructor Analytics Service for QuizGenius MVP
Handles instructor analytics, test results summaries, and student performance data
Implements Phase 5.3: Instructor Results Interface
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError
import statistics

from services.auto_grading_service import AutoGradingService, TestResult
from services.test_creation_service import TestCreationService
from services.user_service import UserService
from utils.dynamodb_utils import get_current_timestamp, generate_id
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestSummary:
    """Data structure for test summary statistics"""
    test_id: str
    test_title: str
    instructor_id: str
    total_students_attempted: int
    total_students_completed: int
    completion_rate: float
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    passing_rate: float
    average_time_taken: Optional[float]
    total_questions: int
    created_date: str
    last_attempt_date: Optional[str]

@dataclass
class StudentPerformance:
    """Data structure for individual student performance"""
    student_id: str
    student_name: str
    student_email: str
    test_id: str
    attempt_id: str
    score: float
    passed: bool
    time_taken: Optional[int]
    completed_at: str
    correct_answers: int
    total_questions: int
    attempt_number: int

@dataclass
class QuestionAnalytics:
    """Data structure for question-level analytics"""
    question_id: str
    question_number: int
    question_text: str
    question_type: str
    correct_answer: str
    total_attempts: int
    correct_attempts: int
    incorrect_attempts: int
    accuracy_rate: float
    most_common_wrong_answer: Optional[str]

@dataclass
class InstructorDashboard:
    """Data structure for instructor dashboard data"""
    instructor_id: str
    total_tests_created: int
    total_tests_published: int
    total_student_attempts: int
    total_students_reached: int
    average_test_score: float
    recent_activity: List[Dict[str, Any]]
    top_performing_tests: List[TestSummary]
    tests_needing_attention: List[TestSummary]

class InstructorAnalyticsError(Exception):
    """Custom exception for instructor analytics errors"""
    pass

class InstructorAnalyticsService:
    """
    Service for instructor analytics and results management
    """
    
    def __init__(self):
        """Initialize the instructor analytics service"""
        try:
            self.config = Config()
            self.grading_service = AutoGradingService()
            self.test_service = TestCreationService()
            self.user_service = UserService()
            
            # Initialize DynamoDB client
            self.dynamodb = boto3.resource('dynamodb', region_name=self.config.AWS_REGION)
            
            # Table references
            self.tests_table = self.dynamodb.Table('QuizGenius_Tests')
            self.attempts_table = self.dynamodb.Table('QuizGenius_TestAttempts')
            self.results_table = self.dynamodb.Table('QuizGenius_Results')
            self.users_table = self.dynamodb.Table('QuizGenius_Users')
            
            # Verify table access
            self._verify_table_access()
            
            logger.info("InstructorAnalyticsService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize InstructorAnalyticsService: {str(e)}")
            raise InstructorAnalyticsError(f"Service initialization failed: {str(e)}")
    
    def _verify_table_access(self):
        """Verify access to required tables"""
        try:
            self.tests_table.load()
            self.attempts_table.load()
            self.results_table.load()
            self.users_table.load()
        except Exception as e:
            logger.error(f"Cannot access DynamoDB tables: {str(e)}")
            raise InstructorAnalyticsError(f"Cannot access DynamoDB tables: {str(e)}")
    
    def get_instructor_dashboard(self, instructor_id: str) -> InstructorDashboard:
        """
        Get comprehensive dashboard data for an instructor
        
        Args:
            instructor_id: Instructor user ID
            
        Returns:
            InstructorDashboard with complete analytics
        """
        try:
            # Get instructor's tests
            instructor_tests = self._get_instructor_tests(instructor_id)
            
            # Calculate overall statistics
            total_tests_created = len(instructor_tests)
            total_tests_published = len([t for t in instructor_tests if t.get('status') == 'published'])
            
            # Get all results for instructor's tests
            all_results = []
            total_students_reached = set()
            
            for test in instructor_tests:
                test_results = self._get_test_results(test['test_id'])
                all_results.extend(test_results)
                total_students_reached.update(result.student_id for result in test_results)
            
            total_student_attempts = len(all_results)
            total_students_reached = len(total_students_reached)
            
            # Calculate average score across all tests
            if all_results:
                average_test_score = sum(result.percentage_score for result in all_results) / len(all_results)
            else:
                average_test_score = 0.0
            
            # Get recent activity
            recent_activity = self._get_recent_activity(instructor_id, limit=10)
            
            # Get top performing tests
            test_summaries = []
            for test in instructor_tests:
                if test.get('status') == 'published':
                    summary = self.get_test_summary(test['test_id'], instructor_id)
                    if summary:
                        test_summaries.append(summary)
            
            # Sort by average score for top performing
            top_performing_tests = sorted(test_summaries, key=lambda x: x.average_score, reverse=True)[:5]
            
            # Tests needing attention (low completion rate or low average score)
            tests_needing_attention = [
                t for t in test_summaries 
                if t.completion_rate < 0.5 or t.average_score < 60
            ][:5]
            
            dashboard = InstructorDashboard(
                instructor_id=instructor_id,
                total_tests_created=total_tests_created,
                total_tests_published=total_tests_published,
                total_student_attempts=total_student_attempts,
                total_students_reached=total_students_reached,
                average_test_score=average_test_score,
                recent_activity=recent_activity,
                top_performing_tests=top_performing_tests,
                tests_needing_attention=tests_needing_attention
            )
            
            logger.info(f"Generated dashboard for instructor {instructor_id}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to get instructor dashboard: {str(e)}")
            raise InstructorAnalyticsError(f"Failed to generate dashboard: {str(e)}")
    
    def get_test_summary(self, test_id: str, instructor_id: str) -> Optional[TestSummary]:
        """
        Get comprehensive summary statistics for a test
        
        Args:
            test_id: Test ID
            instructor_id: Instructor ID (for security)
            
        Returns:
            TestSummary with complete statistics
        """
        try:
            # Verify test ownership
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data or test_data.get('instructor_id') != instructor_id:
                raise InstructorAnalyticsError("Unauthorized access to test")
            
            # Get all results for this test
            test_results = self._get_test_results(test_id)
            
            if not test_results:
                # Return empty summary for tests with no attempts
                return TestSummary(
                    test_id=test_id,
                    test_title=test_data.get('title', 'Untitled Test'),
                    instructor_id=instructor_id,
                    total_students_attempted=0,
                    total_students_completed=0,
                    completion_rate=0.0,
                    average_score=0.0,
                    median_score=0.0,
                    highest_score=0.0,
                    lowest_score=0.0,
                    passing_rate=0.0,
                    average_time_taken=None,
                    total_questions=len(test_data.get('question_ids', [])),
                    created_date=test_data.get('created_date', ''),
                    last_attempt_date=None
                )
            
            # Calculate statistics
            scores = [result.percentage_score for result in test_results]
            times = [result.time_taken for result in test_results if result.time_taken]
            
            total_students_attempted = len(set(result.student_id for result in test_results))
            total_students_completed = len([r for r in test_results if r.percentage_score is not None])
            completion_rate = total_students_completed / total_students_attempted if total_students_attempted > 0 else 0
            
            average_score = statistics.mean(scores) if scores else 0
            median_score = statistics.median(scores) if scores else 0
            highest_score = max(scores) if scores else 0
            lowest_score = min(scores) if scores else 0
            
            passing_score = test_data.get('passing_score', 70)
            passing_rate = len([s for s in scores if s >= passing_score]) / len(scores) if scores else 0
            
            average_time_taken = statistics.mean(times) if times else None
            
            # Get last attempt date
            last_attempt_date = max(result.graded_at for result in test_results) if test_results else None
            
            summary = TestSummary(
                test_id=test_id,
                test_title=test_data.get('title', 'Untitled Test'),
                instructor_id=instructor_id,
                total_students_attempted=total_students_attempted,
                total_students_completed=total_students_completed,
                completion_rate=completion_rate,
                average_score=average_score,
                median_score=median_score,
                highest_score=highest_score,
                lowest_score=lowest_score,
                passing_rate=passing_rate,
                average_time_taken=average_time_taken,
                total_questions=len(test_data.get('question_ids', [])),
                created_date=test_data.get('created_date', ''),
                last_attempt_date=last_attempt_date
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get test summary for {test_id}: {str(e)}")
            raise InstructorAnalyticsError(f"Failed to generate test summary: {str(e)}")
    
    def get_student_performances(self, test_id: str, instructor_id: str) -> List[StudentPerformance]:
        """
        Get individual student performances for a test
        
        Args:
            test_id: Test ID
            instructor_id: Instructor ID (for security)
            
        Returns:
            List of StudentPerformance objects
        """
        try:
            # Verify test ownership
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data or test_data.get('instructor_id') != instructor_id:
                raise InstructorAnalyticsError("Unauthorized access to test")
            
            # Get all results for this test
            test_results = self._get_test_results(test_id)
            
            performances = []
            for result in test_results:
                # Get student information
                student_info = self._get_student_info(result.student_id)
                
                # Count attempts for this student
                student_attempts = [r for r in test_results if r.student_id == result.student_id]
                attempt_number = len(student_attempts)
                
                performance = StudentPerformance(
                    student_id=result.student_id,
                    student_name=student_info.get('name', 'Unknown Student'),
                    student_email=student_info.get('email', 'unknown@email.com'),
                    test_id=test_id,
                    attempt_id=result.attempt_id,
                    score=result.percentage_score,
                    passed=result.passed,
                    time_taken=result.time_taken,
                    completed_at=result.graded_at,
                    correct_answers=result.correct_answers,
                    total_questions=result.total_questions,
                    attempt_number=attempt_number
                )
                
                performances.append(performance)
            
            # Sort by score (highest first)
            performances.sort(key=lambda x: x.score, reverse=True)
            
            return performances
            
        except Exception as e:
            logger.error(f"Failed to get student performances: {str(e)}")
            raise InstructorAnalyticsError(f"Failed to retrieve student performances: {str(e)}")
    
    def get_question_analytics(self, test_id: str, instructor_id: str) -> List[QuestionAnalytics]:
        """
        Get question-level analytics for a test
        
        Args:
            test_id: Test ID
            instructor_id: Instructor ID (for security)
            
        Returns:
            List of QuestionAnalytics objects
        """
        try:
            # Verify test ownership
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data or test_data.get('instructor_id') != instructor_id:
                raise InstructorAnalyticsError("Unauthorized access to test")
            
            # Get all results for this test
            test_results = self._get_test_results(test_id)
            
            if not test_results:
                return []
            
            # Aggregate question-level data
            question_stats = {}
            
            for result in test_results:
                for q_result in result.question_results:
                    q_id = q_result.question_id
                    
                    if q_id not in question_stats:
                        question_stats[q_id] = {
                            'question_number': q_result.question_number,
                            'question_text': q_result.question_text,
                            'question_type': q_result.question_type,
                            'correct_answer': q_result.correct_answer,
                            'total_attempts': 0,
                            'correct_attempts': 0,
                            'incorrect_attempts': 0,
                            'wrong_answers': []
                        }
                    
                    stats = question_stats[q_id]
                    stats['total_attempts'] += 1
                    
                    if q_result.is_correct:
                        stats['correct_attempts'] += 1
                    else:
                        stats['incorrect_attempts'] += 1
                        if q_result.student_answer:
                            stats['wrong_answers'].append(q_result.student_answer)
            
            # Convert to QuestionAnalytics objects
            analytics = []
            for q_id, stats in question_stats.items():
                accuracy_rate = stats['correct_attempts'] / stats['total_attempts'] if stats['total_attempts'] > 0 else 0
                
                # Find most common wrong answer
                most_common_wrong = None
                if stats['wrong_answers']:
                    from collections import Counter
                    wrong_counter = Counter(stats['wrong_answers'])
                    most_common_wrong = wrong_counter.most_common(1)[0][0]
                
                analytics.append(QuestionAnalytics(
                    question_id=q_id,
                    question_number=stats['question_number'],
                    question_text=stats['question_text'],
                    question_type=stats['question_type'],
                    correct_answer=stats['correct_answer'],
                    total_attempts=stats['total_attempts'],
                    correct_attempts=stats['correct_attempts'],
                    incorrect_attempts=stats['incorrect_attempts'],
                    accuracy_rate=accuracy_rate,
                    most_common_wrong_answer=most_common_wrong
                ))
            
            # Sort by question number
            analytics.sort(key=lambda x: x.question_number)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get question analytics: {str(e)}")
            raise InstructorAnalyticsError(f"Failed to generate question analytics: {str(e)}")
    
    def export_test_results(self, test_id: str, instructor_id: str, format: str = 'json') -> Dict[str, Any]:
        """
        Export test results in various formats
        
        Args:
            test_id: Test ID
            instructor_id: Instructor ID (for security)
            format: Export format ('json', 'csv')
            
        Returns:
            Exported data
        """
        try:
            # Verify test ownership
            test_data = self.test_service.get_test_by_id(test_id)
            if not test_data or test_data.get('instructor_id') != instructor_id:
                raise InstructorAnalyticsError("Unauthorized access to test")
            
            # Get comprehensive data
            test_summary = self.get_test_summary(test_id, instructor_id)
            student_performances = self.get_student_performances(test_id, instructor_id)
            question_analytics = self.get_question_analytics(test_id, instructor_id)
            
            export_data = {
                'test_summary': asdict(test_summary) if test_summary else None,
                'student_performances': [asdict(p) for p in student_performances],
                'question_analytics': [asdict(q) for q in question_analytics],
                'export_timestamp': get_current_timestamp(),
                'export_format': format
            }
            
            logger.info(f"Exported test results for {test_id} in {format} format")
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export test results: {str(e)}")
            raise InstructorAnalyticsError(f"Failed to export results: {str(e)}")
    
    def _get_instructor_tests(self, instructor_id: str) -> List[Dict[str, Any]]:
        """Get all tests created by an instructor"""
        try:
            response = self.tests_table.query(
                IndexName='TestsByCreator-Index',
                KeyConditionExpression='created_by = :instructor_id',
                ExpressionAttributeValues={':instructor_id': instructor_id}
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Failed to get instructor tests: {str(e)}")
            return []
    
    def _get_test_results(self, test_id: str) -> List[TestResult]:
        """Get all results for a specific test"""
        try:
            response = self.results_table.query(
                IndexName='ResultsByTest-Index',
                KeyConditionExpression='test_id = :test_id',
                ExpressionAttributeValues={':test_id': test_id}
            )
            
            results = []
            for result_data in response.get('Items', []):
                # Convert to TestResult object (simplified version)
                from services.auto_grading_service import QuestionResult
                
                question_results = []
                for qr_data in result_data.get('question_results', []):
                    question_result = QuestionResult(**qr_data)
                    question_results.append(question_result)
                
                test_result = TestResult(
                    result_id=result_data['result_id'],
                    attempt_id=result_data['attempt_id'],
                    test_id=result_data['test_id'],
                    student_id=result_data['student_id'],
                    total_questions=result_data['total_questions'],
                    correct_answers=result_data['correct_answers'],
                    incorrect_answers=result_data['incorrect_answers'],
                    unanswered_questions=result_data['unanswered_questions'],
                    total_points_earned=result_data['total_points_earned'],
                    total_points_possible=result_data['total_points_possible'],
                    percentage_score=result_data['percentage_score'],
                    passing_score=result_data['passing_score'],
                    passed=result_data['passed'],
                    time_taken=result_data.get('time_taken'),
                    graded_at=result_data['graded_at'],
                    question_results=question_results
                )
                
                results.append(test_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get test results: {str(e)}")
            return []
    
    def _get_student_info(self, student_id: str) -> Dict[str, str]:
        """Get student information"""
        try:
            response = self.users_table.get_item(
                Key={'user_id': student_id}
            )
            
            if 'Item' in response:
                user = response['Item']
                return {
                    'name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    'email': user.get('email', 'unknown@email.com')
                }
            
            return {'name': 'Unknown Student', 'email': 'unknown@email.com'}
            
        except Exception as e:
            logger.warning(f"Could not get student info: {str(e)}")
            return {'name': 'Unknown Student', 'email': 'unknown@email.com'}
    
    def _get_recent_activity(self, instructor_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity for instructor dashboard"""
        try:
            # Get recent test results for instructor's tests
            instructor_tests = self._get_instructor_tests(instructor_id)
            test_ids = [test['test_id'] for test in instructor_tests]
            
            recent_activity = []
            
            # Get recent results across all instructor's tests
            for test_id in test_ids[:5]:  # Limit to recent tests
                test_results = self._get_test_results(test_id)
                
                for result in test_results[-3:]:  # Last 3 results per test
                    student_info = self._get_student_info(result.student_id)
                    test_info = next((t for t in instructor_tests if t['test_id'] == test_id), {})
                    
                    activity = {
                        'type': 'test_completion',
                        'student_name': student_info['name'],
                        'test_title': test_info.get('title', 'Unknown Test'),
                        'score': result.percentage_score,
                        'passed': result.passed,
                        'timestamp': result.graded_at
                    }
                    
                    recent_activity.append(activity)
            
            # Sort by timestamp (most recent first)
            recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return recent_activity[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {str(e)}")
            return []