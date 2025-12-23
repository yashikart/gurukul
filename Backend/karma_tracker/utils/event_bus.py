"""
Real-Time Event Bus for KarmaChain

Implements a lightweight event bus system with channels for real-time,
multiplayer-ready communication using an in-memory approach.
"""

import json
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading

# Setup logging
logger = logging.getLogger(__name__)

class Channel(Enum):
    """Available event channels"""
    KARMA_FEEDBACK = "karma.feedback"
    KARMA_LIFECYCLE = "karma.lifecycle"
    KARMA_ANALYTICS = "karma.analytics"

@dataclass
class EventBusMessage:
    """Structure for event bus messages"""
    message_id: str
    channel: str
    payload: Dict[str, Any]
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class EventBus:
    """Real-time event bus implementation"""
    
    def __init__(self):
        """Initialize the event bus"""
        self.subscribers: Dict[str, List[Callable]] = {
            Channel.KARMA_FEEDBACK.value: [],
            Channel.KARMA_LIFECYCLE.value: [],
            Channel.KARMA_ANALYTICS.value: []
        }
        self.lock = threading.RLock()
        self.message_history: List[EventBusMessage] = []
        self.max_history = 1000  # Keep last 1000 messages for debugging
        
    def subscribe(self, channel: Channel, callback: Callable[[EventBusMessage], None]):
        """
        Subscribe to a channel
        
        Args:
            channel: Channel to subscribe to
            callback: Function to call when message is published
        """
        with self.lock:
            if callback not in self.subscribers[channel.value]:
                self.subscribers[channel.value].append(callback)
                logger.info(f"Subscribed to channel {channel.value}")
    
    def unsubscribe(self, channel: Channel, callback: Callable[[EventBusMessage], None]):
        """
        Unsubscribe from a channel
        
        Args:
            channel: Channel to unsubscribe from
            callback: Function to remove from subscribers
        """
        with self.lock:
            if callback in self.subscribers[channel.value]:
                self.subscribers[channel.value].remove(callback)
                logger.info(f"Unsubscribed from channel {channel.value}")
    
    def publish(self, channel: Channel, payload: Dict[str, Any], 
                metadata: Optional[Dict[str, Any]] = None) -> EventBusMessage:
        """
        Publish a message to a channel
        
        Args:
            channel: Channel to publish to
            payload: Message payload
            metadata: Optional metadata
            
        Returns:
            EventBusMessage: Published message
        """
        message = EventBusMessage(
            message_id=str(uuid.uuid4()),
            channel=channel.value,
            payload=payload,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata
        )
        
        # Store in history
        with self.lock:
            self.message_history.append(message)
            # Keep only the last max_history messages
            if len(self.message_history) > self.max_history:
                self.message_history = self.message_history[-self.max_history:]
        
        # Notify subscribers
        subscribers = self.subscribers.get(channel.value, [])
        for callback in subscribers:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in subscriber callback for channel {channel.value}: {str(e)}")
        
        logger.info(f"Published message to {channel.value} with ID {message.message_id}")
        return message
    
    def get_recent_messages(self, channel: Optional[Channel] = None, 
                           limit: int = 10) -> List[EventBusMessage]:
        """
        Get recent messages from the event bus
        
        Args:
            channel: Optional channel to filter by
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        with self.lock:
            if channel:
                filtered_messages = [
                    msg for msg in self.message_history 
                    if msg.channel == channel.value
                ]
            else:
                filtered_messages = self.message_history
            
            return filtered_messages[-limit:] if filtered_messages else []

# Global event bus instance
event_bus = EventBus()

# Convenience functions
def publish_karma_feedback(payload: Dict[str, Any], 
                          metadata: Optional[Dict[str, Any]] = None) -> EventBusMessage:
    """Publish a message to the karma feedback channel"""
    return event_bus.publish(Channel.KARMA_FEEDBACK, payload, metadata)

def publish_karma_lifecycle(payload: Dict[str, Any], 
                           metadata: Optional[Dict[str, Any]] = None) -> EventBusMessage:
    """Publish a message to the karma lifecycle channel"""
    return event_bus.publish(Channel.KARMA_LIFECYCLE, payload, metadata)

def publish_karma_analytics(payload: Dict[str, Any], 
                           metadata: Optional[Dict[str, Any]] = None) -> EventBusMessage:
    """Publish a message to the karma analytics channel"""
    return event_bus.publish(Channel.KARMA_ANALYTICS, payload, metadata)

def subscribe_to_karma_feedback(callback: Callable[[EventBusMessage], None]):
    """Subscribe to the karma feedback channel"""
    event_bus.subscribe(Channel.KARMA_FEEDBACK, callback)

def subscribe_to_karma_lifecycle(callback: Callable[[EventBusMessage], None]):
    """Subscribe to the karma lifecycle channel"""
    event_bus.subscribe(Channel.KARMA_LIFECYCLE, callback)

def subscribe_to_karma_analytics(callback: Callable[[EventBusMessage], None]):
    """Subscribe to the karma analytics channel"""
    event_bus.subscribe(Channel.KARMA_ANALYTICS, callback)