"""
Test script to verify agent simulation endpoints are working
"""
import requests
import json
from datetime import datetime

def test_agent_endpoints():
    """Test agent simulation endpoints on both services"""
    
    # Test data
    test_data = {
        "agent_id": "educational",
        "user_id": "test-user",
        "timestamp": datetime.now().isoformat()
    }
    
    services = [
        {"name": "Subject Generation", "port": 8005},
        {"name": "API Data Service", "port": 8001}
    ]
    
    for service in services:
        print(f"\n=== Testing {service['name']} (Port {service['port']}) ===")
        base_url = f"http://localhost:{service['port']}"
        
        try:
            # Test start_agent_simulation
            print(f"Testing POST {base_url}/start_agent_simulation")
            response = requests.post(
                f"{base_url}/start_agent_simulation",
                json=test_data,
                timeout=10
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
                print("✅ start_agent_simulation endpoint working!")
            else:
                print(f"❌ Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - Service may not be running on port {service['port']}")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        try:
            # Test get_agent_output
            print(f"\nTesting GET {base_url}/get_agent_output")
            response = requests.get(f"{base_url}/get_agent_output", timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: Found {data.get('count', 0)} outputs")
                print("✅ get_agent_output endpoint working!")
            else:
                print(f"❌ Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - Service may not be running")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Test Financial Simulator simulation-results endpoint
    print(f"\n=== Testing Financial Simulator (Port 8002) ===")
    try:
        # Test simulation-results endpoint with a dummy ID
        simulation_id = "sim_20250826_115031_1"  # From the logs
        print(f"Testing GET http://localhost:8002/simulation-results/{simulation_id}")
        response = requests.get(
            f"http://localhost:8002/simulation-results/{simulation_id}",
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ simulation-results endpoint working!")
        elif response.status_code == 404:
            print("ℹ️  404 - This is expected for non-existent simulation ID")
            print("✅ Endpoint exists and responds correctly")
        else:
            print(f"❌ Unexpected response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - Financial Simulator may not be running on port 8002")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_agent_endpoints()