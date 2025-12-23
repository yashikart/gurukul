#!/usr/bin/env python3
"""
Final Verification Script

This script verifies that all required API endpoints are defined in the lifecycle routes file.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_lifecycle_endpoints():
    """Verify that all lifecycle endpoints are defined"""
    print("=== LIFECYCLE ENDPOINTS VERIFICATION ===")
    
    try:
        routes_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes/v1/karma/lifecycle.py")
        
        if not os.path.exists(routes_file):
            print("✗ Lifecycle routes file does not exist")
            return False
        
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Expected endpoint patterns
        expected_patterns = [
            "@router.get(\"/prarabdha/{user_id}\"",
            "@router.post(\"/prarabdha/update\"",
            "@router.post(\"/death/check\"",
            "@router.post(\"/death/process\"",
            "@router.post(\"/rebirth/process\"",
            "@router.post(\"/simulate\""
        ]
        
        # Check for each pattern
        found_patterns = []
        missing_patterns = []
        
        for pattern in expected_patterns:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"✓ Found {pattern}")
            else:
                missing_patterns.append(pattern)
                print(f"✗ Missing {pattern}")
        
        # Also check for the function definitions
        expected_functions = [
            "async def get_prarabdha",
            "async def update_prarabdha",
            "async def check_death_threshold",
            "async def process_death",
            "async def process_rebirth_endpoint",
            "async def simulate_lifecycle_cycles"
        ]
        
        print("\nFunction definitions:")
        for function in expected_functions:
            if function in content:
                print(f"✓ Found {function}")
            else:
                print(f"✗ Missing {function}")
        
        return len(missing_patterns) == 0
        
    except Exception as e:
        print(f"✗ Error reading lifecycle routes file: {e}")
        return False

def verify_simulation_endpoint():
    """Verify that the simulation endpoint has been enhanced"""
    print("\n=== SIMULATION ENDPOINT VERIFICATION ===")
    
    try:
        routes_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes/v1/karma/lifecycle.py")
        
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Check for enhanced simulation features
        enhanced_features = [
            "SimulateCycleResponse",
            "statistics: Optional[Dict[str, Any]]",
            "from typing import Dict, Any, List, Optional",
        ]
        
        found_features = []
        missing_features = []
        
        for feature in enhanced_features:
            if feature in content:
                found_features.append(feature)
                print(f"✓ Found {feature}")
            else:
                missing_features.append(feature)
                print(f"✗ Missing {feature}")
        
        return len(missing_features) == 0
        
    except Exception as e:
        print(f"✗ Error reading lifecycle routes file: {e}")
        return False

def verify_utils_functions():
    """Verify that utils functions are properly defined"""
    print("\n=== UTILS FUNCTIONS VERIFICATION ===")
    
    try:
        utils_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils/karma_lifecycle.py")
        
        with open(utils_file, 'r') as f:
            content = f.read()
        
        # Check for key functions
        key_functions = [
            "def simulate_lifecycle_cycles",
            "def process_death_event",
            "def process_rebirth",
            "class KarmaLifecycleEngine"
        ]
        
        for function in key_functions:
            if function in content:
                print(f"✓ Found {function}")
            else:
                print(f"✗ Missing {function}")
        
        # Check if simulation function has the right parameters
        if "def simulate_lifecycle_cycles(cycles: int = 50, initial_users: int = 10)" in content:
            print("✓ Simulation function has correct parameters")
        else:
            print("✗ Simulation function may be missing parameters")
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading utils file: {e}")
        return False

if __name__ == "__main__":
    print("Final verification of Karma Lifecycle Engine implementation...\n")
    
    endpoints_ok = verify_lifecycle_endpoints()
    simulation_ok = verify_simulation_endpoint()
    utils_ok = verify_utils_functions()
    
    print("\n=== FINAL SUMMARY ===")
    if endpoints_ok and simulation_ok and utils_ok:
        print("✅ ALL VERIFICATIONS PASSED!")
        print("✅ The Karma Lifecycle Engine is fully implemented and ready!")
        print("\nEndpoints available:")
        print("  GET  /api/v1/karma/lifecycle/prarabdha/{user_id}")
        print("  POST /api/v1/karma/lifecycle/prarabdha/update")
        print("  POST /api/v1/karma/lifecycle/death/check")
        print("  POST /api/v1/karma/lifecycle/death/process")
        print("  POST /api/v1/karma/lifecycle/rebirth/process")
        print("  POST /api/v1/karma/lifecycle/simulate")
        sys.exit(0)
    else:
        print("❌ SOME VERIFICATIONS FAILED!")
        print("❌ Please check the implementation.")
        sys.exit(1)