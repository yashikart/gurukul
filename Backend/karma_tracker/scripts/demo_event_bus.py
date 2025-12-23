#!/usr/bin/env python3
"""
Demo script for the Real-Time Event Bus
"""

import sys
import os
import time
import json

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from utils.event_bus import (
    EventBus, Channel, EventBusMessage,
    publish_karma_feedback, publish_karma_lifecycle, publish_karma_analytics,
    subscribe_to_karma_feedback, subscribe_to_karma_lifecycle, subscribe_to_karma_analytics
)

def feedback_handler(message: EventBusMessage):
    """Handle karma feedback events"""
    print(f"📬 Feedback Event Received:")
    print(f"   ID: {message.message_id}")
    print(f"   User: {message.payload.get('user_id', 'Unknown')}")
    print(f"   Type: {message.payload.get('type', 'Unknown')}")
    print(f"   Time: {message.timestamp}")
    print()

def lifecycle_handler(message: EventBusMessage):
    """Handle karma lifecycle events"""
    print(f"🔄 Lifecycle Event Received:")
    print(f"   ID: {message.message_id}")
    print(f"   Event: {message.payload.get('event_type', 'Unknown')}")
    print(f"   User: {message.payload.get('user_id', 'Unknown')}")
    print(f"   Time: {message.timestamp}")
    print()

def analytics_handler(message: EventBusMessage):
    """Handle karma analytics events"""
    print(f"📊 Analytics Event Received:")
    print(f"   ID: {message.message_id}")
    print(f"   Report: {message.payload.get('report_type', 'Unknown')}")
    print(f"   Time: {message.timestamp}")
    print()

def main():
    print("🚀 KarmaChain Real-Time Event Bus Demo")
    print("=" * 50)
    
    # Subscribe to all channels
    print("🔌 Subscribing to event channels...")
    subscribe_to_karma_feedback(feedback_handler)
    subscribe_to_karma_lifecycle(lifecycle_handler)
    subscribe_to_karma_analytics(analytics_handler)
    print("✅ Subscriptions established\n")
    
    # Demonstrate publishing events
    print("📨 Publishing sample events...\n")
    
    # Publish a feedback event
    print("1. Publishing karma feedback event...")
    feedback_payload = {
        "user_id": "user-123",
        "type": "karmic_influence",
        "data": {
            "user_id": "user-123",
            "overall_influence": {
                "reward_score": 85.5,
                "penalty_score": 12.3,
                "behavioral_bias": 5.2,
                "dynamic_influence": 78.4,
                "net_karma": 1500
            },
            "module_influence": {
                "academy": {
                    "event_count": 25,
                    "total_influence": 1200.5
                }
            }
        }
    }
    feedback_message = publish_karma_feedback(feedback_payload)
    print(f"   Published feedback event with ID: {feedback_message.message_id}\n")
    
    # Publish a lifecycle event
    print("2. Publishing karma lifecycle event...")
    lifecycle_payload = {
        "event_type": "role_change",
        "user_id": "user-456",
        "data": {
            "old_role": "student",
            "new_role": "mentor",
            "promotion_date": "2025-12-06"
        }
    }
    lifecycle_message = publish_karma_lifecycle(lifecycle_payload)
    print(f"   Published lifecycle event with ID: {lifecycle_message.message_id}\n")
    
    # Publish an analytics event
    print("3. Publishing karma analytics event...")
    analytics_payload = {
        "report_type": "daily_summary",
        "data": {
            "total_users": 1250,
            "active_users": 842,
            "events_processed": 3456,
            "avg_karma_score": 1250.5
        }
    }
    analytics_message = publish_karma_analytics(analytics_payload)
    print(f"   Published analytics event with ID: {analytics_message.message_id}\n")
    
    # Wait a bit to see the handlers process the events
    time.sleep(1)
    
    print("✅ Demo completed successfully!")
    print("\n💡 The event bus is now ready for real-time, multiplayer-ready communication!")

if __name__ == "__main__":
    main()