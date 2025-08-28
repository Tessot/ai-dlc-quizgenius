#!/usr/bin/env python3
"""
End-to-End PDF Upload and Question Generation Test
Tests the complete workflow from PDF upload to question generation
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_utils import PDFProcessor
from services.content_validation_service import ContentValidationService
from services.question_generation_service import QuestionGenerationService, QuestionGenerationRequest
from services.question_storage_service import QuestionStorageService
from services.bedrock_service import BedrockService
from utils.session_manager import SessionManager
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EndToEndPDFWorkflowTest:
    """Test the complete PDF upload and question generation workflow"""
    
    def __init__(self):
        """Initialize the test with all required services"""
        self.config = Config()
        self.pdf_processor = PDFProcessor()
        self.bedrock_service = BedrockService()
        self.content_validator = ContentValidationService()
        self.question_generator = QuestionGenerationService()
        self.question_storage = QuestionStorageService()
        self.session_manager = SessionManager()
        
        # Test configuration
        self.sample_pdf_path = "../05_sample_docs/Money.pdf"
        self.test_user_id = "test_instructor_001"
        self.test_results = []
        
        print("🚀 End-to-End PDF Workflow Test Initialized")
        print(f"📄 Sample PDF: {self.sample_pdf_path}")
        print("=" * 60)
    
    def run_complete_test(self):
        """Run the complete end-to-end test"""
        try:
            print("🧪 Starting Complete End-to-End PDF Workflow Test")
            print("=" * 60)
            
            # Step 1: Check PDF file exists
            if not self.check_pdf_exists():
                return False
            
            # Step 2: Test PDF processing
            if not self.test_pdf_processing():
                return False
            
            # Step 3: Test content validation
            if not self.test_content_validation():
                return False
            
            # Step 4: Test question generation
            if not self.test_question_generation():
                return False
            
            # Step 5: Test question storage
            if not self.test_question_storage():
                return False
            
            # Print final results
            self.print_test_summary()
            
            return all(result['success'] for result in self.test_results)
            
        except Exception as e:
            logger.error(f"Complete test failed: {str(e)}")
            self.record_test_result("Complete Workflow", False, f"Test failed: {str(e)}")
            return False
    
    def check_pdf_exists(self):
        """Check if the sample PDF file exists"""
        try:
            pdf_path = Path(self.sample_pdf_path)
            if not pdf_path.exists():
                self.record_test_result("PDF File Check", False, f"PDF file not found: {self.sample_pdf_path}")
                return False
            
            file_size = pdf_path.stat().st_size
            self.record_test_result("PDF File Check", True, f"PDF found, size: {file_size} bytes")
            return True
            
        except Exception as e:
            self.record_test_result("PDF File Check", False, f"Error checking PDF: {str(e)}")
            return False
    
    def test_pdf_processing(self):
        """Test PDF text extraction"""
        try:
            print("\n📖 Testing PDF Processing...")
            
            # Read PDF file
            with open(self.sample_pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            # Extract text using Bedrock
            extraction_result = self.bedrock_service.extract_text_from_pdf(pdf_content, "test_sample.pdf")
            
            if not extraction_result['success']:
                self.record_test_result("PDF Text Extraction", False, f"Extraction failed: {extraction_result.get('error', 'Unknown error')}")
                return False
            
            extracted_text = extraction_result['extracted_text']
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                self.record_test_result("PDF Text Extraction", False, "Insufficient text extracted")
                return False
            
            # Store extracted text for later tests
            self.extracted_text = extracted_text
            
            word_count = len(extracted_text.split())
            char_count = len(extracted_text)
            
            self.record_test_result("PDF Text Extraction", True, 
                                  f"Extracted {word_count} words, {char_count} characters")
            
            # Print sample of extracted text
            print(f"📝 Sample extracted text (first 200 chars):")
            print(f"   {extracted_text[:200]}...")
            
            return True
            
        except Exception as e:
            self.record_test_result("PDF Text Extraction", False, f"Error: {str(e)}")
            return False
    
    def test_content_validation(self):
        """Test content validation"""
        try:
            print("\n✅ Testing Content Validation...")
            
            # Validate content
            validation_result = self.content_validator.validate_content(
                self.extracted_text, 
                filename="test_sample.pdf"
            )
            
            # Store validation result for later tests
            self.validation_result = validation_result
            
            # Check validation results
            success = validation_result.is_suitable and validation_result.quality_score > 0
            
            details = (f"Quality Score: {validation_result.quality_score:.1f}/10, "
                      f"Suitable: {validation_result.is_suitable}, "
                      f"Word Count: {validation_result.word_count}")
            
            self.record_test_result("Content Validation", success, details)
            
            # Print validation details
            print(f"📊 Validation Results:")
            print(f"   Quality Score: {validation_result.quality_score:.1f}/10")
            print(f"   Suitable for Questions: {validation_result.is_suitable}")
            print(f"   Word Count: {validation_result.word_count}")
            print(f"   Issues: {len(validation_result.issues)}")
            print(f"   Recommendations: {len(validation_result.recommendations)}")
            
            if validation_result.issues:
                print(f"   ⚠️  Issues found:")
                for issue in validation_result.issues[:3]:  # Show first 3
                    print(f"      - {issue}")
            
            return success
            
        except Exception as e:
            self.record_test_result("Content Validation", False, f"Error: {str(e)}")
            return False
    
    def test_question_generation(self):
        """Test question generation"""
        try:
            print("\n🤖 Testing Question Generation...")
            
            # Create question generation request
            request = QuestionGenerationRequest(
                content=self.extracted_text,
                question_types=['multiple_choice', 'true_false'],
                num_questions=3,  # Generate 3 questions for testing
                difficulty_level='intermediate',
                topics=['mathematics', 'money'],  # Based on the PDF content
                user_id=self.test_user_id,
                document_id="test_doc_001"
            )
            
            # Generate questions
            generation_result = self.question_generator.generate_questions(request)
            
            # Store generation result for later tests
            self.generation_result = generation_result
            
            if not generation_result.success:
                error_msg = f"Generation failed: {generation_result.errors[0] if generation_result.errors else 'Unknown error'}"
                if generation_result.errors:
                    error_msg += f", Errors: {generation_result.errors}"
                self.record_test_result("Question Generation", False, error_msg)
                return False
            
            # Check generated questions
            questions = generation_result.generated_questions
            if not questions or len(questions) == 0:
                self.record_test_result("Question Generation", False, "No questions generated")
                return False
            
            # Validate question structure
            valid_questions = 0
            for question in questions:
                if (hasattr(question, 'question_text') and 
                    hasattr(question, 'correct_answer') and 
                    hasattr(question, 'question_type')):
                    valid_questions += 1
            
            success = valid_questions > 0
            details = f"Generated {len(questions)} questions, {valid_questions} valid"
            
            self.record_test_result("Question Generation", success, details)
            
            # Print question details
            print(f"🎯 Generation Results:")
            print(f"   Total Questions: {len(questions)}")
            print(f"   Valid Questions: {valid_questions}")
            print(f"   Success: {generation_result.success}")
            
            # Show sample questions
            for i, question in enumerate(questions[:2], 1):  # Show first 2 questions
                print(f"\n   📝 Sample Question {i}:")
                print(f"      Type: {getattr(question, 'question_type', 'Unknown')}")
                print(f"      Text: {getattr(question, 'question_text', 'No text')[:100]}...")
                print(f"      Answer: {getattr(question, 'correct_answer', 'No answer')}")
            
            return success
            
        except Exception as e:
            self.record_test_result("Question Generation", False, f"Error: {str(e)}")
            return False
    
    def test_question_storage(self):
        """Test question storage"""
        try:
            print("\n💾 Testing Question Storage...")
            
            if not hasattr(self, 'generation_result') or not self.generation_result.generated_questions:
                self.record_test_result("Question Storage", False, "No questions to store")
                return False
            
            # Store questions directly (they are already GeneratedQuestion objects)
            questions_to_store = self.generation_result.generated_questions
            
            # Store questions
            storage_result = self.question_storage.store_questions_batch(
                questions_to_store,
                "test_doc_001",
                self.test_user_id
            )
            
            success = storage_result.get('success', False)
            stored_count = storage_result.get('stored_successfully', 0)
            total_count = storage_result.get('total_questions', 0)
            
            details = f"Stored {stored_count}/{total_count} questions"
            
            self.record_test_result("Question Storage", success, details)
            
            print(f"💾 Storage Results:")
            print(f"   Success: {success}")
            print(f"   Stored: {stored_count}/{total_count}")
            
            if storage_result.get('errors'):
                print(f"   Errors: {storage_result['errors']}")
            
            return success
            
        except Exception as e:
            self.record_test_result("Question Storage", False, f"Error: {str(e)}")
            return False
    
    def record_test_result(self, test_name, success, details):
        """Record a test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}: {details}")
    
    def print_test_summary(self):
        """Print a summary of all test results"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['test_name']}: {result['details']}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! The PDF workflow is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")

def main():
    """Run the end-to-end test"""
    print("🧪 QuizGenius End-to-End PDF Workflow Test")
    print("=" * 60)
    
    # Initialize and run test
    test = EndToEndPDFWorkflowTest()
    success = test.run_complete_test()
    
    if success:
        print("\n🎉 End-to-End Test COMPLETED SUCCESSFULLY!")
        return 0
    else:
        print("\n❌ End-to-End Test FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())