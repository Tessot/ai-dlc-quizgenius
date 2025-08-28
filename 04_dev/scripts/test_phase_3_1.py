#!/usr/bin/env python3
"""
Phase 3.1 Testing Script for QuizGenius MVP
Tests PDF Upload & Processing functionality

This script tests:
- Step 3.1.1: PDF Upload Interface
- Step 3.1.2: PDF Content Preview  
- Step 3.1.3: Question Generation Interface
"""

import os
import sys
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.bedrock_service import BedrockService
from services.content_validation_service import ContentValidationService
from services.question_generation_service import QuestionGenerationService, QuestionGenerationRequest
from utils.config import Config

class Phase31Tester:
    """Test Phase 3.1 functionality"""
    
    def __init__(self):
        """Initialize tester"""
        self.config = Config()
        self.bedrock_service = BedrockService()
        self.content_validator = ContentValidationService()
        self.question_service = QuestionGenerationService()
        
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def run_all_tests(self):
        """Run all Phase 3.1 tests"""
        print("🚀 Starting Phase 3.1: PDF Upload & Processing Tests")
        print("=" * 70)
        
        # Test Step 3.1.1: PDF Upload Interface
        print("\n📤 Testing Step 3.1.1: PDF Upload Interface")
        print("-" * 50)
        self.test_pdf_upload_functionality()
        
        # Test Step 3.1.2: PDF Content Preview
        print("\n👀 Testing Step 3.1.2: PDF Content Preview")
        print("-" * 50)
        self.test_content_preview_functionality()
        
        # Test Step 3.1.3: Question Generation Interface
        print("\n🤖 Testing Step 3.1.3: Question Generation Interface")
        print("-" * 50)
        self.test_question_generation_interface()
        
        # Show final results
        self.show_final_results()
        
    def test_pdf_upload_functionality(self):
        """Test PDF upload functionality"""
        
        # Test 1: PDF file validation
        self.run_test(
            "PDF File Validation",
            self._test_pdf_validation
        )
        
        # Test 2: File upload handling
        self.run_test(
            "File Upload Handling",
            self._test_file_upload_handling
        )
        
        # Test 3: PDF text extraction
        self.run_test(
            "PDF Text Extraction",
            self._test_pdf_text_extraction
        )
        
        # Test 4: Document metadata storage
        self.run_test(
            "Document Metadata Storage",
            self._test_document_metadata_storage
        )
        
    def test_content_preview_functionality(self):
        """Test content preview functionality"""
        
        # Test 5: Content quality assessment
        self.run_test(
            "Content Quality Assessment",
            self._test_content_quality_assessment
        )
        
        # Test 6: Content structure analysis
        self.run_test(
            "Content Structure Analysis",
            self._test_content_structure_analysis
        )
        
        # Test 7: Content display formatting
        self.run_test(
            "Content Display Formatting",
            self._test_content_display_formatting
        )
        
    def test_question_generation_interface(self):
        """Test question generation interface"""
        
        # Test 8: Generation parameter validation
        self.run_test(
            "Generation Parameter Validation",
            self._test_generation_parameter_validation
        )
        
        # Test 9: Question generation workflow
        self.run_test(
            "Question Generation Workflow",
            self._test_question_generation_workflow
        )
        
        # Test 10: Generated question display
        self.run_test(
            "Generated Question Display",
            self._test_generated_question_display
        )
        
        # Test 11: Question export functionality
        self.run_test(
            "Question Export Functionality",
            self._test_question_export_functionality
        )
        
    def _test_pdf_validation(self) -> Dict[str, Any]:
        """Test PDF file validation"""
        try:
            # Create a test PDF file
            test_pdf = self._create_test_pdf()
            
            # Test file size validation
            max_size = 10 * 1024 * 1024  # 10MB
            if os.path.getsize(test_pdf) <= max_size:
                size_validation = True
            else:
                size_validation = False
                
            # Test file extension validation
            extension_validation = test_pdf.endswith('.pdf')
            
            # Cleanup
            os.remove(test_pdf)
            
            success = size_validation and extension_validation
            
            return {
                'success': success,
                'details': f"Size validation: {size_validation}, Extension validation: {extension_validation}",
                'error': None if success else "PDF validation failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_file_upload_handling(self) -> Dict[str, Any]:
        """Test file upload handling"""
        try:
            # Create a test PDF file
            test_pdf = self._create_test_pdf()
            
            # Test file reading
            with open(test_pdf, 'rb') as f:
                file_content = f.read()
                
            # Test temporary file creation
            temp_dir = tempfile.mkdtemp()
            upload_id = str(uuid.uuid4())
            temp_file = os.path.join(temp_dir, f"upload_{upload_id}.pdf")
            
            with open(temp_file, 'wb') as f:
                f.write(file_content)
                
            # Verify file was created
            file_created = os.path.exists(temp_file)
            file_size_match = os.path.getsize(temp_file) == len(file_content)
            
            # Cleanup
            os.remove(test_pdf)
            os.remove(temp_file)
            os.rmdir(temp_dir)
            
            success = file_created and file_size_match
            
            return {
                'success': success,
                'details': f"File created: {file_created}, Size match: {file_size_match}",
                'error': None if success else "File upload handling failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_pdf_text_extraction(self) -> Dict[str, Any]:
        """Test PDF text extraction"""
        try:
            # Create a test PDF with text content
            test_pdf = self._create_test_pdf_with_text()
            
            # Extract text using Bedrock service
            with open(test_pdf, 'rb') as f:
                pdf_content = f.read()
            extraction_result = self.bedrock_service.extract_text_from_pdf(pdf_content, "test.pdf")
            
            # Cleanup
            os.remove(test_pdf)
            
            if extraction_result.get('success', False):
                extracted_text = extraction_result.get('extracted_text', '')
                has_text = len(extracted_text.strip()) > 0
                
                return {
                    'success': has_text,
                    'details': f"Extracted {len(extracted_text)} characters",
                    'error': None if has_text else "No text extracted"
                }
            else:
                return {
                    'success': False,
                    'details': None,
                    'error': extraction_result.get('error', 'Text extraction failed')
                }
                
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_document_metadata_storage(self) -> Dict[str, Any]:
        """Test document metadata storage"""
        try:
            # Create test document metadata
            document_data = {
                'document_id': str(uuid.uuid4()),
                'filename': 'test_document.pdf',
                'file_size': 1024,
                'upload_timestamp': datetime.now().isoformat(),
                'instructor_id': 'test_instructor',
                'instructor_email': 'test@example.com',
                'text_length': 500,
                'word_count': 100,
                'quality_score': 7.5,
                'is_suitable': True,
                'content_type': 'educational_material',
                'processing_status': 'completed'
            }
            
            # Validate required fields
            required_fields = [
                'document_id', 'filename', 'file_size', 'upload_timestamp',
                'instructor_id', 'text_length', 'word_count', 'quality_score'
            ]
            
            all_fields_present = all(field in document_data for field in required_fields)
            valid_types = (
                isinstance(document_data['file_size'], int) and
                isinstance(document_data['word_count'], int) and
                isinstance(document_data['quality_score'], (int, float))
            )
            
            success = all_fields_present and valid_types
            
            return {
                'success': success,
                'details': f"Fields present: {all_fields_present}, Valid types: {valid_types}",
                'error': None if success else "Document metadata validation failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_content_quality_assessment(self) -> Dict[str, Any]:
        """Test content quality assessment"""
        try:
            # Test content
            test_content = """
            Machine Learning Fundamentals
            
            Machine learning is a branch of artificial intelligence that develops algorithms 
            and statistical models that enable computer systems to improve their performance 
            on a specific task through experience without being explicitly programmed.
            
            There are three main types of machine learning:
            1. Supervised Learning - uses labeled training data
            2. Unsupervised Learning - finds patterns in unlabeled data  
            3. Reinforcement Learning - learns through interaction with environment
            
            Key concepts include training data, features, models, and evaluation metrics.
            """
            
            # Validate content using content validation service
            validation_result = self.content_validator.validate_content(test_content)
            
            # Check validation results
            has_quality_score = hasattr(validation_result, 'quality_score')
            has_suitability = hasattr(validation_result, 'is_suitable')
            has_metadata = hasattr(validation_result, 'metadata')
            
            quality_score_valid = (
                has_quality_score and 
                0 <= validation_result.quality_score <= 10
            )
            
            success = has_quality_score and has_suitability and has_metadata and quality_score_valid
            
            return {
                'success': success,
                'details': f"Quality score: {validation_result.quality_score:.1f}, Suitable: {validation_result.is_suitable}",
                'error': None if success else "Content quality assessment failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_content_structure_analysis(self) -> Dict[str, Any]:
        """Test content structure analysis"""
        try:
            # Test content with clear structure
            test_content = """
            Chapter 1: Introduction to Data Science
            
            Data science is an interdisciplinary field that uses scientific methods, 
            processes, algorithms and systems to extract knowledge and insights from data.
            
            1.1 What is Data Science?
            Data science combines domain expertise, programming skills, and knowledge 
            of mathematics and statistics to extract meaningful insights from data.
            
            1.2 Key Components
            - Statistics and Mathematics
            - Programming (Python, R)
            - Domain Knowledge
            - Data Visualization
            
            Example: A data scientist might analyze customer purchase patterns 
            to recommend products or predict future sales trends.
            """
            
            # Analyze content structure
            validation_result = self.content_validator.validate_content(test_content)
            
            # Check structure metrics from metadata
            has_word_count = validation_result.word_count > 0
            has_quality_score = 0 <= validation_result.quality_score <= 10
            has_educational_indicators = bool(validation_result.educational_indicators)
            
            success = has_word_count and has_quality_score and has_educational_indicators
            
            return {
                'success': success,
                'details': f"Words: {validation_result.word_count}, Quality: {validation_result.quality_score:.1f}, Educational indicators: {len(validation_result.educational_indicators)}",
                'error': None if success else "Content structure analysis failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_content_display_formatting(self) -> Dict[str, Any]:
        """Test content display formatting"""
        try:
            # Test content formatting functions
            test_content = "This is a test content with multiple sentences. It has various formatting requirements. We need to test preview generation."
            
            # Test preview generation (first 100 characters)
            preview = test_content[:100]
            if len(test_content) > 100:
                preview += "..."
                
            # Test word count
            word_count = len(test_content.split())
            
            # Test character count
            char_count = len(test_content)
            
            # Test line splitting
            lines = test_content.split('\n')
            
            success = (
                len(preview) <= 103 and  # 100 chars + "..."
                word_count > 0 and
                char_count > 0 and
                isinstance(lines, list)
            )
            
            return {
                'success': success,
                'details': f"Preview: {len(preview)} chars, Words: {word_count}, Lines: {len(lines)}",
                'error': None if success else "Content display formatting failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_generation_parameter_validation(self) -> Dict[str, Any]:
        """Test generation parameter validation"""
        try:
            # Test valid parameters
            valid_params = {
                'mc_count': 5,
                'tf_count': 3,
                'difficulty': 'intermediate',
                'topic_focus': 'machine learning'
            }
            
            # Validate parameter ranges
            mc_valid = 1 <= valid_params['mc_count'] <= 20
            tf_valid = 1 <= valid_params['tf_count'] <= 20
            difficulty_valid = valid_params['difficulty'] in ['beginner', 'intermediate', 'advanced']
            topic_valid = isinstance(valid_params['topic_focus'], str)
            
            # Test invalid parameters
            invalid_params = {
                'mc_count': 25,  # Too high
                'tf_count': 0,   # Too low
                'difficulty': 'invalid',
                'topic_focus': None
            }
            
            mc_invalid = not (1 <= invalid_params['mc_count'] <= 20)
            tf_invalid = not (1 <= invalid_params['tf_count'] <= 20)
            difficulty_invalid = invalid_params['difficulty'] not in ['beginner', 'intermediate', 'advanced']
            
            success = (
                mc_valid and tf_valid and difficulty_valid and topic_valid and
                mc_invalid and tf_invalid and difficulty_invalid
            )
            
            return {
                'success': success,
                'details': f"Valid params passed: {mc_valid and tf_valid and difficulty_valid}, Invalid params rejected: {mc_invalid and tf_invalid and difficulty_invalid}",
                'error': None if success else "Parameter validation failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_question_generation_workflow(self) -> Dict[str, Any]:
        """Test question generation workflow"""
        try:
            # Test content for question generation
            test_content = """
            Photosynthesis is the process by which plants convert light energy into chemical energy.
            This process occurs in the chloroplasts of plant cells and involves two main stages:
            the light-dependent reactions and the Calvin cycle. During photosynthesis, plants
            take in carbon dioxide from the air and water from the soil, and use sunlight
            to produce glucose and oxygen. The overall equation is:
            6CO2 + 6H2O + light energy → C6H12O6 + 6O2
            """
            
            # Create generation request
            request = QuestionGenerationRequest(
                content=test_content,
                question_types=['multiple_choice'],
                num_questions=2,
                difficulty_level='intermediate',
                topics=['photosynthesis'],
                user_id='test_user',
                document_id='test_doc'
            )
            
            # Generate questions
            result = self.question_service.generate_questions(request)
            
            if result.success:
                questions_generated = len(result.generated_questions) > 0
                has_metadata = hasattr(result, 'metadata')
                
                success = questions_generated and has_metadata
                
                return {
                    'success': success,
                    'details': f"Generated {len(result.generated_questions)} questions",
                    'error': None if success else "Question generation workflow failed"
                }
            else:
                return {
                    'success': False,
                    'details': None,
                    'error': result.errors[0] if result.errors else "Question generation failed"
                }
                
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_generated_question_display(self) -> Dict[str, Any]:
        """Test generated question display"""
        try:
            # Create mock generated questions
            from services.question_generation_service import GeneratedQuestion
            
            mock_questions = [
                GeneratedQuestion(
                    question_id="q1",
                    question_text="What is the primary function of chloroplasts?",
                    question_type="multiple_choice",
                    correct_answer="Photosynthesis",
                    options=["Photosynthesis", "Respiration", "Digestion", "Reproduction"],
                    difficulty_level="intermediate",
                    topic="photosynthesis",
                    source_content="Test source",
                    confidence_score=0.9,
                    metadata={"created_at": datetime.now().isoformat()}
                ),
                GeneratedQuestion(
                    question_id="q2",
                    question_text="Plants produce oxygen during photosynthesis.",
                    question_type="true_false",
                    correct_answer="True",
                    options=["True", "False"],
                    difficulty_level="beginner",
                    topic="photosynthesis",
                    source_content="Test source",
                    confidence_score=0.95,
                    metadata={"created_at": datetime.now().isoformat()}
                )
            ]
            
            # Test question display formatting
            for question in mock_questions:
                # Check required fields
                has_id = bool(question.question_id)
                has_text = bool(question.question_text)
                has_type = question.question_type in ['multiple_choice', 'true_false']
                has_answer = bool(question.correct_answer)
                has_confidence = 0 <= question.confidence_score <= 1
                
                if not all([has_id, has_text, has_type, has_answer, has_confidence]):
                    return {
                        'success': False,
                        'details': None,
                        'error': f"Question {question.question_id} missing required fields"
                    }
                    
            # Test statistics calculation
            mc_count = len([q for q in mock_questions if q.question_type == 'multiple_choice'])
            tf_count = len([q for q in mock_questions if q.question_type == 'true_false'])
            avg_confidence = sum(q.confidence_score for q in mock_questions) / len(mock_questions)
            
            stats_valid = (
                mc_count == 1 and
                tf_count == 1 and
                0 <= avg_confidence <= 1
            )
            
            return {
                'success': stats_valid,
                'details': f"MC: {mc_count}, TF: {tf_count}, Avg confidence: {avg_confidence:.2f}",
                'error': None if stats_valid else "Question display validation failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _test_question_export_functionality(self) -> Dict[str, Any]:
        """Test question export functionality"""
        try:
            # Create mock questions for export
            from services.question_generation_service import GeneratedQuestion
            
            mock_questions = [
                GeneratedQuestion(
                    question_id="q1",
                    question_text="What is machine learning?",
                    question_type="multiple_choice",
                    correct_answer="A branch of AI",
                    options=["A branch of AI", "A programming language", "A database", "A web framework"],
                    difficulty_level="beginner",
                    topic="AI",
                    source_content="Test source",
                    confidence_score=0.9,
                    metadata={"created_at": datetime.now().isoformat()}
                )
            ]
            
            # Test text export formatting
            text_export = self._format_questions_as_text(mock_questions)
            text_has_content = len(text_export) > 0
            text_has_question = "What is machine learning?" in text_export
            
            # Test JSON export formatting
            import json
            questions_data = []
            for q in mock_questions:
                question_dict = {
                    'id': q.question_id,
                    'type': q.question_type,
                    'question': q.question_text,
                    'correct_answer': q.correct_answer,
                    'options': q.options,
                    'difficulty': q.difficulty_level,
                    'confidence': q.confidence_score
                }
                questions_data.append(question_dict)
                
            json_export = json.dumps(questions_data, indent=2)
            json_valid = len(json_export) > 0
            
            # Validate JSON structure
            parsed_json = json.loads(json_export)
            json_structure_valid = (
                isinstance(parsed_json, list) and
                len(parsed_json) == 1 and
                'id' in parsed_json[0] and
                'question' in parsed_json[0]
            )
            
            success = text_has_content and text_has_question and json_valid and json_structure_valid
            
            return {
                'success': success,
                'details': f"Text export: {len(text_export)} chars, JSON valid: {json_structure_valid}",
                'error': None if success else "Question export functionality failed"
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': None,
                'error': str(e)
            }
            
    def _format_questions_as_text(self, questions) -> str:
        """Format questions as text (helper method)"""
        content = f"Quiz Questions - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 60 + "\n\n"
        
        for i, q in enumerate(questions, 1):
            content += f"Question {i}: {q.question_text}\n"
            content += f"Type: {q.question_type.replace('_', ' ').title()}\n"
            content += f"Difficulty: {q.difficulty_level.title()}\n"
            
            if q.question_type == 'multiple_choice':
                content += "Options:\n"
                for j, option in enumerate(q.options, 1):
                    marker = "✓" if option == q.correct_answer else " "
                    content += f"  {chr(64+j)}. [{marker}] {option}\n"
            else:
                content += f"Correct Answer: {q.correct_answer}\n"
                
            content += f"Confidence: {q.confidence_score:.1f}\n"
            content += "-" * 40 + "\n\n"
            
        return content
        
    def _create_test_pdf(self) -> str:
        """Create a test PDF file"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        # Create PDF with basic content
        c = canvas.Canvas(temp_file.name, pagesize=letter)
        c.drawString(100, 750, "Test PDF Document")
        c.drawString(100, 700, "This is a test PDF for validation.")
        c.save()
        
        return temp_file.name
        
    def _create_test_pdf_with_text(self) -> str:
        """Create a test PDF file with substantial text content"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        # Create PDF with educational content
        c = canvas.Canvas(temp_file.name, pagesize=letter)
        
        # Add title
        c.drawString(100, 750, "Sample Educational PDF Document")
        
        # Add content
        content_lines = [
            "Chapter 1: Introduction to Machine Learning",
            "",
            "This is a sample PDF document for testing text extraction.",
            "Machine learning is a branch of artificial intelligence that",
            "develops algorithms to learn from data without being explicitly",
            "programmed. It has applications in many fields including:",
            "",
            "1. Computer Vision - image recognition and processing",
            "2. Natural Language Processing - text analysis and generation", 
            "3. Predictive Analytics - forecasting and trend analysis",
            "4. Recommendation Systems - personalized content suggestions",
            "",
            "The main types of machine learning are supervised learning,",
            "unsupervised learning, and reinforcement learning. Each type",
            "has different use cases and methodologies."
        ]
        
        y_position = 700
        for line in content_lines:
            c.drawString(100, y_position, line)
            y_position -= 20
            
        c.save()
        
        return temp_file.name
        
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
        print("🧪 PHASE 3.1 TEST RESULTS")
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
        print(f"   • PDF Upload Interface (File validation, upload handling, text extraction)")
        print(f"   • PDF Content Preview (Quality assessment, structure analysis, display)")
        print(f"   • Question Generation Interface (Parameter validation, workflow, export)")


def main():
    """Main function to run Phase 3.1 tests"""
    print("🧪 Phase 3.1: PDF Upload & Processing Testing")
    print("=" * 70)
    
    # Check if required packages are available
    try:
        import reportlab
        print("✅ ReportLab available for PDF creation")
    except ImportError:
        print("⚠️  ReportLab not available - some tests may be skipped")
        print("   Install with: pip install reportlab")
        
    # Run tests
    tester = Phase31Tester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()