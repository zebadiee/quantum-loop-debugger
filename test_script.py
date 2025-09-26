
#!/usr/bin/env python3
"""
Test Script for Quantum Loop Debugger
This script intentionally contains errors to demonstrate the self-healing system
"""

import random
import time
import sys

def test_import_error():
    """Test case that triggers import errors"""
    print("🧪 Testing import error scenario...")
    try:
        # This will fail if the module is not installed
        import nonexistent_module
        print("✅ Import test passed")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        raise

def test_name_error():
    """Test case that triggers name errors"""
    print("🧪 Testing name error scenario...")
    try:
        # This will fail because 'undefined_variable' is not defined
        result = undefined_variable + 10
        print(f"✅ Name test passed: {result}")
        return True
    except NameError as e:
        print(f"❌ Name error: {e}")
        raise

def test_type_error():
    """Test case that triggers type errors"""
    print("🧪 Testing type error scenario...")
    try:
        # This will fail because you can't add string and integer
        result = "hello" + 5
        print(f"✅ Type test passed: {result}")
        return True
    except TypeError as e:
        print(f"❌ Type error: {e}")
        raise

def test_file_not_found():
    """Test case that triggers file not found errors"""
    print("🧪 Testing file not found scenario...")
    try:
        # This will fail if the file doesn't exist
        with open("nonexistent_file.txt", "r") as f:
            content = f.read()
        print(f"✅ File test passed: {len(content)} characters read")
        return True
    except FileNotFoundError as e:
        print(f"❌ File not found error: {e}")
        raise

def test_division_by_zero():
    """Test case that triggers division by zero"""
    print("🧪 Testing division by zero scenario...")
    try:
        # This will fail with division by zero
        result = 10 / 0
        print(f"✅ Division test passed: {result}")
        return True
    except ZeroDivisionError as e:
        print(f"❌ Division by zero error: {e}")
        raise

def test_index_error():
    """Test case that triggers index errors"""
    print("🧪 Testing index error scenario...")
    try:
        # This will fail with index out of range
        my_list = [1, 2, 3]
        result = my_list[10]
        print(f"✅ Index test passed: {result}")
        return True
    except IndexError as e:
        print(f"❌ Index error: {e}")
        raise

def test_key_error():
    """Test case that triggers key errors"""
    print("🧪 Testing key error scenario...")
    try:
        # This will fail with key not found
        my_dict = {"a": 1, "b": 2}
        result = my_dict["nonexistent_key"]
        print(f"✅ Key test passed: {result}")
        return True
    except KeyError as e:
        print(f"❌ Key error: {e}")
        raise

def test_attribute_error():
    """Test case that triggers attribute errors"""
    print("🧪 Testing attribute error scenario...")
    try:
        # This will fail because strings don't have 'nonexistent_method'
        result = "hello".nonexistent_method()
        print(f"✅ Attribute test passed: {result}")
        return True
    except AttributeError as e:
        print(f"❌ Attribute error: {e}")
        raise

def test_value_error():
    """Test case that triggers value errors"""
    print("🧪 Testing value error scenario...")
    try:
        # This will fail because "hello" can't be converted to int
        result = int("hello")
        print(f"✅ Value test passed: {result}")
        return True
    except ValueError as e:
        print(f"❌ Value error: {e}")
        raise

def test_success_case():
    """Test case that should always pass"""
    print("🧪 Testing success scenario...")
    result = 2 + 2
    if result == 4:
        print("✅ Success test passed: 2 + 2 = 4")
        return True
    else:
        print(f"❌ Success test failed: 2 + 2 = {result}")
        return False

# Test scenarios with different failure rates
TEST_SCENARIOS = [
    ("import_error", test_import_error, 0.9),      # 90% chance to fail
    ("name_error", test_name_error, 0.8),          # 80% chance to fail
    ("type_error", test_type_error, 0.7),          # 70% chance to fail
    ("file_not_found", test_file_not_found, 0.6),  # 60% chance to fail
    ("division_by_zero", test_division_by_zero, 0.5), # 50% chance to fail
    ("index_error", test_index_error, 0.4),        # 40% chance to fail
    ("key_error", test_key_error, 0.3),            # 30% chance to fail
    ("attribute_error", test_attribute_error, 0.2), # 20% chance to fail
    ("value_error", test_value_error, 0.1),        # 10% chance to fail
    ("success", test_success_case, 0.0),           # 0% chance to fail (always pass)
]

def main():
    """Main test execution"""
    print("=" * 60)
    print("🧪 QUANTUM LOOP DEBUGGER - TEST SCRIPT")
    print("=" * 60)
    
    # Randomly select a test scenario
    scenario_name, test_func, failure_rate = random.choice(TEST_SCENARIOS)
    
    print(f"🎯 Selected test scenario: {scenario_name}")
    print(f"📊 Failure probability: {failure_rate * 100}%")
    print("-" * 40)
    
    # Simulate some processing time
    time.sleep(1)
    
    try:
        # Decide whether to run the failing version or success version
        if random.random() < failure_rate:
            print(f"🎲 Running failing version of {scenario_name}")
            test_func()
        else:
            print(f"🎲 Running success version of {scenario_name}")
            test_success_case()
        
        print("\n🎉 Test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {str(e)}")
        print(f"🔬 This failure will trigger the Quantum Loop Debugger")
        return 1

if __name__ == "__main__":
    sys.exit(main())
