#!/usr/bin/env python3
"""
KarmaChain Sample Log Generator
Generates sample logs to demonstrate accurate karma computation across multiple users.
"""

import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

# Sample users
USERS = [
    {"id": "alice_dev", "role": "developer", "description": "Software engineer focused on ethical coding practices"},
    {"id": "bob_student", "role": "student", "description": "University student learning computer science"},
    {"id": "charlie_mentor", "role": "mentor", "description": "Experienced developer mentoring newcomers"},
    {"id": "diana_researcher", "role": "researcher", "description": "Academic researcher in AI ethics"},
    {"id": "eve_entrepreneur", "role": "entrepreneur", "description": "Tech startup founder with focus on social impact"}
]

# Sample actions with karma values
ACTIONS = [
    # Positive actions
    {"action": "completing_lessons", "karma": 5, "token": "DharmaPoints", "description": "Completed online course module"},
    {"action": "helping_peers", "karma": 10, "token": "SevaPoints", "description": "Helped colleague debug code"},
    {"action": "solving_doubts", "karma": 8, "token": "SevaPoints", "description": "Answered questions on forum"},
    {"action": "selfless_service", "karma": 25, "token": "PunyaTokens", "description": "Volunteered for open source project"},
    {"action": "mentor_newcomers", "karma": 30, "token": "PunyaTokens", "description": "Mentored junior developers"},
    {"action": "ethical_coding", "karma": 15, "token": "DharmaPoints", "description": "Implemented privacy-by-design features"},
    {"action": "knowledge_sharing", "karma": 12, "token": "SevaPoints", "description": "Wrote technical blog post"},
    
    # Negative actions
    {"action": "cheat", "karma": -10, "token": "PaapTokens.minor", "description": "Copied code without attribution"},
    {"action": "break_promise", "karma": -5, "token": "PaapTokens.minor", "description": "Missed code review deadline"},
    {"action": "disrespect_guru", "karma": -15, "token": "PaapTokens.medium", "description": "Dismissed mentor's advice"},
    {"action": "false_speech", "karma": -8, "token": "PaapTokens.minor", "description": "Misrepresented project status"},
    {"action": "theft", "karma": -30, "token": "PaapTokens.medium", "description": "Used proprietary code without permission"},
    {"action": "harm_others", "karma": -25, "token": "PaapTokens.medium", "description": "Submitted code with security vulnerabilities"},
    {"action": "violence", "karma": -50, "token": "PaapTokens.maha", "description": "Cyberbullying in online communities"}
]

# Atonement activities
ATONEMENTS = [
    {"type": "Jap", "units": 108, "karma_boost": 5},
    {"type": "Tap", "units": 3, "karma_boost": 8},
    {"type": "Bhakti", "units": 7, "karma_boost": 6},
    {"type": "Daan", "units": 50, "karma_boost": 10}
]

def generate_sample_logs() -> List[Dict[str, Any]]:
    """Generate sample logs for multiple users over time"""
    logs = []
    start_time = datetime.now() - timedelta(days=30)
    
    # Generate logs for each user
    for user in USERS:
        user_logs = []
        current_time = start_time
        karma_balance = 0
        token_balances = {
            "DharmaPoints": 0,
            "SevaPoints": 0,
            "PunyaTokens": 0,
            "PaapTokens": {"minor": 0, "medium": 0, "maha": 0}
        }
        
        # Generate 10-20 actions per user
        num_actions = random.randint(10, 20)
        for i in range(num_actions):
            # Select a random action
            action = random.choice(ACTIONS)
            
            # Update time
            current_time += timedelta(hours=random.randint(1, 24))
            
            # Update balances
            if "." in action["token"]:
                # Nested token (e.g., PaapTokens.minor)
                token_parts = action["token"].split(".")
                main_token = token_parts[0]
                sub_token = token_parts[1]
                if main_token in token_balances:
                    if isinstance(token_balances[main_token], dict):
                        token_balances[main_token][sub_token] += abs(action["karma"]) if action["karma"] < 0 else action["karma"]
            else:
                # Simple token
                if action["token"] in token_balances:
                    token_balances[action["token"]] += action["karma"]
            
            # Update karma balance
            karma_balance += action["karma"]
            
            # Create log entry
            log_entry = {
                "timestamp": current_time.isoformat(),
                "user_id": user["id"],
                "user_role": user["role"],
                "user_description": user["description"],
                "event_type": "karma_action",
                "action": action["action"],
                "description": action["description"],
                "karma_impact": action["karma"],
                "token_type": action["token"],
                "current_karma_balance": karma_balance,
                "token_balances": token_balances.copy(),
                "sequence": i + 1
            }
            user_logs.append(log_entry)
            
            # Occasionally add atonement
            if random.random() < 0.3 and action["karma"] < 0:
                atonement = random.choice(ATONEMENTS)
                current_time += timedelta(hours=1)
                karma_balance += atonement["karma_boost"]
                
                # Update token balances for atonement
                # Simplified - in reality this would reduce PaapTokens
                token_balances["DharmaPoints"] += atonement["karma_boost"]
                
                atonement_log = {
                    "timestamp": current_time.isoformat(),
                    "user_id": user["id"],
                    "user_role": user["role"],
                    "user_description": user["description"],
                    "event_type": "atonement",
                    "atonement_type": atonement["type"],
                    "units": atonement["units"],
                    "karma_impact": atonement["karma_boost"],
                    "current_karma_balance": karma_balance,
                    "token_balances": token_balances.copy(),
                    "sequence": i + 1.5  # Between actions
                }
                user_logs.append(atonement_log)
        
        logs.extend(user_logs)
    
    # Sort logs by timestamp
    logs.sort(key=lambda x: x["timestamp"])
    return logs

def generate_summary_report(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary report from the logs"""
    user_stats = {}
    
    # Initialize stats for each user
    for user in USERS:
        user_stats[user["id"]] = {
            "user_id": user["id"],
            "role": user["role"],
            "description": user["description"],
            "total_actions": 0,
            "positive_actions": 0,
            "negative_actions": 0,
            "total_karma": 0,
            "atonements": 0,
            "final_balances": {}
        }
    
    # Process logs
    for log in logs:
        user_id = log["user_id"]
        stats = user_stats[user_id]
        
        if log["event_type"] == "karma_action":
            stats["total_actions"] += 1
            if log["karma_impact"] > 0:
                stats["positive_actions"] += 1
            else:
                stats["negative_actions"] += 1
            stats["total_karma"] += log["karma_impact"]
        elif log["event_type"] == "atonement":
            stats["atonements"] += 1
            stats["total_karma"] += log["karma_impact"]
        
        # Update final balances
        stats["final_balances"] = log["token_balances"]
    
    return {
        "report_generated": datetime.now().isoformat(),
        "total_events": len(logs),
        "time_period_days": 30,
        "user_statistics": user_stats,
        "leaderboard": sorted(
            [{"user_id": k, "total_karma": v["total_karma"]} for k, v in user_stats.items()],
            key=lambda x: x["total_karma"],
            reverse=True
        )
    }

def save_logs_and_report():
    """Generate and save logs and report"""
    print("Generating sample karma logs...")
    
    # Create logs directory if it doesn't exist
    logs_dir = "sample_logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate logs
    logs = generate_sample_logs()
    
    # Save detailed logs
    logs_file = os.path.join(logs_dir, "karma_chain_sample_logs.json")
    with open(logs_file, "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"Saved {len(logs)} log entries to {logs_file}")
    
    # Generate and save summary report
    report = generate_summary_report(logs)
    report_file = os.path.join(logs_dir, "karma_chain_summary_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Saved summary report to {report_file}")
    
    # Print summary to console
    print("\n" + "="*60)
    print("KARMA CHAIN SAMPLE LOGS SUMMARY")
    print("="*60)
    
    print(f"Total events logged: {report['total_events']}")
    print(f"Time period: {report['time_period_days']} days")
    print(f"Number of users: {len(report['user_statistics'])}")
    
    print("\nLEADERBOARD:")
    print("-" * 30)
    for i, entry in enumerate(report["leaderboard"], 1):
        print(f"{i}. {entry['user_id']}: {entry['total_karma']} karma")
    
    print("\nUSER STATISTICS:")
    print("-" * 30)
    for user_id, stats in report["user_statistics"].items():
        print(f"\n{user_id} ({stats['role']}):")
        print(f"  Total karma: {stats['total_karma']}")
        print(f"  Actions: {stats['total_actions']} ({stats['positive_actions']} positive, {stats['negative_actions']} negative)")
        print(f"  Atonements: {stats['atonements']}")
        print("  Final token balances:")
        for token, value in stats["final_balances"].items():
            if isinstance(value, dict):
                for sub_token, sub_value in value.items():
                    print(f"    {token}.{sub_token}: {sub_value}")
            else:
                print(f"    {token}: {value}")
    
    print("\n" + "="*60)
    print("Sample logs generation complete!")
    print("="*60)

if __name__ == "__main__":
    save_logs_and_report()