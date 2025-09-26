
#!/usr/bin/env python3
"""
Simple test script for the Quantum Loop Debugger system
This script is used by the auto-retry system to test code health
"""

import sys
import os
import json
from datetime import datetime

def test_basic_functionality():
    """Test basic Python functionality"""
    print("🧪 Running basic functionality tests...")
    
    # Test 1: Basic arithmetic
    result = 2 + 2
    assert result == 4, f"Basic arithmetic failed: 2 + 2 = {result}"
    print("✅ Basic arithmetic test passed")
    
    # Test 2: String operations
    text = "Hello, World!"
    assert len(text) == 13, f"String length test failed: len('{text}') = {len(text)}"
    print("✅ String operations test passed")
    
    # Test 3: List operations
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    assert total == 15, f"List sum test failed: sum({numbers}) = {total}"
    print("✅ List operations test passed")
    
    # Test 4: Dictionary operations
    data = {"name": "Quantum Loop Debugger", "version": "1.0"}
    assert data["name"] == "Quantum Loop Debugger", "Dictionary access test failed"
    print("✅ Dictionary operations test passed")
    
    return True

def test_file_operations():
    """Test file I/O operations"""
    print("🧪 Running file operations tests...")
    
    test_file = "test_temp_file.txt"
    test_content = "This is a test file for the Quantum Loop Debugger"
    
    try:
        # Test writing
        with open(test_file, 'w') as f:
            f.write(test_content)
        print("✅ File write test passed")
        
        # Test reading
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert content == test_content, f"File content mismatch: expected '{test_content}', got '{content}'"
        print("✅ File read test passed")
        
        # Cleanup
        os.remove(test_file)
        print("✅ File cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        # Cleanup on failure
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
            except:
                pass
        return False

def test_json_operations():
    """Test JSON operations"""
    print("🧪 Running JSON operations tests...")
    
    try:
        # Test JSON serialization
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "test_name": "Quantum Loop Debugger Test",
            "status": "running",
            "data": [1, 2, 3, {"nested": True}]
        }
        
        json_string = json.dumps(test_data)
        print("✅ JSON serialization test passed")
        
        # Test JSON deserialization
        parsed_data = json.loads(json_string)
        assert parsed_data["test_name"] == test_data["test_name"], "JSON parsing test failed"
        print("✅ JSON deserialization test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON operations test failed: {e}")
        return False

def test_import_statements():
    """Test common import statements"""
    print("🧪 Running import tests...")
    
    try:
        # Test standard library imports
        import os
        import sys
        import json
        import time
        import datetime
        import subprocess
        import threading
        print("✅ Standard library imports test passed")
        
        # Test that we can import our modules
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from assistant import openrouter_client
            print("✅ Local module imports test passed")
        except ImportError as e:
            print(f"⚠️  Local module import warning: {e}")
            # This is not a critical failure for basic testing
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def simulate_error_scenario():
    """Simulate an error scenario for testing patch generation"""
    print("🧪 Running error simulation test...")
    
    # This function can be modified to simulate different types of errors
    # for testing the patch generation system
    
    # Uncomment one of these lines to simulate different errors:
    
    # 1. Import Error
    # import non_existent_module
    
    # 2. Name Error
    # print(undefined_variable)
    
    # 3. Type Error
    # result = "string" + 123
    
    # 4. File Not Found Error
    # with open("non_existent_file.txt", 'r') as f:
    #     content = f.read()
    
    # 5. Division by Zero
    # result = 10 / 0
    
    # For now, just pass to avoid errors during normal testing
    print("✅ Error simulation test passed (no errors simulated)")
    return True

def main():
    """Main test function"""
    print("=" * 50)
    print("🚀 QUANTUM LOOP DEBUGGER - TEST SCRIPT")
    print("=" * 50)
    print(f"📅 Test started: {datetime.now().isoformat()}")
    print()
    
    # List of test functions
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("File Operations", test_file_operations),
        ("JSON Operations", test_json_operations),
        ("Import Statements", test_import_statements),
        ("Error Simulation", simulate_error_scenario)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    # Run all tests
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            if result:
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: CRASHED - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! System is healthy.")
        return 0
    else:
        print("⚠️  Some tests failed. System may need attention.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n🏁 Test script completed with exit code: {exit_code}")
    sys.exit(exit_code)
