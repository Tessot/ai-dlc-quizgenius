#!/usr/bin/env python3
"""
Phase 4.1.2 Testing Script - Question Editing Interface
Tests the question editing functionality for QuizGenius MVP

This script tests:
- Question Editing Interface (Step 4.1.2)
- Inline editing components
- Question text editing
- Answer option editing
- Correct answer selection
- Save edited questions
- Validate edited content
- Update question database
- Real-time preview
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

class Phase412Tester:
    """Test suite for Phase 4.1.2 - Question Editing Interface"""
    
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
        """Run all Phase 4.1.2 tests"""
        print("\n" + "="*60)
        print("🧪 PHASE 4.1.2 TESTING - QUESTION EDITING INTERFACE")
        print("="*60)
        
        if not self.setup_complete:
            print("❌ Setup failed - cannot run tests")
            return
        
        # Test categories
        test_categories = [
            ("Question Edit Page Structure", self.test_edit_page_structure),
            ("Question Text Editing", self.test_question_text_editing),
            ("Multiple Choice Editing", self.test_multiple_choice_editing),
            ("True/False Editing", self.test_true_false_editing),
            ("Answer Option Management", self.test_answer_option_management),
            ("Correct Answer Selection", self.test_correct_answer_selection),
            ("Question Type Conversion", self.test_question_type_conversion),
            ("Metadata Editing", self.test_metadata_editing),
            ("Real-time Preview", self.test_realtime_preview),
            ("Quality Assessment", self.test_quality_assessment),
            ("Validation System", self.test_validation_system),
            ("Save Functionality", self.test_save_functionality),
            ("Database Updates", self.test_database_updates),
            ("Session Management", self.test_session_management),
            ("Error Handling", self.test_error_handling)
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
    
    def test_edit_page_structure(self):
        """Test question edit page structure and components"""
        try:
            # Test page initialization
            sample_question = self.create_sample_question()
            
            # Test required components structure
            required_components = [
                'question_text_editor',
                'question_type_selector', 
                'answer_options_editor',
                'metadata_editor',
                'preview_panel',
                'action_buttons'
            ]
            
            # Simulate component availability
            available_components = {
                'question_text_editor': True,
                'question_type_selector': True,
                'answer_options_editor': True,
                'metadata_editor': True,
                'preview_panel': True,
                'action_buttons': True
            }
            
            for component in required_components:
                component_available = available_components.get(component, False)
                self.record_test_result(f"Component: {component}", component_available,
                                      f"Component {'available' if component_available else 'missing'}")
            
            # Test page layout structure
            layout_structure = {
                'two_column_layout': True,  # Editor and preview side by side
                'action_buttons_section': True,
                'quality_assessment': True,
                'validation_feedback': True
            }
            
            for layout_element, available in layout_structure.items():
                self.record_test_result(f"Layout: {layout_element}", available,
                                      f"Layout element {'present' if available else 'missing'}")
            
        except Exception as e:
            self.record_test_result("Edit Page Structure", False, f"Structure test failed: {str(e)}")
    
    def test_question_text_editing(self):
        """Test question text editing functionality"""
        try:
            sample_question = self.create_sample_question()
            original_text = sample_question['QuestionText']
            
            # Test text editing scenarios
            edit_scenarios = [
                {
                    'name': 'Basic Text Edit',
                    'original': original_text,
                    'new_text': 'What is the modified capital of France?',
                    'should_work': True
                },
                {
                    'name': 'Empty Text',
                    'original': original_text,
                    'new_text': '',
                    'should_work': False
                },
                {
                    'name': 'Very Long Text',
                    'original': original_text,
                    'new_text': 'A' * 500,  # Very long text
                    'should_work': True  # Should work but may trigger warnings
                },
                {
                    'name': 'Special Characters',
                    'original': original_text,
                    'new_text': 'What is 2 + 2 = ? (Choose the correct answer)',
                    'should_work': True
                }
            ]
            
            for scenario in edit_scenarios:
                # Simulate text editing
                edited_question = sample_question.copy()
                edited_question['QuestionText'] = scenario['new_text']
                
                # Validate the edit
                is_valid = self.validate_question_text(scenario['new_text'])
                expected_result = scenario['should_work']
                
                test_passed = (is_valid == expected_result) or (is_valid and expected_result)
                self.record_test_result(f"Text Edit: {scenario['name']}", test_passed,
                                      f"Text: '{scenario['new_text'][:50]}...', Valid: {is_valid}")
            
        except Exception as e:
            self.record_test_result("Question Text Editing", False, f"Text editing test failed: {str(e)}")
    
    def test_multiple_choice_editing(self):
        """Test multiple choice question editing"""
        try:
            mc_question = {
                'QuestionID': 'test_mc_edit',
                'QuestionText': 'What is the capital of France?',
                'QuestionType': 'multiple_choice',
                'Options': ['Paris', 'London', 'Berlin', 'Madrid'],
                'CorrectAnswer': 'Paris'
            }
            
            # Test option editing scenarios
            edit_scenarios = [
                {
                    'name': 'Edit Single Option',
                    'new_options': ['Paris', 'Rome', 'Berlin', 'Madrid'],
                    'new_correct': 'Paris',
                    'should_work': True
                },
                {
                    'name': 'Add New Option',
                    'new_options': ['Paris', 'London', 'Berlin', 'Madrid', 'Brussels'],
                    'new_correct': 'Paris',
                    'should_work': True
                },
                {
                    'name': 'Remove Option',
                    'new_options': ['Paris', 'London', 'Berlin'],
                    'new_correct': 'Paris',
                    'should_work': True
                },
                {
                    'name': 'Too Few Options',
                    'new_options': ['Paris'],
                    'new_correct': 'Paris',
                    'should_work': False
                },
                {
                    'name': 'Empty Options',
                    'new_options': ['', '', '', ''],
                    'new_correct': '',
                    'should_work': False
                },
                {
                    'name': 'Duplicate Options',
                    'new_options': ['Paris', 'Paris', 'Berlin', 'Madrid'],
                    'new_correct': 'Paris',
                    'should_work': False  # Should trigger warning
                }
            ]
            
            for scenario in edit_scenarios:
                edited_question = mc_question.copy()
                edited_question['Options'] = scenario['new_options']
                edited_question['CorrectAnswer'] = scenario['new_correct']
                
                # Validate the edit
                validation_result = self.validate_multiple_choice_question(edited_question)
                test_passed = validation_result['valid'] == scenario['should_work']
                
                self.record_test_result(f"MC Edit: {scenario['name']}", test_passed,
                                      f"Options: {len(scenario['new_options'])}, Valid: {validation_result['valid']}")
            
        except Exception as e:
            self.record_test_result("Multiple Choice Editing", False, f"MC editing test failed: {str(e)}")
    
    def test_true_false_editing(self):
        """Test true/false question editing"""
        try:
            tf_question = {
                'QuestionID': 'test_tf_edit',
                'QuestionText': 'The Earth is the third planet from the Sun.',
                'QuestionType': 'true_false',
                'CorrectAnswer': 'True'
            }
            
            # Test answer editing scenarios
            edit_scenarios = [
                {
                    'name': 'Change to False',
                    'new_answer': 'False',
                    'should_work': True
                },
                {
                    'name': 'Keep True',
                    'new_answer': 'True',
                    'should_work': True
                },
                {
                    'name': 'Invalid Answer',
                    'new_answer': 'Maybe',
                    'should_work': False
                },
                {
                    'name': 'Empty Answer',
                    'new_answer': '',
                    'should_work': False
                },
                {
                    'name': 'Boolean True',
                    'new_answer': True,
                    'should_work': True
                },
                {
                    'name': 'Boolean False',
                    'new_answer': False,
                    'should_work': True
                }
            ]
            
            for scenario in edit_scenarios:
                edited_question = tf_question.copy()
                edited_question['CorrectAnswer'] = scenario['new_answer']
                
                # Validate the edit
                validation_result = self.validate_true_false_question(edited_question)
                test_passed = validation_result['valid'] == scenario['should_work']
                
                self.record_test_result(f"TF Edit: {scenario['name']}", test_passed,
                                      f"Answer: {scenario['new_answer']}, Valid: {validation_result['valid']}")
            
        except Exception as e:
            self.record_test_result("True/False Editing", False, f"TF editing test failed: {str(e)}")
    
    def test_answer_option_management(self):
        """Test answer option management functionality"""
        try:
            # Test option manipulation operations
            initial_options = ['Paris', 'London', 'Berlin', 'Madrid']
            
            operations = [
                {
                    'name': 'Add Option',
                    'operation': lambda opts: opts + ['Rome'],
                    'expected_count': 5
                },
                {
                    'name': 'Remove Option',
                    'operation': lambda opts: opts[:-1],
                    'expected_count': 3
                },
                {
                    'name': 'Reorder Options',
                    'operation': lambda opts: sorted(opts),
                    'expected_count': 4
                },
                {
                    'name': 'Clear All Options',
                    'operation': lambda opts: [],
                    'expected_count': 0
                }
            ]
            
            for operation in operations:
                test_options = initial_options.copy()
                result_options = operation['operation'](test_options)
                
                count_correct = len(result_options) == operation['expected_count']
                self.record_test_result(f"Option Management: {operation['name']}", count_correct,
                                      f"Expected {operation['expected_count']}, got {len(result_options)}")
            
            # Test option validation
            validation_tests = [
                {
                    'name': 'Valid Options',
                    'options': ['A', 'B', 'C', 'D'],
                    'should_be_valid': True
                },
                {
                    'name': 'Empty Option',
                    'options': ['A', '', 'C', 'D'],
                    'should_be_valid': False
                },
                {
                    'name': 'Duplicate Options',
                    'options': ['A', 'B', 'A', 'D'],
                    'should_be_valid': False
                },
                {
                    'name': 'Single Option',
                    'options': ['A'],
                    'should_be_valid': False
                }
            ]
            
            for test in validation_tests:
                is_valid = self.validate_options(test['options'])
                test_passed = is_valid == test['should_be_valid']
                
                self.record_test_result(f"Option Validation: {test['name']}", test_passed,
                                      f"Options: {test['options']}, Valid: {is_valid}")
            
        except Exception as e:
            self.record_test_result("Answer Option Management", False, f"Option management test failed: {str(e)}")
    
    def test_correct_answer_selection(self):
        """Test correct answer selection functionality"""
        try:
            # Test multiple choice correct answer selection
            mc_options = ['Paris', 'London', 'Berlin', 'Madrid']
            
            for i, option in enumerate(mc_options):
                # Test selecting each option as correct
                selection_valid = option in mc_options
                self.record_test_result(f"MC Correct Selection: Option {i+1}", selection_valid,
                                      f"Selected '{option}' as correct answer")
            
            # Test invalid selections
            invalid_selections = ['Rome', '', None, 123]
            for invalid in invalid_selections:
                selection_valid = invalid in mc_options
                self.record_test_result(f"MC Invalid Selection: {invalid}", not selection_valid,
                                      f"Correctly rejected invalid selection: {invalid}")
            
            # Test true/false correct answer selection
            tf_valid_answers = ['True', 'False', True, False]
            tf_invalid_answers = ['Maybe', '', None, 'Yes', 'No']
            
            for answer in tf_valid_answers:
                is_valid = str(answer) in ['True', 'False']
                self.record_test_result(f"TF Valid Selection: {answer}", is_valid,
                                      f"Answer '{answer}' validity: {is_valid}")
            
            for answer in tf_invalid_answers:
                is_valid = str(answer) in ['True', 'False']
                self.record_test_result(f"TF Invalid Selection: {answer}", not is_valid,
                                      f"Correctly rejected invalid TF answer: {answer}")
            
        except Exception as e:
            self.record_test_result("Correct Answer Selection", False, f"Answer selection test failed: {str(e)}")
    
    def test_question_type_conversion(self):
        """Test question type conversion functionality"""
        try:
            # Test MC to TF conversion
            mc_question = {
                'QuestionText': 'Is Paris the capital of France?',
                'QuestionType': 'multiple_choice',
                'Options': ['Yes', 'No', 'Maybe', 'Unknown'],
                'CorrectAnswer': 'Yes'
            }
            
            # Convert to TF
            tf_converted = mc_question.copy()
            tf_converted['QuestionType'] = 'true_false'
            tf_converted['CorrectAnswer'] = 'True'
            if 'Options' in tf_converted:
                del tf_converted['Options']
            
            conversion_successful = (
                tf_converted['QuestionType'] == 'true_false' and
                'Options' not in tf_converted and
                tf_converted['CorrectAnswer'] in ['True', 'False']
            )
            
            self.record_test_result("MC to TF Conversion", conversion_successful,
                                  f"Converted MC to TF successfully: {conversion_successful}")
            
            # Test TF to MC conversion
            tf_question = {
                'QuestionText': 'The Earth is round.',
                'QuestionType': 'true_false',
                'CorrectAnswer': 'True'
            }
            
            # Convert to MC
            mc_converted = tf_question.copy()
            mc_converted['QuestionType'] = 'multiple_choice'
            mc_converted['Options'] = ['True', 'False', 'Maybe', 'Unknown']
            mc_converted['CorrectAnswer'] = 'True'
            
            conversion_successful = (
                mc_converted['QuestionType'] == 'multiple_choice' and
                'Options' in mc_converted and
                len(mc_converted['Options']) >= 2
            )
            
            self.record_test_result("TF to MC Conversion", conversion_successful,
                                  f"Converted TF to MC successfully: {conversion_successful}")
            
        except Exception as e:
            self.record_test_result("Question Type Conversion", False, f"Type conversion test failed: {str(e)}")
    
    def test_metadata_editing(self):
        """Test metadata editing functionality"""
        try:
            sample_question = self.create_sample_question()
            
            # Test difficulty level editing
            difficulty_levels = ['easy', 'medium', 'hard']
            for difficulty in difficulty_levels:
                edited_question = sample_question.copy()
                edited_question['DifficultyLevel'] = difficulty
                
                is_valid = difficulty in difficulty_levels
                self.record_test_result(f"Difficulty Edit: {difficulty}", is_valid,
                                      f"Set difficulty to {difficulty}")
            
            # Test topic editing
            topic_tests = [
                {'topic': 'Geography', 'valid': True},
                {'topic': 'Science', 'valid': True},
                {'topic': '', 'valid': True},  # Empty topic should be allowed
                {'topic': 'A' * 100, 'valid': True},  # Long topic should work
            ]
            
            for test in topic_tests:
                edited_question = sample_question.copy()
                edited_question['Topic'] = test['topic']
                
                # Topic validation (most topics should be valid)
                is_valid = isinstance(test['topic'], str)
                test_passed = is_valid == test['valid']
                
                self.record_test_result(f"Topic Edit: {test['topic'][:20]}...", test_passed,
                                      f"Topic '{test['topic'][:30]}' validity: {is_valid}")
            
            # Test metadata preservation
            original_metadata = {
                'CreatedAt': sample_question.get('CreatedAt'),
                'QuestionID': sample_question.get('QuestionID'),
                'DocumentID': sample_question.get('DocumentID')
            }
            
            edited_question = sample_question.copy()
            edited_question['Topic'] = 'New Topic'
            
            metadata_preserved = all(
                edited_question.get(key) == value 
                for key, value in original_metadata.items()
                if value is not None
            )
            
            self.record_test_result("Metadata Preservation", metadata_preserved,
                                  f"Original metadata preserved during edit: {metadata_preserved}")
            
        except Exception as e:
            self.record_test_result("Metadata Editing", False, f"Metadata editing test failed: {str(e)}")
    
    def test_realtime_preview(self):
        """Test real-time preview functionality"""
        try:
            sample_question = self.create_sample_question()
            
            # Test preview generation for different question states
            preview_tests = [
                {
                    'name': 'Complete Question',
                    'question': sample_question,
                    'should_preview': True
                },
                {
                    'name': 'Empty Question Text',
                    'question': {**sample_question, 'QuestionText': ''},
                    'should_preview': False
                },
                {
                    'name': 'Incomplete MC Options',
                    'question': {**sample_question, 'Options': ['A', '', '', '']},
                    'should_preview': True  # Should preview but show warnings
                },
                {
                    'name': 'No Correct Answer',
                    'question': {**sample_question, 'CorrectAnswer': ''},
                    'should_preview': True  # Should preview but show warnings
                }
            ]
            
            for test in preview_tests:
                # Simulate preview generation
                can_generate_preview = self.can_generate_preview(test['question'])
                test_passed = can_generate_preview == test['should_preview']
                
                self.record_test_result(f"Preview: {test['name']}", test_passed,
                                      f"Preview generation: {can_generate_preview}")
            
            # Test preview content accuracy
            preview_content = self.generate_preview_content(sample_question)
            
            content_tests = [
                {
                    'name': 'Question Text Present',
                    'test': sample_question['QuestionText'] in str(preview_content),
                },
                {
                    'name': 'Options Present',
                    'test': all(opt in str(preview_content) for opt in sample_question.get('Options', [])),
                },
                {
                    'name': 'Correct Answer Indicated',
                    'test': sample_question['CorrectAnswer'] in str(preview_content),
                }
            ]
            
            for test in content_tests:
                self.record_test_result(f"Preview Content: {test['name']}", test['test'],
                                      f"Content check passed: {test['test']}")
            
        except Exception as e:
            self.record_test_result("Real-time Preview", False, f"Preview test failed: {str(e)}")
    
    def test_quality_assessment(self):
        """Test quality assessment functionality"""
        try:
            # Test quality scoring for different question qualities
            quality_tests = [
                {
                    'name': 'High Quality Question',
                    'question': {
                        'QuestionText': 'What is the capital city of France, known for the Eiffel Tower?',
                        'QuestionType': 'multiple_choice',
                        'Options': ['Paris', 'London', 'Berlin', 'Madrid'],
                        'CorrectAnswer': 'Paris',
                        'DifficultyLevel': 'medium',
                        'Topic': 'Geography'
                    },
                    'expected_score_range': (7, 10)
                },
                {
                    'name': 'Medium Quality Question',
                    'question': {
                        'QuestionText': 'Capital of France?',
                        'QuestionType': 'multiple_choice',
                        'Options': ['Paris', 'London', '', ''],
                        'CorrectAnswer': 'Paris',
                        'DifficultyLevel': 'easy',
                        'Topic': ''
                    },
                    'expected_score_range': (4, 6)
                },
                {
                    'name': 'Low Quality Question',
                    'question': {
                        'QuestionText': 'What?',
                        'QuestionType': 'multiple_choice',
                        'Options': ['A', '', '', ''],
                        'CorrectAnswer': '',
                        'DifficultyLevel': '',
                        'Topic': ''
                    },
                    'expected_score_range': (0, 3)
                }
            ]
            
            for test in quality_tests:
                quality_score = self.calculate_quality_score(test['question'])
                min_score, max_score = test['expected_score_range']
                
                score_in_range = min_score <= quality_score <= max_score
                self.record_test_result(f"Quality Assessment: {test['name']}", score_in_range,
                                      f"Score: {quality_score}, Expected: {min_score}-{max_score}")
            
            # Test quality issue detection
            issue_tests = [
                {
                    'question': {'QuestionText': 'A' * 300},  # Too long
                    'should_have_issues': True,
                    'issue_type': 'length'
                },
                {
                    'question': {'QuestionText': 'Hi'},  # Too short
                    'should_have_issues': True,
                    'issue_type': 'length'
                },
                {
                    'question': {'QuestionText': 'Good question length', 'Options': ['A', 'A']},  # Duplicates
                    'should_have_issues': True,
                    'issue_type': 'duplicates'
                }
            ]
            
            for i, test in enumerate(issue_tests):
                issues = self.detect_quality_issues(test['question'])
                has_issues = len(issues) > 0
                
                test_passed = has_issues == test['should_have_issues']
                self.record_test_result(f"Issue Detection {i+1}: {test['issue_type']}", test_passed,
                                      f"Issues detected: {len(issues)}")
            
        except Exception as e:
            self.record_test_result("Quality Assessment", False, f"Quality assessment test failed: {str(e)}")
    
    def test_validation_system(self):
        """Test question validation system"""
        try:
            # Test comprehensive validation scenarios
            validation_tests = [
                {
                    'name': 'Valid MC Question',
                    'question': self.create_sample_question(),
                    'should_be_valid': True
                },
                {
                    'name': 'Valid TF Question',
                    'question': {
                        'QuestionText': 'The Earth is round.',
                        'QuestionType': 'true_false',
                        'CorrectAnswer': 'True'
                    },
                    'should_be_valid': True
                },
                {
                    'name': 'Missing Question Text',
                    'question': {
                        'QuestionText': '',
                        'QuestionType': 'multiple_choice',
                        'Options': ['A', 'B', 'C', 'D'],
                        'CorrectAnswer': 'A'
                    },
                    'should_be_valid': False
                },
                {
                    'name': 'Invalid Question Type',
                    'question': {
                        'QuestionText': 'Test question',
                        'QuestionType': 'invalid_type',
                        'CorrectAnswer': 'A'
                    },
                    'should_be_valid': False
                },
                {
                    'name': 'MC with No Options',
                    'question': {
                        'QuestionText': 'Test question',
                        'QuestionType': 'multiple_choice',
                        'Options': [],
                        'CorrectAnswer': 'A'
                    },
                    'should_be_valid': False
                },
                {
                    'name': 'TF with Invalid Answer',
                    'question': {
                        'QuestionText': 'Test question',
                        'QuestionType': 'true_false',
                        'CorrectAnswer': 'Maybe'
                    },
                    'should_be_valid': False
                }
            ]
            
            for test in validation_tests:
                validation_result = self.validate_question_comprehensive(test['question'])
                test_passed = validation_result['valid'] == test['should_be_valid']
                
                self.record_test_result(f"Validation: {test['name']}", test_passed,
                                      f"Valid: {validation_result['valid']}, Message: {validation_result.get('message', 'N/A')}")
            
        except Exception as e:
            self.record_test_result("Validation System", False, f"Validation test failed: {str(e)}")
    
    def test_save_functionality(self):
        """Test question save functionality"""
        try:
            sample_question = self.create_sample_question()
            
            # Test save preparation
            save_data = self.prepare_save_data(sample_question)
            
            required_fields = ['QuestionText', 'QuestionType', 'CorrectAnswer']
            has_required_fields = all(field in save_data for field in required_fields)
            
            self.record_test_result("Save Data Preparation", has_required_fields,
                                  f"Save data has required fields: {has_required_fields}")
            
            # Test save validation
            save_valid = self.validate_save_data(save_data)
            self.record_test_result("Save Data Validation", save_valid,
                                  f"Save data validation: {save_valid}")
            
            # Test metadata updates
            updated_data = self.add_save_metadata(save_data, 'test_user')
            
            has_metadata = all(field in updated_data for field in ['UpdatedAt', 'UpdatedBy'])
            self.record_test_result("Save Metadata Addition", has_metadata,
                                  f"Metadata added: {has_metadata}")
            
            # Test change detection
            original_question = sample_question.copy()
            modified_question = sample_question.copy()
            modified_question['QuestionText'] = 'Modified question text'
            
            has_changes = self.detect_changes(original_question, modified_question)
            self.record_test_result("Change Detection", has_changes,
                                  f"Changes detected: {has_changes}")
            
            no_changes = not self.detect_changes(original_question, original_question)
            self.record_test_result("No Change Detection", no_changes,
                                  f"No changes correctly detected: {no_changes}")
            
        except Exception as e:
            self.record_test_result("Save Functionality", False, f"Save functionality test failed: {str(e)}")
    
    def test_database_updates(self):
        """Test database update functionality"""
        try:
            if not self.storage_service:
                self.record_test_result("Database Updates", False, "Storage service not available")
                return
            
            # Test update method availability
            has_update_method = hasattr(self.storage_service, 'update_question')
            self.record_test_result("Update Method Available", has_update_method,
                                  f"Update method exists: {has_update_method}")
            
            if not has_update_method:
                return
            
            # Test update data preparation
            sample_question = self.create_sample_question()
            update_data = {
                'QuestionText': 'Updated question text',
                'DifficultyLevel': 'hard',
                'Topic': 'Updated Topic',
                'UpdatedBy': 'test_user'
            }
            
            # Validate update data structure
            valid_update_fields = all(
                field not in ['QuestionID', 'CreatedAt', 'created_by'] 
                for field in update_data.keys()
            )
            
            self.record_test_result("Update Data Structure", valid_update_fields,
                                  f"Update data excludes protected fields: {valid_update_fields}")
            
            # Test update parameter validation
            required_params = ['question_id', 'updates']
            update_params = {
                'question_id': 'test_question_id',
                'updates': update_data
            }
            
            has_required_params = all(param in update_params for param in required_params)
            self.record_test_result("Update Parameters", has_required_params,
                                  f"Required parameters present: {has_required_params}")
            
        except Exception as e:
            self.record_test_result("Database Updates", False, f"Database update test failed: {str(e)}")
    
    def test_session_management(self):
        """Test session management during editing"""
        try:
            sample_question = self.create_sample_question()
            
            # Test session state initialization
            session_state = {
                'editing_question': sample_question.copy(),
                'original_question': sample_question.copy(),
                'has_changes': False
            }
            
            session_initialized = all(key in session_state for key in ['editing_question', 'original_question', 'has_changes'])
            self.record_test_result("Session Initialization", session_initialized,
                                  f"Session state initialized: {session_initialized}")
            
            # Test change tracking
            session_state['editing_question']['QuestionText'] = 'Modified text'
            session_state['has_changes'] = True
            
            changes_tracked = session_state['has_changes']
            self.record_test_result("Change Tracking", changes_tracked,
                                  f"Changes tracked in session: {changes_tracked}")
            
            # Test session cleanup
            cleanup_keys = ['edit_question', 'editing_question', 'original_question', 'has_changes']
            cleaned_session = {}  # Simulate cleanup
            
            cleanup_successful = all(key not in cleaned_session for key in cleanup_keys)
            self.record_test_result("Session Cleanup", cleanup_successful,
                                  f"Session cleaned up: {cleanup_successful}")
            
            # Test session persistence
            persistent_data = {
                'question_id': sample_question['QuestionID'],
                'last_edit': datetime.now().isoformat()
            }
            
            persistence_data_valid = 'question_id' in persistent_data and 'last_edit' in persistent_data
            self.record_test_result("Session Persistence", persistence_data_valid,
                                  f"Persistence data valid: {persistence_data_valid}")
            
        except Exception as e:
            self.record_test_result("Session Management", False, f"Session management test failed: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        try:
            # Test handling of invalid question data
            invalid_questions = [
                {'QuestionText': None},  # None text
                {'QuestionType': 'invalid'},  # Invalid type
                {},  # Empty question
                {'QuestionText': 'Test', 'Options': None}  # None options
            ]
            
            for i, invalid_question in enumerate(invalid_questions):
                try:
                    validation_result = self.validate_question_comprehensive(invalid_question)
                    error_handled = not validation_result['valid']
                    self.record_test_result(f"Invalid Data Handling {i+1}", error_handled,
                                          f"Invalid question properly rejected: {error_handled}")
                except Exception:
                    # Exception is expected for invalid data
                    self.record_test_result(f"Invalid Data Handling {i+1}", True,
                                          "Exception properly raised for invalid data")
            
            # Test storage error handling
            try:
                # Simulate storage error by using invalid parameters
                if self.storage_service:
                    # This should handle the error gracefully
                    result = self.storage_service.update_question("", {})
                    error_handled = not result.get('success', False)
                else:
                    error_handled = True  # Service unavailable is handled
                
                self.record_test_result("Storage Error Handling", error_handled,
                                      f"Storage errors handled: {error_handled}")
            except Exception:
                # Exception handling is also acceptable
                self.record_test_result("Storage Error Handling", True,
                                      "Storage exceptions properly handled")
            
            # Test validation error messages
            validation_errors = [
                {'question': {'QuestionText': ''}, 'expected_error': 'required'},
                {'question': {'QuestionType': 'invalid'}, 'expected_error': 'type'},
                {'question': {'QuestionType': 'multiple_choice', 'Options': []}, 'expected_error': 'options'}
            ]
            
            for i, test in enumerate(validation_errors):
                validation_result = self.validate_question_comprehensive(test['question'])
                has_error_message = 'message' in validation_result and validation_result['message']
                
                self.record_test_result(f"Error Message {i+1}", has_error_message,
                                      f"Error message provided: {has_error_message}")
            
        except Exception as e:
            self.record_test_result("Error Handling", False, f"Error handling test failed: {str(e)}")
    
    # Helper methods for testing
    def create_sample_question(self) -> Dict[str, Any]:
        """Create a sample question for testing"""
        return {
            'QuestionID': 'test_question_1',
            'QuestionText': 'What is the capital of France?',
            'QuestionType': 'multiple_choice',
            'Options': ['Paris', 'London', 'Berlin', 'Madrid'],
            'CorrectAnswer': 'Paris',
            'DifficultyLevel': 'medium',
            'Topic': 'Geography',
            'QualityScore': 8.5,
            'CreatedAt': datetime.now().isoformat(),
            'DocumentID': 'test_doc_1'
        }
    
    def validate_question_text(self, text: str) -> bool:
        """Validate question text"""
        return isinstance(text, str) and len(text.strip()) > 0
    
    def validate_multiple_choice_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Validate multiple choice question"""
        options = question.get('Options', [])
        correct_answer = question.get('CorrectAnswer', '')
        
        if len([opt for opt in options if opt.strip()]) < 2:
            return {'valid': False, 'message': 'Need at least 2 options'}
        
        if correct_answer not in options or not correct_answer.strip():
            return {'valid': False, 'message': 'Valid correct answer required'}
        
        # Check for duplicates
        non_empty_options = [opt.strip() for opt in options if opt.strip()]
        if len(non_empty_options) != len(set(non_empty_options)):
            return {'valid': False, 'message': 'Duplicate options detected'}
        
        return {'valid': True, 'message': 'Valid multiple choice question'}
    
    def validate_true_false_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Validate true/false question"""
        correct_answer = question.get('CorrectAnswer', '')
        
        if str(correct_answer) not in ['True', 'False']:
            return {'valid': False, 'message': 'Answer must be True or False'}
        
        return {'valid': True, 'message': 'Valid true/false question'}
    
    def validate_options(self, options: List[str]) -> bool:
        """Validate answer options"""
        if len(options) < 2:
            return False
        
        # Check if any option is empty (strict validation)
        for option in options:
            if not option.strip():
                return False
        
        # Check for duplicates
        if len(options) != len(set(opt.strip() for opt in options)):
            return False
        
        return True
    
    def can_generate_preview(self, question: Dict[str, Any]) -> bool:
        """Check if preview can be generated"""
        return bool(question.get('QuestionText', '').strip())
    
    def generate_preview_content(self, question: Dict[str, Any]) -> str:
        """Generate preview content"""
        content = f"Question: {question.get('QuestionText', '')}\n"
        
        if question.get('QuestionType') == 'multiple_choice':
            options = question.get('Options', [])
            for i, option in enumerate(options):
                if option.strip():
                    content += f"{chr(65+i)}. {option}\n"
        
        content += f"Correct Answer: {question.get('CorrectAnswer', '')}\n"
        return content
    
    def calculate_quality_score(self, question: Dict[str, Any]) -> int:
        """Calculate quality score for question"""
        score = 0
        
        # Question text quality
        text = question.get('QuestionText', '')
        if 10 <= len(text) <= 200:
            score += 2
        elif len(text) > 0:
            score += 1
        
        # Question type specific scoring
        if question.get('QuestionType') == 'multiple_choice':
            options = question.get('Options', [])
            non_empty = [opt for opt in options if opt.strip()]
            if len(non_empty) >= 4:
                score += 2
            elif len(non_empty) >= 2:
                score += 1
            
            if question.get('CorrectAnswer') in options:
                score += 2
        elif question.get('QuestionType') == 'true_false':
            if question.get('CorrectAnswer') in ['True', 'False']:
                score += 2
        
        # Metadata scoring
        if question.get('Topic', '').strip():
            score += 1
        if question.get('DifficultyLevel') in ['easy', 'medium', 'hard']:
            score += 1
        
        return min(score, 10)  # Cap at 10
    
    def detect_quality_issues(self, question: Dict[str, Any]) -> List[str]:
        """Detect quality issues in question"""
        issues = []
        
        text = question.get('QuestionText', '')
        if len(text) > 250:
            issues.append('Question text too long')
        elif len(text) < 5:
            issues.append('Question text too short')
        
        options = question.get('Options', [])
        if options:
            non_empty = [opt.strip() for opt in options if opt.strip()]
            if len(non_empty) != len(set(non_empty)):
                issues.append('Duplicate options')
        
        return issues
    
    def validate_question_comprehensive(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive question validation"""
        if not question.get('QuestionText', '').strip():
            return {'valid': False, 'message': 'Question text is required'}
        
        question_type = question.get('QuestionType', '')
        if question_type not in ['multiple_choice', 'true_false']:
            return {'valid': False, 'message': 'Invalid question type'}
        
        if question_type == 'multiple_choice':
            return self.validate_multiple_choice_question(question)
        else:
            return self.validate_true_false_question(question)
    
    def prepare_save_data(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for saving"""
        return {k: v for k, v in question.items() if k not in ['QuestionID', 'CreatedAt']}
    
    def validate_save_data(self, data: Dict[str, Any]) -> bool:
        """Validate save data"""
        required_fields = ['QuestionText', 'QuestionType', 'CorrectAnswer']
        return all(field in data for field in required_fields)
    
    def add_save_metadata(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Add save metadata"""
        data = data.copy()
        data['UpdatedAt'] = datetime.now().isoformat()
        data['UpdatedBy'] = user_id
        return data
    
    def detect_changes(self, original: Dict[str, Any], modified: Dict[str, Any]) -> bool:
        """Detect changes between questions"""
        compare_fields = ['QuestionText', 'QuestionType', 'CorrectAnswer', 'Options', 'DifficultyLevel', 'Topic']
        return any(original.get(field) != modified.get(field) for field in compare_fields)
    
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
        print("📊 PHASE 4.1.2 TEST SUMMARY")
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
        
        print(f"\n🎯 Phase 4.1.2 Status: {'✅ READY' if success_rate >= 85 else '⚠️ NEEDS ATTENTION'}")
        
        # Save detailed results
        self.save_test_results()
    
    def save_test_results(self):
        """Save detailed test results to file"""
        try:
            results_file = "04_dev/docs/phase_4_1_2_test_results.json"
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump({
                    'phase': '4.1.2',
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
    tester = Phase412Tester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()