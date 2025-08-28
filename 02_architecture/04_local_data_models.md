# QuizGenius MVP - DynamoDB Data Models

## Overview
This document defines the DynamoDB data models and table structures for the QuizGenius MVP Streamlit application. All data is stored in AWS DynamoDB tables as specified in the user stories, with the Streamlit application connecting via boto3.

---

## DynamoDB Table Architecture

```
QuizGenius DynamoDB Tables:

┌─────────────────────────────────────────────────────────────────┐
│                        Core Tables                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │     Users       │    │   Documents     │                    │
│  │                 │    │                 │                    │
│  │ PK: user_id     │    │ PK: doc_id      │                    │
│  │ SK: profile     │    │ SK: metadata    │                    │
│  │ • Instructors   │    │ • PDF info      │                    │
│  │ • Students      │    │ • Extracted     │                    │
│  │ • Auth data     │    │   text          │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   Questions     │    │     Tests       │                    │
│  │                 │    │                 │                    │
│  │ PK: question_id │    │ PK: test_id     │                    │
│  │ SK: version     │    │ SK: config      │                    │
│  │ • MC Questions  │    │ • Test setup    │                    │
│  │ • T/F Questions │    │ • Questions     │                    │
│  │ • Metadata      │    │ • Settings      │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   TestAttempts  │    │   Results       │                    │
│  │                 │    │                 │                    │
│  │ PK: attempt_id  │    │ PK: result_id   │                    │
│  │ SK: student_id  │    │ SK: summary     │                    │
│  │ • Responses     │    │ • Scores        │                    │
│  │ • Timing        │    │ • Analytics     │                    │
│  │ • Status        │    │ • Reports       │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Global Secondary Indexes (GSI):
• UsersByRole: user_role (PK) + created_at (SK)
• QuestionsByCreator: created_by (PK) + created_at (SK)  
• TestsByStatus: status (PK) + created_at (SK)
• AttemptsByStudent: student_id (PK) + completed_at (SK)
• AttemptsByTest: test_id (PK) + completed_at (SK)
```

---

## 1. DynamoDB Table: Users

### 1.1 Table Schema
```
Table Name: QuizGenius-Users
Partition Key: user_id (String)
Sort Key: record_type (String)
Billing Mode: On-Demand
```

### 1.2 Item Structure - Instructor Profile
```json
{
  "user_id": "inst_12345",
  "record_type": "profile",
  "username": "john_doe",
  "email": "john.doe@university.edu",
  "password_hash": "hashed_password_string",
  "user_role": "instructor",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "title": "Professor",
    "department": "Computer Science",
    "institution": "University Name"
  },
  "account_info": {
    "created_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T14:22:00Z",
    "status": "active",
    "email_verified": true
  },
  "preferences": {
    "default_question_types": ["multiple_choice", "true_false"],
    "default_mc_options": 4,
    "default_time_limit": 30,
    "auto_save": true
  },
  "statistics": {
    "pdfs_uploaded": 5,
    "questions_generated": 150,
    "tests_created": 12,
    "total_students_tested": 45
  },
  "ttl": null,
  "version": 1
}
```

### 1.3 Item Structure - Student Profile
```json
{
  "user_id": "stud_67890",
  "record_type": "profile",
  "username": "jane_smith",
  "email": "jane.smith@student.university.edu",
  "password_hash": "hashed_password_string",
  "user_role": "student",
  "profile": {
    "first_name": "Jane",
    "last_name": "Smith",
    "student_id": "STU2024001",
    "program": "Computer Science",
    "year": "Junior"
  },
  "account_info": {
    "created_at": "2024-01-10T09:15:00Z",
    "last_login": "2024-01-20T16:45:00Z",
    "status": "active",
    "email_verified": true
  },
  "preferences": {
    "show_explanations": true,
    "review_incorrect_only": false,
    "email_notifications": true
  },
  "statistics": {
    "tests_taken": 8,
    "total_questions_answered": 120,
    "average_score": 78.5,
    "total_time_spent_minutes": 240
  },
  "ttl": null,
  "version": 1
}
```

### 1.4 Global Secondary Index - UsersByRole
```
Index Name: UsersByRole-Index
Partition Key: user_role (String)
Sort Key: created_at (String)
Projection: ALL
```

### 1.5 Access Patterns
```python
# Get user profile
response = dynamodb.get_item(
    Key={
        'user_id': 'inst_12345',
        'record_type': 'profile'
    }
)

# Query all instructors
response = dynamodb.query(
    IndexName='UsersByRole-Index',
    KeyConditionExpression=Key('user_role').eq('instructor')
)

# Update user statistics
response = dynamodb.update_item(
    Key={
        'user_id': 'inst_12345',
        'record_type': 'profile'
    },
    UpdateExpression='SET statistics.tests_created = statistics.tests_created + :val',
    ExpressionAttributeValues={':val': 1}
)
```

---

## 2. Content and Question Data Models

### 2.1 PDF Document Metadata Model
```json
{
  "schema_version": "1.0",
  "document_id": "pdf_abc123",
  "upload_info": {
    "original_filename": "lecture_chapter_5.pdf",
    "uploaded_by": "inst_12345",
    "uploaded_at": "2024-01-20T10:30:00Z",
    "file_size_bytes": 2048576,
    "file_path": "data/content/pdfs/inst_12345/1705747800_lecture_chapter_5.pdf"
  },
  "processing_info": {
    "status": "completed",
    "processed_at": "2024-01-20T10:32:15Z",
    "processing_time_seconds": 135,
    "bedrock_job_id": "bedrock_job_xyz789"
  },
  "content_analysis": {
    "total_pages": 15,
    "word_count": 3450,
    "character_count": 18750,
    "language": "en",
    "content_type": "educational",
    "topics_detected": ["algorithms", "data structures", "complexity analysis"]
  },
  "quality_metrics": {
    "quality_score": 85,
    "readability_score": 78,
    "educational_content_score": 92,
    "suitable_for_questions": true,
    "issues": []
  },
  "extraction_result": {
    "text_file_path": "data/content/extracted_text/inst_12345/pdf_abc123_text.json",
    "extraction_method": "bedrock_data_automation",
    "confidence_score": 0.95
  }
}
```

### 2.2 Extracted Text Model
```json
{
  "schema_version": "1.0",
  "document_id": "pdf_abc123",
  "extraction_info": {
    "extracted_at": "2024-01-20T10:32:15Z",
    "method": "bedrock_data_automation",
    "confidence_score": 0.95
  },
  "content": {
    "raw_text": "Full extracted text content here...",
    "cleaned_text": "Processed and cleaned text content here...",
    "structured_content": {
      "title": "Chapter 5: Advanced Algorithms",
      "sections": [
        {
          "heading": "5.1 Introduction",
          "content": "Section content here..."
        },
        {
          "heading": "5.2 Sorting Algorithms",
          "content": "Section content here..."
        }
      ],
      "key_concepts": ["sorting", "searching", "optimization"],
      "definitions": [
        {
          "term": "Algorithm",
          "definition": "A step-by-step procedure for solving a problem"
        }
      ]
    }
  },
  "statistics": {
    "word_count": 3450,
    "sentence_count": 245,
    "paragraph_count": 28,
    "average_sentence_length": 14.1
  }
}
```

### 2.3 Question Schema Models

#### Multiple Choice Question Model
```json
{
  "schema_version": "1.0",
  "question_id": "mc_question_001",
  "type": "multiple_choice",
  "metadata": {
    "created_by": "inst_12345",
    "created_at": "2024-01-20T11:00:00Z",
    "source_document": "pdf_abc123",
    "generation_method": "bedrock_ai",
    "last_modified": "2024-01-20T11:15:00Z",
    "version": 1
  },
  "content": {
    "question": "What is the time complexity of the quicksort algorithm in the average case?",
    "options": {
      "A": "O(n)",
      "B": "O(n log n)",
      "C": "O(n²)",
      "D": "O(log n)"
    },
    "correct_answer": "B",
    "explanation": "Quicksort has an average-case time complexity of O(n log n) due to the divide-and-conquer approach with balanced partitions.",
    "difficulty": "medium",
    "topic": "algorithms",
    "learning_objective": "Understand time complexity analysis"
  },
  "usage_stats": {
    "times_used": 3,
    "correct_responses": 15,
    "total_responses": 20,
    "success_rate": 0.75
  },
  "tags": ["algorithms", "complexity", "sorting"],
  "status": "active"
}
```

#### True/False Question Model
```json
{
  "schema_version": "1.0",
  "question_id": "tf_question_001",
  "type": "true_false",
  "metadata": {
    "created_by": "inst_12345",
    "created_at": "2024-01-20T11:05:00Z",
    "source_document": "pdf_abc123",
    "generation_method": "bedrock_ai",
    "last_modified": "2024-01-20T11:05:00Z",
    "version": 1
  },
  "content": {
    "statement": "Binary search requires the input array to be sorted.",
    "correct_answer": true,
    "explanation": "Binary search algorithm relies on the sorted property of the array to eliminate half of the search space in each iteration.",
    "difficulty": "easy",
    "topic": "algorithms",
    "learning_objective": "Understand binary search prerequisites"
  },
  "usage_stats": {
    "times_used": 2,
    "correct_responses": 18,
    "total_responses": 20,
    "success_rate": 0.90
  },
  "tags": ["algorithms", "search", "binary_search"],
  "status": "active"
}
```

### 2.4 Question Generation History Model
```json
{
  "schema_version": "1.0",
  "generation_id": "gen_xyz789",
  "generation_info": {
    "instructor_id": "inst_12345",
    "source_document": "pdf_abc123",
    "generated_at": "2024-01-20T11:00:00Z",
    "bedrock_model": "anthropic.claude-3-haiku-20240307-v1:0",
    "generation_time_seconds": 45
  },
  "parameters": {
    "num_multiple_choice": 10,
    "num_true_false": 5,
    "difficulty_level": "mixed",
    "topics_focus": ["algorithms", "data_structures"]
  },
  "results": {
    "total_generated": 15,
    "successful_generations": 14,
    "failed_generations": 1,
    "questions": [
      {
        "question_id": "mc_question_001",
        "type": "multiple_choice",
        "status": "generated"
      },
      {
        "question_id": "tf_question_001",
        "type": "true_false",
        "status": "generated"
      }
    ]
  },
  "quality_assessment": {
    "average_quality_score": 82,
    "issues_found": 1,
    "manual_review_required": false
  }
}
```

---

## 3. Test and Assessment Data Models

### 3.1 Test Configuration Model
```json
{
  "schema_version": "1.0",
  "test_id": "test_001",
  "metadata": {
    "title": "Chapter 5 Quiz: Advanced Algorithms",
    "description": "Test your understanding of sorting and searching algorithms",
    "created_by": "inst_12345",
    "created_at": "2024-01-20T12:00:00Z",
    "last_modified": "2024-01-20T12:30:00Z",
    "version": 1
  },
  "configuration": {
    "time_limit_minutes": 30,
    "shuffle_questions": true,
    "shuffle_options": true,
    "show_results_immediately": true,
    "allow_review": true,
    "max_attempts": 1,
    "passing_score": 70
  },
  "questions": [
    {
      "question_id": "mc_question_001",
      "order": 1,
      "points": 2
    },
    {
      "question_id": "tf_question_001",
      "order": 2,
      "points": 1
    }
  ],
  "scoring": {
    "total_points": 15,
    "question_weights": "equal",
    "partial_credit": false,
    "penalty_for_wrong": 0
  },
  "access_control": {
    "status": "published",
    "published_at": "2024-01-20T12:30:00Z",
    "available_from": "2024-01-21T09:00:00Z",
    "available_until": "2024-01-28T23:59:59Z",
    "allowed_students": "all",
    "password_protected": false
  },
  "statistics": {
    "total_attempts": 0,
    "completed_attempts": 0,
    "average_score": 0,
    "average_time_minutes": 0
  }
}
```

### 3.2 Test-Question Relationship Model
```json
{
  "schema_version": "1.0",
  "test_id": "test_001",
  "question_mappings": [
    {
      "question_id": "mc_question_001",
      "position": 1,
      "points": 2,
      "required": true,
      "time_limit_seconds": null,
      "custom_instructions": null
    },
    {
      "question_id": "tf_question_001",
      "position": 2,
      "points": 1,
      "required": true,
      "time_limit_seconds": null,
      "custom_instructions": null
    }
  ],
  "question_pools": [],
  "randomization_rules": {
    "shuffle_questions": true,
    "shuffle_options": true,
    "random_selection": false,
    "pool_selection_count": null
  }
}
```

### 3.3 Test Publication Status Model
```json
{
  "schema_version": "1.0",
  "test_id": "test_001",
  "publication_info": {
    "status": "published",
    "created_at": "2024-01-20T12:00:00Z",
    "published_at": "2024-01-20T12:30:00Z",
    "published_by": "inst_12345",
    "last_updated": "2024-01-20T12:30:00Z"
  },
  "availability": {
    "start_date": "2024-01-21T09:00:00Z",
    "end_date": "2024-01-28T23:59:59Z",
    "timezone": "UTC",
    "always_available": false
  },
  "access_settings": {
    "public": true,
    "password_required": false,
    "password_hash": null,
    "allowed_attempts": 1,
    "time_limit_enforced": true
  },
  "visibility": {
    "show_in_student_list": true,
    "show_results_to_students": true,
    "show_correct_answers": true,
    "show_explanations": true
  }
}
```

---

## 4. Results and Analytics Data Models

### 4.1 Test Attempt Model
```json
{
  "schema_version": "1.0",
  "attempt_id": "attempt_001",
  "test_info": {
    "test_id": "test_001",
    "test_title": "Chapter 5 Quiz: Advanced Algorithms",
    "test_version": 1
  },
  "student_info": {
    "student_id": "stud_67890",
    "username": "jane_smith",
    "student_name": "Jane Smith"
  },
  "attempt_details": {
    "attempt_number": 1,
    "started_at": "2024-01-21T10:00:00Z",
    "submitted_at": "2024-01-21T10:25:30Z",
    "time_taken_seconds": 1530,
    "status": "completed",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  },
  "responses": [
    {
      "question_id": "mc_question_001",
      "question_type": "multiple_choice",
      "student_answer": "B",
      "correct_answer": "B",
      "is_correct": true,
      "points_earned": 2,
      "points_possible": 2,
      "time_spent_seconds": 45,
      "answer_timestamp": "2024-01-21T10:02:15Z"
    },
    {
      "question_id": "tf_question_001",
      "question_type": "true_false",
      "student_answer": false,
      "correct_answer": true,
      "is_correct": false,
      "points_earned": 0,
      "points_possible": 1,
      "time_spent_seconds": 30,
      "answer_timestamp": "2024-01-21T10:03:45Z"
    }
  ],
  "scoring": {
    "total_points_earned": 2,
    "total_points_possible": 3,
    "percentage_score": 66.67,
    "letter_grade": "D",
    "passed": false,
    "passing_threshold": 70
  },
  "analytics": {
    "questions_correct": 1,
    "questions_incorrect": 1,
    "questions_skipped": 0,
    "average_time_per_question": 765,
    "difficulty_performance": {
      "easy": {"correct": 0, "total": 1},
      "medium": {"correct": 1, "total": 1},
      "hard": {"correct": 0, "total": 0}
    }
  }
}
```

### 4.2 Individual Question Response Model
```json
{
  "schema_version": "1.0",
  "response_id": "resp_001",
  "attempt_id": "attempt_001",
  "question_info": {
    "question_id": "mc_question_001",
    "question_type": "multiple_choice",
    "question_text": "What is the time complexity of the quicksort algorithm in the average case?",
    "correct_answer": "B",
    "points_possible": 2
  },
  "student_response": {
    "answer_given": "B",
    "is_correct": true,
    "points_earned": 2,
    "confidence_level": null,
    "time_spent_seconds": 45,
    "answer_changed": false,
    "initial_answer": "B",
    "final_answer": "B"
  },
  "timing_data": {
    "question_viewed_at": "2024-01-21T10:01:30Z",
    "first_answer_at": "2024-01-21T10:02:15Z",
    "final_answer_at": "2024-01-21T10:02:15Z",
    "time_to_first_answer": 45,
    "total_time_on_question": 45
  },
  "interaction_data": {
    "view_count": 1,
    "answer_changes": 0,
    "help_accessed": false,
    "explanation_viewed": false
  }
}
```

### 4.3 Basic Scoring and Grading Data Model
```json
{
  "schema_version": "1.0",
  "grading_session_id": "grade_001",
  "attempt_id": "attempt_001",
  "grading_info": {
    "graded_at": "2024-01-21T10:25:35Z",
    "grading_method": "automatic",
    "grader_id": "system",
    "grading_time_seconds": 2
  },
  "scoring_details": {
    "raw_score": 2,
    "max_score": 3,
    "percentage": 66.67,
    "weighted_score": 66.67,
    "letter_grade": "D",
    "grade_points": 1.0
  },
  "question_scores": [
    {
      "question_id": "mc_question_001",
      "points_earned": 2,
      "points_possible": 2,
      "percentage": 100.0,
      "feedback": "Correct! Well done."
    },
    {
      "question_id": "tf_question_001",
      "points_earned": 0,
      "points_possible": 1,
      "percentage": 0.0,
      "feedback": "Incorrect. Binary search requires a sorted array."
    }
  ],
  "grade_breakdown": {
    "multiple_choice": {
      "correct": 1,
      "total": 1,
      "percentage": 100.0
    },
    "true_false": {
      "correct": 0,
      "total": 1,
      "percentage": 0.0
    }
  }
}
```

### 4.4 Instructor Reporting Data Model
```json
{
  "schema_version": "1.0",
  "report_id": "report_001",
  "test_id": "test_001",
  "report_info": {
    "generated_at": "2024-01-21T15:00:00Z",
    "generated_by": "inst_12345",
    "report_type": "test_summary",
    "date_range": {
      "start": "2024-01-21T00:00:00Z",
      "end": "2024-01-21T23:59:59Z"
    }
  },
  "test_statistics": {
    "total_attempts": 20,
    "completed_attempts": 18,
    "incomplete_attempts": 2,
    "average_score": 78.5,
    "median_score": 80.0,
    "highest_score": 100.0,
    "lowest_score": 45.0,
    "standard_deviation": 12.3,
    "pass_rate": 0.75
  },
  "question_analysis": [
    {
      "question_id": "mc_question_001",
      "question_text": "What is the time complexity...",
      "total_responses": 18,
      "correct_responses": 15,
      "success_rate": 0.833,
      "average_time_seconds": 52,
      "difficulty_rating": "medium",
      "discrimination_index": 0.65
    }
  ],
  "student_performance": [
    {
      "student_id": "stud_67890",
      "student_name": "Jane Smith",
      "score": 66.67,
      "time_taken": 1530,
      "attempt_date": "2024-01-21T10:25:30Z",
      "status": "completed"
    }
  ],
  "recommendations": [
    "Question tf_question_001 has low success rate (45%). Consider reviewing or revising.",
    "Average completion time is 25 minutes. Consider adjusting time limit.",
    "75% pass rate indicates appropriate difficulty level."
  ]
}
```

---

## 5. DynamoDB Access Patterns

### 5.1 DynamoDB Query Patterns
```python
# DynamoDB access patterns for QuizGenius MVP

import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Dict, List, Optional

class DynamoDBClient:
    def __init__(self, region_name: str = "us-east-1"):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.tables = {
            'users': self.dynamodb.Table('QuizGenius-Users'),
            'documents': self.dynamodb.Table('QuizGenius-Documents'),
            'questions': self.dynamodb.Table('QuizGenius-Questions'),
            'tests': self.dynamodb.Table('QuizGenius-Tests'),
            'test_attempts': self.dynamodb.Table('QuizGenius-TestAttempts'),
            'results': self.dynamodb.Table('QuizGenius-Results')
        }
    
    # User data access patterns
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile from DynamoDB"""
        try:
            response = self.tables['users'].get_item(
                Key={
                    'user_id': user_id,
                    'record_type': 'profile'
                }
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def create_user_profile(self, user_data: Dict) -> bool:
        """Create user profile in DynamoDB"""
        try:
            self.tables['users'].put_item(Item=user_data)
            return True
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False
    
    # Question data access patterns
    def store_questions(self, questions: List[Dict]) -> bool:
        """Store generated questions in DynamoDB"""
        try:
            with self.tables['questions'].batch_writer() as batch:
                for question in questions:
                    batch.put_item(Item=question)
            return True
        except Exception as e:
            print(f"Error storing questions: {e}")
            return False
    
    def get_questions_by_creator(self, creator_id: str) -> List[Dict]:
        """Get questions created by specific instructor"""
        try:
            response = self.tables['questions'].query(
                IndexName='QuestionsByCreator-Index',
                KeyConditionExpression=Key('created_by').eq(creator_id)
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting questions: {e}")
            return []
    
    # Test data access patterns
    def store_test(self, test_data: Dict) -> bool:
        """Store test configuration in DynamoDB"""
        try:
            self.tables['tests'].put_item(Item=test_data)
            return True
        except Exception as e:
            print(f"Error storing test: {e}")
            return False
    
    def get_published_tests(self) -> List[Dict]:
        """Get all published tests"""
        try:
            response = self.tables['tests'].query(
                IndexName='TestsByStatus-Index',
                KeyConditionExpression=Key('status').eq('published')
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting published tests: {e}")
            return []
    
    # Results data access patterns
    def store_test_attempt(self, attempt_data: Dict) -> bool:
        """Store test attempt in DynamoDB"""
        try:
            self.tables['test_attempts'].put_item(Item=attempt_data)
            return True
        except Exception as e:
            print(f"Error storing test attempt: {e}")
            return False
    
    def get_student_attempts(self, student_id: str) -> List[Dict]:
        """Get all attempts by a student"""
        try:
            response = self.tables['test_attempts'].query(
                IndexName='AttemptsByStudent-Index',
                KeyConditionExpression=Key('student_id').eq(student_id)
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting student attempts: {e}")
            return []
    
    def get_test_attempts(self, test_id: str) -> List[Dict]:
        """Get all attempts for a specific test"""
        try:
            response = self.tables['test_attempts'].query(
                IndexName='AttemptsByTest-Index',
                KeyConditionExpression=Key('test_id').eq(test_id)
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting test attempts: {e}")
            return []
```

### 5.2 DynamoDB Data Validation
```python
# DynamoDB data validation for QuizGenius MVP

from typing import Dict, Any, List
import re
from datetime import datetime

class DynamoDBValidator:
    
    @staticmethod
    def validate_user_item(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user data before storing in DynamoDB"""
        errors = []
        
        # Required fields
        required_fields = ["user_id", "record_type", "username", "email", "user_role"]
        for field in required_fields:
            if field not in user_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate user_id format
        if "user_id" in user_data:
            if not re.match(r"^(inst|stud)_[a-zA-Z0-9]+$", user_data["user_id"]):
                errors.append("Invalid user_id format")
        
        # Validate email format
        if "email" in user_data:
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", user_data["email"]):
                errors.append("Invalid email format")
        
        # Validate user role
        if "user_role" in user_data:
            if user_data["user_role"] not in ["instructor", "student"]:
                errors.append("Invalid user role")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    @staticmethod
    def validate_question_item(question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate question data before storing in DynamoDB"""
        errors = []
        
        # Required fields
        required_fields = ["question_id", "type", "metadata", "content"]
        for field in required_fields:
            if field not in question_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate question type
        if "type" in question_data:
            if question_data["type"] not in ["multiple_choice", "true_false"]:
                errors.append("Invalid question type")
        
        # Validate metadata
        if "metadata" in question_data:
            metadata = question_data["metadata"]
            if "created_by" not in metadata or "created_at" not in metadata:
                errors.append("Missing required metadata fields")
        
        # Validate content based on type
        if "content" in question_data and "type" in question_data:
            content_validation = DynamoDBValidator._validate_question_content(
                question_data["content"], question_data["type"]
            )
            errors.extend(content_validation["errors"])
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    @staticmethod
    def _validate_question_content(content: Dict[str, Any], question_type: str) -> Dict[str, Any]:
        """Validate question content based on type"""
        errors = []
        
        if question_type == "multiple_choice":
            # Validate multiple choice content
            if "question" not in content:
                errors.append("Missing question text")
            if "options" not in content:
                errors.append("Missing answer options")
            elif len(content["options"]) < 2:
                errors.append("Multiple choice questions need at least 2 options")
            if "correct_answer" not in content:
                errors.append("Missing correct answer")
        
        elif question_type == "true_false":
            # Validate true/false content
            if "statement" not in content:
                errors.append("Missing statement text")
            if "correct_answer" not in content:
                errors.append("Missing correct answer")
            elif content["correct_answer"] not in [True, False]:
                errors.append("True/false answer must be boolean")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    @staticmethod
    def validate_test_item(test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test data before storing in DynamoDB"""
        errors = []
        
        # Required fields
        required_fields = ["test_id", "metadata", "configuration", "questions"]
        for field in required_fields:
            if field not in test_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate metadata
        if "metadata" in test_data:
            metadata = test_data["metadata"]
            required_meta = ["title", "created_by", "created_at"]
            for field in required_meta:
                if field not in metadata:
                    errors.append(f"Missing metadata field: {field}")
        
        # Validate questions array
        if "questions" in test_data:
            questions = test_data["questions"]
            if not isinstance(questions, list) or len(questions) == 0:
                errors.append("Test must have at least one question")
            
            for i, question in enumerate(questions):
                if "question_id" not in question:
                    errors.append(f"Question {i+1} missing question_id")
                if "points" not in question:
                    errors.append(f"Question {i+1} missing points")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    @staticmethod
    def validate_test_attempt_item(attempt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test attempt data before storing in DynamoDB"""
        errors = []
        
        # Required fields
        required_fields = ["attempt_id", "test_info", "student_info", "attempt_details"]
        for field in required_fields:
            if field not in attempt_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate test_info
        if "test_info" in attempt_data:
            test_info = attempt_data["test_info"]
            if "test_id" not in test_info:
                errors.append("Missing test_id in test_info")
        
        # Validate student_info
        if "student_info" in attempt_data:
            student_info = attempt_data["student_info"]
            if "student_id" not in student_info:
                errors.append("Missing student_id in student_info")
        
        # Validate responses if present
        if "responses" in attempt_data:
            responses = attempt_data["responses"]
            if not isinstance(responses, list):
                errors.append("Responses must be a list")
        
        return {"valid": len(errors) == 0, "errors": errors}
```

### 5.3 DynamoDB Table Management
```python
# DynamoDB table creation and management

import boto3
from botocore.exceptions import ClientError

class DynamoDBTableManager:
    
    def __init__(self, region_name: str = "us-east-1"):
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.region_name = region_name
    
    def create_all_tables(self):
        """Create all required DynamoDB tables"""
        tables = [
            self._get_users_table_definition(),
            self._get_documents_table_definition(),
            self._get_questions_table_definition(),
            self._get_tests_table_definition(),
            self._get_test_attempts_table_definition(),
            self._get_results_table_definition()
        ]
        
        for table_def in tables:
            self._create_table_if_not_exists(table_def)
    
    def _create_table_if_not_exists(self, table_definition: dict):
        """Create table if it doesn't exist"""
        table_name = table_definition['TableName']
        
        try:
            # Check if table exists
            self.dynamodb.describe_table(TableName=table_name)
            print(f"Table {table_name} already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                try:
                    self.dynamodb.create_table(**table_definition)
                    print(f"Created table {table_name}")
                    
                    # Wait for table to be active
                    waiter = self.dynamodb.get_waiter('table_exists')
                    waiter.wait(TableName=table_name)
                    print(f"Table {table_name} is now active")
                    
                except ClientError as create_error:
                    print(f"Error creating table {table_name}: {create_error}")
            else:
                print(f"Error checking table {table_name}: {e}")
    
    def _get_users_table_definition(self) -> dict:
        """Get Users table definition"""
        return {
            'TableName': 'QuizGenius-Users',
            'KeySchema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'record_type', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'record_type', 'AttributeType': 'S'},
                {'AttributeName': 'user_role', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'UsersByRole-Index',
                    'KeySchema': [
                        {'AttributeName': 'user_role', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    
    def _get_documents_table_definition(self) -> dict:
        """Get Documents table definition"""
        return {
            'TableName': 'QuizGenius-Documents',
            'KeySchema': [
                {'AttributeName': 'document_id', 'KeyType': 'HASH'},
                {'AttributeName': 'record_type', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'document_id', 'AttributeType': 'S'},
                {'AttributeName': 'record_type', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    
    def _get_questions_table_definition(self) -> dict:
        """Get Questions table definition"""
        return {
            'TableName': 'QuizGenius-Questions',
            'KeySchema': [
                {'AttributeName': 'question_id', 'KeyType': 'HASH'},
                {'AttributeName': 'version', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'question_id', 'AttributeType': 'S'},
                {'AttributeName': 'version', 'AttributeType': 'N'},
                {'AttributeName': 'created_by', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'QuestionsByCreator-Index',
                    'KeySchema': [
                        {'AttributeName': 'created_by', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    
    def _get_tests_table_definition(self) -> dict:
        """Get Tests table definition"""
        return {
            'TableName': 'QuizGenius-Tests',
            'KeySchema': [
                {'AttributeName': 'test_id', 'KeyType': 'HASH'},
                {'AttributeName': 'record_type', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'test_id', 'AttributeType': 'S'},
                {'AttributeName': 'record_type', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'TestsByStatus-Index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    
    def _get_test_attempts_table_definition(self) -> dict:
        """Get TestAttempts table definition"""
        return {
            'TableName': 'QuizGenius-TestAttempts',
            'KeySchema': [
                {'AttributeName': 'attempt_id', 'KeyType': 'HASH'},
                {'AttributeName': 'student_id', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'attempt_id', 'AttributeType': 'S'},
                {'AttributeName': 'student_id', 'AttributeType': 'S'},
                {'AttributeName': 'test_id', 'AttributeType': 'S'},
                {'AttributeName': 'completed_at', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'AttemptsByStudent-Index',
                    'KeySchema': [
                        {'AttributeName': 'student_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'completed_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'AttemptsByTest-Index',
                    'KeySchema': [
                        {'AttributeName': 'test_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'completed_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    
    def _get_results_table_definition(self) -> dict:
        """Get Results table definition"""
        return {
            'TableName': 'QuizGenius-Results',
            'KeySchema': [
                {'AttributeName': 'result_id', 'KeyType': 'HASH'},
                {'AttributeName': 'record_type', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'result_id', 'AttributeType': 'S'},
                {'AttributeName': 'record_type', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
```

---

## Summary

This DynamoDB data models document provides:

1. **Complete DynamoDB Architecture** - Six core tables with proper partition/sort key design
2. **Detailed Schema Models** - DynamoDB item structures for users, questions, tests, and results
3. **Data Relationships** - Clear relationships between different data entities using DynamoDB patterns
4. **Access Patterns** - Efficient DynamoDB query patterns with GSI support
5. **Validation Framework** - Data integrity validation for DynamoDB items
6. **Table Management** - Automated DynamoDB table creation and configuration
7. **Storage Optimization** - Efficient DynamoDB storage patterns with proper indexing

The models support all MVP requirements using AWS DynamoDB as specified in the user stories, providing:
- **Scalable Storage**: DynamoDB's managed NoSQL database
- **High Performance**: Optimized query patterns with Global Secondary Indexes
- **Data Integrity**: Comprehensive validation before data storage
- **AWS Integration**: Native integration with other AWS services used in the application

This architecture aligns with user stories 4.4.1, 4.4.2, and 4.4.3 which specifically require DynamoDB for data storage.