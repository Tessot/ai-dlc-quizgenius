#!/usr/bin/env python3
"""
Development Data Seeding Script for QuizGenius MVP

This script populates DynamoDB tables with sample data for development and testing.
Includes sample users, documents, questions, tests, and results.
"""

import boto3
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from botocore.exceptions import ClientError
from utils.config import get_aws_session

def generate_sample_users():
    """Generate sample user data"""
    users = [
        {
            'user_id': 'instructor-001',
            'email': 'instructor@example.com',
            'role': 'instructor',
            'first_name': 'John',
            'last_name': 'Smith',
            'created_date': '2024-01-15T10:00:00Z',
            'status': 'active'
        },
        {
            'user_id': 'instructor-002', 
            'email': 'teacher@example.com',
            'role': 'instructor',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'created_date': '2024-01-16T14:30:00Z',
            'status': 'active'
        },
        {
            'user_id': 'student-001',
            'email': 'student1@example.com',
            'role': 'student',
            'first_name': 'Alice',
            'last_name': 'Brown',
            'created_date': '2024-01-20T09:15:00Z',
            'status': 'active'
        },
        {
            'user_id': 'student-002',
            'email': 'student2@example.com',
            'role': 'student',
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'created_date': '2024-01-21T11:45:00Z',
            'status': 'active'
        },
        {
            'user_id': 'student-003',
            'email': 'student3@example.com',
            'role': 'student',
            'first_name': 'Carol',
            'last_name': 'Davis',
            'created_date': '2024-01-22T16:20:00Z',
            'status': 'active'
        }
    ]
    return users

def generate_sample_documents():
    """Generate sample document data"""
    documents = [
        {
            'document_id': 'doc-001',
            'filename': 'introduction_to_python.pdf',
            'uploaded_by': 'instructor-001',
            'upload_date': '2024-01-25T10:00:00Z',
            'file_size': 2048576,
            'processing_status': 'completed',
            'extracted_text': 'Python is a high-level programming language...',
            'content_quality_score': Decimal('0.85'),
            'page_count': 15
        },
        {
            'document_id': 'doc-002',
            'filename': 'data_structures_basics.pdf',
            'uploaded_by': 'instructor-001',
            'upload_date': '2024-01-26T14:30:00Z',
            'file_size': 3145728,
            'processing_status': 'completed',
            'extracted_text': 'Data structures are fundamental concepts...',
            'content_quality_score': Decimal('0.92'),
            'page_count': 22
        },
        {
            'document_id': 'doc-003',
            'filename': 'web_development_fundamentals.pdf',
            'uploaded_by': 'instructor-002',
            'upload_date': '2024-01-27T09:15:00Z',
            'file_size': 4194304,
            'processing_status': 'completed',
            'extracted_text': 'Web development involves creating websites...',
            'content_quality_score': Decimal('0.78'),
            'page_count': 28
        }
    ]
    return documents

def generate_sample_questions():
    """Generate sample question data"""
    questions = [
        {
            'question_id': 'q-001',
            'document_id': 'doc-001',
            'created_by': 'instructor-001',
            'created_date': '2024-01-25T11:00:00Z',
            'question_type': 'multiple_choice',
            'question_text': 'What is Python primarily known for?',
            'options': [
                'Being a snake species',
                'High-level programming language',
                'Mathematical calculations only',
                'Hardware programming'
            ],
            'correct_answer': 1,
            'difficulty': 'easy',
            'topic': 'Python Basics'
        },
        {
            'question_id': 'q-002',
            'document_id': 'doc-001',
            'created_by': 'instructor-001',
            'created_date': '2024-01-25T11:05:00Z',
            'question_type': 'true_false',
            'question_text': 'Python is an interpreted language.',
            'correct_answer': True,
            'difficulty': 'medium',
            'topic': 'Python Characteristics'
        },
        {
            'question_id': 'q-003',
            'document_id': 'doc-002',
            'created_by': 'instructor-001',
            'created_date': '2024-01-26T15:00:00Z',
            'question_type': 'multiple_choice',
            'question_text': 'Which of the following is a linear data structure?',
            'options': [
                'Tree',
                'Graph',
                'Array',
                'Hash Table'
            ],
            'correct_answer': 2,
            'difficulty': 'medium',
            'topic': 'Data Structures'
        },
        {
            'question_id': 'q-004',
            'document_id': 'doc-003',
            'created_by': 'instructor-002',
            'created_date': '2024-01-27T10:00:00Z',
            'question_type': 'true_false',
            'question_text': 'HTML stands for HyperText Markup Language.',
            'correct_answer': True,
            'difficulty': 'easy',
            'topic': 'Web Development'
        }
    ]
    return questions

def generate_sample_tests():
    """Generate sample test data"""
    tests = [
        {
            'test_id': 'test-001',
            'title': 'Python Fundamentals Quiz',
            'description': 'Basic quiz covering Python programming concepts',
            'created_by': 'instructor-001',
            'created_date': '2024-01-28T10:00:00Z',
            'status': 'published',
            'question_ids': ['q-001', 'q-002'],
            'time_limit': 30,  # minutes
            'total_questions': 2,
            'passing_score': 70
        },
        {
            'test_id': 'test-002',
            'title': 'Data Structures Assessment',
            'description': 'Assessment on basic data structure concepts',
            'created_by': 'instructor-001',
            'created_date': '2024-01-29T14:00:00Z',
            'status': 'published',
            'question_ids': ['q-003'],
            'time_limit': 20,
            'total_questions': 1,
            'passing_score': 80
        },
        {
            'test_id': 'test-003',
            'title': 'Web Development Basics',
            'description': 'Introduction to web development concepts',
            'created_by': 'instructor-002',
            'created_date': '2024-01-30T09:00:00Z',
            'status': 'draft',
            'question_ids': ['q-004'],
            'time_limit': 15,
            'total_questions': 1,
            'passing_score': 75
        }
    ]
    return tests

def generate_sample_test_attempts():
    """Generate sample test attempt data"""
    attempts = [
        {
            'attempt_id': 'attempt-001',
            'test_id': 'test-001',
            'student_id': 'student-001',
            'attempt_date': '2024-02-01T10:30:00Z',
            'start_time': '2024-02-01T10:30:00Z',
            'end_time': '2024-02-01T10:45:00Z',
            'status': 'completed',
            'answers': {
                'q-001': 1,  # correct
                'q-002': True  # correct
            },
            'time_taken': 15  # minutes
        },
        {
            'attempt_id': 'attempt-002',
            'test_id': 'test-001',
            'student_id': 'student-002',
            'attempt_date': '2024-02-01T14:00:00Z',
            'start_time': '2024-02-01T14:00:00Z',
            'end_time': '2024-02-01T14:20:00Z',
            'status': 'completed',
            'answers': {
                'q-001': 0,  # incorrect
                'q-002': True  # correct
            },
            'time_taken': 20
        },
        {
            'attempt_id': 'attempt-003',
            'test_id': 'test-002',
            'student_id': 'student-003',
            'attempt_date': '2024-02-02T11:15:00Z',
            'start_time': '2024-02-02T11:15:00Z',
            'end_time': '2024-02-02T11:25:00Z',
            'status': 'completed',
            'answers': {
                'q-003': 2  # correct
            },
            'time_taken': 10
        }
    ]
    return attempts

def generate_sample_results():
    """Generate sample results data"""
    results = [
        {
            'result_id': 'result-001',
            'attempt_id': 'attempt-001',
            'test_id': 'test-001',
            'student_id': 'student-001',
            'total_questions': 2,
            'correct_answers': 2,
            'incorrect_answers': 0,
            'score_percentage': Decimal('100.0'),
            'passed': True,
            'graded_date': '2024-02-01T10:45:30Z',
            'question_results': [
                {
                    'question_id': 'q-001',
                    'student_answer': 1,
                    'correct_answer': 1,
                    'is_correct': True
                },
                {
                    'question_id': 'q-002',
                    'student_answer': True,
                    'correct_answer': True,
                    'is_correct': True
                }
            ]
        },
        {
            'result_id': 'result-002',
            'attempt_id': 'attempt-002',
            'test_id': 'test-001',
            'student_id': 'student-002',
            'total_questions': 2,
            'correct_answers': 1,
            'incorrect_answers': 1,
            'score_percentage': Decimal('50.0'),
            'passed': False,
            'graded_date': '2024-02-01T14:20:15Z',
            'question_results': [
                {
                    'question_id': 'q-001',
                    'student_answer': 0,
                    'correct_answer': 1,
                    'is_correct': False
                },
                {
                    'question_id': 'q-002',
                    'student_answer': True,
                    'correct_answer': True,
                    'is_correct': True
                }
            ]
        },
        {
            'result_id': 'result-003',
            'attempt_id': 'attempt-003',
            'test_id': 'test-002',
            'student_id': 'student-003',
            'total_questions': 1,
            'correct_answers': 1,
            'incorrect_answers': 0,
            'score_percentage': Decimal('100.0'),
            'passed': True,
            'graded_date': '2024-02-02T11:25:10Z',
            'question_results': [
                {
                    'question_id': 'q-003',
                    'student_answer': 2,
                    'correct_answer': 2,
                    'is_correct': True
                }
            ]
        }
    ]
    return results

def seed_table(dynamodb, table_name, items):
    """Seed a table with sample data"""
    table = dynamodb.Table(table_name)
    
    print(f"📝 Seeding {table_name} with {len(items)} items...")
    
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
        print(f"✅ Successfully seeded {table_name}")
    except ClientError as e:
        print(f"❌ Error seeding {table_name}: {e}")
        raise

def main():
    """Main function to seed all tables with development data"""
    print("🌱 Seeding DynamoDB tables with development data")
    print("=" * 60)
    
    try:
        # Get AWS session
        session = get_aws_session()
        dynamodb = session.resource('dynamodb')
        
        # Generate sample data
        users = generate_sample_users()
        documents = generate_sample_documents()
        questions = generate_sample_questions()
        tests = generate_sample_tests()
        attempts = generate_sample_test_attempts()
        results = generate_sample_results()
        
        # Seed all tables
        seed_table(dynamodb, 'QuizGenius_Users', users)
        seed_table(dynamodb, 'QuizGenius_Documents', documents)
        seed_table(dynamodb, 'QuizGenius_Questions', questions)
        seed_table(dynamodb, 'QuizGenius_Tests', tests)
        seed_table(dynamodb, 'QuizGenius_TestAttempts', attempts)
        seed_table(dynamodb, 'QuizGenius_Results', results)
        
        print("\n" + "=" * 60)
        print("✅ All tables seeded successfully!")
        print("\n📊 Data summary:")
        print(f"  • Users: {len(users)} ({sum(1 for u in users if u['role'] == 'instructor')} instructors, {sum(1 for u in users if u['role'] == 'student')} students)")
        print(f"  • Documents: {len(documents)}")
        print(f"  • Questions: {len(questions)}")
        print(f"  • Tests: {len(tests)}")
        print(f"  • Test Attempts: {len(attempts)}")
        print(f"  • Results: {len(results)}")
        
    except Exception as e:
        print(f"\n❌ Error during data seeding: {e}")
        raise

if __name__ == "__main__":
    main()