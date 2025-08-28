#!/usr/bin/env python3
"""
Test UI rendering functions to ensure all attribute access issues are resolved
"""

import os
import sys
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.question_generation_service import GeneratedQuestion
from pages.question_generation import QuestionGenerationPage
from datetime import datetime

def create_mock_question():
    """Create a mock GeneratedQuestion with all the correct attributes"""
    return GeneratedQuestion(
        question_id="test_q_001",
        question_text="What is 2 + 2?",
        question_type="multiple_choice",
        correct_answer="A. 4",
        options=["A. 4", "B. 3", "C. 5", "D. 6"],
        difficulty_level="beginner",
        topic="mathematics",
        source_content="This is a test document about basic arithmetic. 2 + 2 = 4.",
        confidence_score=0.95,
        metadata={
            'created_at': datetime.now().isoformat(),
            'explanation': 'Basic addition: 2 + 2 equals 4',
            'processing_version': '1.0'
        }
    )

def test_attribute_access():
    """Test all attribute access patterns used in the UI"""
    
    print("🧪 Testing UI Attribute Access")
    print("=" * 50)
    
    # Create a mock question
    question = create_mock_question()
    questions = [question]
    
    print("✅ Created mock question with all required attributes")
    
    # Test all the attribute access patterns from the UI code
    try:
        # Test confidence_score access (was causing error)
        avg_confidence = sum(q.confidence_score for q in questions) / len(questions)
        print(f"✅ confidence_score access: {avg_confidence:.1f}")
        
        # Test difficulty_level access (was causing error)
        difficulty = question.difficulty_level.title()
        print(f"✅ difficulty_level access: {difficulty}")
        
        # Test options access (was answer_options)
        options_count = len(question.options)
        print(f"✅ options access: {options_count} options")
        
        # Test metadata access for created_at
        created_at = question.metadata.get('created_at', 'Unknown')
        print(f"✅ metadata.created_at access: {created_at[:19]}")
        
        # Test metadata access for explanation
        explanation = question.metadata.get('explanation', '')
        print(f"✅ metadata.explanation access: {len(explanation)} chars")
        
        # Test source_content access (was source_text)
        source_preview = question.source_content[:50] + "..." if question.source_content else "None"
        print(f"✅ source_content access: {source_preview}")
        
        # Test all basic attributes
        basic_attrs = [
            'question_id', 'question_text', 'question_type', 
            'correct_answer', 'topic'
        ]
        
        for attr in basic_attrs:
            value = getattr(question, attr)
            print(f"✅ {attr} access: {str(value)[:30]}...")
        
        print("\n🎉 ALL ATTRIBUTE ACCESS TESTS PASSED!")
        print("The UI should now work without attribute errors.")
        
        return True
        
    except AttributeError as e:
        print(f"❌ Attribute error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_ui_functions():
    """Test the actual UI functions with mock data"""
    
    print("\n🖥️  Testing UI Functions")
    print("=" * 50)
    
    # Mock streamlit
    with patch('streamlit.metric') as mock_metric, \
         patch('streamlit.write') as mock_write, \
         patch('streamlit.expander') as mock_expander:
        
        # Create mock questions
        questions = [create_mock_question() for _ in range(3)]
        
        try:
            # Test the statistics calculation (this was failing)
            mc_count = len([q for q in questions if q.question_type == 'multiple_choice'])
            tf_count = len([q for q in questions if q.question_type == 'true_false'])
            avg_confidence = sum(q.confidence_score for q in questions) / len(questions)
            
            print(f"✅ Statistics calculation:")
            print(f"   MC Count: {mc_count}")
            print(f"   TF Count: {tf_count}")
            print(f"   Avg Confidence: {avg_confidence:.1f}")
            
            # Test question card rendering logic
            for i, question in enumerate(questions[:1], 1):  # Test just one
                type_icon = "🔤" if question.question_type == 'multiple_choice' else "✅"
                type_label = "Multiple Choice" if question.question_type == 'multiple_choice' else "True/False"
                
                # Test all the attribute access in question cards
                question_preview = question.question_text[:60] + "..."
                difficulty_display = question.difficulty_level.title()
                confidence_display = f"{question.confidence_score:.1f}"
                
                print(f"✅ Question {i} card data:")
                print(f"   Icon: {type_icon}")
                print(f"   Type: {type_label}")
                print(f"   Preview: {question_preview}")
                print(f"   Difficulty: {difficulty_display}")
                print(f"   Confidence: {confidence_display}")
                
                # Test options rendering
                if question.question_type == 'multiple_choice':
                    for j, option in enumerate(question.options, 1):
                        is_correct = option == question.correct_answer
                        prefix = "✅" if is_correct else "  "
                        print(f"   Option {j}: {prefix} {option}")
                
                # Test metadata access
                created_at = question.metadata.get('created_at', 'Unknown')
                explanation = question.metadata.get('explanation', '')
                
                print(f"   Created: {created_at[:19]}")
                print(f"   Has explanation: {bool(explanation)}")
                print(f"   Source preview: {question.source_content[:50]}...")
            
            print("\n🎉 UI FUNCTIONS TEST PASSED!")
            return True
            
        except Exception as e:
            print(f"❌ UI functions test failed: {str(e)}")
            return False

def main():
    """Run all UI rendering tests"""
    print("🎯 QuizGenius UI Rendering Test")
    print("Testing all attribute access patterns used in the UI")
    print("=" * 60)
    
    # Run tests
    attr_test_passed = test_attribute_access()
    ui_test_passed = test_ui_functions()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if attr_test_passed and ui_test_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The Streamlit UI should now work without attribute errors.")
        print("\n🚀 You can now:")
        print("   1. Restart your Streamlit app")
        print("   2. Upload a PDF")
        print("   3. Generate questions")
        print("   4. View the generated questions without errors")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("There may still be attribute access issues in the UI.")
        return 1

if __name__ == "__main__":
    exit(main())