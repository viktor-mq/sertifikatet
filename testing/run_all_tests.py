#!/usr/bin/env python3
"""
Quick Test Runner for Gamification System
Runs all tests and provides clear pass/fail status
"""

import subprocess
import sys
import os

def run_gamification_tests():
    """Run the gamification integration tests"""
    print("🚀 Running Gamification System Tests...")
    print("=" * 60)
    
    # Change to the project directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_dir)
    
    try:
        # Run the integration tests
        result = subprocess.run(
            [sys.executable, 'testing/test_gamification_integration.py'],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Check if all tests passed
        if result.returncode == 0 and "6/6 tests passed" in result.stdout:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED!")
            print("✅ Gamification system is ready for production!")
            print("\n📋 Next steps:")
            print("1. Visit /quiz/test-modal to test the visual modal system")
            print("2. Take a real quiz to test end-to-end functionality")
            print("3. Deploy to production!")
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ TESTS FAILED!")
            print("Some tests are still failing. Check the output above for details.")
            print("\n📋 Next steps:")
            print("1. Review the failing test details")
            print("2. Fix any remaining issues")
            print("3. Run tests again")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def create_modal_test_page():
    """Create the modal test page"""
    try:
        result = subprocess.run(
            [sys.executable, 'testing/create_modal_test.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Modal test page created successfully")
            print("Visit: http://localhost:5000/quiz/test-modal")
        else:
            print(f"⚠️ Modal test page creation had issues: {result.stderr}")
            
    except Exception as e:
        print(f"⚠️ Could not create modal test page: {e}")


def main():
    """Main test runner"""
    print("🧪 GAMIFICATION SYSTEM TEST RUNNER")
    print("This will verify that all critical fixes are working correctly.")
    print()
    
    # Run the integration tests
    tests_passed = run_gamification_tests()
    
    print("\n" + "-" * 60)
    
    # Create modal test page regardless of test results
    print("📄 Creating modal test page...")
    create_modal_test_page()
    
    print("\n" + "=" * 60)
    
    if tests_passed:
        print("🎯 FINAL STATUS: READY FOR PRODUCTION!")
        print("\nThe gamification system has passed all tests and is ready for deployment.")
        exit(0)
    else:
        print("⚠️ FINAL STATUS: ISSUES REMAIN")
        print("\nSome tests are still failing. Please review and fix before deployment.")
        exit(1)


if __name__ == '__main__':
    main()
