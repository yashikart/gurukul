# !/usr/bin/env python3
"""
KarmaChain Demo CLI
A simple command-line interface to demonstrate and validate the Karma Tracker functionality.
"""

import requests
import json
import time
import sys
import argparse
import os
from datetime import datetime
from typing import Dict, Any, Optional

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

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}{Colors.RESET}\n")

def print_step(step_num: int, total_steps: int, description: str):
    """Print a formatted step description"""
    print(f"{Colors.YELLOW}[Step {step_num}/{total_steps}] {description}{Colors.RESET}")

def print_success(message: str, data: Optional[Any] = None):
    """Print success message with optional data"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    if data:
        if isinstance(data, dict) and len(data) <= 3:
            print(f"{Colors.GREEN}  Response: {data}{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}  Response: {json.dumps(data, indent=2) if isinstance(data, dict) else data}{Colors.RESET}")

def print_error(message: str, error_data: Optional[Any] = None):
    """Print error message with optional data"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    if error_data:
        print(f"{Colors.RED}  Error: {json.dumps(error_data, indent=2) if isinstance(error_data, dict) else error_data}{Colors.RESET}")

def make_api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
    """Make API request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
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

def check_system_health() -> bool:
    """Check if the system is healthy"""
    print_step(1, 1, "Checking system health...")
    
    # Try to get stats endpoint
    response = make_api_request("GET", "/stats/system")
    if response:
        print_success(f"System is accessible")
        return True
    
    # Try basic health check
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=API_TIMEOUT)
        if response.status_code == 200:
            print_success("System health endpoint is accessible")
            return True
    except:
        pass
    
    print_error("System is not accessible. Please ensure KarmaChain is running.")
    return False

def demo_karma_workflow(user_id: str = "demo_user") -> bool:
    """Demonstrate the complete karma workflow"""
    print_header("KarmaChain Workflow Demo")
    print(f"{Colors.BLUE}User ID: {user_id}{Colors.RESET}")
    print(f"{Colors.BLUE}API Base: {BASE_URL}{Colors.RESET}")
    
    # Check system health first
    if not check_system_health():
        return False
    
    print_header("Starting Karma Workflow Demo")
    
    # Step 1: Get initial karma profile
    print_step(1, 6, "Getting initial karma profile...")
    response = make_api_request("GET", f"/api/v1/karma/{user_id}")
    if response:
        print_success("Initial karma profile retrieved")
        initial_karma = response.get("net_karma", 0)
        print(f"{Colors.GREEN}  Net karma: {initial_karma}{Colors.RESET}")
    else:
        # Create user by logging an action
        print_step(1, 6, "Creating user by logging first action...")
        action_data = {
            "user_id": user_id,
            "action": "completing_lessons",
            "role": "learner",
            "context": "Demo workflow initialization"
        }
        response = make_api_request("POST", "/api/v1/log-action/", action_data)
        if response:
            print_success("User created and initial action logged")
        else:
            print_error("Failed to create user")
            return False
    
    time.sleep(1)
    
    # Step 2: Log a positive karma action
    print_step(2, 6, "Logging a positive karma action...")
    positive_action_data = {
        "user_id": user_id,
        "action": "helping_peers",
        "role": "learner",
        "intensity": 1.5,
        "context": "Helped classmates with assignment",
        "metadata": {
            "subject": "mathematics",
            "duration_minutes": 30
        }
    }
    
    response = make_api_request("POST", "/api/v1/log-action/", positive_action_data)
    if response:
        karma_impact = response.get("karma_impact", 0)
        print_success(f"Positive action logged: +{karma_impact} karma")
        print(f"{Colors.GREEN}  Reward: {response.get('reward_value', 0)} {response.get('reward_token', 'tokens')}{Colors.RESET}")
    else:
        print_error("Failed to log positive action")
        return False
    
    time.sleep(1)
    
    # Step 3: Log a negative karma action
    print_step(3, 6, "Logging a negative karma action...")
    negative_action_data = {
        "user_id": user_id,
        "action": "cheat",
        "role": "learner",
        "intensity": 1.0,
        "context": "Attempted to cheat on quiz",
        "metadata": {
            "subject": "history",
            "quiz_type": "online"
        }
    }
    
    response = make_api_request("POST", "/api/v1/log-action/", negative_action_data)
    if response:
        karma_impact = response.get("karma_impact", 0)
        print_success(f"Negative action logged: {karma_impact} karma")
        if response.get("paap_generated"):
            print(f"{Colors.GREEN}  Paap generated: {response.get('paap_value', 0)} ({response.get('paap_severity', 'unknown')}){Colors.RESET}")
    else:
        print_error("Failed to log negative action")
        return False
    
    time.sleep(1)
    
    # Step 4: Get updated karma profile
    print_step(4, 6, "Getting updated karma profile...")
    response = make_api_request("GET", f"/api/v1/karma/{user_id}")
    if response:
        print_success("Updated karma profile retrieved")
        net_karma = response.get("net_karma", 0)
        merit_score = response.get("merit_score", 0)
        paap_score = response.get("paap_score", 0)
        print(f"{Colors.GREEN}  Net karma: {net_karma}{Colors.RESET}")
        print(f"{Colors.GREEN}  Merit score: {merit_score}{Colors.RESET}")
        print(f"{Colors.GREEN}  Paap score: {paap_score}{Colors.RESET}")
        
        # Show token balances
        balances = response.get("balances", {})
        if balances:
            print(f"{Colors.GREEN}  Token balances:{Colors.RESET}")
            for token, value in balances.items():
                if isinstance(value, dict):
                    for sub_token, sub_value in value.items():
                        print(f"{Colors.GREEN}    {token}.{sub_token}: {sub_value}{Colors.RESET}")
                else:
                    print(f"{Colors.GREEN}    {token}: {value}{Colors.RESET}")
    else:
        print_error("Failed to get updated karma profile")
        return False
    
    time.sleep(1)
    
    # Step 5: Submit atonement for the negative action
    print_step(5, 6, "Submitting atonement for negative action...")
    atonement_data = {
        "user_id": user_id,
        "plan_id": "demo_plan_001",
        "atonement_type": "Jap",
        "amount": 108,
        "proof_text": "Completed 108 repetitions of Om Mani Padme Hum as atonement"
    }
    
    response = make_api_request("POST", "/api/v1/submit-atonement/", atonement_data)
    if response:
        print_success("Atonement submitted successfully")
        karma_adjustment = response.get("karma_adjustment", 0)
        paap_reduction = response.get("paap_reduction", 0)
        print(f"{Colors.GREEN}  Karma adjustment: +{karma_adjustment}{Colors.RESET}")
        print(f"{Colors.GREEN}  Paap reduction: -{paap_reduction}{Colors.RESET}")
    else:
        print_error("Failed to submit atonement")
        return False
    
    time.sleep(1)
    
    # Step 6: Get final karma profile
    print_step(6, 6, "Getting final karma profile...")
    response = make_api_request("GET", f"/api/v1/karma/{user_id}")
    if response:
        print_success("Final karma profile retrieved")
        net_karma = response.get("net_karma", 0)
        merit_score = response.get("merit_score", 0)
        paap_score = response.get("paap_score", 0)
        print(f"{Colors.GREEN}  Net karma: {net_karma}{Colors.RESET}")
        print(f"{Colors.GREEN}  Merit score: {merit_score}{Colors.RESET}")
        print(f"{Colors.GREEN}  Paap score: {paap_score}{Colors.RESET}")
        
        # Show corrective guidance
        guidance = response.get("corrective_guidance", [])
        if guidance:
            print(f"{Colors.GREEN}  Corrective guidance:{Colors.RESET}")
            for rec in guidance[:3]:  # Show first 3 recommendations
                print(f"{Colors.GREEN}    {rec.get('practice', 'Unknown')}: {rec.get('reason', 'No reason')}{Colors.RESET}")
    else:
        print_error("Failed to get final karma profile")
        return False
    
    print_header("Demo Workflow Complete!")
    print(f"{Colors.GREEN}✓ Karma workflow demonstration completed successfully!{Colors.RESET}")
    return True

def demo_multiple_users() -> bool:
    """Demonstrate karma tracking for multiple users"""
    print_header("Multi-User Karma Tracking Demo")
    
    users = [
        {"id": "alice_demo", "actions": ["completing_lessons", "helping_peers", "selfless_service"]},
        {"id": "bob_demo", "actions": ["cheat", "helping_peers", "completing_lessons"]},
        {"id": "charlie_demo", "actions": ["selfless_service", "solving_doubts", "meditate_daily"]}
    ]
    
    user_results = {}
    
    for i, user in enumerate(users, 1):
        user_id = user["id"]
        actions = user["actions"]
        
        print_step(i, len(users), f"Processing user {user_id}...")
        
        # Log actions for this user
        for action in actions:
            action_data = {
                "user_id": user_id,
                "action": action,
                "role": "learner",
                "intensity": 1.0,
                "context": f"Demo action: {action}"
            }
            
            response = make_api_request("POST", "/api/v1/log-action/", action_data)
            if not response:
                print_error(f"Failed to log action {action} for user {user_id}")
                continue
        
        # Get final karma profile
        response = make_api_request("GET", f"/api/v1/karma/{user_id}")
        if response:
            net_karma = response.get("net_karma", 0)
            user_results[user_id] = net_karma
            print_success(f"User {user_id} final karma: {net_karma}")
        else:
            print_error(f"Failed to get karma profile for user {user_id}")
            user_results[user_id] = 0
    
    # Display results
    print_header("Multi-User Results")
    sorted_results = sorted(user_results.items(), key=lambda x: x[1], reverse=True)
    for user_id, karma in sorted_results:
        print(f"{Colors.GREEN}{user_id}: {karma} karma{Colors.RESET}")
    
    return True

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="KarmaChain Demo CLI - Demonstrate and validate the Karma Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/demo_cli.py                    # Run basic karma workflow demo
  python scripts/demo_cli.py --multi            # Run multi-user demo
  python scripts/demo_cli.py --user alice       # Use custom user ID
  python scripts/demo_cli.py --url http://localhost:9000  # Use different API URL
        """
    )
    
    parser.add_argument(
        "--multi", 
        action="store_true",
        help="Run multi-user demo instead of single user"
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
    
    print(f"{Colors.CYAN}KarmaChain Demo CLI{Colors.RESET}")
    print(f"{Colors.BLUE}API URL: {BASE_URL}{Colors.RESET}")
    
    try:
        if args.multi:
            success = demo_multiple_users()
        else:
            success = demo_karma_workflow(args.user)
        
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