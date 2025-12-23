#!/usr/bin/env python3
"""
API Structure Test

This script verifies the API structure by examining the route definitions directly.
"""

import sys
import os
import ast

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_routes_file(file_path):
    """Parse a routes file and extract endpoint information"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse the Python code
    tree = ast.parse(content)
    
    endpoints = []
    
    # Look for function definitions with router decorators
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for decorators
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ['get', 'post', 'put', 'delete']:
                        # Extract the path from the decorator
                        if decorator.args:
                            path_arg = decorator.args[0]
                            if isinstance(path_arg, ast.Constant):
                                path = path_arg.value
                                method = decorator.func.attr.upper()
                                endpoints.append({
                                    'path': path,
                                    'method': method,
                                    'function': node.name
                                })
    
    return endpoints

def verify_lifecycle_api_structure():
    """Verify the lifecycle API structure"""
    print("=== LIFECYCLE API STRUCTURE VERIFICATION ===")
    
    try:
        routes_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes/v1/karma/lifecycle.py")
        
        if not os.path.exists(routes_file):
            print("✗ Lifecycle routes file does not exist")
            return False
        
        endpoints = parse_routes_file(routes_file)
        
        # Expected endpoints
        expected_endpoints = [
            {'path': '/prarabdha/{user_id}', 'method': 'GET'},
            {'path': '/prarabdha/update', 'method': 'POST'},
            {'path': '/death/check', 'method': 'POST'},
            {'path': '/death/process', 'method': 'POST'},
            {'path': '/rebirth/process', 'method': 'POST'},
            {'path': '/simulate', 'method': 'POST'}
        ]
        
        # Check which endpoints are present
        found_endpoints = []
        missing_endpoints = []
        
        for expected in expected_endpoints:
            found = False
            for endpoint in endpoints:
                if (endpoint['path'] == expected['path'] and 
                    endpoint['method'] == expected['method']):
                    found_endpoints.append(endpoint)
                    found = True
                    break
            
            if not found:
                missing_endpoints.append(expected)
        
        # Print results
        print(f"Found {len(found_endpoints)} lifecycle endpoints:")
        for endpoint in found_endpoints:
            print(f"  ✓ {endpoint['method']} {endpoint['path']} -> {endpoint['function']}")
        
        if missing_endpoints:
            print(f"\nMissing {len(missing_endpoints)} lifecycle endpoints:")
            for endpoint in missing_endpoints:
                print(f"  ✗ {endpoint['method']} {endpoint['path']}")
        else:
            print("\n✓ All expected lifecycle endpoints are present!")
        
        return len(missing_endpoints) == 0
        
    except Exception as e:
        print(f"✗ Error parsing lifecycle routes file: {e}")
        return False

def verify_main_app_includes_lifecycle():
    """Verify that the main app includes the lifecycle router"""
    print("\n=== MAIN APP LIFECYCLE INTEGRATION VERIFICATION ===")
    
    try:
        main_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
        
        if not os.path.exists(main_file):
            print("✗ Main app file does not exist")
            return False
        
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Check for lifecycle router inclusion
        if "lifecycle_router" in content and "include_router" in content:
            print("✓ Main app includes lifecycle router")
            return True
        else:
            print("✗ Main app does not include lifecycle router")
            return False
        
    except Exception as e:
        print(f"✗ Error reading main app file: {e}")
        return False

if __name__ == "__main__":
    print("Verifying Karma Lifecycle Engine API structure...\n")
    
    structure_ok = verify_lifecycle_api_structure()
    integration_ok = verify_main_app_includes_lifecycle()
    
    print("\n=== SUMMARY ===")
    if structure_ok and integration_ok:
        print("✓ API structure is correctly defined!")
        print("✓ The Karma Lifecycle Engine endpoints are properly structured.")
        sys.exit(0)
    else:
        print("✗ API structure has issues.")
        sys.exit(1)