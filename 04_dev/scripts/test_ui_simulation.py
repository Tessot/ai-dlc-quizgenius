#!/usr/bin/env python3
"""
UI Simulation Test - Exactly mimics what happens in the Streamlit UI
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.bedrock_service import BedrockService
from services.content_validation_service import ContentValidationService
from services.question_generation_service import QuestionGenerationService, QuestionGenerationRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ui_workflow():
    """Test the exact workflow that happens in the UI"""
    
    print("🎯 Testing UI Workflow - Exact Simulation")
    print("=" * 60)
    
    # Step 1: Initialize services (as the UI does)
    print("\n📋 Step 1: Initialize Services")
    bedrock_service = BedrockService()
    content_validator = ContentValidationService()
    question_generator = QuestionGenerationService()
    print("✅ Services initialized")
    
    # Step 2: Load and process PDF (as the UI does)
    print("\n📄 Step 2: Process PDF")
    sample_pdf_path = "../05_sample_docs/Money.pdf"
    
    with open(sample_pdf_path, 'rb') as pdf_file:
        pdf_content = pdf_file.read()
    
    # Extract text using Bedrock
    extraction_result = bedrock_service.extract_text_from_pdf(pdf_content, "Money.pdf")
    
    if not extraction_result['success']:
        print(f"❌ PDF extraction failed: {extraction_result.get('error')}")
        return False
    
    extracted_text = extraction_result['extracted_text']
    print(f"✅ Text extracted: {len(extracted_text)} characters")
    
    # Validate content
    validation_result = content_validator.validate_content(extracted_text, "Money.pdf")
    
    if not validation_result.is_suitable:
        print(f"❌ Content validation failed: {validation_result.issues}")
        return False
    
    print(f"✅ Content validated: Quality {validation_result.quality_score:.1f}/10")
    
    # Step 3: Generate questions (exactly as the UI does)
    print("\n🤖 Step 3: Generate Questions")
    
    # These are the exact parameters from the UI
    mc_count = 2
    tf_count = 1
    difficulty = 'intermediate'
    topic_focus = 'mathematics'
    
    print(f"📝 Parameters: MC={mc_count}, TF={tf_count}, Difficulty={difficulty}, Topic={topic_focus}")
    
    # Create the exact request structure the UI uses
    generation_request = QuestionGenerationRequest(
        content=extracted_text,
        question_types=['multiple_choice', 'true_false'],
        num_questions=mc_count + tf_count,
        difficulty_level=difficulty,
        topics=[topic_focus] if topic_focus else [],
        user_id="test_instructor_ui",
        document_id="test_doc_ui_001"
    )
    
    # Generate questions using the same service call
    print("🔄 Calling question generation service...")
    generation_result = question_generator.generate_questions(generation_request)
    
    if not generation_result.success:
        error_msg = generation_result.errors[0] if generation_result.errors else "Unknown error"
        print(f"❌ Question generation failed: {error_msg}")
        if hasattr(generation_result, 'errors') and generation_result.errors:
            print(f"   Additional errors: {generation_result.errors}")
        return False
    
    # Test the exact attribute access that the UI uses
    print("🔍 Testing attribute access...")
    try:
        # This is the exact line that was failing in the UI
        questions = generation_result.generated_questions
        print(f"✅ Successfully accessed .generated_questions: {len(questions)} questions")
        
        # Validate question structure
        valid_questions = 0
        for i, question in enumerate(questions):
            print(f"\n📝 Question {i+1}:")
            print(f"   Type: {getattr(question, 'question_type', 'Unknown')}")
            print(f"   Text: {getattr(question, 'question_text', 'No text')[:80]}...")
            print(f"   Answer: {getattr(question, 'correct_answer', 'No answer')}")
            
            if hasattr(question, 'options') and question.options:
                print(f"   Options: {question.options}")
            
            # Check if question has required attributes
            if (hasattr(question, 'question_text') and 
                hasattr(question, 'correct_answer') and 
                hasattr(question, 'question_type')):
                valid_questions += 1
        
        print(f"\n✅ Question validation: {valid_questions}/{len(questions)} questions are valid")
        
        if valid_questions == 0:
            print("❌ No valid questions generated")
            return False
            
        return True
        
    except AttributeError as e:
        print(f"❌ Attribute error: {str(e)}")
        print("   This is the exact error you're seeing in the UI!")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Run the UI simulation test"""
    print("🎯 QuizGenius UI Simulation Test")
    print("This test exactly mimics what happens when you use the Streamlit UI")
    print("=" * 60)
    
    try:
        success = test_ui_workflow()
        
        if success:
            print("\n🎉 UI SIMULATION TEST PASSED!")
            print("The Streamlit application should work correctly.")
        else:
            print("\n❌ UI SIMULATION TEST FAILED!")
            print("This explains why you're getting errors in the UI.")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 Test crashed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())