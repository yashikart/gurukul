"""
Comprehensive Health Check for All Gurukul Services
"""
import os
import sys
import requests
import json
from datetime import datetime

class ServiceHealthChecker:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "unknown"
        }
    
    def check_service(self, name, url, port):
        """Check if a service is running"""
        try:
            response = requests.get(f"{url}:{port}/health", timeout=5)
            if response.status_code == 200:
                self.results["services"][name] = {
                    "status": "✅ HEALTHY",
                    "url": f"{url}:{port}",
                    "response_time": response.elapsed.total_seconds()
                }
                return True
            else:
                self.results["services"][name] = {
                    "status": f"⚠️ UNHEALTHY (HTTP {response.status_code})",
                    "url": f"{url}:{port}"
                }
                return False
        except requests.exceptions.ConnectionError:
            self.results["services"][name] = {
                "status": "❌ NOT RUNNING",
                "url": f"{url}:{port}",
                "error": "Connection refused"
            }
            return False
        except requests.exceptions.Timeout:
            self.results["services"][name] = {
                "status": "⏰ TIMEOUT",
                "url": f"{url}:{port}",
                "error": "Request timeout"
            }
            return False
        except Exception as e:
            self.results["services"][name] = {
                "status": "❌ ERROR",
                "url": f"{url}:{port}",
                "error": str(e)
            }
            return False
    
    def check_all_services(self):
        """Check all Gurukul services"""
        print("=" * 60)
        print("GURUKUL PLATFORM - COMPREHENSIVE HEALTH CHECK")
        print("=" * 60)
        print()
        
        services = [
            ("Backend Main", "http://localhost", 8002),
            ("Chatbot Service", "http://localhost", 8001),
            ("Frontend", "http://localhost", 5173),
            ("TTS Service", "http://localhost", 8007),
        ]
        
        healthy_count = 0
        total_count = len(services)
        
        for name, url, port in services:
            print(f"Checking {name}...", end=" ")
            is_healthy = self.check_service(name, url, port)
            if is_healthy:
                healthy_count += 1
            print(self.results["services"][name]["status"])
        
        print()
        print("=" * 60)
        print(f"SUMMARY: {healthy_count}/{total_count} services healthy")
        print("=" * 60)
        print()
        
        # Determine overall status
        if healthy_count == total_count:
            self.results["overall_status"] = "✅ ALL SERVICES HEALTHY"
        elif healthy_count > 0:
            self.results["overall_status"] = f"⚠️ PARTIAL ({healthy_count}/{total_count} healthy)"
        else:
            self.results["overall_status"] = "❌ ALL SERVICES DOWN"
        
        print(f"Overall Status: {self.results['overall_status']}")
        print()
        
        # Detailed report
        print("DETAILED REPORT:")
        print("-" * 60)
        for service_name, service_data in self.results["services"].items():
            print(f"\n{service_name}:")
            for key, value in service_data.items():
                print(f"  {key}: {value}")
        
        print()
        print("=" * 60)
        
        # Save report
        report_file = "health_check_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"Report saved to: {report_file}")
        
        return healthy_count == total_count

if __name__ == "__main__":
    checker = ServiceHealthChecker()
    all_healthy = checker.check_all_services()
    
    if not all_healthy:
        print()
        print("⚠️ RECOMMENDATIONS:")
        print("1. Make sure all services are started")
        print("2. Check if ports are not blocked by firewall/antivirus")
        print("3. Disable browser ad blockers for localhost")
        print("4. Run: START_ALL.bat to start all services")
        sys.exit(1)
    else:
        print()
        print("✅ All services are running correctly!")
        sys.exit(0)
