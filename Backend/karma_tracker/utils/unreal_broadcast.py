"""
Unreal Engine Broadcast Module

This module handles WebSocket communication with Unreal Engine clients,
broadcasting karmic events, feedback signals, and lifecycle events.
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KarmaEvent:
    """Represents a karmic event to be broadcast to Unreal Engine"""
    event_id: str
    user_id: str
    event_type: str  # life_event, death_event, rebirth, feedback_signal, etc.
    timestamp: str
    data: Dict[str, Any]
    priority: str = "normal"  # low, normal, high, critical

@dataclass
class ClientConnection:
    """Represents a connected Unreal Engine client"""
    websocket: websockets.WebSocketServerProtocol
    client_id: str
    connected_at: str
    subscriptions: List[str]  # Event types this client is interested in

class UnrealBroadcastManager:
    """Manages WebSocket connections and broadcasts to Unreal Engine clients"""
    
    def __init__(self):
        self.clients: Dict[str, ClientConnection] = {}
        self.event_queue: List[KarmaEvent] = []
        self.running = False
        
    async def register_client(self, websocket: websockets.WebSocketServerProtocol, client_id: str, subscriptions: List[str] = None):
        """Register a new Unreal Engine client"""
        if subscriptions is None:
            subscriptions = ["life_event", "death_event", "rebirth", "feedback_signal", "analytics"]
            
        connection = ClientConnection(
            websocket=websocket,
            client_id=client_id,
            connected_at=datetime.utcnow().isoformat(),
            subscriptions=subscriptions
        )
        
        self.clients[client_id] = connection
        logger.info(f"Client {client_id} registered with subscriptions: {subscriptions}")
        
        # Send welcome message
        welcome_msg = {
            "type": "welcome",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to KarmaChain Unreal Broadcast Service"
        }
        await websocket.send(json.dumps(welcome_msg))
        
    async def unregister_client(self, client_id: str):
        """Unregister a disconnected client"""
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"Client {client_id} unregistered")
            
    async def broadcast_event(self, event: KarmaEvent):
        """Broadcast a karmic event to all subscribed clients"""
        disconnected_clients = []
        
        for client_id, connection in self.clients.items():
            try:
                # Check if client is subscribed to this event type
                if event.event_type in connection.subscriptions:
                    # Send event to client
                    event_dict = asdict(event)
                    await connection.websocket.send(json.dumps(event_dict))
                    logger.debug(f"Sent {event.event_type} event to client {client_id}")
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Client {client_id} connection closed")
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error sending event to client {client_id}: {e}")
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.unregister_client(client_id)
            
    async def send_to_client(self, client_id: str, event: KarmaEvent):
        """Send an event to a specific client"""
        if client_id in self.clients:
            try:
                event_dict = asdict(event)
                await self.clients[client_id].websocket.send(json.dumps(event_dict))
                logger.debug(f"Sent event to client {client_id}")
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Client {client_id} connection closed")
                await self.unregister_client(client_id)
            except Exception as e:
                logger.error(f"Error sending event to client {client_id}: {e}")
                
    def queue_event(self, event: KarmaEvent):
        """Add an event to the broadcast queue"""
        self.event_queue.append(event)
        logger.debug(f"Event queued: {event.event_type}")
        
    async def process_queue(self):
        """Process the event queue and broadcast events"""
        while self.running and self.event_queue:
            event = self.event_queue.pop(0)
            await self.broadcast_event(event)
            
    async def start_server(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket server"""
        self.running = True
        
        async def handler(websocket, path):
            # Extract client ID from path or generate one
            client_id = path.strip("/") if path and path != "/" else f"client_{int(datetime.utcnow().timestamp())}"
            
            # Register client
            await self.register_client(websocket, client_id)
            
            try:
                # Listen for messages from client (if needed)
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        logger.info(f"Received message from {client_id}: {data}")
                        # Handle client messages if needed
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from {client_id}: {message}")
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Client {client_id} disconnected")
            finally:
                await self.unregister_client(client_id)
        
        server = await websockets.serve(handler, host, port)
        logger.info(f"Unreal Broadcast Server started on {host}:{port}")
        
        # Process event queue continuously
        while self.running:
            await self.process_queue()
            await asyncio.sleep(0.1)
            
        server.close()
        await server.wait_closed()
        
    def stop_server(self):
        """Stop the WebSocket server"""
        self.running = False
        logger.info("Unreal Broadcast Server stopped")
        
    async def simulate_karmic_events(self, num_players: int = 10):
        """Simulate karmic events for multiple players"""
        import uuid
        import random
        
        event_types = ["life_event", "death_event", "rebirth", "feedback_signal", "analytics"]
        actions = ["helping_peers", "completing_lessons", "selfless_service", "cheat", "meditation"]
        lokas = ["Swarga", "Mrityuloka", "Antarloka", "Naraka"]
        
        simulation_log = []
        
        for i in range(num_players):
            user_id = f"player_{i+1}"
            
            # Simulate 5-10 events per player
            num_events = random.randint(5, 10)
            for j in range(num_events):
                event_type = random.choice(event_types)
                event_id = str(uuid.uuid4())
                timestamp = datetime.utcnow().isoformat()
                
                # Generate event-specific data
                if event_type == "life_event":
                    data = {
                        "action": random.choice(actions),
                        "karma_impact": round(random.uniform(-10, 50), 2),
                        "role_progression": random.choice(["learner", "volunteer", "seva", "guru"])
                    }
                elif event_type == "death_event":
                    data = {
                        "loka_assignment": random.choice(lokas),
                        "net_karma": round(random.uniform(-200, 500), 2),
                        "rebirth_count": random.randint(0, 5)
                    }
                elif event_type == "rebirth":
                    data = {
                        "new_user_id": f"reborn_{user_id}_{j+1}",
                        "inherited_karma": round(random.uniform(0, 300), 2),
                        "starting_level": random.choice(["learner", "volunteer"])
                    }
                elif event_type == "feedback_signal":
                    data = {
                        "net_influence": round(random.uniform(-50, 100), 2),
                        "module_impacts": {
                            "finance": round(random.uniform(-10, 30), 2),
                            "game": round(random.uniform(-5, 20), 2),
                            "gurukul": round(random.uniform(-5, 25), 2),
                            "insight": round(random.uniform(-10, 35), 2)
                        }
                    }
                elif event_type == "analytics":
                    data = {
                        "karma_trend": random.choice(["increasing", "decreasing", "stable"]),
                        "paap_punya_ratio": round(random.uniform(0.1, 3.0), 2),
                        "engagement_score": random.randint(1, 100)
                    }
                else:
                    data = {"message": f"Generic event {j+1} for {user_id}"}
                
                # Create event
                event = KarmaEvent(
                    event_id=event_id,
                    user_id=user_id,
                    event_type=event_type,
                    timestamp=timestamp,
                    data=data,
                    priority=random.choice(["low", "normal", "high", "critical"])
                )
                
                # Queue for broadcast
                self.queue_event(event)
                
                # Log for simulation report
                simulation_log.append({
                    "event_id": event_id,
                    "user_id": user_id,
                    "event_type": event_type,
                    "timestamp": timestamp,
                    "data": data
                })
                
                # Small delay to simulate real-time events
                await asyncio.sleep(0.1)
        
        return simulation_log

# Global instance
broadcast_manager = UnrealBroadcastManager()

# Convenience functions
async def broadcast_karmic_event(event: KarmaEvent):
    """Broadcast a karmic event to all connected Unreal clients"""
    await broadcast_manager.broadcast_event(event)

async def send_event_to_client(client_id: str, event: KarmaEvent):
    """Send an event to a specific Unreal client"""
    await broadcast_manager.send_to_client(client_id, event)

def queue_karmic_event(event: KarmaEvent):
    """Queue a karmic event for broadcast"""
    broadcast_manager.queue_event(event)

async def start_unreal_broadcast_server(host: str = "localhost", port: int = 8765):
    """Start the Unreal Engine broadcast server"""
    await broadcast_manager.start_server(host, port)

def stop_unreal_broadcast_server():
    """Stop the Unreal Engine broadcast server"""
    broadcast_manager.stop_server()

async def run_player_simulation(num_players: int = 10):
    """Run a simulation with multiple players"""
    return await broadcast_manager.simulate_karmic_events(num_players)