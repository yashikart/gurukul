"""
Service Health Check Script
Tests all backend services to ensure they are running correctly with proper CORS
"""

import requests
import time
import json
from datetime import datetime

# Service configurations
SERVICES = {
    "Base Backend": {
        "url": "http://localhost:8000/health",
        "port": 8000,
        "description": "Main API service"
    },
    "API Data Service": {
        "url": "http://localhost:8001/health", 
        "port": 8001,
        "description": "Data processing service"
    },
    "Financial Simulator": {
        "url": "http://localhost:8002/health",
        "port": 8002,
        "description": "Financial forecasting and simulation"
    },
    "Memory Management": {
        "url": "http://localhost:8003/memory/health",
        "port": 8003,
        "description": "User memory and session management"
    },
    "Akash Service": {
        "url": "http://localhost:8004/health",
        "port": 8004,
        "description": "Auth and memory gateway"
    },
    "Subject Generation": {
        "url": "http://localhost:8005/health",
        "port": 8005,
        "description": "Educational content generation"
    },
    "Wellness API + Forecasting": {
        "url": "http://localhost:8006/",
        "port": 8006,
        "description": "Orchestration and advanced forecasting"
    },
    "TTS Service": {
        "url": "http://localhost:8007/api/health",
        "port": 8007,
        "description": "Text-to-Speech service"
    }
}

FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173", 
    "http://localhost:5174"
]

def test_service_health(service_name, config):
    """Test if a service is healthy"""
    try:
        response = requests.get(config["url"], timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def test_cors(service_name, config):
    """Test CORS configuration for frontend origins"""
    cors_results = {}
    
    for origin in FRONTEND_ORIGINS:
        try:
            # Test preflight OPTIONS request
            headers = {
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            response = requests.options(config["url"], headers=headers, timeout=5)
            
            # Check if CORS headers are present
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            # Determine if CORS is properly configured
            allows_origin = (
                cors_headers["Access-Control-Allow-Origin"] == origin or 
                cors_headers["Access-Control-Allow-Origin"] == "*"
            )
            
            cors_results[origin] = {
                "status": "✅ PASS" if allows_origin else "❌ FAIL",
                "headers": cors_headers
            }
            
        except Exception as e:
            cors_results[origin] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
    
    return cors_results

def main():
    """Main health check function"""
    print("="*80)
    print("🏥 GURUKUL BACKEND SERVICES HEALTH CHECK")
    print("="*80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    healthy_services = 0
    total_services = len(SERVICES)
    
    for service_name, config in SERVICES.items():
        print(f"🔍 Testing {service_name}...")
        print(f"   URL: {config['url']}")
        print(f"   Description: {config['description']}")
        
        # Test health
        is_healthy, health_data = test_service_health(service_name, config)
        
        if is_healthy:
            print(f"   Health: ✅ HEALTHY")
            healthy_services += 1
            
            # Test CORS if service is healthy
            print(f"   🌐 Testing CORS configuration...")
            cors_results = test_cors(service_name, config)
            
            for origin, result in cors_results.items():
                print(f"     {origin}: {result['status']}")
                if result['status'] == "❌ FAIL":
                    print(f"       Issue: Origin not allowed")
                elif result['status'] == "❌ ERROR":
                    print(f"       Error: {result.get('error', 'Unknown error')}")
            
        else:
            print(f"   Health: ❌ UNHEALTHY - {health_data}")
            print(f"   🌐 CORS: ⏭️  SKIPPED (service not running)")
        
        print()
    
    # Summary
    print("="*80)
    print("📊 HEALTH CHECK SUMMARY")
    print("="*80)
    print(f"✅ Healthy Services: {healthy_services}/{total_services}")
    print(f"❌ Unhealthy Services: {total_services - healthy_services}/{total_services}")
    
    if healthy_services == total_services:
        print("🎉 ALL SERVICES ARE HEALTHY!")
        print("🌐 Frontend should be able to connect to all backend services")
    else:
        print("⚠️  SOME SERVICES ARE DOWN!")
        print("💡 Recommendations:")
        print("   1. Run: cd Backend && start_all_services.bat")
        print("   2. Wait 30-60 seconds for all services to start")
        print("   3. Check for port conflicts or missing dependencies")
        print("   4. Re-run this health check")
    
    print()
    print("🔧 Need help? Check the logs in the service terminal windows")
    print("📖 Documentation: Backend/README.md")
    print("="*80)

if __name__ == "__main__":
    main()