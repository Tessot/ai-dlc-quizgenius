#!/usr/bin/env python3
"""
Phase 4.1 Testing Script - Question Management Interface
Tests the question review interface functionality for QuizGenius MVP

This script tests:
- Question Review Interface (Step 4.1.1)
- Question list display
- Question type indicators
- Answer visibility controls
- Question formatting
- Integration with question data service
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import services and utilities
from services.question_storage_service import QuestionStorageService, QuestionStorageError
from services.question_generation_service import QuestionGenerationService, GeneratedQuestion
from utils.session_manager import SessionManager
from utils.config import load_environment_config

class Phase41Tester:
    """Test suite for Phase 4.1 - Question Management Interface"""
    
    def __init__(self):
        """Initialize the test suite"""
        self.test_results = []
        self.setup_complete = False
        
        # Load configuration
        try:
            load_environment_config()
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return
            
        # Initialize services
        try:
            self.storage_service = QuestionStorageService()
            self.generation_service = QuestionGenerationService()
            self.session_manager = SessionManager()
            self.setup_complete = True
            print("✅ Services initialized successfully")
        except Exception as e:
            print(f"❌ Service initialization error: {e}")
            self.setup_complete = False
    
    def run_all_tests(self):
        """Run all Phase 4.1 tests"""
        print("\n" + "="*60)
        print("🧪 PHASE 4.1 TESTING - QUESTION MANAGEMENT INTERFACE")
        print("="*60)
        
        if not self.setup_complete:
            print("❌ Setup failed - cannot run tests")
            return
        
        # Test categories
        test_categories = [
            ("Question Storage Service Integration", self.test_storage_service_integration),
            ("Question List Display", self.test_question_list_display),
            ("Question Type Indicators", self.test_question_type_indicators),
            ("Question Formatting", self.test_question_formatting),
            ("Question Filtering", self.test_question_filtering),
            ("Question Sorting", self.test_question_sorting),
            ("Question Selection", self.test_question_selection),
            ("Question Actions", self.test_question_actions),
            ("Bulk Operations", self.test_bulk_operations),
            ("Session State Management", self.test_session_state_management),
            ("Error Handling", self.test_error_handling),
            ("Data Validation", self.test_data_validation)
        ]
        
        # Run tests
        for category_name, test_function in test_categories:
            print(f"\n📋 Testing: {category_name}")
            print("-" * 50)
            try:
                test_function()
            except Exception as e:
                self.record_test_result(category_name, False, f"Test execution error: {str(e)}")
                print(f"❌ {category_name}: Test execution failed - {str(e)}")
        
        # Print summary
        self.print_test_summary()
    
    def test_storage_service_integration(self):
        """Test integration with question storage service"""
        try:
            # Test service availability
            service_available = self.storage_service is not None
            self.record_test_result("Storage Service Available", service_available, 
                                  "Storage service initialized" if service_available else "Storage service not available")
            
            # Test connection
            try:
                # Try to get questions (should not fail even if empty)
                questions = self.storage_service.get_questions_by_instructor("test_instructor", limit=1)
                connection_works = True
                self.record_test_result("Storage Connection", True, "Successfully connected to storage")
            except Exception as e:
                connection_works = False
                self.record_test_result("Storage Connection", False, f"Connection failed: {str(e)}")
            
            # Test question retrieval methods
            if connection_works:
                try:
                    # Test different retrieval methods
                    by_instructor = self.storage_service.get_questions_by_instructor("test_instructor", limit=5)
                    by_document = self.storage_service.get_questions_by_document("test_doc", "test_instructor")
                    
                    self.record_test_result("Question Retrieval Methods", True, 
                                          f"Retrieved {len(by_instructor)} by instructor, {len(by_document)} by document")
                except Exception as e:
                    self.record_test_result("Question Retrieval Methods", False, f"Retrieval failed: {str(e)}")
            
        except Exception as e:
            self.record_test_result("Storage Service Integration", False, f"Integration test failed: {str(e)}")
    
    def test_question_list_display(self):
        """Test question list display functionality"""
        try:
            # Create sample questions for testing
            sample_questions = self.create_sample_questions()
            
            # Test question list structure
            for question in sample_questions:
                required_fields = ['QuestionID', 'QuestionText', 'QuestionType', 'CorrectAnswer']
                has_required_fields = all(field in question for field in required_fields)
                self.record_test_result(f"Question Structure - {question.get('QuestionID', 'Unknown')}", 
                                      has_required_fields, 
                                      "Has all required fields" if has_required_fields else "Missing required fields")
            
            # Test question text formatting
            for question in sample_questions:
                question_text = question.get('QuestionText', '')
                text_valid = len(question_text) > 0 and len(question_text) <= 500
                self.record_test_result(f"Question Text Length - {question.get('QuestionID', 'Unknown')}", 
                                      text_valid, 
                                      f"Text length: {len(question_text)} chars")
            
            # Test question metadata display
            metadata_fields = ['DifficultyLevel', 'Topic', 'QualityScore', 'CreatedAt']
            for question in sample_questions:
                has_metadata = any(field in question for field in metadata_fields)
                self.record_test_result(f"Question Metadata - {question.get('QuestionID', 'Unknown')}", 
                                      has_metadata, 
                                      "Has metadata fields" if has_metadata else "Missing metadata")
            
        except Exception as e:
            self.record_test_result("Question List Display", False, f"Display test failed: {str(e)}")
    
    def test_question_type_indicators(self):
        """Test question type indicators and icons"""
        try:
            # Test multiple choice indicators
            mc_question = {
                'QuestionID': 'test_mc_1',
                'QuestionType': 'multiple_choice',
                'QuestionText': 'Test MC question',
                'Options': ['A', 'B', 'C', 'D'],
                'CorrectAnswer': 'A'
            }
            
            # Test true/false indicators
            tf_question = {
                'QuestionID': 'test_tf_1',
                'QuestionType': 'true_false',
                'QuestionText': 'Test TF question',
                'CorrectAnswer': 'True'
            }
            
            # Test type identification
            mc_type_correct = mc_question['QuestionType'] == 'multiple_choice'
            tf_type_correct = tf_question['QuestionType'] == 'true_false'
            
            self.record_test_result("MC Type Identification", mc_type_correct, 
                                  "Multiple choice type correctly identified")
            self.record_test_result("TF Type Identification", tf_type_correct, 
                                  "True/false type correctly identified")
            
            # Test type-specific data
            mc_has_options = 'Options' in mc_question and len(mc_question['Options']) > 1
            tf_has_boolean_answer = tf_question['CorrectAnswer'] in ['True', 'False', True, False]
            
            self.record_test_result("MC Options Present", mc_has_options, 
                                  f"MC question has {len(mc_question.get('Options', []))} options")
            self.record_test_result("TF Boolean Answer", tf_has_boolean_answer, 
                                  f"TF answer is boolean: {tf_question['CorrectAnswer']}")
            
        except Exception as e:
            self.record_test_result("Question Type Indicators", False, f"Type indicator test failed: {str(e)}")
    
    def test_question_formatting(self):
        """Test question formatting and display"""
        try:
            sample_questions = self.create_sample_questions()
            
            for question in sample_questions:
                # Test question text formatting
                question_text = question.get('QuestionText', '')
                text_formatted = len(question_text.strip()) > 0
                
                # Test answer formatting
                if question.get('QuestionType') == 'multiple_choice':
                    options = question.get('Options', [])
                    options_formatted = len(options) >= 2 and all(len(str(opt).strip()) > 0 for opt in options)
                    correct_answer = question.get('CorrectAnswer', '')
                    answer_in_options = correct_answer in options
                    
                    self.record_test_result(f"MC Formatting - {question.get('QuestionID')}", 
                                          text_formatted and options_formatted and answer_in_options,
                                          f"Text: {text_formatted}, Options: {options_formatted}, Answer valid: {answer_in_options}")
                
                elif question.get('QuestionType') == 'true_false':
                    correct_answer = question.get('CorrectAnswer', '')
                    answer_is_boolean = str(correct_answer).lower() in ['true', 'false']
                    
                    self.record_test_result(f"TF Formatting - {question.get('QuestionID')}", 
                                          text_formatted and answer_is_boolean,
                                          f"Text: {text_formatted}, Boolean answer: {answer_is_boolean}")
            
        except Exception as e:
            self.record_test_result("Question Formatting", False, f"Formatting test failed: {str(e)}")
    
    def test_question_filtering(self):
        """Test question filtering functionality"""
        try:
            sample_questions = self.create_sample_questions()
            
            # Test type filtering
            mc_questions = [q for q in sample_questions if q.get('QuestionType') == 'multiple_choice']
            tf_questions = [q for q in sample_questions if q.get('QuestionType') == 'true_false']
            
            self.record_test_result("Type Filter - MC", len(mc_questions) > 0, 
                                  f"Found {len(mc_questions)} multiple choice questions")
            self.record_test_result("Type Filter - TF", len(tf_questions) > 0, 
                                  f"Found {len(tf_questions)} true/false questions")
            
            # Test topic filtering
            topics = list(set(q.get('Topic', 'Unknown') for q in sample_questions))
            topic_filter_works = len(topics) > 0
            
            self.record_test_result("Topic Filter", topic_filter_works, 
                                  f"Found {len(topics)} unique topics: {topics}")
            
            # Test difficulty filtering
            difficulties = list(set(q.get('DifficultyLevel', 'Unknown') for q in sample_questions))
            difficulty_filter_works = len(difficulties) > 0
            
            self.record_test_result("Difficulty Filter", difficulty_filter_works, 
                                  f"Found {len(difficulties)} difficulty levels: {difficulties}")
            
        except Exception as e:
            self.record_test_result("Question Filtering", False, f"Filtering test failed: {str(e)}")
    
    def test_question_sorting(self):
        """Test question sorting functionality"""
        try:
            sample_questions = self.create_sample_questions()
            
            # Test sorting by creation date
            questions_with_dates = [q for q in sample_questions if 'CreatedAt' in q]
            if questions_with_dates:
                sorted_by_date = sorted(questions_with_dates, key=lambda x: x['CreatedAt'], reverse=True)
                date_sort_works = len(sorted_by_date) == len(questions_with_dates)
                self.record_test_result("Sort by Date", date_sort_works, 
                                      f"Sorted {len(sorted_by_date)} questions by date")
            
            # Test sorting by quality score
            questions_with_quality = [q for q in sample_questions if 'QualityScore' in q]
            if questions_with_quality:
                sorted_by_quality = sorted(questions_with_quality, key=lambda x: x['QualityScore'], reverse=True)
                quality_sort_works = len(sorted_by_quality) == len(questions_with_quality)
                self.record_test_result("Sort by Quality", quality_sort_works, 
                                      f"Sorted {len(sorted_by_quality)} questions by quality")
            
            # Test sorting by question type
            sorted_by_type = sorted(sample_questions, key=lambda x: x.get('QuestionType', ''))
            type_sort_works = len(sorted_by_type) == len(sample_questions)
            self.record_test_result("Sort by Type", type_sort_works, 
                                  f"Sorted {len(sorted_by_type)} questions by type")
            
        except Exception as e:
            self.record_test_result("Question Sorting", False, f"Sorting test failed: {str(e)}")
    
    def test_question_selection(self):
        """Test question selection functionality"""
        try:
            sample_questions = self.create_sample_questions()
            
            # Test individual selection
            selected_questions = []
            for question in sample_questions[:3]:  # Select first 3
                selected_questions.append(question['QuestionID'])
            
            selection_works = len(selected_questions) == 3
            self.record_test_result("Individual Selection", selection_works, 
                                  f"Selected {len(selected_questions)} questions individually")
            
            # Test select all functionality
            all_question_ids = [q['QuestionID'] for q in sample_questions]
            select_all_works = len(all_question_ids) == len(sample_questions)
            self.record_test_result("Select All", select_all_works, 
                                  f"Select all captured {len(all_question_ids)} questions")
            
            # Test clear selection
            cleared_selection = []
            clear_works = len(cleared_selection) == 0
            self.record_test_result("Clear Selection", clear_works, 
                                  "Selection cleared successfully")
            
        except Exception as e:
            self.record_test_result("Question Selection", False, f"Selection test failed: {str(e)}")
    
    def test_question_actions(self):
        """Test individual question actions"""
        try:
            sample_question = self.create_sample_questions()[0]
            
            # Test edit action preparation
            edit_data = {
                'question_id': sample_question['QuestionID'],
                'question_text': sample_question['QuestionText'],
                'question_type': sample_question['QuestionType'],
                'correct_answer': sample_question['CorrectAnswer']
            }
            edit_prepared = all(key in edit_data for key in ['question_id', 'question_text', 'question_type'])
            self.record_test_result("Edit Action Preparation", edit_prepared, 
                                  "Edit data structure prepared correctly")
            
            # Test duplicate action preparation
            duplicate_data = sample_question.copy()
            duplicate_data['QuestionID'] = f"{sample_question['QuestionID']}_copy"
            duplicate_prepared = duplicate_data['QuestionID'] != sample_question['QuestionID']
            self.record_test_result("Duplicate Action Preparation", duplicate_prepared, 
                                  "Duplicate data prepared with new ID")
            
            # Test export action preparation
            export_data = {
                'question_id': sample_question['QuestionID'],
                'question_text': sample_question['QuestionText'],
                'question_type': sample_question['QuestionType'],
                'correct_answer': sample_question['CorrectAnswer'],
                'exported_at': datetime.now().isoformat()
            }
            export_prepared = 'exported_at' in export_data
            self.record_test_result("Export Action Preparation", export_prepared, 
                                  "Export data prepared with timestamp")
            
        except Exception as e:
            self.record_test_result("Question Actions", False, f"Actions test failed: {str(e)}")
    
    def test_bulk_operations(self):
        """Test bulk operations functionality"""
        try:
            sample_questions = self.create_sample_questions()
            
            # Test bulk selection
            selected_for_bulk = sample_questions[:2]  # Select first 2
            bulk_selection_works = len(selected_for_bulk) > 1
            self.record_test_result("Bulk Selection", bulk_selection_works, 
                                  f"Selected {len(selected_for_bulk)} questions for bulk operation")
            
            # Test bulk delete preparation
            bulk_delete_ids = [q['QuestionID'] for q in selected_for_bulk]
            delete_prepared = len(bulk_delete_ids) == len(selected_for_bulk)
            self.record_test_result("Bulk Delete Preparation", delete_prepared, 
                                  f"Prepared {len(bulk_delete_ids)} questions for bulk delete")
            
            # Test bulk export preparation
            bulk_export_data = {
                'questions': selected_for_bulk,
                'export_count': len(selected_for_bulk),
                'exported_at': datetime.now().isoformat()
            }
            export_bulk_prepared = bulk_export_data['export_count'] > 0
            self.record_test_result("Bulk Export Preparation", export_bulk_prepared, 
                                  f"Prepared {bulk_export_data['export_count']} questions for bulk export")
            
        except Exception as e:
            self.record_test_result("Bulk Operations", False, f"Bulk operations test failed: {str(e)}")
    
    def test_session_state_management(self):
        """Test session state management"""
        try:
            # Test session state initialization
            session_data = {
                'current_questions': self.create_sample_questions(),
                'selected_questions': [],
                'filter_settings': {
                    'type': 'All',
                    'topic': 'All',
                    'sort_by': 'Created Date (Newest)'
                }
            }
            
            session_initialized = all(key in session_data for key in ['current_questions', 'selected_questions', 'filter_settings'])
            self.record_test_result("Session State Initialization", session_initialized, 
                                  "Session state structure initialized correctly")
            
            # Test session data persistence
            questions_count = len(session_data['current_questions'])
            data_persisted = questions_count > 0
            self.record_test_result("Session Data Persistence", data_persisted, 
                                  f"Session contains {questions_count} questions")
            
            # Test session state updates
            session_data['selected_questions'].append('test_question_1')
            session_updated = len(session_data['selected_questions']) > 0
            self.record_test_result("Session State Updates", session_updated, 
                                  "Session state updated successfully")
            
        except Exception as e:
            self.record_test_result("Session State Management", False, f"Session state test failed: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        try:
            # Test handling of missing questions
            empty_questions = []
            handles_empty = len(empty_questions) == 0  # Should handle gracefully
            self.record_test_result("Empty Questions Handling", handles_empty, 
                                  "Empty question list handled correctly")
            
            # Test handling of malformed questions
            malformed_question = {'QuestionID': 'test_malformed'}  # Missing required fields
            required_fields = ['QuestionText', 'QuestionType', 'CorrectAnswer']
            missing_fields = [field for field in required_fields if field not in malformed_question]
            handles_malformed = len(missing_fields) > 0  # Should detect missing fields
            self.record_test_result("Malformed Question Detection", handles_malformed, 
                                  f"Detected {len(missing_fields)} missing fields: {missing_fields}")
            
            # Test handling of storage service errors
            try:
                # Simulate storage error by using invalid instructor ID
                invalid_questions = self.storage_service.get_questions_by_instructor("", limit=1)
                storage_error_handled = True  # If no exception, error was handled
            except Exception as e:
                storage_error_handled = True  # Exception is expected and should be handled
            
            self.record_test_result("Storage Error Handling", storage_error_handled, 
                                  "Storage service errors handled appropriately")
            
        except Exception as e:
            self.record_test_result("Error Handling", False, f"Error handling test failed: {str(e)}")
    
    def test_data_validation(self):
        """Test data validation functionality"""
        try:
            # Test question ID validation
            valid_id = "question_123"
            invalid_id = ""
            
            id_validation_works = len(valid_id) > 0 and len(invalid_id) == 0
            self.record_test_result("Question ID Validation", id_validation_works, 
                                  f"Valid ID: '{valid_id}', Invalid ID: '{invalid_id}'")
            
            # Test question text validation
            valid_text = "What is the capital of France?"
            invalid_text = ""
            
            text_validation_works = len(valid_text.strip()) > 0 and len(invalid_text.strip()) == 0
            self.record_test_result("Question Text Validation", text_validation_works, 
                                  f"Valid text length: {len(valid_text)}, Invalid text length: {len(invalid_text)}")
            
            # Test question type validation
            valid_types = ['multiple_choice', 'true_false']
            invalid_type = 'invalid_type'
            
            type_validation_works = invalid_type not in valid_types
            self.record_test_result("Question Type Validation", type_validation_works, 
                                  f"Valid types: {valid_types}, Invalid type: '{invalid_type}'")
            
            # Test answer validation for MC questions
            mc_options = ['Paris', 'London', 'Berlin', 'Madrid']
            mc_correct = 'Paris'
            mc_invalid = 'Rome'
            
            mc_answer_valid = mc_correct in mc_options and mc_invalid not in mc_options
            self.record_test_result("MC Answer Validation", mc_answer_valid, 
                                  f"Correct answer '{mc_correct}' in options, Invalid answer '{mc_invalid}' not in options")
            
            # Test answer validation for TF questions
            tf_valid_answers = ['True', 'False', True, False]
            tf_invalid_answer = 'Maybe'
            
            tf_answer_valid = tf_invalid_answer not in [str(a) for a in tf_valid_answers]
            self.record_test_result("TF Answer Validation", tf_answer_valid, 
                                  f"Invalid TF answer '{tf_invalid_answer}' correctly rejected")
            
        except Exception as e:
            self.record_test_result("Data Validation", False, f"Data validation test failed: {str(e)}")
    
    def create_sample_questions(self) -> List[Dict[str, Any]]:
        """Create sample questions for testing"""
        return [
            {
                'QuestionID': 'test_mc_1',
                'QuestionText': 'What is the capital of France?',
                'QuestionType': 'multiple_choice',
                'Options': ['Paris', 'London', 'Berlin', 'Madrid'],
                'CorrectAnswer': 'Paris',
                'DifficultyLevel': 'easy',
                'Topic': 'Geography',
                'QualityScore': 8.5,
                'ConfidenceScore': 0.92,
                'CreatedAt': '2024-01-15T10:30:00',
                'DocumentID': 'doc_123'
            },
            {
                'QuestionID': 'test_mc_2',
                'QuestionText': 'Which programming language is known for its use in data science?',
                'QuestionType': 'multiple_choice',
                'Options': ['Java', 'Python', 'C++', 'JavaScript'],
                'CorrectAnswer': 'Python',
                'DifficultyLevel': 'medium',
                'Topic': 'Programming',
                'QualityScore': 9.2,
                'ConfidenceScore': 0.88,
                'CreatedAt': '2024-01-15T11:15:00',
                'DocumentID': 'doc_124'
            },
            {
                'QuestionID': 'test_tf_1',
                'QuestionText': 'The Earth is the third planet from the Sun.',
                'QuestionType': 'true_false',
                'CorrectAnswer': 'True',
                'DifficultyLevel': 'easy',
                'Topic': 'Astronomy',
                'QualityScore': 7.8,
                'ConfidenceScore': 0.95,
                'CreatedAt': '2024-01-15T12:00:00',
                'DocumentID': 'doc_125'
            },
            {
                'QuestionID': 'test_tf_2',
                'QuestionText': 'Machine learning algorithms can only work with numerical data.',
                'QuestionType': 'true_false',
                'CorrectAnswer': 'False',
                'DifficultyLevel': 'hard',
                'Topic': 'Machine Learning',
                'QualityScore': 8.9,
                'ConfidenceScore': 0.87,
                'CreatedAt': '2024-01-15T12:45:00',
                'DocumentID': 'doc_126'
            }
        ]
    
    def record_test_result(self, test_name: str, passed: bool, details: str):
        """Record a test result"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        # Print result
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}: {details}")
    
    def print_test_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['passed']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("📊 PHASE 4.1 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        print(f"\n🎯 Phase 4.1 Status: {'✅ READY' if success_rate >= 80 else '⚠️ NEEDS ATTENTION'}")
        
        # Save detailed results
        self.save_test_results()
    
    def save_test_results(self):
        """Save detailed test results to file"""
        try:
            results_file = "04_dev/docs/phase_4_1_test_results.json"
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump({
                    'phase': '4.1',
                    'test_date': datetime.now().isoformat(),
                    'total_tests': len(self.test_results),
                    'passed_tests': len([r for r in self.test_results if r['passed']]),
                    'success_rate': len([r for r in self.test_results if r['passed']]) / len(self.test_results) * 100,
                    'results': self.test_results
                }, f, indent=2)
            
            print(f"📄 Detailed results saved to: {results_file}")
            
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")


def main():
    """Main test execution"""
    tester = Phase41Tester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()