#!/usr/bin/env python3
"""
QuizGenius MVP - Phase 1.1 Test Script

This script tests only what should be working in Phase 1.1:
- Project structure
- AWS credentials
- Basic configuration
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_project_structure():
    """Test project directory structure"""
    
    print("📁 Testing project structure...")
    
    required_dirs = [
        'components',
        'services', 
        'models',
        'utils',
        'pages',
        'scripts',
        'tests',
    ]
    
    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ - missing")
            return False
    
    # Check key files
    key_files = [
        'main.py',
        'requirements.txt',
        '.env',
        'README.md',
        'utils/config.py'
    ]
    
    for file_name in key_files:
        file_path = os.path.join(project_root, file_name)
        if os.path.exists(file_path):
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} - missing")
            return False
    
    return True


def test_aws_integration():
    """Test AWS credentials and basic service access"""
    
    print("\n🔐 Testing AWS integration...")
    
    try:
        from utils.config import Config
        import boto3
        
        # Test configuration loading
        print(f"  ✅ Configuration loaded (Region: {Config.AWS_REGION})")
        
        # Test AWS credentials
        session = Config.get_boto3_session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"  ✅ AWS credentials valid")
        print(f"     Account: {identity.get('Account', 'N/A')}")
        print(f"     Region: {Config.AWS_REGION}")
        
        # Test basic service clients
        dynamodb = session.client('dynamodb')
        bedrock = session.client('bedrock-runtime')
        cognito = session.client('cognito-idp')
        
        print(f"  ✅ AWS service clients created")
        
        return True
        
    except Exception as e:
        print(f"  ❌ AWS integration error: {e}")
        return False


def main():
    """Run Phase 1.1 tests"""
    
    print("🚀 QuizGenius MVP - Phase 1.1 Test")
    print("Testing: Project Setup & AWS Integration")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("AWS Integration", test_aws_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Phase 1.1 Test Summary:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Phase 1.1 Complete! Ready to proceed to Phase 1.2")
        print("Next: DynamoDB Tables Creation")
        return 0
    else:
        print("\n⚠️  Phase 1.1 needs attention.")
        return 1


if __name__ == "__main__":
    exit(main())