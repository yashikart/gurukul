"""
Test script to verify 422 error fix for agent simulation endpoints
"""
import requests
import json
from datetime import datetime

def test_422_fix():
    """Test the specific 422 error scenarios that were failing"""
    
    print("="*60)
    print("🔧 TESTING 422 ERROR FIX")
    print("="*60)
    
    # Test cases that were causing 422 errors
    test_cases = [
        {
            "name": "Basic Agent Simulation (Minimal Data)",
            "url": "http://localhost:8001/start_agent_simulation",
            "payload": {
                "agent_id": "educational",
                "user_id": "test-user",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "name": "Agent Simulation with Financial Profile",
            "url": "http://localhost:8001/start_agent_simulation", 
            "payload": {
                "agent_id": "financial",
                "user_id": "test-user",
                "timestamp": datetime.now().isoformat(),
                "financial_profile": {
                    "name": "Test User",
                    "monthly_income": 50000,
                    "financial_goal": "Save for future"
                }
            }
        },
        {
            "name": "Agent Simulation with EduMentor Profile",
            "url": "http://localhost:8001/start_agent_simulation",
            "payload": {
                "agent_id": "educational", 
                "user_id": "test-user",
                "timestamp": datetime.now().isoformat(),
                "edu_mentor_profile": {
                    "selectedSubject": "Mathematics",
                    "topic": "Algebra"
                }
            }
        },
        {
            "name": "Agent Simulation with Both Profiles",
            "url": "http://localhost:8001/start_agent_simulation",
            "payload": {
                "agent_id": "wellness",
                "user_id": "test-user", 
                "timestamp": datetime.now().isoformat(),
                "financial_profile": {
                    "name": "Test User",
                    "monthly_income": 45000
                },
                "edu_mentor_profile": {
                    "selectedSubject": "Health",
                    "topic": "Wellness"
                }
            }
        },
        {
            "name": "Reset Agent Simulation",
            "url": "http://localhost:8001/reset_agent_simulation",
            "payload": {
                "user_id": "test-user",
                "timestamp": datetime.now().isoformat()
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\\n🧪 Testing: {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        print(f"   Payload: {json.dumps(test_case['payload'], indent=4)}")
        
        try:
            response = requests.post(
                test_case['url'],
                json=test_case['payload'],
                timeout=10
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS")
                print(f"   Response: {data.get('message', 'No message')}")
                
                # Check for additional context
                if 'additional_context' in data:
                    print(f"   Context: {data['additional_context']}")
                    
                results.append({"test": test_case['name'], "status": "PASS", "code": 200})
                
            elif response.status_code == 422:
                print(f"   ❌ 422 VALIDATION ERROR (Still failing)")
                try:
                    error_data = response.json()
                    print(f"   Error details: {json.dumps(error_data, indent=4)}")
                except:
                    print(f"   Raw error: {response.text}")
                results.append({"test": test_case['name'], "status": "FAIL", "code": 422})
                
            else:
                print(f"   ⚠️  Unexpected Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                results.append({"test": test_case['name'], "status": "UNEXPECTED", "code": response.status_code})
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION FAILED - Service may not be running on port 8001")
            results.append({"test": test_case['name'], "status": "CONNECTION_ERROR", "code": "N/A"})
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({"test": test_case['name'], "status": "ERROR", "code": "N/A"})
    
    # Summary
    print("\\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] in ['CONNECTION_ERROR', 'ERROR', 'UNEXPECTED'])
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Errors: {errors}")
    print(f"📝 Total: {len(results)}")
    
    if failed == 0 and errors == 0:
        print("\\n🎉 ALL TESTS PASSED! 422 errors have been resolved!")
    elif failed > 0:
        print("\\n🔧 422 errors still persist. Additional debugging needed.")
    else:
        print("\\n⚠️  Some tests encountered connection issues.")
        
    print("\\n📋 DETAILED RESULTS:")
    for result in results:
        status_emoji = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
        print(f"   {status_emoji} {result['test']}: {result['status']} (HTTP {result['code']})")

def test_get_endpoints():
    """Test the GET endpoints to ensure they work"""
    print("\\n" + "="*60) 
    print("📤 TESTING GET ENDPOINTS")
    print("="*60)
    
    get_endpoints = [
        "http://localhost:8001/get_agent_output",
        "http://localhost:8001/agent_logs"
    ]
    
    for endpoint in get_endpoints:
        print(f"\\n🔍 Testing: {endpoint}")
        try:
            response = requests.get(endpoint, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS - Count: {data.get('count', 'N/A')}")
            else:
                print(f"   ❌ Error: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION FAILED")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

if __name__ == "__main__":
    print("🚀 STARTING 422 ERROR FIX VERIFICATION")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_422_fix()
    test_get_endpoints()
    
    print("\\n🏁 TESTING COMPLETED")
    print("\\nℹ️  If tests still show 422 errors:")
    print("1. Restart the API Data service (port 8001)")
    print("2. Ensure the AgentSimulationRequest model includes optional fields")
    print("3. Check frontend payload structure matches backend expectations")