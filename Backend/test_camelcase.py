import requests
import json
from datetime import datetime

def test_camelcase_data():
    print("Testing camelCase data format from frontend...")
    
    # Test the exact payload that frontend sends with camelCase
    payload = {
        "agentId": "educational",
        "userId": "test-user-camel",
        "timestamp": datetime.now().isoformat(),
        "financialProfile": {"income": 5000, "goal": "savings"},
        "eduMentorProfile": {"subject": "mathematics"}
    }
    
    print(f"Testing camelCase payload: {json.dumps(payload, indent=2)}")
    
    # Test both services
    services = [
        "http://localhost:8001/start_agent_simulation",
        "http://localhost:8005/start_agent_simulation"
    ]
    
    for url in services:
        print(f"\nTesting {url}")
        try:
            response = requests.post(url, json=payload, timeout=5)
            print(f"Status: {response.status_code}")
            if response.status_code == 422:
                print("422 Error Details:")
                print(response.text)
            elif response.status_code == 200:
                print("Success!")
                print(response.json())
            else:
                print(f"Other error: {response.text}")
        except Exception as e:
            print(f"Connection error: {e}")

if __name__ == "__main__":
    test_camelcase_data()