#!/usr/bin/env python3
"""
Demo script for Audit Scheduler
Shows how to schedule daily audit exports
"""
import sys
import os
import asyncio
import tempfile
from datetime import time

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.audit_scheduler import (
    audit_scheduler,
    set_audit_export_time,
    enable_audit_scheduler,
    disable_audit_scheduler
)

async def demo_audit_scheduling():
    """Demonstrate audit scheduling functionality"""
    print("Audit Scheduler Demo")
    print("=" * 30)
    
    # Create temporary directory for exports
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory for exports: {temp_dir}")
    
    # Update scheduler configuration
    audit_scheduler.config["export_directory"] = temp_dir
    audit_scheduler.config["export_filename"] = "demo_telemetry_bridge.json"
    
    # Set export time to 5 seconds from now (for demo purposes)
    from datetime import datetime, timedelta
    now = datetime.now()
    export_time = (now + timedelta(seconds=5)).time()
    
    print(f"Setting export time to: {export_time}")
    set_audit_export_time(export_time)
    
    # Enable scheduler
    print("Enabling audit scheduler...")
    enable_audit_scheduler()
    
    # Start scheduler for a short time to demonstrate
    print("Starting scheduler (will run for 10 seconds)...")
    print("Press Ctrl+C to stop early")
    
    try:
        # Run scheduler for 10 seconds
        await asyncio.wait_for(audit_scheduler.start_scheduler(), timeout=10.0)
    except asyncio.TimeoutError:
        print("Scheduler demo completed (10 seconds elapsed)")
    except KeyboardInterrupt:
        print("Scheduler demo stopped by user")
    finally:
        # Stop scheduler
        audit_scheduler.stop_scheduler()
        print("Scheduler stopped")
    
    # Check if export file was created
    export_file = os.path.join(temp_dir, "demo_telemetry_bridge.json")
    if os.path.exists(export_file):
        print(f"✓ Export file created: {export_file}")
        # Show file size
        file_size = os.path.getsize(export_file)
        print(f"  File size: {file_size} bytes")
    else:
        print("ℹ No export file created (scheduler may not have triggered)")

def show_scheduler_configuration():
    """Show current scheduler configuration"""
    print("\nCurrent Scheduler Configuration:")
    print("-" * 30)
    print(f"Enabled: {audit_scheduler.enabled}")
    print(f"Export Time: {audit_scheduler.export_time}")
    print(f"Running: {audit_scheduler.running}")

if __name__ == "__main__":
    print("Audit Scheduler Demonstration")
    print("=" * 40)
    
    # Show initial configuration
    show_scheduler_configuration()
    
    # Run demo
    try:
        asyncio.run(demo_audit_scheduling())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    
    # Show final configuration
    show_scheduler_configuration()
    
    print("\nDemo completed!")