#!/usr/bin/env python3
"""
User Service Testing Script for QuizGenius MVP

This script tests the user service functionality including:
- User creation
- User retrieval (by ID and email)
- User updates
- User deletion
- User queries by role
- User search functionality
"""

import sys
import json
import os

# Add the parent directory to the path so we can import from services and utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.user_service import UserService, UserServiceError
from utils.dynamodb_utils import generate_id

def test_user_service_initialization():
    """Test user service initialization"""
    print("🔍 Testing user service initialization...")
    
    try:
        user_service = UserService()
        print(f"  ✅ User service initialized successfully")
        return True, user_service
    except Exception as e:
        print(f"  ❌ User service initialization failed: {e}")
        return False, None

def test_user_creation(user_service):
    """Test user creation functionality"""
    print("\n🔍 Testing user creation...")
    
    # Test data
    test_users = [
        {
            'email': 'test.instructor.service@example.com',
            'first_name': 'Test',
            'last_name': 'Instructor',
            'role': 'instructor'
        },
        {
            'email': 'test.student.service@example.com',
            'first_name': 'Test',
            'last_name': 'Student',
            'role': 'student'
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            result = user_service.create_user(user_data)
            
            if result['success']:
                print(f"  ✅ Created {user_data['role']}: {result['user_id']}")
                created_users.append(result['user_data'])
            else:
                print(f"  ❌ Failed to create {user_data['role']}: {result}")
                
        except UserServiceError as e:
            if "already exists" in str(e):
                print(f"  ⚠️  {user_data['role']} already exists (expected for repeated tests)")
                # Try to get existing user
                existing_user = user_service.get_user_by_email(user_data['email'])
                if existing_user:
                    created_users.append(existing_user)
            else:
                print(f"  ❌ User creation failed: {e}")
                return False, []
        except Exception as e:
            print(f"  ❌ Unexpected error during user creation: {e}")
            return False, []
    
    return len(created_users) > 0, created_users

def test_user_retrieval(user_service, test_users):
    """Test user retrieval functionality"""
    print("\n🔍 Testing user retrieval...")
    
    if not test_users:
        print("  ⚠️  No test users available for retrieval tests")
        return False
    
    success_count = 0
    
    for user in test_users:
        try:
            # Test get by ID
            retrieved_by_id = user_service.get_user_by_id(user['user_id'])
            if retrieved_by_id and retrieved_by_id['user_id'] == user['user_id']:
                print(f"  ✅ Retrieved user by ID: {user['user_id']}")
                success_count += 1
            else:
                print(f"  ❌ Failed to retrieve user by ID: {user['user_id']}")
            
            # Test get by email
            retrieved_by_email = user_service.get_user_by_email(user['email'])
            if retrieved_by_email and retrieved_by_email['email'] == user['email']:
                print(f"  ✅ Retrieved user by email: {user['email']}")
                success_count += 1
            else:
                print(f"  ❌ Failed to retrieve user by email: {user['email']}")
                
        except Exception as e:
            print(f"  ❌ Error retrieving user {user['user_id']}: {e}")
    
    return success_count > 0

def test_user_updates(user_service, test_users):
    """Test user update functionality"""
    print("\n🔍 Testing user updates...")
    
    if not test_users:
        print("  ⚠️  No test users available for update tests")
        return False
    
    success_count = 0
    
    for user in test_users[:1]:  # Test with first user only
        try:
            # Test basic update
            updates = {
                'first_name': 'Updated',
                'last_name': 'Name'
            }
            
            result = user_service.update_user(user['user_id'], updates)
            
            if result['success']:
                print(f"  ✅ Updated user: {user['user_id']}")
                success_count += 1
                
                # Verify update
                updated_user = user_service.get_user_by_id(user['user_id'])
                if (updated_user and 
                    updated_user['first_name'] == 'Updated' and 
                    updated_user['last_name'] == 'Name'):
                    print(f"  ✅ Update verified: {user['user_id']}")
                    success_count += 1
                else:
                    print(f"  ❌ Update verification failed: {user['user_id']}")
            else:
                print(f"  ❌ Failed to update user: {result}")
                
        except Exception as e:
            print(f"  ❌ Error updating user {user['user_id']}: {e}")
    
    return success_count > 0

def test_user_queries(user_service):
    """Test user query functionality"""
    print("\n🔍 Testing user queries...")
    
    success_count = 0
    
    try:
        # Test get users by role
        instructors = user_service.get_users_by_role('instructor', limit=10)
        students = user_service.get_users_by_role('student', limit=10)
        
        print(f"  ✅ Found {len(instructors)} instructors")
        print(f"  ✅ Found {len(students)} students")
        success_count += 2
        
        # Test user statistics
        stats = user_service.get_user_statistics()
        print(f"  ✅ User statistics: {stats['total_users']} total, {stats['active_users']} active")
        success_count += 1
        
        # Test search functionality
        search_results = user_service.search_users('test', limit=5)
        print(f"  ✅ Search results: {len(search_results)} users found")
        success_count += 1
        
    except Exception as e:
        print(f"  ❌ Error during user queries: {e}")
    
    return success_count > 0

def test_last_login_update(user_service, test_users):
    """Test last login update functionality"""
    print("\n🔍 Testing last login updates...")
    
    if not test_users:
        print("  ⚠️  No test users available for login tests")
        return False
    
    try:
        user = test_users[0]
        result = user_service.update_last_login(user['user_id'])
        
        if result['success']:
            print(f"  ✅ Updated last login for user: {user['user_id']}")
            print(f"  • Last login: {result['last_login']}")
            print(f"  • Login count: {result['login_count']}")
            return True
        else:
            print(f"  ❌ Failed to update last login: {result}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error updating last login: {e}")
        return False

def test_user_deletion(user_service, test_users):
    """Test user deletion functionality (soft delete)"""
    print("\n🔍 Testing user deletion...")
    
    if not test_users:
        print("  ⚠️  No test users available for deletion tests")
        return False
    
    try:
        # Test soft delete on last user
        user_to_delete = test_users[-1]
        result = user_service.delete_user(user_to_delete['user_id'])
        
        if result['success']:
            print(f"  ✅ Soft deleted user: {user_to_delete['user_id']}")
            
            # Verify soft delete
            deleted_user = user_service.get_user_by_id(user_to_delete['user_id'])
            if deleted_user and deleted_user.get('status') == 'deleted':
                print(f"  ✅ Soft delete verified: status = {deleted_user['status']}")
                return True
            else:
                print(f"  ❌ Soft delete verification failed")
                return False
        else:
            print(f"  ❌ Failed to delete user: {result}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error deleting user: {e}")
        return False

def cleanup_test_users(user_service, test_users):
    """Clean up test users (hard delete)"""
    print("\n🧹 Cleaning up test users...")
    
    for user in test_users:
        try:
            user_service.hard_delete_user(user['user_id'])
            print(f"  ✅ Cleaned up user: {user['user_id']}")
        except Exception as e:
            print(f"  ⚠️  Could not clean up user {user['user_id']}: {e}")

def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "=" * 60)
    print("📊 User Service Test Report")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.
values() if result)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! User service is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the setup and fix any issues.")
        return False

def main():
    """Main function to run all user service tests"""
    print("🧪 User Service Testing for QuizGenius MVP")
    print("=" * 60)
    
    test_results = {}
    test_users = []
    
    # Test 1: Service initialization
    init_success, user_service = test_user_service_initialization()
    test_results['service_initialization'] = init_success
    
    if not init_success:
        print("\n❌ Cannot proceed with tests - service initialization failed")
        sys.exit(1)
    
    # Test 2: User creation
    creation_success, test_users = test_user_creation(user_service)
    test_results['user_creation'] = creation_success
    
    # Test 3: User retrieval
    retrieval_success = test_user_retrieval(user_service, test_users)
    test_results['user_retrieval'] = retrieval_success
    
    # Test 4: User updates
    update_success = test_user_updates(user_service, test_users)
    test_results['user_updates'] = update_success
    
    # Test 5: User queries
    query_success = test_user_queries(user_service)
    test_results['user_queries'] = query_success
    
    # Test 6: Last login updates
    login_success = test_last_login_update(user_service, test_users)
    test_results['last_login_updates'] = login_success
    
    # Test 7: User deletion
    deletion_success = test_user_deletion(user_service, test_users)
    test_results['user_deletion'] = deletion_success
    
    # Generate report
    success = generate_test_report(test_results)
    
    # Cleanup test users
    if test_users:
        cleanup_test_users(user_service, test_users)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()