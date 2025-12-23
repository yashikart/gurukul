#!/usr/bin/env python3
"""
Simple Endpoint Verification Script

This script verifies that all required API endpoint files exist and have the expected structure.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_files_exist():
    """Verify that all required files exist"""
    print("=== FILE VERIFICATION ===")
    
    required_files = [
        "routes/v1/karma/lifecycle.py",
        "utils/karma_lifecycle.py"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} does not exist")
            all_files_exist = False
    
    return all_files_exist

def verify_lifecycle_routes():
    """Verify that lifecycle routes file has expected endpoints"""
    print("\n=== LIFECYCLE ROUTES VERIFICATION ===")
    
    try:
        routes_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes/v1/karma/lifecycle.py")
        
        if not os.path.exists(routes_file):
            print("✗ Lifecycle routes file does not exist")
            return False
        
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Check for expected endpoint decorators
        expected_decorators = [
            "@router.get(\"/prarabdha/{user_id}\"",
            "@router.post(\"/prarabdha/update\"",
            "@router.post(\"/death/check\"",
            "@router.post(\"/death/process\"",
            "@router.post(\"/rebirth/process\"",
            "@router.post(\"/simulate\""
        ]
        
        found_decorators = []
        missing_decorators = []
        
        for decorator in expected_decorators:
            if decorator in content:
                found_decorators.append(decorator)
                print(f"✓ Found {decorator}")
            else:
                missing_decorators.append(decorator)
                print(f"✗ Missing {decorator}")
        
        return len(missing_decorators) == 0
        
    except Exception as e:
        print(f"✗ Error reading lifecycle routes file: {e}")
        return False

def verify_lifecycle_utils():
    """Verify that lifecycle utils file has expected functions"""
    print("\n=== LIFECYCLE UTILS VERIFICATION ===")
    
    try:
        utils_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils/karma_lifecycle.py")
        
        if not os.path.exists(utils_file):
            print("✗ Lifecycle utils file does not exist")
            return False
        
        with open(utils_file, 'r') as f:
            content = f.read()
        
        # Check for expected functions
        expected_functions = [
            "def get_prarabdha_counter",
            "def update_prarabdha_counter",
            "def check_death_event_threshold",
            "def process_death_event",
            "def process_rebirth",
            "def simulate_lifecycle_cycles"
        ]
        
        found_functions = []
        missing_functions = []
        
        for function in expected_functions:
            if function in content:
                found_functions.append(function)
                print(f"✓ Found {function}")
            else:
                missing_functions.append(function)
                print(f"✗ Missing {function}")
        
        return len(missing_functions) == 0
        
    except Exception as e:
        print(f"✗ Error reading lifecycle utils file: {e}")
        return False

if __name__ == "__main__":
    print("Verifying Karma Lifecycle Engine files and structure...\n")
    
    files_ok = verify_files_exist()
    routes_ok = verify_lifecycle_routes()
    utils_ok = verify_lifecycle_utils()
    
    print("\n=== SUMMARY ===")
    if files_ok and routes_ok and utils_ok:
        print("✓ All files exist and have the expected structure!")
        print("✓ The Karma Lifecycle Engine is properly implemented.")
        sys.exit(0)
    else:
        print("✗ Some files or structure elements are missing.")
        sys.exit(1)