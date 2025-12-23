"""
Karma Lifecycle API Routes

This module provides API endpoints for the karmic lifecycle engine.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from utils.karma_lifecycle import (
    get_prarabdha_counter, 
    update_prarabdha_counter, 
    check_death_event_threshold, 
    process_death_event, 
    process_rebirth
)

router = APIRouter()

class PrarabdhaRequest(BaseModel):
    """Request model for Prarabdha counter operations"""
    user_id: str
    increment: float = 0.0

class PrarabdhaResponse(BaseModel):
    """Response model for Prarabdha counter operations"""
    user_id: str
    prarabdha: float
    timestamp: str

class DeathThresholdRequest(BaseModel):
    """Request model for death threshold check"""
    user_id: str

class DeathThresholdResponse(BaseModel):
    """Response model for death threshold check"""
    user_id: str
    current_prarabdha: float
    death_threshold: float
    threshold_reached: bool
    details: Dict[str, Any]

class DeathEventRequest(BaseModel):
    """Request model for death event processing"""
    user_id: str

class DeathEventResponse(BaseModel):
    """Response model for death event processing"""
    status: str
    user_id: str
    loka: str
    description: str
    inheritance: Dict[str, Any]
    timestamp: str

class RebirthRequest(BaseModel):
    """Request model for rebirth processing"""
    user_id: str

class RebirthResponse(BaseModel):
    """Response model for rebirth processing"""
    status: str
    old_user_id: str
    new_user_id: str
    inheritance: Dict[str, Any]
    starting_level: str
    timestamp: str

class SimulateCycleRequest(BaseModel):
    """Request model for lifecycle simulation"""
    cycles: int = 50
    initial_users: int = 10

class SimulateCycleResponse(BaseModel):
    """Response model for lifecycle simulation"""
    status: str
    cycles_simulated: int
    results: List[Dict[str, Any]]
    timestamp: str
    statistics: Optional[Dict[str, Any]] = None

@router.get("/prarabdha/{user_id}", response_model=PrarabdhaResponse)
async def get_prarabdha(user_id: str):
    """
    Get the current Prarabdha karma counter for a user.
    
    Args:
        user_id (str): The user's ID
        
    Returns:
        PrarabdhaResponse: Current Prarabdha value
    """
    try:
        prarabdha = get_prarabdha_counter(user_id)
        return PrarabdhaResponse(
            user_id=user_id,
            prarabdha=prarabdha,
            timestamp=datetime.utcnow().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Prarabdha: {str(e)}")

@router.post("/prarabdha/update", response_model=PrarabdhaResponse)
async def update_prarabdha(request: PrarabdhaRequest):
    """
    Update the Prarabdha karma counter for a user.
    
    Args:
        request (PrarabdhaRequest): Prarabdha update request
        
    Returns:
        PrarabdhaResponse: Updated Prarabdha value
    """
    try:
        new_prarabdha = update_prarabdha_counter(request.user_id, request.increment)
        return PrarabdhaResponse(
            user_id=request.user_id,
            prarabdha=new_prarabdha,
            timestamp=datetime.utcnow().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating Prarabdha: {str(e)}")

@router.post("/death/check", response_model=DeathThresholdResponse)
async def check_death_threshold(request: DeathThresholdRequest):
    """
    Check if a user has reached the death threshold.
    
    Args:
        request (DeathThresholdRequest): Death threshold check request
        
    Returns:
        DeathThresholdResponse: Death threshold check results
    """
    try:
        threshold_reached, details = check_death_event_threshold(request.user_id)
        return DeathThresholdResponse(
            user_id=request.user_id,
            current_prarabdha=details["current_prarabdha"],
            death_threshold=details["death_threshold"],
            threshold_reached=details["threshold_reached"],
            details=details,
            timestamp=datetime.utcnow().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking death threshold: {str(e)}")

@router.post("/death/process", response_model=DeathEventResponse)
async def process_death(request: DeathEventRequest):
    """
    Process a death event for a user who has reached the threshold.
    
    Args:
        request (DeathEventRequest): Death event processing request
        
    Returns:
        DeathEventResponse: Death event processing results
    """
    try:
        result = process_death_event(request.user_id)
        return DeathEventResponse(
            status=result["status"],
            user_id=result["user_id"],
            loka=result["loka"],
            description=result["description"],
            inheritance=result["inheritance"],
            timestamp=datetime.utcnow().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing death event: {str(e)}")

@router.post("/rebirth/process", response_model=RebirthResponse)
async def process_rebirth_endpoint(request: RebirthRequest):
    """
    Process a rebirth for a user.
    
    Args:
        request (RebirthRequest): Rebirth processing request
        
    Returns:
        RebirthResponse: Rebirth processing results
    """
    try:
        result = process_rebirth(request.user_id)
        return RebirthResponse(
            status=result["status"],
            old_user_id=result["old_user_id"],
            new_user_id=result["new_user_id"],
            inheritance=result["inheritance"],
            starting_level=result["starting_level"],
            timestamp=datetime.utcnow().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing rebirth: {str(e)}")

@router.post("/simulate", response_model=SimulateCycleResponse)
async def simulate_lifecycle_cycles(request: SimulateCycleRequest):
    """
    Simulate karmic lifecycle cycles for testing purposes.
    
    Args:
        request (SimulateCycleRequest): Simulation request
        
    Returns:
        SimulateCycleResponse: Simulation results
    """
    try:
        # Import required modules for simulation
        from utils.karma_lifecycle import KarmaLifecycleEngine
        from database import users_col
        import random
        import time
        
        # Initialize lifecycle engine
        engine = KarmaLifecycleEngine()
        
        # Create initial users for simulation
        initial_users = []
        results = []
        
        # Create initial users
        for i in range(request.initial_users):
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
            initial_users.append(user_id)
        
        # Track simulation statistics
        total_births = len(initial_users)
        total_deaths = 0
        total_rebirths = 0
        loka_distribution = {"Swarga": 0, "Mrityuloka": 0, "Antarloka": 0, "Naraka": 0}
        
        # Run simulation cycles
        for cycle in range(request.cycles):
            cycle_events = []
            
            # Process each user in this cycle
            for user_id in initial_users:
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
                        
                        # Update user list - replace old user with new one
                        if user_id in initial_users:
                            index = initial_users.index(user_id)
                            initial_users[index] = rebirth_result["new_user_id"]
                
                except Exception as e:
                    cycle_events.append({
                        "type": "error",
                        "user_id": user_id,
                        "error": str(e)
                    })
            
            results.append({
                "cycle": cycle + 1,
                "events": cycle_events
            })
        
        # Compile final statistics
        statistics = {
            "total_cycles": request.cycles,
            "initial_users": request.initial_users,
            "total_births": total_births,
            "total_deaths": total_deaths,
            "total_rebirths": total_rebirths,
            "loka_distribution": loka_distribution,
            "final_active_users": len(initial_users)
        }
        
        return SimulateCycleResponse(
            status="simulation_completed",
            cycles_simulated=request.cycles,
            results=results,
            timestamp=datetime.utcnow().isoformat(),
            statistics=statistics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating lifecycle: {str(e)}")
