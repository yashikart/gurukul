"""
Karma Lifecycle Engine - Implements the karmic lifecycle of Birth → Life → Death → Rebirth
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from database import users_col, death_events_col
from config import LOKA_THRESHOLDS, KARMA_FACTORS
from utils.event_bus import EventBus, Channel, publish_karma_lifecycle
from utils.karma_engine import calculate_net_karma

class KarmaLifecycleEngine:
    """Manages the karmic lifecycle of users in the KarmaChain system"""
    
    def __init__(self):
        self.event_bus = EventBus()
    
    def get_user_prarabdha(self, user_id: str) -> float:
        """
        Get the current Prarabdha karma counter for a user.
        
        Args:
            user_id (str): The user's ID
            
        Returns:
            float: The user's Prarabdha karma value
        """
        user = users_col.find_one({"user_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        balances = user.get("balances", {})
        return balances.get("PrarabdhaKarma", 0.0)
    
    def update_prarabdha(self, user_id: str, increment: float) -> float:
        """
        Update the Prarabdha karma counter for a user.
        
        Args:
            user_id (str): The user's ID
            increment (float): The amount to increment Prarabdha by
            
        Returns:
            float: The new Prarabdha karma value
        """
        user = users_col.find_one({"user_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        balances = user.get("balances", {})
        current_prarabdha = balances.get("PrarabdhaKarma", 0.0)
        new_prarabdha = current_prarabdha + increment
        
        # Update the user's Prarabdha karma
        users_col.update_one(
            {"user_id": user_id},
            {"$set": {"balances.PrarabdhaKarma": new_prarabdha}}
        )
        
        # Publish lifecycle event
        event_metadata = {
            "source": "karma_lifecycle_engine",
            "user_id": user_id,
            "event_type": "prarabdha_update"
        }
        event_payload = {
            "user_id": user_id,
            "previous_prarabdha": current_prarabdha,
            "increment": increment,
            "new_prarabdha": new_prarabdha,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        publish_karma_lifecycle(event_payload, event_metadata)
        
        return new_prarabdha
    
    def check_death_threshold(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a user has reached the death threshold based on their Prarabdha karma.
        
        Args:
            user_id (str): The user's ID
            
        Returns:
            Tuple[bool, Dict]: (threshold_reached, details)
        """
        user = users_col.find_one({"user_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        prarabdha = self.get_user_prarabdha(user_id)
        
        # Death threshold is when Prarabdha reaches a certain negative value
        # For this implementation, we'll use -100 as the threshold
        death_threshold = -100.0
        threshold_reached = prarabdha <= death_threshold
        
        details = {
            "user_id": user_id,
            "current_prarabdha": prarabdha,
            "death_threshold": death_threshold,
            "threshold_reached": threshold_reached
        }
        
        return threshold_reached, details
    
    def calculate_sanchita_inheritance(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate karma inheritance based on Sanchita rules.
        
        Args:
            user (Dict): The user document
            
        Returns:
            Dict: The inherited karma values
        """
        balances = user.get("balances", {})
        
        # Calculate net karma
        net_karma_result = calculate_net_karma(user)
        net_karma = net_karma_result["net_karma"]
        
        # Sanchita karma inheritance rules:
        # 1. Positive karma carries over at 20%
        # 2. Negative karma carries over at 50% (karmic debt is harder to escape)
        carryover_positive = 0.0
        carryover_negative = 0.0
        
        if net_karma > 0:
            carryover_positive = net_karma * 0.2
        elif net_karma < 0:
            carryover_negative = abs(net_karma) * 0.5
        
        # Calculate inherited Sanchita karma
        current_sanchita = balances.get("SanchitaKarma", 0.0)
        inherited_sanchita = current_sanchita + carryover_positive - carryover_negative
        
        return {
            "inherited_sanchita": max(0, inherited_sanchita),  # Cannot be negative
            "carryover_positive": carryover_positive,
            "carryover_negative": carryover_negative,
            "net_karma": net_karma
        }
    
    def generate_new_user_id(self) -> str:
        """
        Generate a new unique user ID for rebirth.
        
        Returns:
            str: A new unique user ID
        """
        return f"user_{uuid.uuid4().hex[:12]}"
    
    def trigger_death_event(self, user_id: str) -> Dict[str, Any]:
        """
        Trigger a death event for a user who has reached the threshold.
        
        Args:
            user_id (str): The user's ID
            
        Returns:
            Dict: Death event results
        """
        user = users_col.find_one({"user_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Calculate loka assignment based on net karma
        net_karma_result = calculate_net_karma(user)
        net_karma = net_karma_result["net_karma"]
        
        # Determine loka based on thresholds
        assigned_loka = "Mrityuloka"  # Default loka (middle realm)
        description = "The mortal realm, where souls continue their journey."
        
        for loka, threshold in LOKA_THRESHOLDS.items():
            if net_karma >= threshold["min_karma"] and net_karma <= threshold["max_karma"]:
                assigned_loka = loka
                description = threshold["description"]
                break
        
        # Calculate karma inheritance
        inheritance = self.calculate_sanchita_inheritance(user)
        
        # Store death event in database
        death_event_doc = {
            "user_id": user_id,
            "username": user.get("username", "Unknown"),
            "loka": assigned_loka,
            "description": description,
            "inheritance": inheritance,
            "final_balances": user.get("balances", {}),
            "net_karma": net_karma,
            "merit_score": user.get("merit_score", 0),
            "role": user.get("role", "Unknown"),
            "rebirth_count": user.get("rebirth_count", 0),
            "timestamp": datetime.now(timezone.utc),
            "status": "completed"
        }
        
        death_events_col.insert_one(death_event_doc)
        
        # Publish lifecycle event
        event_metadata = {
            "source": "karma_lifecycle_engine",
            "user_id": user_id,
            "event_type": "death_event"
        }
        event_payload = {
            "user_id": user_id,
            "loka": assigned_loka,
            "description": description,
            "inheritance": inheritance,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        publish_karma_lifecycle(event_payload, event_metadata)
        
        return {
            "status": "death_event_triggered",
            "user_id": user_id,
            "loka": assigned_loka,
            "description": description,
            "inheritance": inheritance
        }
    
    def rebirth_user(self, user_id: str) -> Dict[str, Any]:
        """
        Process a user's rebirth, creating a new identity with inherited karma.
        
        Args:
            user_id (str): The user's ID
            
        Returns:
            Dict: Rebirth results including new user ID
        """
        user = users_col.find_one({"user_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Calculate karma inheritance
        inheritance = self.calculate_sanchita_inheritance(user)
        
        # Generate new user ID
        new_user_id = self.generate_new_user_id()
        
        # Create new user with inherited karma
        new_balances = {
            "DharmaPoints": 0,
            "SevaPoints": 0,
            "PunyaTokens": 0,
            "PaapTokens": {
                "minor": 0,
                "medium": 0,
                "maha": 0
            },
            "SanchitaKarma": inheritance["inherited_sanchita"],
            "PrarabdhaKarma": 0.0,  # Reset for new life
            "DridhaKarma": 0.0,
            "AdridhaKarma": 0.0
        }
        
        # Determine starting level based on inherited karma
        starting_level = "learner"  # Default starting level
        if inheritance["inherited_sanchita"] > 100:
            starting_level = "volunteer"
        if inheritance["inherited_sanchita"] > 300:
            starting_level = "seva"
        
        # Create new user document
        new_user = {
            "user_id": new_user_id,
            "username": f"{user.get('username', 'Unknown')}_{user.get('rebirth_count', 0) + 1}",
            "balances": new_balances,
            "role": starting_level,
            "rebirth_count": user.get("rebirth_count", 0) + 1,
            "created_at": datetime.now(timezone.utc),
            "last_rebirth": {
                "timestamp": datetime.now(timezone.utc),
                "previous_user_id": user_id,
                "inheritance": inheritance
            }
        }
        
        # Insert new user into database
        users_col.insert_one(new_user)
        
        # Mark original user as deceased
        users_col.update_one(
            {"user_id": user_id},
            {"$set": {"status": "deceased", "deceased_at": datetime.now(timezone.utc)}}
        )
        
        # Publish lifecycle event
        event_metadata = {
            "source": "karma_lifecycle_engine",
            "user_id": user_id,
            "event_type": "rebirth"
        }
        event_payload = {
            "old_user_id": user_id,
            "new_user_id": new_user_id,
            "inheritance": inheritance,
            "starting_level": starting_level,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        publish_karma_lifecycle(event_payload, event_metadata)
        
        return {
            "status": "rebirth_completed",
            "old_user_id": user_id,
            "new_user_id": new_user_id,
            "inheritance": inheritance,
            "starting_level": starting_level
        }

# Global instance
lifecycle_engine = KarmaLifecycleEngine()

def get_prarabdha_counter(user_id: str) -> float:
    """Get the current Prarabdha karma counter for a user."""
    return lifecycle_engine.get_user_prarabdha(user_id)

def update_prarabdha_counter(user_id: str, increment: float) -> float:
    """Update the Prarabdha karma counter for a user."""
    return lifecycle_engine.update_prarabdha(user_id, increment)

def process_death_event(user_id: str) -> Dict[str, Any]:
    """Process a death event for a user."""
    return lifecycle_engine.trigger_death_event(user_id)

def process_rebirth(user_id: str) -> Dict[str, Any]:
    """Process a rebirth for a user."""
    return lifecycle_engine.rebirth_user(user_id)

def check_death_event_threshold(user_id: str) -> Tuple[bool, Dict[str, Any]]:
    """Check if a user has reached the death threshold."""
    return lifecycle_engine.check_death_threshold(user_id)

def simulate_lifecycle_cycles(cycles: int = 50, initial_users: int = 10) -> Dict[str, Any]:
    """
    Simulate karmic lifecycle cycles for testing purposes.
    
    Args:
        cycles (int): Number of cycles to simulate (default: 50)
        initial_users (int): Number of initial users to create (default: 10)
        
    Returns:
        Dict: Simulation results and statistics
    """
    import random
    import time
    from datetime import datetime
    
    # Create initial users for simulation
    initial_user_ids = []
    
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
    
    # Track simulation statistics
    total_births = len(initial_user_ids)
    total_deaths = 0
    total_rebirths = 0
    loka_distribution = {"Swarga": 0, "Mrityuloka": 0, "Antarloka": 0, "Naraka": 0}
    
    active_users = initial_user_ids.copy()
    results = []
    
    # Run simulation cycles
    for cycle in range(cycles):
        cycle_events = []
        
        # Process each user in this cycle
        users_to_remove = []
        users_to_add = []
        
        for user_id in active_users:
            try:
                # Simulate life events - update Prarabdha
                prarabdha_change = random.uniform(-20, 30)
                lifecycle_engine.update_prarabdha(user_id, prarabdha_change)
                cycle_events.append({
                    "type": "life_event",
                    "user_id": user_id,
                    "prarabdha_change": prarabdha_change
                })
                
                # Check for death threshold
                threshold_reached, details = lifecycle_engine.check_death_threshold(user_id)
                if threshold_reached:
                    # Process death event
                    death_result = lifecycle_engine.trigger_death_event(user_id)
                    total_deaths += 1
                    loka_distribution[death_result["loka"]] += 1
                    cycle_events.append({
                        "type": "death",
                        "user_id": user_id,
                        "loka": death_result["loka"]
                    })
                    
                    # Process rebirth
                    rebirth_result = lifecycle_engine.rebirth_user(user_id)
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
    
    return {
        "status": "simulation_completed",
        "cycles_simulated": cycles,
        "results": results,
        "statistics": statistics
    }
