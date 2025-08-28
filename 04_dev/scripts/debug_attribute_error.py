#!/usr/bin/env python3
"""
Debug script to reproduce the exact attribute error you're seeing
"""

import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.question_generation_service import QuestionGenerationService, QuestionGenerationRequest

def test_attribute_access():
    """Test the exact attribute access that's failing"""
    
    print("🔍 Testing QuestionGenerationResult attribute access")
    print("=" * 60)
    
    # Initialize service
    question_service = QuestionGenerationService()
    
    # Create a request with sufficient content
    long_content = """
    Mathematics is a fundamental subject that deals with numbers, quantities, and shapes. 
    Basic arithmetic operations include addition, subtraction, multiplication, and division.
    For example, 2 + 2 = 4, and 3 × 5 = 15. The area of a circle is calculated using the formula π × r², 
    where r is the radius. Geometry involves the study of shapes, angles, and spatial relationships.
    A triangle has three sides and three angles, and the sum of interior angles in any triangle is always 180 degrees.
    Algebra uses variables and equations to solve problems. For instance, if x + 5 = 10, then x = 5.
    Fractions represent parts of a whole, such as 1/2 or 3/4. Percentages are another way to express fractions,
    where 50% equals 1/2 and 75% equals 3/4. Understanding these basic concepts is essential for more advanced
    mathematical topics like calculus, statistics, and trigonometry.
    """
    
    request = QuestionGenerationRequest(
        content=long_content,
        question_types=['multiple_choice'],
        num_questions=1,
        difficulty_level='beginner',
        topics=['mathematics'],
        user_id='test_user',
        document_id='test_doc'
    )
    
    print("📝 Generating questions...")
    result = question_service.generate_questions(request)
    
    print(f"✅ Generation success: {result.success}")
    
    if result.success:
        print("\n🔍 Testing attribute access...")
        
        # Test the old attribute (should fail)
        try:
            questions_old = result.questions
            print(f"❌ OLD ATTRIBUTE (.questions) worked: {len(questions_old)} questions")
            print("   This means the old attribute still exists!")
        except AttributeError as e:
            print(f"✅ OLD ATTRIBUTE (.questions) failed as expected: {str(e)}")
        
        # Test the new attribute (should work)
        try:
            questions_new = result.generated_questions
            print(f"✅ NEW ATTRIBUTE (.generated_questions) worked: {len(questions_new)} questions")
        except AttributeError as e:
            print(f"❌ NEW ATTRIBUTE (.generated_questions) failed: {str(e)}")
            print("   This means the new attribute doesn't exist!")
        
        # Show the actual attributes available
        print(f"\n📋 Available attributes on result object:")
        for attr in dir(result):
            if not attr.startswith('_'):
                print(f"   - {attr}")
    
    else:
        error_msg = result.errors[0] if result.errors else "Unknown error"
        print(f"❌ Generation failed: {error_msg}")

if __name__ == "__main__":
    test_attribute_access()