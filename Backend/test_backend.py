#!/usr/bin/env python3
"""
Backend Health Check and Test Script
Tests all backend endpoints and services
"""

import requests
import json
from colorama import init, Fore, Style

init(autoreset=True)

def test_endpoint(name, url, method="GET", data=None):
    """Test a single endpoint"""
    try:
        print(f"\n{Fore.CYAN}Testing {name}...{Style.RESET_ALL}")
        print(f"URL: {url}")
        
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"{Fore.GREEN}✓ SUCCESS{Style.RESET_ALL}")
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Response: {response.text[:200]}")
            return True
        else:
            print(f"{Fore.RED}✗ FAILED{Style.RESET_ALL}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}✗ CONNECTION FAILED - Service not running{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ ERROR: {str(e)}{Style.RESET_ALL}")
        return False

def main():
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}GURUKUL BACKEND HEALTH CHECK{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    results = {}
    
    # Test main backend
    results['Main Backend'] = test_endpoint(
        "Main Backend - Root",
        "http://localhost:8000/"
    )
    
    results['Health Check'] = test_endpoint(
        "Main Backend - Health",
        "http://localhost:8000/health"
    )
    
    # Test mounted services
    services = [
        ("Base Backend", "http://localhost:8000/api/v1/base/"),
        ("Memory Management", "http://localhost:8000/api/v1/memory/"),
        ("Financial Simulator", "http://localhost:8000/api/v1/financial/"),
        ("Subject Generation", "http://localhost:8000/api/v1/subjects/"),
        ("Akash Service", "http://localhost:8000/api/v1/akash/"),
        ("TTS Service", "http://localhost:8000/api/v1/tts/"),
    ]
    
    for name, url in services:
        results[name] = test_endpoint(name, url)
    
    # Test standalone services (if running)
    standalone = [
        ("Chat API", "http://localhost:8001/health"),
        ("Financial API", "http://localhost:8002/health"),
        ("Memory API", "http://localhost:8003/health"),
        ("Agent API", "http://localhost:8005/health"),
    ]
    
    for name, url in standalone:
        results[name] = test_endpoint(name, url)
    
    # Summary
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}TEST SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        icon = f"{Fore.GREEN}✓{Style.RESET_ALL}" if status else f"{Fore.RED}✗{Style.RESET_ALL}"
        print(f"{icon} {name}")
    
    print(f"\n{Fore.CYAN}Results: {passed}/{total} tests passed{Style.RESET_ALL}")
    
    if passed == total:
        print(f"{Fore.GREEN}All services are operational!{Style.RESET_ALL}")
    elif passed > 0:
        print(f"{Fore.YELLOW}Some services are not running. Check the logs above.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}No services are running. Please start the backend.{Style.RESET_ALL}")
        print(f"\nTo start: python main.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
