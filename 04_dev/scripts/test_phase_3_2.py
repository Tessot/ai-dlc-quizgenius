#!/usr/bin/env python3
"""
Phase 3.2 Testing Script for QuizGenius MVP
Tests Question Processing Backend functionality

This script tests:
- Step 3.2.1: Multiple Choice Processing
- Step 3.2.2: True/False Processing  
- Step 3.2.3: Question Data Storage
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.question_processor import QuestionProcessor, ProcessedQuestion
from services.question_storage_service import QuestionStorageService
from services.question_generation_service import GeneratedQuestion
from utils.config import Config

class Phase32Tester:
    """Test Phase 3.2 functionality"""
    
    def __init__(self):
        """Initialize tester"""
        self.config = Config()
        self.question_processor = QuestionProcessor()
        
        # Try to initialize storage service (may fail if DynamoDB not available)
        try:
            self.storage_service = QuestionStorageService()
            self.storage_available = True
        except Exception as e:
            print(f"⚠️  Storage service not available: {e}")
            self.storage_service = None
            self.storage_available = False
        
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def run_all_tests(self):
        """Run all Phase 3.2 tests"""
        print("🚀 Starting Phase 3.2: Question Processing Backend Tests")
        print("=" * 70)
        
        # Test Step 3.2.1: Multiple Choice Processing
        print("\n🔤 Testing Step 3.2.1: Multiple Choice Processing")
        print("-" * 50)
        self.test_multiple_choice_processing()
        
        # Test Step 3.2.2: True/False Processing
        print("\n✅ Testing Step 3.2.2: True/False Processing")
        print("-" * 50)
        self.test_true_false_processing()
        
        # Test Step 3.2.3: Question Data Storage
        print("\n💾 Testing Step 3.2.3: Question Data Storage")
        print("-" * 50)
        self.test_question_data_storage()
        
        # Show final results
        self.show_final_results()
        
    def test_multiple_choice_processing(self):
        """Test multiple choice question processing"""
        
        # Test 1: MC question validation
        self.run_test(
            "MC Question Validation",
            self._test_mc_question_validation
        )
        
        # Test 2: MC question enhancement
        self.run_test(
            "MC Question Enhancement",
            self._test_mc_question_enhancement
        )
        
        # Test 3: Distractor quality assessment
        self.run_test(
            "Distractor Quality Assessment",
            self._test_distractor_quality_assessment
        )
        
        # Test 4: MC quality scoring
        self.run_test(
            "MC Quality Scoring",
            self._test_mc_quality_scoring
        )
        
    def test_true_false_processing(self):
        """Test true/false question processing"""
        
        # Test 5: T/F question validation
        self.run_test(
            "T/F Question Validation",
            self._test_tf_question_validation
        )
        
        # Test 6: Statement clarity validation
        self.run_test(
            "Statement Clarity Validation",
            self._test_statement_clarity_validation
        )
        
        # Test 7: Ambiguity detection
        self.run_test(
            "Ambiguity Detection",
            self._test_ambiguity_detection
        )
        
        # Test 8: T/F quality scoring
        self.run_test(
            "T/F Quality Scoring",
            self._test_tf_quality_scoring
        )
        
    def test_question_data_storage(self):
        """Test question data storage functionality"""
        
        if not self.storage_available:
            print("⚠️  Skipping storage tests - DynamoDB not available")
            return
        
        # Test 9: Single question storage
        self.run_test(
            "Single Question Storage",
            self._test_single_question_storage
        )
        
        # Test 10: Batch question storage
        self.run_test(
            "Batch Question Storage",
            self._test_batch_question_storage
        )
        
        # Test 11: Question retrieval
        self.run_test(
            "Question Retrieval",
            self._test_question_retrieval
        )
        
        # Test 12: Question update
        self.run_test(
            "Question Update",
            self._test_question_update
        )
        
        # Test 13: Question statistics
        self.run_test(
            "Question Statistics",
            self._test_question_statistics
        )
        
    def _test_mc_question_validation(self) -> Dict[str, Any]:
        """Test multiple choice question validation"""
        try:
            # Create test MC question
            test_question = self._create_test_mc_question()
            
            # Process the question
            processed = self.question_processor.process_multiple_choice_question(test_question)
            
            # Check validation results
            validation = processed.validation_result
            has_validation = validation is not None
            has_quality_score = hasattr(validation, 'quality_score')
            has_issues = hasattr(validation, 'issues')
            has_suggestions = hasattr(validation, 'suggestions')
            
            success = has_validation and has_quality_score and has_issues and has_suggestions
            
            return {
                'success': success,
                'details': f"Quality score: {validation.quality_score:.1f}, Issues: {len(validation.issues)}, Suggestions: {len(validation.suggestions)}",
                'error': None if success else "MC question validation failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_mc_question_enhancement(self) -> Dict[str, Any]:
        """Test multiple choice question enhancement"""
        try:
            # Create test question with issues
            test_question = GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                question_text="what is machine learning",  # No capitalization, no question mark
                question_type="multiple_choice",
                correct_answer="AI branch",
                options=["AI branch", "programming language", "database", "web framework"],
                difficulty_level="beginner",
                topic="AI",
                source_content="Test content",
                confidence_score=0.8,
                metadata={}
            )
            
            # Process the question
            processed = self.question_processor.process_multiple_choice_question(test_question)
            
            # Check enhancements
            text_enhanced = processed.processed_text != test_question.question_text
            text_has_question_mark = processed.processed_text.endswith('?')
            text_capitalized = processed.processed_text[0].isupper()
            
            success = text_enhanced and text_has_question_mark and text_capitalized
            
            return {
                'success': success,
                'details': f"Original: '{test_question.question_text}' -> Enhanced: '{processed.processed_text}'",
                'error': None if success else "MC question enhancement failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_distractor_quality_assessment(self) -> Dict[str, Any]:
        """Test distractor quality assessment"""
        try:
            # Create question with varying distractor quality
            test_question = GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                question_text="What is the capital of France?",
                question_type="multiple_choice",
                correct_answer="Paris",
                options=["Paris", "London", "Berlin", "Madrid"],
                difficulty_level="beginner",
                topic="Geography",
                source_content="Test content",
                confidence_score=0.9,
                metadata={}
            )
            
            # Process the question
            processed = self.question_processor.process_multiple_choice_question(test_question)
            
            # Check if distractor assessment was performed
            validation_details = processed.validation_result.validation_details
            has_distractor_quality = 'distractor_quality' in validation_details
            
            if has_distractor_quality:
                distractor_info = validation_details['distractor_quality']
                has_distractors = 'distractors' in distractor_info
                has_scores = 'individual_scores' in distractor_info
                has_average = 'average_plausibility' in distractor_info
                
                success = has_distractors and has_scores and has_average
            else:
                success = False
            
            return {
                'success': success,
                'details': f"Distractor assessment available: {has_distractor_quality}",
                'error': None if success else "Distractor quality assessment failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_mc_quality_scoring(self) -> Dict[str, Any]:
        """Test MC quality scoring"""
        try:
            # Test with good quality question
            good_question = self._create_test_mc_question()
            processed_good = self.question_processor.process_multiple_choice_question(good_question)
            
            # Test with poor quality question
            poor_question = GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                question_text="What?",  # Too short
                question_type="multiple_choice",
                correct_answer="A",
                options=["A", "B", "C"],  # Only 3 options, too short
                difficulty_level="beginner",
                topic="Test",
                source_content="Test",
                confidence_score=0.5,
                metadata={}
            )
            processed_poor = self.question_processor.process_multiple_choice_question(poor_question)
            
            # Check scoring
            good_score = processed_good.quality_score
            poor_score = processed_poor.quality_score
            
            score_range_valid = 0 <= good_score <= 10 and 0 <= poor_score <= 10
            good_better_than_poor = good_score > poor_score
            
            success = score_range_valid and good_better_than_poor
            
            return {
                'success': success,
                'details': f"Good question score: {good_score:.1f}, Poor question score: {poor_score:.1f}",
                'error': None if success else "MC quality scoring failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_tf_question_validation(self) -> Dict[str, Any]:
        """Test true/false question validation"""
        try:
            # Create test T/F question
            test_question = self._create_test_tf_question()
            
            # Process the question
            processed = self.question_processor.process_true_false_question(test_question)
            
            # Check validation results
            validation = processed.validation_result
            has_validation = validation is not None
            has_quality_score = hasattr(validation, 'quality_score')
            has_issues = hasattr(validation, 'issues')
            has_suggestions = hasattr(validation, 'suggestions')
            
            success = has_validation and has_quality_score and has_issues and has_suggestions
            
            return {
                'success': success,
                'details': f"Quality score: {validation.quality_score:.1f}, Issues: {len(validation.issues)}, Suggestions: {len(validation.suggestions)}",
                'error': None if success else "T/F question validation failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_statement_clarity_validation(self) -> Dict[str, Any]:
        """Test statement clarity validation"""
        try:
            # Create statement with clarity issues
            unclear_question = GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Machine learning is sometimes used in many applications, often with various results.",  # Ambiguous words
                question_type="true_false",
                correct_answer="True",
                options=["True", "False"],
                difficulty_level="intermediate",
                topic="AI",
                source_content="Test content",
                confidence_score=0.7,
                metadata={}
            )
            
            # Process the question
            processed = self.question_processor.process_true_false_question(unclear_question)
            
            # Check if ambiguity was detected
            validation = processed.validation_result
            ambiguity_detected = any('ambiguous' in issue.lower() for issue in validation.issues)
            has_clarity_metadata = 'ambiguity_detected' in processed.metadata
            
            success = ambiguity_detected or has_clarity_metadata
            
            return {
                'success': success,
                'details': f"Ambiguity detected: {ambiguity_detected}, Issues found: {len(validation.issues)}",
                'error': None if success else "Statement clarity validation failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_ambiguity_detection(self) -> Dict[str, Any]:
        """Test ambiguity detection in T/F questions"""
        try:
            # Test with clear statement
            clear_question = GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Water boils at 100 degrees Celsius at sea level.",
                question_type="true_false",
                correct_answer="True",
                options=["True", "False"],
                difficulty_level="beginner",
                topic="Science",
                source_content="Test content",
                confidence_score=0.9,
                metadata={}
            )
            
            # Test with ambiguous statement
            ambiguous_question = GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Most people usually prefer various types of food sometimes.",
                question_type="true_false",
                correct_answer="True",
                options=["True", "False"],
                difficulty_level="beginner",
                topic="General",
                source_content="Test content",
                confidence_score=0.5,
                metadata={}
            )
            
            # Process both questions
            processed_clear = self.question_processor.process_true_false_question(clear_question)
            processed_ambiguous = self.question_processor.process_true_false_question(ambiguous_question)
            
            # Check detection
            clear_issues = len(processed_clear.validation_result.issues)
            ambiguous_issues = len(processed_ambiguous.validation_result.issues)
            
            detection_working = ambiguous_issues > clear_issues
            
            return {
                'success': detection_working,
                'details': f"Clear statement issues: {clear_issues}, Ambiguous statement issues: {ambiguous_issues}",
                'error': None if detection_working else "Ambiguity detection failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_tf_quality_scoring(self) -> Dict[str, Any]:
        """Test T/F quality scoring"""
        try:
            # Test with good quality T/F question
            good_question = self._create_test_tf_question()
            processed_good = self.question_processor.process_true_false_question(good_question)
            
            # Test with poor quality T/F question
            poor_question = GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Yes?",  # Too short, has question mark
                question_type="true_false",
                correct_answer="Maybe",  # Invalid answer
                options=["True", "False"],
                difficulty_level="beginner",
                topic="Test",
                source_content="Test",
                confidence_score=0.3,
                metadata={}
            )
            processed_poor = self.question_processor.process_true_false_question(poor_question)
            
            # Check scoring
            good_score = processed_good.quality_score
            poor_score = processed_poor.quality_score
            
            score_range_valid = 0 <= good_score <= 10 and 0 <= poor_score <= 10
            good_better_than_poor = good_score > poor_score
            
            success = score_range_valid and good_better_than_poor
            
            return {
                'success': success,
                'details': f"Good T/F score: {good_score:.1f}, Poor T/F score: {poor_score:.1f}",
                'error': None if success else "T/F quality scoring failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_single_question_storage(self) -> Dict[str, Any]:
        """Test storing a single question"""
        try:
            # Create test question
            test_question = self._create_test_mc_question()
            document_id = str(uuid.uuid4())
            instructor_id = "test_instructor"
            
            # Store the question
            result = self.storage_service.store_question(
                test_question, document_id, instructor_id
            )
            
            # Check result
            success = result.get('success', False)
            has_question_id = 'question_id' in result
            has_timestamp = 'storage_timestamp' in result
            
            storage_success = success and has_question_id and has_timestamp
            
            return {
                'success': storage_success,
                'details': f"Stored question: {result.get('question_id', 'Unknown')}",
                'error': None if storage_success else "Single question storage failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_batch_question_storage(self) -> Dict[str, Any]:
        """Test storing multiple questions in batch"""
        try:
            # Create test questions
            questions = [
                self._create_test_mc_question(),
                self._create_test_tf_question(),
                self._create_test_mc_question()
            ]
            
            document_id = str(uuid.uuid4())
            instructor_id = "test_instructor"
            
            # Store questions in batch
            result = self.storage_service.store_questions_batch(
                questions, document_id, instructor_id
            )
            
            # Check result
            success = result.get('success', False)
            stored_count = result.get('stored_successfully', 0)
            total_count = result.get('total_questions', 0)
            
            batch_success = success and stored_count == total_count == len(questions)
            
            return {
                'success': batch_success,
                'details': f"Stored {stored_count}/{total_count} questions",
                'error': None if batch_success else "Batch question storage failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_question_retrieval(self) -> Dict[str, Any]:
        """Test retrieving questions"""
        try:
            # Create and store a test question
            test_question = self._create_test_mc_question()
            document_id = str(uuid.uuid4())
            instructor_id = "test_instructor"
            
            # Store the question
            store_result = self.storage_service.store_question(
                test_question, document_id, instructor_id
            )
            
            if not store_result.get('success'):
                return {
                    'success': False,
                    'details': None,
                    'error': "Failed to store question for retrieval test"
                }
            
            # Retrieve the question
            retrieved = self.storage_service.get_question(test_question.question_id)
            
            # Check retrieval
            retrieval_success = retrieved is not None
            correct_id = retrieved.get('QuestionID') == test_question.question_id if retrieved else False
            
            success = retrieval_success and correct_id
            
            return {
                'success': success,
                'details': f"Retrieved question: {retrieved.get('QuestionID', 'None') if retrieved else 'None'}",
                'error': None if success else "Question retrieval failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_question_update(self) -> Dict[str, Any]:
        """Test updating a question"""
        try:
            # Create and store a test question
            test_question = self._create_test_mc_question()
            document_id = str(uuid.uuid4())
            instructor_id = "test_instructor"
            
            # Store the question
            store_result = self.storage_service.store_question(
                test_question, document_id, instructor_id
            )
            
            if not store_result.get('success'):
                return {
                    'success': False,
                    'details': None,
                    'error': "Failed to store question for update test"
                }
            
            # Update the question
            updates = {
                'QuestionText': 'Updated question text?',
                'QualityScore': 9.5
            }
            
            update_result = self.storage_service.update_question(
                test_question.question_id, updates
            )
            
            # Check update
            update_success = update_result.get('success', False)
            has_updated_item = 'updated_item' in update_result
            
            success = update_success and has_updated_item
            
            return {
                'success': success,
                'details': f"Update successful: {update_success}",
                'error': None if success else "Question update failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_question_statistics(self) -> Dict[str, Any]:
        """Test question statistics generation"""
        try:
            instructor_id = "test_instructor"
            
            # Get statistics
            stats = self.storage_service.get_question_statistics(instructor_id)
            
            # Check statistics structure
            required_fields = [
                'total_questions', 'multiple_choice_questions', 'true_false_questions',
                'average_quality_score', 'average_confidence_score', 'topic_distribution'
            ]
            
            has_all_fields = all(field in stats for field in required_fields)
            valid_counts = (
                isinstance(stats.get('total_questions'), int) and
                isinstance(stats.get('multiple_choice_questions'), int) and
                isinstance(stats.get('true_false_questions'), int)
            )
            
            success = has_all_fields and valid_counts
            
            return {
                'success': success,
                'details': f"Total questions: {stats.get('total_questions', 0)}, MC: {stats.get('multiple_choice_questions', 0)}, T/F: {stats.get('true_false_questions', 0)}",
                'error': None if success else "Question statistics failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _create_test_mc_question(self) -> GeneratedQuestion:
        """Create a test multiple choice question"""
        return GeneratedQuestion(
            question_id=str(uuid.uuid4()),
            question_text="What is the primary function of the CPU in a computer?",
            question_type="multiple_choice",
            correct_answer="Process instructions and perform calculations",
            options=[
                "Process instructions and perform calculations",
                "Store data permanently",
                "Display graphics on the screen",
                "Connect to the internet"
            ],
            difficulty_level="intermediate",
            topic="Computer Science",
            source_content="Computer architecture fundamentals",
            confidence_score=0.85,
            metadata={"created_at": datetime.now().isoformat()}
        )
        
    def _create_test_tf_question(self) -> GeneratedQuestion:
        """Create a test true/false question"""
        return GeneratedQuestion(
            question_id=str(uuid.uuid4()),
            question_text="The CPU is responsible for executing program instructions.",
            question_type="true_false",
            correct_answer="True",
            options=["True", "False"],
            difficulty_level="beginner",
            topic="Computer Science",
            source_content="Computer architecture fundamentals",
            confidence_score=0.92,
            metadata={"created_at": datetime.now().isoformat()}
        )
        
    def run_test(self, test_name: str, test_function):
        """Run a single test"""
        self.total_tests += 1
        
        try:
            print(f"🔍 Testing {test_name}...")
            result = test_function()
            
            if result['success']:
                self.passed_tests += 1
                print(f"   ✅ PASS: {test_name}")
                if result['details']:
                    print(f"      📊 {result['details']}")
                self.test_results.append({
                    'name': test_name,
                    'status': 'PASS',
                    'details': result['details'],
                    'error': None
                })
            else:
                print(f"   ❌ FAIL: {test_name}")
                if result['error']:
                    print(f"      ⚠️  {result['error']}")
                self.test_results.append({
                    'name': test_name,
                    'status': 'FAIL',
                    'details': result['details'],
                    'error': result['error']
                })
                
        except Exception as e:
            print(f"   ❌ FAIL: {test_name}")
            print(f"      ⚠️  Exception: {str(e)}")
            self.test_results.append({
                'name': test_name,
                'status': 'FAIL',
                'details': None,
                'error': str(e)
            })
            
    def show_final_results(self):
        """Show final test results"""
        print("\n" + "=" * 70)
        print("🧪 PHASE 3.2 TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.total_tests - self.passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.passed_tests == self.total_tests:
            print("\n🎯 Overall Status: ✅ ALL TESTS PASSED")
        else:
            print("\n🎯 Overall Status: ❌ SOME TESTS FAILED")
            
        # Show failed tests
        failed_tests = [t for t in self.test_results if t['status'] == 'FAIL']
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   • {test['name']}: {test['error']}")
                
        print(f"\n📋 Test Categories Covered:")
        print(f"   • Multiple Choice Processing (Validation, enhancement, quality scoring)")
        print(f"   • True/False Processing (Validation, clarity, ambiguity detection)")
        if self.storage_available:
            print(f"   • Question Data Storage (Storage, retrieval, updates, statistics)")
        else:
            print(f"   • Question Data Storage (⚠️  Skipped - DynamoDB not available)")


def main():
    """Main function to run Phase 3.2 tests"""
    print("🧪 Phase 3.2: Question Processing Backend Testing")
    print("=" * 70)
    
    # Run tests
    tester = Phase32Tester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()