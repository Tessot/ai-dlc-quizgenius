#!/usr/bin/env python3
"""
Question Generation Service Testing Script for QuizGenius MVP
This script tests the AI-powered question generation functionality using AWS Bedrock.
Tests Step 2.2.1: Bedrock Question Generation (US-4.2.1 - 8 points)
Author: Expert Software Engineer
"""

import sys
import os
import json
import time
from typing import Dict, List, Any

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.question_generation_service import (
    QuestionGenerationService, QuestionGenerationRequest, QuestionGenerationResult,
    GeneratedQuestion, QuestionGenerationError, create_generation_request,
    generate_questions_from_content
)
from utils.config import load_environment_config

class QuestionGenerationTester:
    """Comprehensive test class for question generation functionality"""
    
    def __init__(self):
        """Initialize the tester"""
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
        # Sample educational content for testing
        self.sample_content = {
            'short': """
            Machine learning is a subset of artificial intelligence. It uses algorithms to learn from data.
            """,
            'medium': """
            Machine Learning Fundamentals
            
            Machine learning is a subset of artificial intelligence (AI) that focuses on algorithms 
            that can learn from and make predictions or decisions based on data. Unlike traditional 
            programming where explicit instructions are given, machine learning algorithms build 
            mathematical models based on training data.
            
            There are three main types of machine learning:
            
            1. Supervised Learning: Uses labeled training data to learn a mapping from inputs to outputs.
               Examples include classification and regression problems.
            
            2. Unsupervised Learning: Finds hidden patterns in data without labeled examples.
               Common techniques include clustering and dimensionality reduction.
            
            3. Reinforcement Learning: Learns through interaction with an environment, receiving 
               rewards or penalties for actions taken.
            
            Key concepts in machine learning include features (input variables), models (mathematical 
            representations), training (the learning process), and evaluation (measuring performance).
            """,
            'long': """
            Introduction to Neural Networks and Deep Learning
            
            Neural networks are computing systems inspired by biological neural networks. They consist 
            of interconnected nodes (neurons) that process information through weighted connections.
            
            Architecture Components:
            - Input Layer: Receives the initial data
            - Hidden Layers: Process information through weighted connections and activation functions
            - Output Layer: Produces the final result
            
            Deep learning refers to neural networks with multiple hidden layers (typically 3 or more).
            These deep architectures can learn complex patterns and representations from data.
            
            Common activation functions include:
            1. ReLU (Rectified Linear Unit): f(x) = max(0, x)
            2. Sigmoid: f(x) = 1 / (1 + e^(-x))
            3. Tanh: f(x) = (e^x - e^(-x)) / (e^x + e^(-x))
            
            Training Process:
            Neural networks learn through backpropagation, which calculates gradients and updates 
            weights to minimize a loss function. The process involves:
            - Forward pass: Data flows through the network to produce predictions
            - Loss calculation: Compare predictions with actual values
            - Backward pass: Calculate gradients and update weights
            - Iteration: Repeat until convergence
            
            Applications of deep learning include image recognition, natural language processing, 
            speech recognition, and autonomous vehicles. Modern architectures like Transformers 
            have revolutionized fields such as machine translation and text generation.
            
            Challenges in deep learning include overfitting, vanishing gradients, and the need 
            for large amounts of training data. Techniques like dropout, batch normalization, 
            and data augmentation help address these issues.
            """
        }
    
    def run_all_tests(self):
        """Run all question generation tests"""
        print("🧪 Question Generation Service Testing for QuizGenius MVP")
        print("=" * 70)
        
        try:
            # Load configuration
            load_environment_config()
            print("✅ Environment configuration loaded")
            
            # Initialize service
            self.service = QuestionGenerationService()
            print("✅ Question generation service initialized")
            print()
            
            # Run tests
            self.test_service_initialization()
            self.test_content_validation()
            self.test_request_validation()
            self.test_content_chunking()
            self.test_multiple_choice_generation()
            self.test_true_false_generation()
            self.test_mixed_question_generation()
            self.test_difficulty_levels()
            self.test_error_handling()
            self.test_response_parsing()
            self.test_question_validation()
            self.test_convenience_functions()
            self.test_statistics_generation()
            
        except Exception as e:
            print(f"❌ Test setup error: {str(e)}")
            return
        
        # Print results
        self.print_test_results()
    
    def test_service_initialization(self):
        """Test service initialization"""
        print("🔍 Testing service initialization...")
        self.total_tests += 1
        
        try:
            service = QuestionGenerationService()
            
            # Check required attributes
            required_attrs = [
                'bedrock_service', 'max_content_length', 'max_questions_per_request',
                'min_content_length', 'mc_prompt_template', 'tf_prompt_template'
            ]
            
            missing_attrs = [attr for attr in required_attrs if not hasattr(service, attr)]
            
            if missing_attrs:
                self.record_test_result(
                    "Service Initialization", 
                    False, 
                    f"Missing attributes: {missing_attrs}"
                )
            else:
                self.record_test_result("Service Initialization", True, "All required attributes present")
                
        except Exception as e:
            self.record_test_result("Service Initialization", False, str(e))
    
    def test_content_validation(self):
        """Test content validation functionality"""
        print("🔍 Testing content validation...")
        
        # Test valid content
        self.total_tests += 1
        try:
            validation = self.service.validate_content_for_generation(self.sample_content['medium'])
            
            if validation['is_suitable'] and validation['quality_score'] > 0:
                self.record_test_result("Content Validation - Valid", True, f"Quality score: {validation['quality_score']}")
            else:
                self.record_test_result("Content Validation - Valid", False, "Valid content marked as unsuitable")
        except Exception as e:
            self.record_test_result("Content Validation - Valid", False, str(e))
        
        # Test invalid content (too short)
        self.total_tests += 1
        try:
            validation = self.service.validate_content_for_generation("Too short")
            
            if not validation['is_suitable']:
                self.record_test_result("Content Validation - Invalid", True, "Short content correctly rejected")
            else:
                self.record_test_result("Content Validation - Invalid", False, "Short content incorrectly accepted")
        except Exception as e:
            self.record_test_result("Content Validation - Invalid", False, str(e))
    
    def test_request_validation(self):
        """Test request validation"""
        print("🔍 Testing request validation...")
        
        # Test valid request
        self.total_tests += 1
        try:
            request = create_generation_request(
                content=self.sample_content['medium'],
                user_id='test_user',
                document_id='test_doc',
                question_types=['multiple_choice'],
                num_questions=3
            )
            
            errors = self.service._validate_request(request)
            
            if not errors:
                self.record_test_result("Request Validation - Valid", True, "Valid request accepted")
            else:
                self.record_test_result("Request Validation - Valid", False, f"Valid request rejected: {errors}")
        except Exception as e:
            self.record_test_result("Request Validation - Valid", False, str(e))
        
        # Test invalid request (no content)
        self.total_tests += 1
        try:
            request = create_generation_request(
                content="",
                user_id='test_user',
                document_id='test_doc'
            )
            
            errors = self.service._validate_request(request)
            
            if errors:
                self.record_test_result("Request Validation - Invalid", True, "Invalid request correctly rejected")
            else:
                self.record_test_result("Request Validation - Invalid", False, "Invalid request incorrectly accepted")
        except Exception as e:
            self.record_test_result("Request Validation - Invalid", False, str(e))
    
    def test_content_chunking(self):
        """Test content chunking functionality"""
        print("🔍 Testing content chunking...")
        self.total_tests += 1
        
        try:
            chunks = self.service._prepare_content_chunks(self.sample_content['long'])
            
            if chunks and all(len(chunk) >= self.service.min_content_length for chunk in chunks):
                self.record_test_result(
                    "Content Chunking", 
                    True, 
                    f"Created {len(chunks)} valid chunks"
                )
            else:
                self.record_test_result("Content Chunking", False, "Invalid chunks created")
                
        except Exception as e:
            self.record_test_result("Content Chunking", False, str(e))
    
    def test_multiple_choice_generation(self):
        """Test multiple choice question generation"""
        print("🔍 Testing multiple choice question generation...")
        self.total_tests += 1
        
        try:
            request = create_generation_request(
                content=self.sample_content['medium'],
                user_id='test_user',
                document_id='test_doc',
                question_types=['multiple_choice'],
                num_questions=2
            )
            
            print("   📡 Calling Bedrock API for MC questions...")
            result = self.service.generate_questions(request)
            
            if result.success and result.generated_questions:
                mc_questions = [q for q in result.generated_questions if q.question_type == 'multiple_choice']
                
                if mc_questions:
                    # Validate question structure
                    valid_questions = all(
                        len(q.options) == 4 and 
                        q.correct_answer in ['A', 'B', 'C', 'D'] and
                        q.question_text
                        for q in mc_questions
                    )
                    
                    if valid_questions:
                        self.record_test_result(
                            "MC Question Generation", 
                            True, 
                            f"Generated {len(mc_questions)} valid MC questions"
                        )
                        
                        # Print sample question for verification
                        sample_q = mc_questions[0]
                        print(f"   📝 Sample question: {sample_q.question_text[:100]}...")
                        print(f"   📊 Confidence: {sample_q.confidence_score}")
                    else:
                        self.record_test_result("MC Question Generation", False, "Invalid question structure")
                else:
                    self.record_test_result("MC Question Generation", False, "No MC questions generated")
            else:
                error_msg = f"Generation failed: {result.errors}" if result.errors else "Unknown error"
                self.record_test_result("MC Question Generation", False, error_msg)
                
        except Exception as e:
            self.record_test_result("MC Question Generation", False, str(e))
    
    def test_true_false_generation(self):
        """Test true/false question generation"""
        print("🔍 Testing true/false question generation...")
        self.total_tests += 1
        
        try:
            request = create_generation_request(
                content=self.sample_content['medium'],
                user_id='test_user',
                document_id='test_doc',
                question_types=['true_false'],
                num_questions=2
            )
            
            print("   📡 Calling Bedrock API for T/F questions...")
            result = self.service.generate_questions(request)
            
            if result.success and result.generated_questions:
                tf_questions = [q for q in result.generated_questions if q.question_type == 'true_false']
                
                if tf_questions:
                    # Validate question structure
                    valid_questions = all(
                        q.correct_answer in ['True', 'False'] and
                        q.question_text and
                        q.options == ['True', 'False']
                        for q in tf_questions
                    )
                    
                    if valid_questions:
                        self.record_test_result(
                            "T/F Question Generation", 
                            True, 
                            f"Generated {len(tf_questions)} valid T/F questions"
                        )
                        
                        # Print sample question for verification
                        sample_q = tf_questions[0]
                        print(f"   📝 Sample statement: {sample_q.question_text[:100]}...")
                        print(f"   ✅ Answer: {sample_q.correct_answer}")
                    else:
                        self.record_test_result("T/F Question Generation", False, "Invalid question structure")
                else:
                    self.record_test_result("T/F Question Generation", False, "No T/F questions generated")
            else:
                error_msg = f"Generation failed: {result.errors}" if result.errors else "Unknown error"
                self.record_test_result("T/F Question Generation", False, error_msg)
                
        except Exception as e:
            self.record_test_result("T/F Question Generation", False, str(e))
    
    def test_mixed_question_generation(self):
        """Test mixed question type generation"""
        print("🔍 Testing mixed question generation...")
        self.total_tests += 1
        
        try:
            request = create_generation_request(
                content=self.sample_content['long'],
                user_id='test_user',
                document_id='test_doc',
                question_types=['multiple_choice', 'true_false'],
                num_questions=4
            )
            
            print("   📡 Calling Bedrock API for mixed questions...")
            result = self.service.generate_questions(request)
            
            if result.success and result.generated_questions:
                mc_count = len([q for q in result.generated_questions if q.question_type == 'multiple_choice'])
                tf_count = len([q for q in result.generated_questions if q.question_type == 'true_false'])
                
                if mc_count > 0 and tf_count > 0:
                    self.record_test_result(
                        "Mixed Question Generation", 
                        True, 
                        f"Generated {mc_count} MC and {tf_count} T/F questions"
                    )
                else:
                    self.record_test_result(
                        "Mixed Question Generation", 
                        False, 
                        f"Only generated {mc_count} MC and {tf_count} T/F questions"
                    )
            else:
                error_msg = f"Generation failed: {result.errors}" if result.errors else "Unknown error"
                self.record_test_result("Mixed Question Generation", False, error_msg)
                
        except Exception as e:
            self.record_test_result("Mixed Question Generation", False, str(e))
    
    def test_difficulty_levels(self):
        """Test different difficulty levels"""
        print("🔍 Testing difficulty levels...")
        
        difficulties = ['beginner', 'intermediate', 'advanced']
        
        for difficulty in difficulties:
            self.total_tests += 1
            try:
                request = create_generation_request(
                    content=self.sample_content['medium'],
                    user_id='test_user',
                    document_id='test_doc',
                    question_types=['multiple_choice'],
                    num_questions=1,
                    difficulty=difficulty
                )
                
                result = self.service.generate_questions(request)
                
                if result.success and result.generated_questions:
                    question = result.generated_questions[0]
                    if question.difficulty_level == difficulty:
                        self.record_test_result(
                            f"Difficulty Level - {difficulty.title()}", 
                            True, 
                            f"Generated {difficulty} level question"
                        )
                    else:
                        self.record_test_result(
                            f"Difficulty Level - {difficulty.title()}", 
                            False, 
                            f"Expected {difficulty}, got {question.difficulty_level}"
                        )
                else:
                    self.record_test_result(
                        f"Difficulty Level - {difficulty.title()}", 
                        False, 
                        "Failed to generate question"
                    )
                    
            except Exception as e:
                self.record_test_result(f"Difficulty Level - {difficulty.title()}", False, str(e))
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("🔍 Testing error handling...")
        
        # Test with invalid content
        self.total_tests += 1
        try:
            request = create_generation_request(
                content="",  # Empty content
                user_id='test_user',
                document_id='test_doc'
            )
            
            result = self.service.generate_questions(request)
            
            if not result.success and result.errors:
                self.record_test_result("Error Handling - Empty Content", True, "Empty content correctly handled")
            else:
                self.record_test_result("Error Handling - Empty Content", False, "Empty content not handled properly")
                
        except Exception as e:
            self.record_test_result("Error Handling - Empty Content", False, str(e))
        
        # Test with invalid question type
        self.total_tests += 1
        try:
            request = QuestionGenerationRequest(
                content=self.sample_content['medium'],
                question_types=['invalid_type'],
                num_questions=1,
                difficulty_level='intermediate',
                topics=[],
                user_id='test_user',
                document_id='test_doc'
            )
            
            result = self.service.generate_questions(request)
            
            if not result.success and result.errors:
                self.record_test_result("Error Handling - Invalid Type", True, "Invalid type correctly handled")
            else:
                self.record_test_result("Error Handling - Invalid Type", False, "Invalid type not handled properly")
                
        except Exception as e:
            self.record_test_result("Error Handling - Invalid Type", False, str(e))
    
    def test_response_parsing(self):
        """Test response parsing functionality"""
        print("🔍 Testing response parsing...")
        
        # Test MC response parsing
        self.total_tests += 1
        try:
            sample_mc_response = '''
            [
              {
                "question": "What is machine learning?",
                "options": ["AI subset", "Programming language", "Database", "Operating system"],
                "correct_answer": "A",
                "explanation": "Machine learning is a subset of AI",
                "topic": "AI Fundamentals",
                "difficulty": "beginner",
                "confidence": 0.9
              }
            ]
            '''
            
            request = create_generation_request(
                content=self.sample_content['medium'],
                user_id='test_user',
                document_id='test_doc'
            )
            
            questions = self.service._parse_mc_response(sample_mc_response, "test content", request)
            
            if questions and len(questions) == 1:
                question = questions[0]
                if (question.question_text == "What is machine learning?" and 
                    question.correct_answer == "A" and 
                    len(question.options) == 4):
                    self.record_test_result("Response Parsing - MC", True, "MC response parsed correctly")
                else:
                    self.record_test_result("Response Parsing - MC", False, "MC response parsed incorrectly")
            else:
                self.record_test_result("Response Parsing - MC", False, "Failed to parse MC response")
                
        except Exception as e:
            self.record_test_result("Response Parsing - MC", False, str(e))
        
        # Test T/F response parsing
        self.total_tests += 1
        try:
            sample_tf_response = '''
            [
              {
                "statement": "Machine learning is a subset of artificial intelligence",
                "correct_answer": "True",
                "explanation": "This is correct based on the definition",
                "topic": "AI Fundamentals",
                "difficulty": "beginner",
                "confidence": 0.95
              }
            ]
            '''
            
            questions = self.service._parse_tf_response(sample_tf_response, "test content", request)
            
            if questions and len(questions) == 1:
                question = questions[0]
                if (question.question_text == "Machine learning is a subset of artificial intelligence" and 
                    question.correct_answer == "True"):
                    self.record_test_result("Response Parsing - T/F", True, "T/F response parsed correctly")
                else:
                    self.record_test_result("Response Parsing - T/F", False, "T/F response parsed incorrectly")
            else:
                self.record_test_result("Response Parsing - T/F", False, "Failed to parse T/F response")
                
        except Exception as e:
            self.record_test_result("Response Parsing - T/F", False, str(e))
    
    def test_question_validation(self):
        """Test question validation functionality"""
        print("🔍 Testing question validation...")
        
        # Test valid MC question
        self.total_tests += 1
        try:
            valid_mc = GeneratedQuestion(
                question_id='test_mc',
                question_text='What is the capital of France?',
                question_type='multiple_choice',
                correct_answer='A',
                options=['Paris', 'London', 'Berlin', 'Madrid'],
                difficulty_level='beginner',
                topic='Geography',
                source_content='Test content',
                confidence_score=0.9,
                metadata={}
            )
            
            is_valid = self.service._validate_mc_question(valid_mc)
            
            if is_valid:
                self.record_test_result("Question Validation - Valid MC", True, "Valid MC question accepted")
            else:
                self.record_test_result("Question Validation - Valid MC", False, "Valid MC question rejected")
                
        except Exception as e:
            self.record_test_result("Question Validation - Valid MC", False, str(e))
        
        # Test invalid MC question (wrong answer format)
        self.total_tests += 1
        try:
            invalid_mc = GeneratedQuestion(
                question_id='test_mc_invalid',
                question_text='What is the capital of France?',
                question_type='multiple_choice',
                correct_answer='Paris',  # Should be A, B, C, or D
                options=['Paris', 'London', 'Berlin', 'Madrid'],
                difficulty_level='beginner',
                topic='Geography',
                source_content='Test content',
                confidence_score=0.9,
                metadata={}
            )
            
            is_valid = self.service._validate_mc_question(invalid_mc)
            
            if not is_valid:
                self.record_test_result("Question Validation - Invalid MC", True, "Invalid MC question rejected")
            else:
                self.record_test_result("Question Validation - Invalid MC", False, "Invalid MC question accepted")
                
        except Exception as e:
            self.record_test_result("Question Validation - Invalid MC", False, str(e))
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        print("🔍 Testing convenience functions...")
        
        # Test create_generation_request
        self.total_tests += 1
        try:
            request = create_generation_request(
                content=self.sample_content['medium'],
                user_id='test_user',
                document_id='test_doc'
            )
            
            if (request.content and request.user_id == 'test_user' and 
                request.document_id == 'test_doc' and request.num_questions == 5):
                self.record_test_result("Convenience - Create Request", True, "Request created with defaults")
            else:
                self.record_test_result("Convenience - Create Request", False, "Request not created properly")
                
        except Exception as e:
            self.record_test_result("Convenience - Create Request", False, str(e))
        
        # Test generate_questions_from_content (if Bedrock is available)
        self.total_tests += 1
        try:
            print("   📡 Testing convenience function with Bedrock...")
            result = generate_questions_from_content(
                content=self.sample_content['short'],  # Use shorter content for faster testing
                user_id='test_user',
                document_id='test_doc',
                num_questions=1
            )
            
            if isinstance(result, QuestionGenerationResult):
                self.record_test_result("Convenience - Generate Questions", True, f"Function returned result object")
            else:
                self.record_test_result("Convenience - Generate Questions", False, "Function returned wrong type")
                
        except Exception as e:
            self.record_test_result("Convenience - Generate Questions", False, str(e))
    
    def test_statistics_generation(self):
        """Test statistics generation"""
        print("🔍 Testing statistics generation...")
        self.total_tests += 1
        
        try:
            # Create a mock result
            mock_questions = [
                GeneratedQuestion(
                    question_id='q1',
                    question_text='Test question 1',
                    question_type='multiple_choice',
                    correct_answer='A',
                    options=['A', 'B', 'C', 'D'],
                    difficulty_level='beginner',
                    topic='Test',
                    source_content='Test content',
                    confidence_score=0.8,
                    metadata={}
                ),
                GeneratedQuestion(
                    question_id='q2',
                    question_text='Test question 2',
                    question_type='true_false',
                    correct_answer='True',
                    options=['True', 'False'],
                    difficulty_level='intermediate',
                    topic='Test',
                    source_content='Test content',
                    confidence_score=0.9,
                    metadata={}
                )
            ]
            
            mock_result = QuestionGenerationResult(
                request_id='test_request',
                success=True,
                generated_questions=mock_questions,
                failed_attempts=0,
                total_attempts=2,
                processing_time_seconds=5.0,
                errors=[],
                warnings=[],
                metadata={}
            )
            
            stats = self.service.get_generation_statistics(mock_result)
            
            expected_fields = ['success_rate', 'questions_by_type', 'questions_by_difficulty', 'average_confidence']
            
            if all(field in stats for field in expected_fields):
                self.record_test_result("Statistics Generation", True, f"Generated complete statistics")
            else:
                missing = [f for f in expected_fields if f not in stats]
                self.record_test_result("Statistics Generation", False, f"Missing fields: {missing}")
                
        except Exception as e:
            self.record_test_result("Statistics Generation", False, str(e))
    
    def record_test_result(self, test_name: str, passed: bool, details: str):
        """Record a test result"""
        if passed:
            self.test_results['passed_tests'] += 1
            status = "✅ PASS"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌ FAIL"
        
        self.test_results['test_details'].append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
        
        print(f"   {status}: {test_name} - {details}")
    
    @property
    def total_tests(self):
        return self.test_results['total_tests']
    
    @total_tests.setter
    def total_tests(self, value):
        self.test_results['total_tests'] = value
    
    def print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 70)
        print("🧪 QUESTION GENERATION SERVICE TEST RESULTS")
        print("=" * 70)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        
        print(f"📊 Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total*100):.1f}%" if total > 0 else "📈 Success Rate: 0%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for test in self.test_results['test_details']:
                if not test['passed']:
                    print(f"   • {test['name']}: {test['details']}")
        
        print(f"\n🎯 Overall Status: {'✅ ALL TESTS PASSED' if failed == 0 else '❌ SOME TESTS FAILED'}")
        
        if total > 0:
            print(f"\n📋 Test Categories Covered:")
            print(f"   • Service Initialization and Configuration")
            print(f"   • Content Validation and Quality Assessment")
            print(f"   • Request Validation and Parameter Checking")
            print(f"   • Content Chunking and Preparation")
            print(f"   • Multiple Choice Question Generation")
            print(f"   • True/False Question Generation")
            print(f"   • Mixed Question Type Generation")
            print(f"   • Difficulty Level Handling")
            print(f"   • Error Handling and Recovery")
            print(f"   • Response Parsing and Validation")
            print(f"   • Question Structure Validation")
            print(f"   • Convenience Functions")
            print(f"   • Statistics Generation")

def main():
    """Main function to run question generation tests"""
    print("🚀 Starting QuizGenius Question Generation Service Tests")
    print("⚠️  Note: These tests require AWS Bedrock access and may take several minutes")
    print("📡 Tests will make actual API calls to AWS Bedrock")
    print()
    
    # Ask for confirmation
    try:
        response = input("Continue with tests? (y/N): ").strip().lower()
        if response != 'y':
            print("Tests cancelled by user")
            return
    except KeyboardInterrupt:
        print("\nTests cancelled by user")
        return
    
    tester = QuestionGenerationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()