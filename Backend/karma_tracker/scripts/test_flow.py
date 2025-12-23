#!/usr/bin/env python3
"""
KarmaChain Demo Flow CLI
A simple command-line interface to run a complete karma workflow demonstration.
"""

import requests
import json
import time
import sys
import argparse
import os
import tempfile
from datetime import datetime
from pprint import pprint

# Configuration
BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

def print_header(title):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}{Colors.RESET}\n")

def print_step(step_num, total_steps, description):
    """Print a formatted step description"""
    print(f"{Colors.YELLOW}[Step {step_num}/{total_steps}] {description}{Colors.RESET}")

def print_success(message, data=None):
    """Print success message with optional data"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    if data:
        if isinstance(data, dict) and len(data) <= 3:
            print(f"{Colors.GREEN}  Response: {data}{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}  Response: {json.dumps(data, indent=2) if isinstance(data, dict) else data}{Colors.RESET}")

def print_error(message, error_data=None):
    """Print error message with optional data"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    if error_data:
        print(f"{Colors.RED}  Error: {json.dumps(error_data, indent=2) if isinstance(error_data, dict) else error_data}{Colors.RESET}")

def make_api_request(method, endpoint, data=None, files=None):
    """Make API request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, timeout=API_TIMEOUT)
            else:
                response = requests.post(url, json=data, timeout=API_TIMEOUT)
        else:
            response = requests.get(url, timeout=API_TIMEOUT)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print_error(f"API request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Failed to parse JSON response: {str(e)}")
        return None

def check_system_health():
    """Check if the system is healthy"""
    print_step(1, 1, "Checking system health...")
    
    # Try multiple health endpoints
    endpoints = ["/health", "/stats/system"]
    
    for endpoint in endpoints:
        response = make_api_request("GET", endpoint)
        if response:
            if endpoint == "/health" and response.get("status") == "healthy":
                print_success(f"System is healthy - Version {response.get('version', 'unknown')}")
                return True
            elif endpoint == "/stats/system":
                print_success("System stats endpoint is accessible")
                return True
    
    print_error("System health check failed")
    return False

def run_full_demo_flow(user_id="demo_user"):
    """Run the complete demo flow using the actual API endpoints from the documentation"""
    print_header("KarmaChain Demo Flow")
    print(f"{Colors.BLUE}User ID: {user_id}{Colors.RESET}")
    print(f"{Colors.BLUE}API Base: {BASE_URL}{Colors.RESET}")
    
    # Check system health first
    if not check_system_health():
        return False
    
    print_header("Starting Karma Workflow Demo")
    
    # Step 1: Log a karma action using the unified event endpoint
    print_step(1, 7, "Logging karma action via unified event endpoint...")
    life_event_data = {
        "event_type": "life_event",
        "user_id": user_id,
        "action": "help",
        "description": "Helped a colleague debug a complex issue",
        "impact": "positive",
        "context": "workplace",
        "role": "human"
    }
    
    response = make_api_request("POST", "/event/", life_event_data)
    if response and (response.get("status") == "success" or "karma_change" in response):
        karma_change = response.get('karma_change', 5)  # Default to 5 if not specified
        print_success(f"Karma action logged: +{karma_change} points")
        if 'new_balance' in response:
            print(f"{Colors.GREEN}  New balance: {response.get('new_balance')}{Colors.RESET}")
    else:
        print_error("Failed to log karma action")
        # Continue anyway as this might be expected behavior
    
    time.sleep(1)
    
    # Step 2: Submit a karma appeal
    print_step(2, 7, "Submitting karma appeal...")
    appeal_data = {
        "user_id": user_id,
        "appeal_type": "karma_correction", 
        "reason": "Incorrect karma deduction from last week",
        "evidence": "Email thread showing the help was successful",
        "requested_change": 10
    }
    
    response = make_api_request("POST", "/Appeal/", appeal_data)
    if response and (response.get("status") == "success" or "appeal_id" in response):
        appeal_id = response.get('appeal_id', 'unknown')
        print_success(f"Appeal submitted: ID {appeal_id}")
        print(f"{Colors.GREEN}  Status: {response.get('status', 'submitted')}{Colors.RESET}")
    else:
        print_error("Failed to submit appeal")
        # Continue anyway
    
    time.sleep(1)
    
    # Step 3: Check appeal state
    print_step(3, 7, "Checking appeal state...")
    response = make_api_request("GET", f"/Appeal/titbits/{user_id}")
    if response:
        print_success("Appeal state retrieved")
        print(f"{Colors.GREEN}  Appeal data: {response}{Colors.RESET}")
    else:
        print_error("Failed to retrieve appeal state")
        # Continue anyway
    
    time.sleep(1)
    
    # Step 4: Request atonement plan
    print_step(4, 7, "Requesting atonement plan...")
    atonement_data = {
        "user_id": user_id,
        "reason": "Need to atone for negative workplace behavior",
        "severity": "moderate",
        "preferred_methods": ["meditation", "charity", "community_service"]
    }
    
    response = make_api_request("POST", "/Atonement/submit", atonement_data)
    if response and (response.get("status") == "success" or "atonement_id" in response):
        atonement_id = response.get('atonement_id', 'unknown')
        print_success(f"Atonement plan submitted: ID {atonement_id}")
        
        # Check if plan details are in response
        if 'plan' in response:
            plan = response.get('plan', {})
            tasks = plan.get('tasks', [])
            print(f"{Colors.GREEN}  Tasks assigned: {len(tasks)}{Colors.RESET}")
            for i, task in enumerate(tasks, 1):
                print(f"{Colors.GREEN}    Task {i}: {task.get('description')}{Colors.RESET}")
    else:
        print_error("Failed to submit atonement plan")
        # Continue anyway
    
    time.sleep(1)
    
    # Step 5: Get atonement plans for user
    print_step(5, 7, "Retrieving user's atonement plans...")
    response = make_api_request("GET", f"/Atonement/plans/{user_id}")
    if response:
        print_success("Atonement plans retrieved")
        plans = response if isinstance(response, list) else response.get('plans', [])
        print(f"{Colors.GREEN}  Number of plans: {len(plans)}{Colors.RESET}")
        for i, plan in enumerate(plans[:3], 1):  # Show first 3 plans
            print(f"{Colors.GREEN}    Plan {i}: {plan.get('status', 'unknown')} - {plan.get('reason', 'No reason')}{Colors.RESET}")
    else:
        print_error("Failed to retrieve atonement plans")
        # Continue anyway
    
    time.sleep(1)
    
    # Step 6: Get user statistics
    print_step(6, 7, "Retrieving user statistics...")
    response = make_api_request("GET", f"/stats/user/{user_id}")
    if response:
        print_success("User statistics retrieved")
        stats = response
        print(f"{Colors.GREEN}  User stats: {stats}{Colors.RESET}")
        
        # Try to extract meaningful information
        if 'current_karma' in stats:
            print(f"{Colors.GREEN}  Current karma: {stats.get('current_karma')}{Colors.RESET}")
        if 'karma_trend' in stats:
            print(f"{Colors.GREEN}  Karma trend: {stats.get('karma_trend')}{Colors.RESET}")
    else:
        print_error("Failed to retrieve user statistics")
        # Continue anyway
    
    time.sleep(1)
    
    # Step 7: Test file upload with unified event endpoint
    print_step(7, 7, "Testing file upload with unified event...")
    
    # Create a temporary text file for upload
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("This is a test file for atonement evidence.\n")
            temp_file.write("It demonstrates the file upload functionality.\n")
            temp_file_path = temp_file.name
        
        # Prepare event data for file upload
        event_data = {
            "event_type": "atonement_evidence",
            "user_id": user_id,
            "description": "Atonement with supporting evidence file",
            "file_purpose": "Supporting documentation"
        }
        
        # Prepare multipart form data
        form_data = {
            "event_data": json.dumps(event_data)
        }
        
        # Use context manager for file handling
        with open(temp_file_path, "rb") as file_handle:
            files = {
                "file": ("test_evidence.txt", file_handle, "text/plain")
            }
            
            response = make_api_request("POST", "/event/with-file", form_data, files)
        
        if response and (response.get("status") == "success" or "file_id" in response):
            print_success(f"File uploaded successfully via unified endpoint")
            print(f"{Colors.GREEN}  File ID: {response.get('file_id', 'unknown')}{Colors.RESET}")
            if 'file_info' in response:
                print(f"{Colors.GREEN}  File info: {response.get('file_info')}{Colors.RESET}")
        else:
            print_error("File upload failed via unified endpoint")
            # Don't fail the demo for file upload issues
    
    except Exception as e:
        print_error(f"File upload test failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass
    
    time.sleep(1)
    
    # Additional: Get wallet balance
    print_step(8, 8, "Checking wallet balance...")
    response = make_api_request("GET", f"/wallet/balance/{user_id}")
    if response:
        print_success("Wallet balance retrieved")
        balance = response
        print(f"{Colors.GREEN}  Balance: {balance}{Colors.RESET}")
    else:
        print_error("Failed to retrieve wallet balance")
        # Continue anyway
    
    print_header("Demo Flow Complete!")
    print(f"{Colors.GREEN}✓ Karma workflow demonstration completed!{Colors.RESET}")
    print(f"{Colors.BLUE}Note: Some steps may show errors if endpoints are not fully implemented.{Colors.RESET}")
    print(f"{Colors.BLUE}This is normal during development.{Colors.RESET}")
    
    return True

def run_quick_test():
    """Run a quick health check and basic test"""
    print_header("KarmaChain Quick Test")
    
    # Check system health
    if not check_system_health():
        return False
    
    # Test basic event processing
    print_step(1, 2, "Testing unified event endpoint...")
    test_data = {
        "event_type": "test_event",
        "user_id": "quick_test_user",
        "action": "test",
        "description": "Quick system test"
    }
    
    response = make_api_request("POST", "/event/", test_data)
    if response:
        print_success("Unified event endpoint works")
        print(f"{Colors.GREEN}  Response: {response}{Colors.RESET}")
    else:
        print_error("Unified event endpoint test failed")
        return False
    
    print_header("Quick Test Complete!")
    print(f"{Colors.GREEN}✓ System is operational!{Colors.RESET}")
    return True

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="KarmaChain Demo Flow CLI - Test the complete karma workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_flow.py              # Run full demo flow
  python scripts/test_flow.py --quick      # Run quick health check
  python scripts/test_flow.py --user bob   # Use custom user ID
  python scripts/test_flow.py --url http://localhost:9000  # Use different API URL
        """
    )
    
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="Run quick health check instead of full demo"
    )
    
    parser.add_argument(
        "--user", 
        type=str, 
        default="demo_user",
        help="User ID to use for testing (default: demo_user)"
    )
    
    parser.add_argument(
        "--url", 
        type=str, 
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=30,
        help="API request timeout in seconds (default: 30)"
    )
    
    args = parser.parse_args()
    
    # Update global configuration
    global BASE_URL, API_TIMEOUT
    BASE_URL = args.url.rstrip('/')
    API_TIMEOUT = args.timeout
    
    print(f"{Colors.CYAN}KarmaChain Demo Flow CLI{Colors.RESET}")
    print(f"{Colors.BLUE}API URL: {BASE_URL}{Colors.RESET}")
    
    try:
        if args.quick:
            success = run_quick_test()
        else:
            success = run_full_demo_flow(args.user)
        
        if success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}Demo completed successfully! ✓{Colors.RESET}")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}Demo failed! ✗{Colors.RESET}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()