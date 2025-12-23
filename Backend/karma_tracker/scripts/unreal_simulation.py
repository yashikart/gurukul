#!/usr/bin/env python3
"""
Unreal Engine Integration Simulation

This script runs a 10-player simulation to validate the Unreal Engine integration,
broadcasting feedback events, lifecycle events, and analytics events.
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.unreal_broadcast import (
    UnrealBroadcastManager, 
    KarmaEvent, 
    broadcast_karmic_event,
    run_player_simulation
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_unreal_simulation():
    """Run the 10-player Unreal Engine integration simulation"""
    logger.info("Starting Unreal Engine Integration Simulation")
    logger.info("==========================================")
    
    # Create broadcast manager
    broadcast_manager = UnrealBroadcastManager()
    
    # Start the server in the background
    server_task = asyncio.create_task(
        broadcast_manager.start_server("localhost", 8765)
    )
    
    # Wait a moment for server to start
    await asyncio.sleep(1)
    
    # Run the 10-player simulation
    logger.info("Running 10-player karmic event simulation...")
    simulation_log = await run_player_simulation(10)
    
    # Process events for 10 seconds to allow broadcasting
    logger.info("Broadcasting events to Unreal clients...")
    start_time = datetime.utcnow()
    
    # Process events for 10 seconds
    while (datetime.utcnow() - start_time).seconds < 10:
        await broadcast_manager.process_queue()
        await asyncio.sleep(0.5)
    
    # Stop the server
    broadcast_manager.stop_server()
    
    # Wait for server task to complete
    try:
        await asyncio.wait_for(server_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Server shutdown timed out")
    
    # Export simulation log
    log_data = {
        "simulation_run": datetime.utcnow().isoformat(),
        "num_players": 10,
        "events": simulation_log,
        "summary": {
            "total_events": len(simulation_log),
            "event_types": {},
            "players": {}
        }
    }
    
    # Generate summary statistics
    for event in simulation_log:
        # Count event types
        event_type = event["event_type"]
        if event_type in log_data["summary"]["event_types"]:
            log_data["summary"]["event_types"][event_type] += 1
        else:
            log_data["summary"]["event_types"][event_type] = 1
            
        # Count players
        user_id = event["user_id"]
        if user_id in log_data["summary"]["players"]:
            log_data["summary"]["players"][user_id] += 1
        else:
            log_data["summary"]["players"][user_id] = 1
    
    # Export to reports directory
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    log_file_path = os.path.join(reports_dir, "unreal_simulation_log.json")
    
    with open(log_file_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Simulation complete! Log exported to: {log_file_path}")
    
    # Print summary
    logger.info("\nSimulation Summary:")
    logger.info(f"  Total Events: {log_data['summary']['total_events']}")
    logger.info("  Event Types:")
    for event_type, count in log_data["summary"]["event_types"].items():
        logger.info(f"    {event_type}: {count}")
    logger.info("  Players:")
    for player, count in list(log_data["summary"]["players"].items())[:5]:  # Show first 5
        logger.info(f"    {player}: {count} events")
    if len(log_data["summary"]["players"]) > 5:
        logger.info(f"    ... and {len(log_data['summary']['players']) - 5} more players")
    
    return log_data

async def validate_unreal_integration():
    """Validate the Unreal Engine integration"""
    logger.info("Validating Unreal Engine Integration")
    logger.info("====================================")
    
    try:
        # Run the simulation
        log_data = await run_unreal_simulation()
        
        # Verify the log was created
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        log_file_path = os.path.join(reports_dir, "unreal_simulation_log.json")
        
        if os.path.exists(log_file_path):
            logger.info("✅ Simulation log successfully exported")
        else:
            logger.error("❌ Failed to export simulation log")
            return False
            
        # Verify log content
        if log_data["total_events"] > 0:
            logger.info("✅ Karmic events were generated and logged")
        else:
            logger.error("❌ No karmic events were generated")
            return False
            
        # Verify all event types are present
        expected_types = {"life_event", "death_event", "rebirth", "feedback_signal", "analytics"}
        actual_types = set(log_data["summary"]["event_types"].keys())
        
        if expected_types.issubset(actual_types):
            logger.info("✅ All expected event types were generated")
        else:
            missing_types = expected_types - actual_types
            logger.warning(f"⚠️  Some event types missing: {missing_types}")
            
        logger.info("✅ Unreal Engine integration validation complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during validation: {e}")
        return False

if __name__ == "__main__":
    # Run the validation
    success = asyncio.run(validate_unreal_integration())
    
    if success:
        logger.info("\n🎉 Unreal Engine Integration Validation SUCCESSFUL!")
        logger.info("   The KarmaChain system is ready for Unreal Engine integration.")
        sys.exit(0)
    else:
        logger.error("\n💥 Unreal Engine Integration Validation FAILED!")
        sys.exit(1)