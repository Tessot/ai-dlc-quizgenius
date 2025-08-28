"""
Simple setup verification script
"""

import os

def verify_setup():
    """Verify basic project setup"""
    
    print("🔍 Verifying QuizGenius MVP setup...")
    
    # Check key files exist
    key_files = [
        'main.py',
        'requirements.txt',
        '.env.example',
        'README.md',
        'utils/config.py',
        'components/auth.py',
        'components/navigation.py'
    ]
    
    missing_files = []
    for file_path in key_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    
    print("\n🎉 Basic setup verification complete!")
    return True

if __name__ == "__main__":
    verify_setup()