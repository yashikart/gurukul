"""
Test both services to identify which one the frontend is calling
"""
import requests
import json
from datetime import datetime

def test_both_services():
    """Test both port 8001 and 8005 to see which has the issue"""
    
    print("="*60)
    print("🔍 TESTING BOTH SERVICES FOR 422 ERROR")
    print("="*60)
    
    # Test payload that matches what frontend sends
    frontend_payload = {
        "agentId": "educational",
        "userId": "test-user",
        "timestamp": datetime.now().isoformat(),
        "financialProfile": {
            "name": "Test User",
            "monthlyIncome": 45000,
            "financialGoal": "Save money"
        }
    }
    
    backend_payload = {
        "agent_id": "educational", 
        "user_id": "test-user",
        "timestamp": datetime.now().isoformat(),
        "financial_profile": {
            "name": "Test User",
            "monthly_income": 45000,
            "financial_goal": "Save money"
        }
    }
    
    services = [
        {
            "name": "API Data Service (Port 8001)",
            "url": "http://localhost:8001/start_agent_simulation",
            "port": 8001
        },
        {
            "name": "Subject Generation (Port 8005)", 
            "url": "http://localhost:8005/start_agent_simulation",
            "port": 8005
        }
    ]
    
    for service in services:
        print(f"\n🏢 Testing: {service['name']}")
        print(f"🌐 URL: {service['url']}")
        
        # Test 1: Frontend format (camelCase)
        print(f"\n   🧪 Test 1: Frontend Format (camelCase)")
        print(f"   📤 Payload: {json.dumps(frontend_payload, indent=6)}")
        
        try:
            response = requests.post(
                service['url'],
                json=frontend_payload,
                timeout=10
            )
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS: {data.get('message', 'No message')}")
            elif response.status_code == 422:
                print(f"   ❌ 422 ERROR")
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        for error in error_data['detail']:
                            field = ' -> '.join(str(loc) for loc in error.get('loc', []))
                            print(f"      Missing field: {field}")
                except:
                    pass
            else:
                print(f"   ⚠️ Status {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION FAILED - Service not running")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test 2: Backend format (snake_case)
        print(f"\n   🧪 Test 2: Backend Format (snake_case)")
        print(f"   📤 Payload: {json.dumps(backend_payload, indent=6)}")
        
        try:
            response = requests.post(
                service['url'],
                json=backend_payload,
                timeout=10
            )
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS: {data.get('message', 'No message')}")
            elif response.status_code == 422:
                print(f"   ❌ 422 ERROR")
            else:
                print(f"   ⚠️ Status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION FAILED")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def check_frontend_config():
    """Check which service the frontend should be calling"""
    print(f"\n" + "="*60)
    print("📋 FRONTEND CONFIGURATION ANALYSIS")
    print("="*60)
    
    print("Based on config.js:")
    print("   🔹 AGENT_API_BASE_URL = http://localhost:8005")
    print("   🔹 Frontend should call Subject Generation service (port 8005)")
    print("\nBased on error logs:")
    print("   🔹 Error shows port 8001 in logs")
    print("   🔹 This suggests frontend is calling API Data service (port 8001)")
    print("\n❓ QUESTION: Why is frontend calling port 8001 instead of 8005?")
    print("\nPossible causes:")
    print("   1. Frontend cache not refreshed")
    print("   2. Different API call bypassing agentApiSlice")
    print("   3. Proxy/routing configuration")
    print("   4. Multiple API configurations")

if __name__ == "__main__":
    print("🚀 TESTING BOTH SERVICES FOR 422 ERROR")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_both_services()
    check_frontend_config()
    
    print(f"\n" + "="*60)
    print("🎯 CONCLUSION")
    print("="*60)
    print("If port 8005 works with frontend format:")
    print("   ✅ The issue is frontend calling wrong service")
    print("   🔧 Solution: Fix frontend routing")
    print("\nIf port 8005 also fails with frontend format:")
    print("   ❌ Model updates didn't apply to Subject Generation")
    print("   🔧 Solution: Update Subject Generation models")