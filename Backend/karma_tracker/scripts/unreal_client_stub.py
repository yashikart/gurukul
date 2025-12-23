#!/usr/bin/env python3
"""
Sample Unreal Engine Client Stub

This script simulates an Unreal Engine client connecting to the KarmaChain
WebSocket broadcast service to validate the integration.
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnrealClientStub:
    """Simulates an Unreal Engine client for testing WebSocket integration"""
    
    def __init__(self, client_id: str = "unreal_client_1"):
        self.client_id = client_id
        self.websocket = None
        self.connected = False
        
    async def connect(self, uri: str = "ws://localhost:8765/unreal_client"):
        """Connect to the KarmaChain broadcast server"""
        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True
            logger.info(f"Connected to {uri} as {self.client_id}")
            
            # Start listening for messages
            await self.listen_for_messages()
            
        except Exception as e:
            logger.error(f"Failed to connect to {uri}: {e}")
            self.connected = False
            
    async def listen_for_messages(self):
        """Listen for incoming messages from the server"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
            self.connected = False
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            self.connected = False
            
    async def handle_message(self, data: dict):
        """Handle incoming messages from the server"""
        message_type = data.get("type", "event")
        
        if message_type == "welcome":
            logger.info(f"Welcome message received: {data.get('message')}")
            # Send a subscription message if needed
            await self.send_subscription_request()
        else:
            logger.info(f"Received karmic event: {data}")
            # Process the karmic event (in a real Unreal client, this would update the UI)
            await self.process_karmic_event(data)
            
    async def send_subscription_request(self):
        """Send a subscription request to the server"""
        subscription_msg = {
            "type": "subscribe",
            "client_id": self.client_id,
            "subscriptions": ["life_event", "death_event", "rebirth", "feedback_signal", "analytics"]
        }
        await self.websocket.send(json.dumps(subscription_msg))
        logger.info("Sent subscription request")
        
    async def process_karmic_event(self, event_data: dict):
        """Process a karmic event (simulating Unreal Engine response)"""
        event_type = event_data.get("event_type", "unknown")
        user_id = event_data.get("user_id", "unknown")
        data = event_data.get("data", {})
        
        # Simulate processing based on event type
        if event_type == "life_event":
            action = data.get("action", "unknown")
            karma_impact = data.get("karma_impact", 0)
            logger.info(f"Player {user_id} performed {action}, karma impact: {karma_impact}")
            
        elif event_type == "death_event":
            loka = data.get("loka_assignment", "unknown")
            net_karma = data.get("net_karma", 0)
            logger.info(f"Player {user_id} died, assigned to {loka} loka with net karma: {net_karma}")
            
        elif event_type == "rebirth":
            new_id = data.get("new_user_id", "unknown")
            inherited_karma = data.get("inherited_karma", 0)
            logger.info(f"Player {user_id} reborn as {new_id} with inherited karma: {inherited_karma}")
            
        elif event_type == "feedback_signal":
            net_influence = data.get("net_influence", 0)
            logger.info(f"Feedback signal for {user_id}: net influence {net_influence}")
            
        elif event_type == "analytics":
            trend = data.get("karma_trend", "unknown")
            logger.info(f"Analytics for {user_id}: karma trend is {trend}")
            
        else:
            logger.info(f"Processing generic event for {user_id}: {event_data}")

async def main():
    """Main function to run the Unreal client stub"""
    logger.info("Starting Unreal Engine Client Stub")
    
    # Create and connect client
    client = UnrealClientStub("unreal_test_client")
    
    # Connect to server
    await client.connect()
    
    # Keep the client running for a while to receive messages
    logger.info("Client running, waiting for events...")
    
    # Run for 30 seconds to receive events
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    logger.info("Unreal Client Stub shutting down")

if __name__ == "__main__":
    asyncio.run(main())