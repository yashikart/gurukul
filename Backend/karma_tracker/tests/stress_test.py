"""
KarmaChain Stress Test Suite
Simulates 100 concurrent users performing various karma actions
to test system performance and reliability under load.
"""

import asyncio
import aiohttp
import time
import json
import random
import sys
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"
CONCURRENT_USERS = 100
ACTIONS_PER_USER = 10
MAX_CONCURRENT_REQUESTS = 50

# Sample actions for realistic testing
KARMA_ACTIONS = [
    {"action_type": "help_elderly", "description": "Helped elderly person cross street", "severity": "minor"},
    {"action_type": "donate_food", "description": "Donated food to homeless shelter", "severity": "medium"},
    {"action_type": "teach_dharma", "description": "Taught spiritual principles", "severity": "major"},
    {"action_type": "disrespect_teacher", "description": "Spoke harshly to teacher", "severity": "medium"},
    {"action_type": "cheat_exam", "description": "Cheated on examination", "severity": "major"},
    {"action_type": "meditate_daily", "description": "Completed 30-day meditation", "severity": "minor"},
    {"action_type": "break_promise", "description": "Broke important promise", "severity": "major"},
    {"action_type": "mentor_student", "description": "Mentored young student", "severity": "medium"},
    {"action_type": "ignore_need", "description": "Ignored someone in need", "severity": "minor"},
    {"action_type": "resolve_conflict", "description": "Resolved family conflict", "severity": "major"}
]

class KarmaStressTester:
    def __init__(self):
        self.results = {
            "start_time": datetime.now().isoformat(),
            "total_requests": 0,



            
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": [],
            "user_results": []
        }
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def create_user_session(self, session: aiohttp.ClientSession, user_id: str) -> Dict[str, Any]:
        """Create a user session and get initial karma profile"""
        try:
            async with self.semaphore:
                start_time = time.time()
                
                # First, create the user by logging an initial action
                create_url = f"{BASE_URL}/api/v1/log-action/"
                create_payload = {
                    "user_id": user_id,
                    "action": "practice_kindness",
                    "role": "learner",
                    "intensity": 1.0,
                    "context": "Initial user creation for stress test",
                    "metadata": {
                        "severity": "minor",
                        "timestamp": datetime.now().isoformat(),
                        "stress_test": True,
                        "initial_creation": True
                    }
                }
                
                async with session.post(create_url, json=create_payload) as create_response:
                    if create_response.status != 200:
                        error_text = await create_response.text()
                        raise Exception(f"Failed to create user: {error_text}")
                
                # Now get the karma profile
                profile_url = f"{BASE_URL}/api/v1/karma/{user_id}"
                async with session.get(profile_url) as response:
                    response_time = time.time() - start_time
                    self.results["response_times"].append(response_time)
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "user_id": user_id,
                            "status": "created",
                            "initial_profile": data,
                            "response_time": response_time
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get user profile: {error_text}")
        
        except Exception as e:
            self.results["errors"].append({
                "user_id": user_id,
                "action": "create_session",
                "error": str(e)
            })
            return {
                "user_id": user_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def perform_karma_action(self, session: aiohttp.ClientSession, user_id: str, action_data: Dict) -> Dict[str, Any]:
        """Perform a single karma action"""
        try:
            async with self.semaphore:
                start_time = time.time()
                
                # Log karma action
                url = f"{BASE_URL}/api/v1/log-action/"
                payload = {
                    "user_id": user_id,
                    "action": action_data["action_type"],
                    "role": random.choice(["learner", "teacher", "seeker", "guide"]),
                    "intensity": random.uniform(0.5, 2.0),
                    "context": action_data["description"],
                    "metadata": {
                        "severity": action_data["severity"],
                        "timestamp": datetime.now().isoformat(),
                        "stress_test": True
                    }
                }
                
                async with session.post(url, json=payload) as response:
                    response_time = time.time() - start_time
                    self.results["response_times"].append(response_time)
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "action": action_data["action_type"],
                            "status": "success",
                            "response_time": response_time,
                            "result": data
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Action failed: {error_text}")
        
        except Exception as e:
            self.results["errors"].append({
                "user_id": user_id,
                "action": action_data["action_type"],
                "error": str(e)
            })
            return {
                "action": action_data["action_type"],
                "status": "failed",
                "error": str(e)
            }
    
    async def get_user_stats(self, session: aiohttp.ClientSession, user_id: str) -> Dict[str, Any]:
        """Get final user statistics"""
        try:
            async with self.semaphore:
                start_time = time.time()
                
                url = f"{BASE_URL}/api/v1/karma/{user_id}"
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    self.results["response_times"].append(response_time)
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "response_time": response_time,
                            "final_stats": data
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get stats: {error_text}")
        
        except Exception as e:
            self.results["errors"].append({
                "user_id": user_id,
                "action": "get_stats",
                "error": str(e)
            })
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def simulate_user_journey(self, session: aiohttp.ClientSession, user_id: str) -> Dict[str, Any]:
        """Simulate a complete user journey with multiple actions"""
        user_result = {
            "user_id": user_id,
            "start_time": time.time(),
            "actions_performed": [],
            "errors": []
        }
        
        try:
            # Create user session
            session_result = await self.create_user_session(session, user_id)
            if session_result["status"] == "failed":
                raise Exception(session_result.get("error", "Session creation failed"))
            
            user_result["initial_profile"] = session_result.get("initial_profile")
            
            # Perform multiple karma actions
            for i in range(ACTIONS_PER_USER):
                action_data = random.choice(KARMA_ACTIONS)
                action_result = await self.perform_karma_action(session, user_id, action_data)
                user_result["actions_performed"].append(action_result)
                
                # Small delay between actions to simulate realistic usage
                await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Get final statistics
            stats_result = await self.get_user_stats(session, user_id)
            user_result["final_stats"] = stats_result
            
            user_result["end_time"] = time.time()
            user_result["total_time"] = user_result["end_time"] - user_result["start_time"]
            user_result["status"] = "completed"
            
        except Exception as e:
            user_result["status"] = "failed"
            user_result["error"] = str(e)
            user_result["errors"].append(str(e))
        
        return user_result
    
    async def run_stress_test(self) -> Dict[str, Any]:
        """Run the complete stress test"""
        logger.info(f"Starting stress test with {CONCURRENT_USERS} concurrent users")
        logger.info(f"Each user will perform {ACTIONS_PER_USER} actions")
        logger.info(f"Maximum concurrent requests: {MAX_CONCURRENT_REQUESTS}")
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Create tasks for all users
            tasks = []
            for i in range(CONCURRENT_USERS):
                user_id = f"stress_user_{i:03d}_{int(time.time())}"
                task = asyncio.create_task(self.simulate_user_journey(session, user_id))
                tasks.append(task)
            
            # Run all tasks concurrently
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in user_results:
                if isinstance(result, Exception):
                    self.results["errors"].append({
                        "type": "exception",
                        "error": str(result)
                    })
                    self.results["failed_requests"] += 1
                else:
                    self.results["user_results"].append(result)
                    if result["status"] == "completed":
                        self.results["successful_requests"] += 1
                    else:
                        self.results["failed_requests"] += 1
        
        end_time = time.time()
        self.results["total_test_time"] = end_time - start_time
        self.results["end_time"] = datetime.now().isoformat()
        
        # Calculate statistics
        self.calculate_statistics()
        
        return self.results
    
    def calculate_statistics(self):
        """Calculate test statistics"""
        if self.results["response_times"]:
            response_times = self.results["response_times"]
            self.results["statistics"] = {
                "total_users": CONCURRENT_USERS,
                "actions_per_user": ACTIONS_PER_USER,
                "total_actions_attempted": CONCURRENT_USERS * ACTIONS_PER_USER,
                "average_response_time": sum(response_times) / len(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
                "success_rate": (self.results["successful_requests"] / CONCURRENT_USERS) * 100,
                "requests_per_second": len(response_times) / self.results["total_test_time"]
            }
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        stats = self.results.get("statistics", {})
        
        report = f"""
{'='*80}
KARMACHAIN STRESS TEST REPORT
{'='*80}

Test Configuration:
- Concurrent Users: {CONCURRENT_USERS}
- Actions per User: {ACTIONS_PER_USER}
- Max Concurrent Requests: {MAX_CONCURRENT_REQUESTS}
- Total Test Time: {self.results.get('total_test_time', 0):.2f} seconds

Results Summary:
- Successful Users: {self.results['successful_requests']}/{CONCURRENT_USERS}
- Success Rate: {stats.get('success_rate', 0):.1f}%
- Total Requests: {len(self.results['response_times'])}
- Failed Requests: {self.results['failed_requests']}

Performance Metrics:
- Average Response Time: {stats.get('average_response_time', 0):.3f}s
- Min Response Time: {stats.get('min_response_time', 0):.3f}s
- Max Response Time: {stats.get('max_response_time', 0):.3f}s
- 95th Percentile: {stats.get('p95_response_time', 0):.3f}s
- Requests per Second: {stats.get('requests_per_second', 0):.1f}

Errors Encountered: {len(self.results['errors'])}
"""
        
        if self.results['errors']:
            report += "\nError Details:\n"
            for error in self.results['errors'][:5]:  # Show first 5 errors
                report += f"- {error}\n"
            if len(self.results['errors']) > 5:
                report += f"... and {len(self.results['errors']) - 5} more errors\n"
        
        report += "\n" + "="*80 + "\n"
        
        return report

async def main():
    """Main test execution"""
    print("🚀 Starting KarmaChain Stress Test")
    print(f"Testing with {CONCURRENT_USERS} concurrent users...")
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status != 200:
                    print("❌ Server health check failed. Make sure KarmaChain is running.")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to KarmaChain server at {BASE_URL}")
        print(f"Error: {e}")
        print("Please start the server first with: python main.py")
        return
    
    # Run stress test
    tester = KarmaStressTester()
    results = await tester.run_stress_test()
    
    # Generate and display report
    report = tester.generate_report()
    print(report)
    
    # Save detailed results
    with open("stress_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"📊 Detailed results saved to stress_test_results.json")
    
    # Performance recommendations
    if results.get("statistics", {}).get("success_rate", 0) < 95:
        print("⚠️  Warning: Success rate is below 95%. Consider optimizing the system.")
    
    if results.get("statistics", {}).get("p95_response_time", 0) > 2.0:
        print("⚠️  Warning: 95th percentile response time is above 2 seconds.")
        print("Consider implementing caching or database optimization.")

if __name__ == "__main__":
    asyncio.run(main())