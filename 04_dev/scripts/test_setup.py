#!/usr/bin/env python3
"""
QuizGenius MVP - Setup Test Script

This script tests the basic project setup and configuration.
"""

import os
import sys
import importlib.util

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_imports():
    """Test that all required modules can be imported"""
    
    print("🔍 Testing module imports...")
    
    modules_to_test = [
        'utils.config',
        'components.auth',
        'components.navigation',
        'pages.instructor.dashboard',
        'pages.student.dashboard',
    ]
    
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            return False
    
    return True


def test_configuration():
    """Test configuration loading"""
    
    print("\n🔧 Testing configuration...")
    
    try:
        from utils.config import Config
        
        # Test basic attributes
        assert hasattr(Config, 'AWS_REGION'), "AWS_REGION not found"
        assert hasattr(Config, 'validate'), "validate method not found"
        
        print(f"  ✅ AWS Region: {Config.AWS_REGION}")
        print(f"  ✅ Debug Mode: {Config.DEBUG}")
        print(f"  ✅ Configuration validation available")
        
        # Test AWS credentials (but don't fail if not configured yet)
        try:
            if Config.validate():
                print(f"  ✅ AWS credentials validated")
            else:
                print(f"  ⚠️  AWS credentials not configured (run 'aws configure')")
        except Exception as e:
            print(f"  ⚠️  AWS credentials test: {e}")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def test_project_structure():
    """Test project directory structure"""
    
    print("\n📁 Testing project structure...")
    
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
    
    return True


def main():
    """Run all setup tests"""
    
    print("🚀 QuizGenius MVP - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
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
    print("📊 Test Summary:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Project setup is complete.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the setup.")
        return 1


if __name__ == "__main__":
    exit(main())