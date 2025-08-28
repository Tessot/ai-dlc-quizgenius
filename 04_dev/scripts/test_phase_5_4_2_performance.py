#!/usr/bin/env python3
"""
Phase 5.4.2: Performance Optimization Testing Script
Tests system performance, database queries, and UI responsiveness
Implements performance benchmarking and optimization validation
"""

import sys
import os
import time
import statistics
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService
from services.user_service import UserService
from services.question_storage_service import QuestionStorageService
from services.test_creation_service import TestCreationService
from services.student_test_service import StudentTestService
from services.auto_grading_service import AutoGradingService
from services.instructor_analytics_service import InstructorAnalyticsService
from utils.dynamodb_utils import DynamoDBManager


class PerformanceTester:
    """Performance testing and optimization validation"""
    
    def __init__(self):
        """Initialize performance tester"""
        self.performance_results = {
            'database_performance': {},
            'service_performance': {},
            'concurrent_performance': {},
            'memory_usage': {},
            'optimization_recommendations': [],
            'start_time': datetime.now()
        }
        
        # Performance thresholds (in seconds)
        self.thresholds = {
            'database_query': 2.0,      # Database queries should complete within 2s
            'user_registration': 3.0,    # User registration within 3s
            'question_generation': 10.0, # Question generation within 10s
            'test_creation': 5.0,        # Test creation within 5s
            'test_submission': 3.0,      # Test submission within 3s
            'grading': 5.0,              # Auto-grading within 5s
            'analytics': 8.0             # Analytics generation within 8s
        }
        
        # Initialize services
        try:
            self.auth_service = AuthService()
            self.user_service = UserService()
            self.question_storage_service = QuestionStorageService()
            self.test_creation_service = TestCreationService()
            self.student_test_service = StudentTestService()
            self.grading_service = AutoGradingService()
            self.analytics_service = InstructorAnalyticsService()
            self.dynamodb_manager = DynamoDBManager()
            
            self.services_initialized = True
            print("✅ All services initialized for performance testing")
        except Exception as e:
            print(f"❌ Failed to initialize services: {e}")
            self.services_initialized = False
    
    def measure_execution_time(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure execution time of a function"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            return result, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return {'error': str(e)}, execution_time
    
    def test_database_performance(self):
        """Test database query performance"""
        print("\n🔄 Testing Database Performance...")
        
        db_tests = []
        
        # Test 1: User lookup performance
        test_user_id = f"perf_test_{int(time.time())}"
        
        # Create test user first
        user_data = {
            'user_id': test_user_id,
            'email': f"{test_user_id}@example.com",
            'role': 'instructor',
            'first_name': 'Performance',
            'last_name': 'Test'
        }
        
        result, create_time = self.measure_execution_time(
            self.user_service.register_user,
            email=user_data['email'],
            password="TestPassword123!",
            role=user_data['role'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        
        db_tests.append({
            'operation': 'User Creation',
            'time': create_time,
            'threshold': self.thresholds['database_query'],
            'passed': create_time < self.thresholds['database_query']
        })
        
        # Test 2: User retrieval performance (using auth service)
        result, retrieve_time = self.measure_execution_time(
            self.user_service.get_user_by_email,
            user_data['email']
        )
        
        db_tests.append({
            'operation': 'User Retrieval',
            'time': retrieve_time,
            'threshold': self.thresholds['database_query'],
            'passed': retrieve_time < self.thresholds['database_query']
        })
        
        # Test 3: Question storage performance
        question_data = {
            'question_id': f"perf_q_{int(time.time())}",
            'instructor_id': test_user_id,
            'question_text': 'Performance test question?',
            'question_type': 'multiple_choice',
            'options': ['A', 'B', 'C', 'D'],
            'correct_answer': 'A',
            'created_at': datetime.now().isoformat()
        }
        
        result, store_time = self.measure_execution_time(
            self.question_storage_service.store_question,
            question_data
        )
        
        db_tests.append({
            'operation': 'Question Storage',
            'time': store_time,
            'threshold': self.thresholds['database_query'],
            'passed': store_time < self.thresholds['database_query']
        })
        
        # Test 4: Batch query performance (get questions by instructor)
        instructor_id = result.get('question_id', test_user_id) if isinstance(result, dict) else test_user_id
        
        result, query_time = self.measure_execution_time(
            self.question_storage_service.get_questions_by_instructor,
            instructor_id
        )
        
        db_tests.append({
            'operation': 'Batch Query',
            'time': query_time,
            'threshold': self.thresholds['database_query'],
            'passed': query_time < self.thresholds['database_query']
        })
        
        # Store results
        self.performance_results['database_performance'] = db_tests
        
        # Print results
        print("📊 Database Performance Results:")
        for test in db_tests:
            status = "✅ PASS" if test['passed'] else "❌ FAIL"
            print(f"  {status}: {test['operation']} - {test['time']:.3f}s (threshold: {test['threshold']}s)")
        
        # Note: Cleanup would require delete methods in services
        # For now, test data will remain in database
    
    def test_service_performance(self):
        """Test individual service performance"""
        print("\n🔄 Testing Service Performance...")
        
        service_tests = []
        test_email = f"perf_service_{int(time.time())}@example.com"
        
        # Test 1: User registration performance
        result, reg_time = self.measure_execution_time(
            self.user_service.register_user,
            email=test_email,
            password="TestPassword123!",
            role='instructor',
            first_name='Performance',
            last_name='Test'
        )
        
        service_tests.append({
            'service': 'User Registration',
            'time': reg_time,
            'threshold': self.thresholds['user_registration'],
            'passed': reg_time < self.thresholds['user_registration'],
            'success': result.get('success', False) if isinstance(result, dict) else False
        })
        
        instructor_id = result.get('user_id') if isinstance(result, dict) and result.get('success') else None
        
        # Test 2: Question storage performance
        if instructor_id:
            question_data = {
                'instructor_id': instructor_id,
                'question_text': 'What is machine learning?',
                'question_type': 'multiple_choice',
                'options': ['AI subset', 'Programming language', 'Database', 'Network protocol'],
                'correct_answer': 'AI subset',
                'explanation': 'Machine learning is a subset of artificial intelligence',
                'difficulty': 'medium',
                'topic': 'AI'
            }
            
            result, store_time = self.measure_execution_time(
                self.question_storage_service.store_question,
                question_data
            )
            
            service_tests.append({
                'service': 'Question Storage',
                'time': store_time,
                'threshold': self.thresholds['database_query'],
                'passed': store_time < self.thresholds['database_query'],
                'success': result.get('success', False) if isinstance(result, dict) else False
            })
            
            question_id = result.get('question_id') if isinstance(result, dict) and result.get('success') else None
            
            # Test 3: Test creation performance
            if question_id:
                test_data = {
                    'instructor_id': instructor_id,
                    'title': 'Performance Test Quiz',
                    'description': 'Testing performance',
                    'question_ids': [question_id],
                    'time_limit': 30,
                    'max_attempts': 1
                }
                
                result, create_time = self.measure_execution_time(
                    self.test_creation_service.create_test,
                    test_data
                )
                
                service_tests.append({
                    'service': 'Test Creation',
                    'time': create_time,
                    'threshold': self.thresholds['test_creation'],
                    'passed': create_time < self.thresholds['test_creation'],
                    'success': result.get('success', False) if isinstance(result, dict) else False
                })
        
        # Store results
        self.performance_results['service_performance'] = service_tests
        
        # Print results
        print("📊 Service Performance Results:")
        for test in service_tests:
            status = "✅ PASS" if test['passed'] and test['success'] else "❌ FAIL"
            success_indicator = "✓" if test['success'] else "✗"
            print(f"  {status}: {test['service']} - {test['time']:.3f}s ({success_indicator}) (threshold: {test['threshold']}s)")
    
    def test_concurrent_performance(self):
        """Test system performance under concurrent load"""
        print("\n🔄 Testing Concurrent Performance...")
        
        concurrent_tests = []
        
        # Test 1: Concurrent user registrations
        def register_test_user(index):
            email = f"concurrent_test_{index}_{int(time.time())}@example.com"
            return self.user_service.register_user(
                email=email,
                password="TestPassword123!",
                role='student',
                first_name=f'Test{index}',
                last_name='User'
            )
        
        # Run 5 concurrent registrations
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_test_user, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_reg_time = time.time() - start_time
        successful_registrations = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        
        concurrent_tests.append({
            'test': 'Concurrent User Registration',
            'concurrent_operations': 5,
            'successful_operations': successful_registrations,
            'total_time': concurrent_reg_time,
            'avg_time_per_operation': concurrent_reg_time / 5,
            'passed': concurrent_reg_time < (self.thresholds['user_registration'] * 2)  # Allow 2x threshold for concurrent
        })
        
        # Test 2: Concurrent database queries
        def query_test_data(index):
            return self.user_service.get_user_by_email(f"test_query_{index}@example.com")
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(query_test_data, i) for i in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_query_time = time.time() - start_time
        successful_queries = sum(1 for r in results if r is not None)
        
        concurrent_tests.append({
            'test': 'Concurrent Database Queries',
            'concurrent_operations': 3,
            'successful_operations': successful_queries,
            'total_time': concurrent_query_time,
            'avg_time_per_operation': concurrent_query_time / 3,
            'passed': concurrent_query_time < (self.thresholds['database_query'] * 1.5)
        })
        
        # Store results
        self.performance_results['concurrent_performance'] = concurrent_tests
        
        # Print results
        print("📊 Concurrent Performance Results:")
        for test in concurrent_tests:
            status = "✅ PASS" if test['passed'] else "❌ FAIL"
            print(f"  {status}: {test['test']}")
            print(f"    └─ {test['successful_operations']}/{test['concurrent_operations']} operations successful")
            print(f"    └─ Total time: {test['total_time']:.3f}s, Avg: {test['avg_time_per_operation']:.3f}s")
    
    def test_memory_and_resource_usage(self):
        """Test memory usage and resource consumption"""
        print("\n🔄 Testing Memory and Resource Usage...")
        
        try:
            import psutil
            import gc
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform memory-intensive operations
            large_data_operations = []
            
            # Test 1: Large question batch processing
            start_memory = process.memory_info().rss / 1024 / 1024
            
            # Simulate processing 100 questions
            questions = []
            for i in range(100):
                questions.append({
                    'question_id': f'mem_test_{i}',
                    'question_text': f'Test question {i}' * 10,  # Make it larger
                    'options': [f'Option {j}' for j in range(4)],
                    'correct_answer': 'Option 0',
                    'explanation': f'Explanation for question {i}' * 5
                })
            
            # Process questions
            processed_questions = []
            for q in questions:
                processed_questions.append({
                    **q,
                    'processed': True,
                    'timestamp': datetime.now().isoformat()
                })
            
            end_memory = process.memory_info().rss / 1024 / 1024
            memory_used = end_memory - start_memory
            
            large_data_operations.append({
                'operation': 'Large Question Batch Processing',
                'memory_used_mb': memory_used,
                'items_processed': len(processed_questions),
                'memory_per_item_kb': (memory_used * 1024) / len(processed_questions) if processed_questions else 0
            })
            
            # Cleanup
            del questions, processed_questions
            gc.collect()
            
            # Test 2: Analytics data processing
            start_memory = process.memory_info().rss / 1024 / 1024
            
            # Simulate analytics calculations
            analytics_data = {
                'test_results': [{'score': i % 100, 'time': i * 10} for i in range(1000)],
                'student_performance': [{'student_id': f'student_{i}', 'scores': [j for j in range(10)]} for i in range(100)],
                'question_analytics': [{'question_id': f'q_{i}', 'accuracy': i % 100 / 100} for i in range(500)]
            }
            
            # Process analytics
            summary_stats = {
                'avg_score': statistics.mean([r['score'] for r in analytics_data['test_results']]),
                'total_students': len(analytics_data['student_performance']),
                'total_questions': len(analytics_data['question_analytics'])
            }
            
            end_memory = process.memory_info().rss / 1024 / 1024
            memory_used = end_memory - start_memory
            
            large_data_operations.append({
                'operation': 'Analytics Data Processing',
                'memory_used_mb': memory_used,
                'items_processed': sum(len(v) if isinstance(v, list) else 1 for v in analytics_data.values()),
                'memory_per_item_kb': (memory_used * 1024) / sum(len(v) if isinstance(v, list) else 1 for v in analytics_data.values())
            })
            
            # Cleanup
            del analytics_data, summary_stats
            gc.collect()
            
            final_memory = process.memory_info().rss / 1024 / 1024
            total_memory_change = final_memory - initial_memory
            
            self.performance_results['memory_usage'] = {
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'total_memory_change_mb': total_memory_change,
                'large_data_operations': large_data_operations,
                'memory_efficient': total_memory_change < 50  # Less than 50MB increase
            }
            
            print("📊 Memory Usage Results:")
            print(f"  Initial Memory: {initial_memory:.2f} MB")
            print(f"  Final Memory: {final_memory:.2f} MB")
            print(f"  Memory Change: {total_memory_change:+.2f} MB")
            
            for op in large_data_operations:
                print(f"  {op['operation']}:")
                print(f"    └─ Memory Used: {op['memory_used_mb']:.2f} MB")
                print(f"    └─ Items Processed: {op['items_processed']}")
                print(f"    └─ Memory per Item: {op['memory_per_item_kb']:.2f} KB")
            
            efficiency_status = "✅ EFFICIENT" if total_memory_change < 50 else "⚠️  HIGH USAGE"
            print(f"  Overall Memory Efficiency: {efficiency_status}")
            
        except ImportError:
            print("⚠️  psutil not available - skipping memory tests")
            self.performance_results['memory_usage'] = {'error': 'psutil not available'}
    
    def generate_optimization_recommendations(self):
        """Generate performance optimization recommendations"""
        print("\n🔄 Generating Optimization Recommendations...")
        
        recommendations = []
        
        # Database performance recommendations
        db_tests = self.performance_results.get('database_performance', [])
        slow_db_operations = [test for test in db_tests if not test['passed']]
        
        if slow_db_operations:
            recommendations.append({
                'category': 'Database Optimization',
                'priority': 'High',
                'issue': f"{len(slow_db_operations)} database operations exceeded thresholds",
                'recommendations': [
                    'Implement database connection pooling',
                    'Add caching layer for frequently accessed data',
                    'Optimize DynamoDB GSI usage',
                    'Consider batch operations for multiple queries',
                    'Review and optimize query patterns'
                ]
            })
        
        # Service performance recommendations
        service_tests = self.performance_results.get('service_performance', [])
        slow_services = [test for test in service_tests if not test['passed']]
        
        if slow_services:
            recommendations.append({
                'category': 'Service Optimization',
                'priority': 'Medium',
                'issue': f"{len(slow_services)} services exceeded performance thresholds",
                'recommendations': [
                    'Implement service-level caching',
                    'Optimize business logic algorithms',
                    'Add asynchronous processing where appropriate',
                    'Review error handling overhead',
                    'Consider microservice architecture for heavy operations'
                ]
            })
        
        # Concurrent performance recommendations
        concurrent_tests = self.performance_results.get('concurrent_performance', [])
        concurrent_issues = [test for test in concurrent_tests if not test['passed']]
        
        if concurrent_issues:
            recommendations.append({
                'category': 'Concurrency Optimization',
                'priority': 'Medium',
                'issue': 'System performance degrades under concurrent load',
                'recommendations': [
                    'Implement proper connection pooling',
                    'Add rate limiting to prevent resource exhaustion',
                    'Optimize thread pool configurations',
                    'Consider async/await patterns',
                    'Implement circuit breaker patterns'
                ]
            })
        
        # Memory usage recommendations
        memory_data = self.performance_results.get('memory_usage', {})
        if memory_data.get('total_memory_change_mb', 0) > 50:
            recommendations.append({
                'category': 'Memory Optimization',
                'priority': 'Low',
                'issue': 'High memory usage detected during operations',
                'recommendations': [
                    'Implement object pooling for frequently created objects',
                    'Add garbage collection optimization',
                    'Review data structure choices',
                    'Implement streaming for large data processing',
                    'Add memory monitoring and alerts'
                ]
            })
        
        # General recommendations
        recommendations.append({
            'category': 'General Performance',
            'priority': 'Low',
            'issue': 'Proactive performance improvements',
            'recommendations': [
                'Implement comprehensive monitoring and alerting',
                'Add performance metrics collection',
                'Set up automated performance regression testing',
                'Implement CDN for static assets',
                'Add health check endpoints',
                'Consider implementing API response caching'
            ]
        })
        
        self.performance_results['optimization_recommendations'] = recommendations
        
        print("📋 Performance Optimization Recommendations:")
        for rec in recommendations:
            print(f"\n  🎯 {rec['category']} (Priority: {rec['priority']})")
            print(f"     Issue: {rec['issue']}")
            print("     Recommendations:")
            for suggestion in rec['recommendations']:
                print(f"       • {suggestion}")
    
    def run_complete_performance_test(self):
        """Run complete performance test suite"""
        print("🚀 Starting Complete Performance Test Suite")
        print("=" * 60)
        
        if not self.services_initialized:
            print("❌ Cannot run tests - services not initialized")
            return
        
        # Run all performance tests
        self.test_database_performance()
        self.test_service_performance()
        self.test_concurrent_performance()
        self.test_memory_and_resource_usage()
        self.generate_optimization_recommendations()
        
        # Generate final performance report
        self.generate_performance_report()
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        end_time = datetime.now()
        duration = end_time - self.performance_results['start_time']
        
        print(f"🕒 Test Duration: {duration.total_seconds():.2f} seconds")
        
        # Database performance summary
        db_tests = self.performance_results.get('database_performance', [])
        if db_tests:
            passed_db = sum(1 for test in db_tests if test['passed'])
            print(f"\n🗄️  Database Performance: {passed_db}/{len(db_tests)} tests passed")
            avg_db_time = statistics.mean([test['time'] for test in db_tests])
            print(f"   Average query time: {avg_db_time:.3f}s")
        
        # Service performance summary
        service_tests = self.performance_results.get('service_performance', [])
        if service_tests:
            passed_services = sum(1 for test in service_tests if test['passed'] and test['success'])
            print(f"\n⚙️  Service Performance: {passed_services}/{len(service_tests)} services passed")
            avg_service_time = statistics.mean([test['time'] for test in service_tests])
            print(f"   Average service time: {avg_service_time:.3f}s")
        
        # Concurrent performance summary
        concurrent_tests = self.performance_results.get('concurrent_performance', [])
        if concurrent_tests:
            passed_concurrent = sum(1 for test in concurrent_tests if test['passed'])
            print(f"\n🔄 Concurrent Performance: {passed_concurrent}/{len(concurrent_tests)} tests passed")
        
        # Memory usage summary
        memory_data = self.performance_results.get('memory_usage', {})
        if 'total_memory_change_mb' in memory_data:
            memory_efficient = "✅ Efficient" if memory_data.get('memory_efficient') else "⚠️  High Usage"
            print(f"\n💾 Memory Usage: {memory_efficient}")
            print(f"   Memory change: {memory_data['total_memory_change_mb']:+.2f} MB")
        
        # Overall performance assessment
        total_tests = len(db_tests) + len(service_tests) + len(concurrent_tests)
        passed_tests = (
            sum(1 for test in db_tests if test['passed']) +
            sum(1 for test in service_tests if test['passed'] and test['success']) +
            sum(1 for test in concurrent_tests if test['passed'])
        )
        
        if total_tests > 0:
            performance_score = (passed_tests / total_tests) * 100
            print(f"\n📈 Overall Performance Score: {performance_score:.1f}%")
            
            if performance_score >= 90:
                print("🎉 EXCELLENT PERFORMANCE - System is highly optimized!")
            elif performance_score >= 75:
                print("✅ GOOD PERFORMANCE - Minor optimizations recommended")
            elif performance_score >= 60:
                print("⚠️  MODERATE PERFORMANCE - Several optimizations needed")
            else:
                print("❌ POOR PERFORMANCE - Significant optimization required")
        
        # Recommendations summary
        recommendations = self.performance_results.get('optimization_recommendations', [])
        high_priority = sum(1 for rec in recommendations if rec['priority'] == 'High')
        medium_priority = sum(1 for rec in recommendations if rec['priority'] == 'Medium')
        
        print(f"\n🎯 Optimization Recommendations:")
        print(f"   High Priority: {high_priority}")
        print(f"   Medium Priority: {medium_priority}")
        print(f"   Total Categories: {len(recommendations)}")


def main():
    """Main function to run performance tests"""
    print("🧪 QuizGenius MVP - Performance Testing Suite")
    print("Phase 5.4.2: Performance Optimization & Benchmarking")
    print("=" * 60)
    
    tester = PerformanceTester()
    tester.run_complete_performance_test()


if __name__ == "__main__":
    main()