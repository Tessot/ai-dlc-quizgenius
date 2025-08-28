"""
Test project structure and basic functionality
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_project_structure():
    """Test that all required directories and files exist"""
    
    base_dir = os.path.join(os.path.dirname(__file__), '..')
    
    # Required directories
    required_dirs = [
        'components',
        'services',
        'models',
        'utils',
        'pages',
        'pages/instructor',
        'pages/student',
        'scripts',
        'tests',
    ]
    
    for dir_name in required_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        assert os.path.exists(dir_path), f"Directory {dir_name} does not exist"
        assert os.path.isdir(dir_path), f"{dir_name} is not a directory"
    
    # Required files
    required_files = [
        'main.py',
        'requirements.txt',
        '.env.example',
        'README.md',
        'utils/config.py',
        'components/auth.py',
        'components/navigation.py',
        'pages/instructor/dashboard.py',
        'pages/student/dashboard.py',
    ]
    
    for file_name in required_files:
        file_path = os.path.join(base_dir, file_name)
        assert os.path.exists(file_path), f"File {file_name} does not exist"
        assert os.path.isfile(file_path), f"{file_name} is not a file"


def test_config_import():
    """Test that configuration can be imported"""
    try:
        from utils.config import Config
        assert hasattr(Config, 'AWS_REGION')
        assert hasattr(Config, 'validate')
    except ImportError as e:
        pytest.fail(f"Failed to import Config: {e}")


def test_components_import():
    """Test that components can be imported"""
    try:
        from components.auth import AuthComponent
        from components.navigation import NavigationComponent
        
        # Test instantiation
        auth = AuthComponent()
        nav = NavigationComponent()
        
        assert auth is not None
        assert nav is not None
    except ImportError as e:
        pytest.fail(f"Failed to import components: {e}")


if __name__ == "__main__":
    pytest.main([__file__])