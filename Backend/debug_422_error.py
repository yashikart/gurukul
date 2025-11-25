"""
Debug script to capture exact 422 error details and test current state
"""
import requests
import json
from datetime import datetime

def debug_422_error():
    """Debug the exact 422 error by testing various payload formats"""
    
    print("="*60)
    print("🔍 DEBUGGING 422 ERROR - DETAILED ANALYSIS")
    print("="*60)
    
    # Test different payload formats to identify the exact issue
    test_payloads = [
        {
            "name": "Minimal Payload (Backend Expected Format)",
            "url": "http://localhost:8001/start_agent_simulation",
            "payload": {
                "agent_id": "educational",
                "user_id": "test-user"
            }
        },
        {
            "name": "Frontend Format (camelCase)",
            "url": "http://localhost:8001/start_agent_simulation", 
            "payload": {
                "agentId": "educational",
                "userId": "test-user"
            }
        },
        {
            "name": "Mixed Format with Financial Profile",
            "url": "http://localhost:8001/start_agent_simulation",
            "payload": {
                "agent_id": "financial",
                "user_id": "test-user",
                "financial_profile": {
                    "name": "Test User",
                    "monthly_income": 50000
                }
            }
        },
        {
            "name": "Frontend Format with All Fields",
            "url": "http://localhost:8001/start_agent_simulation",
            "payload": {
                "agentId": "educational",
                "userId": "test-user",
                "timestamp": datetime.now().isoformat(),
                "financialProfile": {
                    "name": "Test User",
                    "monthlyIncome": 45000,
                    "financialGoal": "Save money"
                },
                "eduMentorProfile": {
                    "selectedSubject": "Math",
                    "topic": "Algebra"
                }
            }
        }
    ]
    
    for test in test_payloads:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"📤 Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            response = requests.post(
                test['url'],
                json=test['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                print(f"📋 Response: {data.get('message', 'No message')}")
                
            elif response.status_code == 422:
                print(f"❌ 422 VALIDATION ERROR - DETAILED BREAKDOWN:")
                try:
                    error_data = response.json()
                    print(f"📄 Full Error Response:")
                    print(json.dumps(error_data, indent=4))
                    
                    # Parse validation errors
                    if 'detail' in error_data and isinstance(error_data['detail'], list):
                        print(f"\n🔍 Validation Error Analysis:")
                        for error in error_data['detail']:
                            field_path = " -> ".join(str(loc) for loc in error.get('loc', []))
                            error_type = error.get('type', 'unknown')
                            message = error.get('msg', 'No message')
                            input_value = error.get('input', 'Not provided')
                            
                            print(f"   ❌ Field: {field_path}")
                            print(f"      Type: {error_type}")
                            print(f"      Message: {message}")
                            print(f"      Input: {input_value}")
                            print()
                            
                except Exception as e:
                    print(f"   📄 Raw Error Text: {response.text}")
                    print(f"   🚫 Could not parse JSON: {e}")
                    
            else:
                print(f"⚠️ Unexpected Status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION FAILED - Service not running on port 8001")
        except Exception as e:
            print(f"❌ ERROR: {e}")

def check_current_model_structure():
    """Check the current Pydantic model structure via introspection"""
    print(f"\n" + "="*60)
    print("🔍 CHECKING CURRENT MODEL STRUCTURE")
    print("="*60)
    
    # Test the API documentation endpoint to see current model structure
    try:
        response = requests.get("http://localhost:8001/docs", timeout=5)
        print(f"📊 API Docs Status: {response.status_code}")
        
        # Try to get OpenAPI schema
        schema_response = requests.get("http://localhost:8001/openapi.json", timeout=5)
        if schema_response.status_code == 200:
            schema = schema_response.json()
            
            # Look for AgentSimulationRequest in the schema
            if 'components' in schema and 'schemas' in schema['components']:
                schemas = schema['components']['schemas']
                
                if 'AgentSimulationRequest' in schemas:
                    model_schema = schemas['AgentSimulationRequest']
                    print(f"✅ Found AgentSimulationRequest model:")
                    print(json.dumps(model_schema, indent=4))
                else:
                    print(f"❌ AgentSimulationRequest not found in schemas")
                    print(f"📋 Available schemas: {list(schemas.keys())}")
            else:
                print(f"❌ No schemas found in OpenAPI spec")
        else:
            print(f"❌ Could not fetch OpenAPI schema: {schema_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking model structure: {e}")

def test_service_health():
    """Test service health and basic connectivity"""
    print(f"\n" + "="*60)
    print("🏥 TESTING SERVICE HEALTH")
    print("="*60)
    
    services = [
        {"name": "API Data Service", "url": "http://localhost:8001/health"},
        {"name": "Subject Generation", "url": "http://localhost:8005/health"},
    ]
    
    for service in services:
        try:
            response = requests.get(service['url'], timeout=5)
            print(f"🔍 {service['name']}: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Healthy")
            else:
                print(f"   ❌ Unhealthy: {response.text}")
        except Exception as e:
            print(f"❌ {service['name']}: Connection failed - {e}")

if __name__ == "__main__":
    print("🚀 STARTING DETAILED 422 ERROR DEBUGGING")
    print(f"⏰ Debug started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_service_health()
    debug_422_error()
    check_current_model_structure()
    
    print(f"\n" + "="*60)
    print("📋 DEBUGGING SUMMARY")
    print("="*60)
    print("If 422 errors persist after this analysis:")
    print("1. Check if the service restart properly applied the model changes")
    print("2. Verify the exact field names and types being sent")
    print("3. Ensure the Pydantic model changes were saved correctly")
    print("4. Consider restarting the API Data service manually")
    print("\n🔧 To restart API Data service manually:")
    print("   cd Backend/api_data")
    print("   python api.py")