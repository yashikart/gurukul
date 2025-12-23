#!/usr/bin/env python3
"""
Karma Lifecycle Simulation Script

This script runs a comprehensive 50-cycle simulation of the karmic lifecycle
(Birth → Life → Death → Rebirth) to demonstrate the Karma Lifecycle Engine.
"""

import sys
import os
import random
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.karma_lifecycle import KarmaLifecycleEngine
from database import users_col


def run_lifecycle_simulation(cycles=50, initial_users=10):
    """
    Run a comprehensive karmic lifecycle simulation.
    
    Args:
        cycles (int): Number of cycles to simulate (default: 50)
        initial_users (int): Number of initial users to create (default: 10)
        
    Returns:
        dict: Simulation results and statistics
    """
    print(f"Starting Karma Lifecycle Simulation ({cycles} cycles, {initial_users} initial users)")
    print("=" * 60)
    
    # Initialize lifecycle engine
    engine = KarmaLifecycleEngine()
    
    # Create initial users for simulation
    initial_user_ids = []
    print(f"\nCreating {initial_users} initial users...")
    
    for i in range(initial_users):
        user_id = f"sim_user_{int(time.time()*1000)}_{i}"
        initial_user = {
            "user_id": user_id,
            "username": f"SimUser{i}",
            "balances": {
                "DharmaPoints": random.randint(0, 100),
                "SevaPoints": random.randint(0, 100),
                "PunyaTokens": random.randint(0, 50),
                "PaapTokens": {
                    "minor": random.randint(0, 10),
                    "medium": random.randint(0, 5),
                    "maha": random.randint(0, 2)
                },
                "SanchitaKarma": random.uniform(0, 200),
                "PrarabdhaKarma": random.uniform(-50, 100),
                "DridhaKarma": random.uniform(0, 100),
                "AdridhaKarma": random.uniform(0, 50)
            },
            "role": random.choice(["learner", "volunteer", "seva", "guru"]),
            "rebirth_count": 0,
            "created_at": datetime.utcnow()
        }
        users_col.insert_one(initial_user)
        initial_user_ids.append(user_id)
        print(f"  Created user: {user_id} (Role: {initial_user['role']})")
    
    # Track simulation statistics
    total_births = len(initial_user_ids)
    total_deaths = 0
    total_rebirths = 0
    loka_distribution = {"Swarga": 0, "Mrityuloka": 0, "Antarloka": 0, "Naraka": 0}
    
    active_users = initial_user_ids.copy()
    results = []
    
    print(f"\nRunning {cycles} simulation cycles...")
    print("-" * 40)
    
    # Run simulation cycles
    for cycle in range(cycles):
        cycle_events = []
        print(f"Cycle {cycle + 1}/{cycles}")
        
        # Process each user in this cycle
        users_to_remove = []
        users_to_add = []
        
        for user_id in active_users:
            try:
                # Simulate life events - update Prarabdha
                prarabdha_change = random.uniform(-20, 30)
                engine.update_prarabdha(user_id, prarabdha_change)
                cycle_events.append({
                    "type": "life_event",
                    "user_id": user_id,
                    "prarabdha_change": prarabdha_change
                })
                
                # Check for death threshold
                threshold_reached, details = engine.check_death_threshold(user_id)
                if threshold_reached:
                    # Process death event
                    death_result = engine.trigger_death_event(user_id)
                    total_deaths += 1
                    loka_distribution[death_result["loka"]] += 1
                    cycle_events.append({
                        "type": "death",
                        "user_id": user_id,
                        "loka": death_result["loka"]
                    })
                    
                    # Process rebirth
                    rebirth_result = engine.rebirth_user(user_id)
                    total_rebirths += 1
                    cycle_events.append({
                        "type": "rebirth",
                        "old_user_id": user_id,
                        "new_user_id": rebirth_result["new_user_id"]
                    })
                    
                    # Mark user for replacement
                    users_to_remove.append(user_id)
                    users_to_add.append(rebirth_result["new_user_id"])
            
            except Exception as e:
                cycle_events.append({
                    "type": "error",
                    "user_id": user_id,
                    "error": str(e)
                })
        
        # Update active users list
        for user_id in users_to_remove:
            active_users.remove(user_id)
        active_users.extend(users_to_add)
        
        results.append({
            "cycle": cycle + 1,
            "events": cycle_events
        })
        
        # Print cycle summary
        deaths_in_cycle = len([e for e in cycle_events if e["type"] == "death"])
        rebirths_in_cycle = len([e for e in cycle_events if e["type"] == "rebirth"])
        if deaths_in_cycle > 0 or rebirths_in_cycle > 0:
            print(f"  Deaths: {deaths_in_cycle}, Rebirths: {rebirths_in_cycle}")
    
    # Compile final statistics
    statistics = {
        "total_cycles": cycles,
        "initial_users": initial_users,
        "total_births": total_births,
        "total_deaths": total_deaths,
        "total_rebirths": total_rebirths,
        "loka_distribution": loka_distribution,
        "final_active_users": len(active_users),
        "simulation_completed": datetime.utcnow().isoformat()
    }
    
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETED")
    print("=" * 60)
    print(f"Total Cycles: {statistics['total_cycles']}")
    print(f"Initial Users: {statistics['initial_users']}")
    print(f"Total Births: {statistics['total_births']}")
    print(f"Total Deaths: {statistics['total_deaths']}")
    print(f"Total Rebirths: {statistics['total_rebirths']}")
    print(f"Final Active Users: {statistics['final_active_users']}")
    print("\nLoka Distribution:")
    for loka, count in statistics['loka_distribution'].items():
        print(f"  {loka}: {count}")
    
    return {
        "status": "simulation_completed",
        "cycles_simulated": cycles,
        "results": results,
        "statistics": statistics
    }


if __name__ == "__main__":
    # Run the simulation with default parameters (50 cycles, 10 initial users)
    try:
        results = run_lifecycle_simulation(cycles=50, initial_users=10)
        
        # Optionally save results to a file
        import json
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"lifecycle_simulation_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {filename}")
        
    except Exception as e:
        print(f"Error running simulation: {str(e)}")
        sys.exit(1)