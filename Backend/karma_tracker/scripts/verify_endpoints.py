#!/usr/bin/env python3
"""
Endpoint Verification Script

This script verifies that all required API endpoints are correctly defined
without requiring a database connection.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_lifecycle_endpoints():
    """Verify that all lifecycle endpoints are correctly defined"""
    try:
        # Import the main app
        from main import app
        
        # Get all routes
        routes = app.routes
        
        # Lifecycle endpoints we expect to find
        expected_lifecycle_endpoints = [
            ("/api/v1/karma/lifecycle/prarabdha/{user_id}", "GET"),
            ("/api/v1/karma/lifecycle/prarabdha/update", "POST"),
            ("/api/v1/karma/lifecycle/death/check", "POST"),
            ("/api/v1/karma/lifecycle/death/process", "POST"),
            ("/api/v1/karma/lifecycle/rebirth/process", "POST"),
            ("/api/v1/karma/lifecycle/simulate", "POST")
        ]
        
        # Check which endpoints are present
        found_endpoints = []
        missing_endpoints = []
        
        for route in routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                path = route.path
                methods = list(route.methods)
                for expected_path, expected_method in expected_lifecycle_endpoints:
                    if expected_path in path and expected_method in methods:
                        found_endpoints.append((path, expected_method))
        
        # Check for missing endpoints
        for expected_path, expected_method in expected_lifecycle_endpoints:
            found = False
            for path, method in found_endpoints:
                if expected_path in path and expected_method == method:
                    found = True
                    break
            if not found:
                missing_endpoints.append((expected_path, expected_method))
        
        # Print results
        print("=== ENDPOINT VERIFICATION RESULTS ===")
        print(f"Found {len(found_endpoints)} lifecycle endpoints:")
        for path, method in found_endpoints:
            print(f"  ✓ {method} {path}")
        
        if missing_endpoints:
            print(f"\nMissing {len(missing_endpoints)} lifecycle endpoints:")
            for path, method in missing_endpoints:
                print(f"  ✗ {method} {path}")
        else:
            print("\n✓ All expected lifecycle endpoints are present!")
        
        # Additional verification - check if the lifecycle router is included
        print("\n=== ROUTER VERIFICATION ===")
        try:
            from routes.v1.karma.lifecycle import router as lifecycle_router
            print(f"✓ Lifecycle router imported successfully")
            print(f"✓ Lifecycle router has {len(lifecycle_router.routes)} routes")
            
            # Show all lifecycle routes
            print("\nLifecycle router routes:")
            for route in lifecycle_router.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    print(f"  {list(route.methods)[0]} {route.path}")
        except Exception as e:
            print(f"✗ Error importing lifecycle router: {e}")
        
        return len(missing_endpoints) == 0
        
    except Exception as e:
        print(f"Error verifying endpoints: {e}")
        return False

def verify_lifecycle_functions():
    """Verify that all required lifecycle functions are available"""
    print("\n=== FUNCTION VERIFICATION ===")
    
    try:
        from utils.karma_lifecycle import (
            get_prarabdha_counter,
            update_prarabdha_counter,
            check_death_event_threshold,
            process_death_event,
            process_rebirth,
            simulate_lifecycle_cycles
        )
        print("✓ All required lifecycle functions are available")
        return True
    except Exception as e:
        print(f"✗ Error importing lifecycle functions: {e}")
        return False

if __name__ == "__main__":
    print("Verifying Karma Lifecycle Engine endpoints and functions...\n")
    
    endpoints_ok = verify_lifecycle_endpoints()
    functions_ok = verify_lifecycle_functions()
    
    print("\n=== SUMMARY ===")
    if endpoints_ok and functions_ok:
        print("✓ All endpoints and functions are correctly defined!")
        print("✓ The Karma Lifecycle Engine is ready for use.")
        sys.exit(0)
    else:
        print("✗ Some endpoints or functions are missing.")
        sys.exit(1)