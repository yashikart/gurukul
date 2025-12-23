
























"""
Tests for the Real-Time Event Bus
"""

import unittest
import time
from utils.event_bus import EventBus, Channel, EventBusMessage

class TestEventBus(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.event_bus = EventBus()
        self.received_messages = []
    
    def test_publish_and_subscribe(self):
        """Test publishing and subscribing to channels"""
        # Define a callback function
        def test_callback(message: EventBusMessage):
            self.received_messages.append(message)
        
        # Subscribe to the feedback channel
        self.event_bus.subscribe(Channel.KARMA_FEEDBACK, test_callback)
        
        # Publish a message
        payload = {
            "user_id": "test-user-123",
            "type": "karmic_influence",
            "data": {"score": 95.5}
        }
        metadata = {
            "source": "test_suite"
        }
        
        message = self.event_bus.publish(Channel.KARMA_FEEDBACK, payload, metadata)
        
        # Verify the message was published
        self.assertIsInstance(message, EventBusMessage)
        self.assertEqual(message.channel, Channel.KARMA_FEEDBACK.value)
        self.assertEqual(message.payload, payload)
        self.assertEqual(message.metadata, metadata)
        
        # Verify the callback was called
        self.assertEqual(len(self.received_messages), 1)
        received_message = self.received_messages[0]
        self.assertEqual(received_message.message_id, message.message_id)
        self.assertEqual(received_message.payload, payload)
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to the same channel"""
        received_messages_1 = []
        received_messages_2 = []
        
        # Define callback functions
        def callback_1(message: EventBusMessage):
            received_messages_1.append(message)
            
        def callback_2(message: EventBusMessage):
            received_messages_2.append(message)
        
        # Subscribe both callbacks to the same channel
        self.event_bus.subscribe(Channel.KARMA_FEEDBACK, callback_1)
        self.event_bus.subscribe(Channel.KARMA_FEEDBACK, callback_2)
        
        # Publish a message
        payload = {"test": "data"}
        self.event_bus.publish(Channel.KARMA_FEEDBACK, payload)
        
        # Verify both callbacks were called
        self.assertEqual(len(received_messages_1), 1)
        self.assertEqual(len(received_messages_2), 1)
        self.assertEqual(received_messages_1[0].payload, payload)
        self.assertEqual(received_messages_2[0].payload, payload)
    
    def test_unsubscribe(self):
        """Test unsubscribing from a channel"""
        received_messages = []
        
        # Define a callback function
        def test_callback(message: EventBusMessage):
            received_messages.append(message)
        
        # Subscribe and then unsubscribe
        self.event_bus.subscribe(Channel.KARMA_FEEDBACK, test_callback)
        self.event_bus.unsubscribe(Channel.KARMA_FEEDBACK, test_callback)
        
        # Publish a message
        self.event_bus.publish(Channel.KARMA_FEEDBACK, {"test": "data"})
        
        # Verify the callback was not called
        self.assertEqual(len(received_messages), 0)
    
    def test_different_channels(self):
        """Test that messages are only sent to the correct channel"""
        feedback_messages = []
        lifecycle_messages = []
        
        # Define callback functions
        def feedback_callback(message: EventBusMessage):
            feedback_messages.append(message)
            
        def lifecycle_callback(message: EventBusMessage):
            lifecycle_messages.append(message)
        
        # Subscribe to different channels
        self.event_bus.subscribe(Channel.KARMA_FEEDBACK, feedback_callback)
        self.event_bus.subscribe(Channel.KARMA_LIFECYCLE, lifecycle_callback)
        
        # Publish to feedback channel
        self.event_bus.publish(Channel.KARMA_FEEDBACK, {"type": "feedback"})
        
        # Publish to lifecycle channel
        self.event_bus.publish(Channel.KARMA_LIFECYCLE, {"type": "lifecycle"})
        
        # Verify messages went to correct channels
        self.assertEqual(len(feedback_messages), 1)
        self.assertEqual(len(lifecycle_messages), 1)
        self.assertEqual(feedback_messages[0].payload["type"], "feedback")
        self.assertEqual(lifecycle_messages[0].payload["type"], "lifecycle")
    
    def test_get_recent_messages(self):
        """Test retrieving recent messages"""
        # Publish several messages
        for i in range(5):
            self.event_bus.publish(
                Channel.KARMA_FEEDBACK, 
                {"message_number": i}
            )
            time.sleep(0.01)  # Ensure different timestamps
        
        # Get recent messages
        recent_messages = self.event_bus.get_recent_messages(limit=3)
        
        # Verify we got the most recent messages
        self.assertEqual(len(recent_messages), 3)
        self.assertEqual(recent_messages[0].payload["message_number"], 2)
        self.assertEqual(recent_messages[1].payload["message_number"], 3)
        self.assertEqual(recent_messages[2].payload["message_number"], 4)
    
    def test_message_history_limit(self):
        """Test that message history is limited"""
        # Temporarily change the max history for this test
        original_max_history = self.event_bus.max_history
        self.event_bus.max_history = 10
        
        try:
            # Publish more messages than the history limit
            for i in range(15):
                self.event_bus.publish(
                    Channel.KARMA_FEEDBACK,
                    {"message_number": i}
                )
            
            # Check that we only have the most recent messages
            recent_messages = self.event_bus.get_recent_messages()
            self.assertEqual(len(recent_messages), 10)
            self.assertEqual(recent_messages[0].payload["message_number"], 5)
            self.assertEqual(recent_messages[-1].payload["message_number"], 14)
        finally:
            # Restore the original max history
            self.event_bus.max_history = original_max_history
    
    def test_convenience_functions(self):
        """Test convenience functions for publishing"""
        received_messages = []
        
        # Define a callback function
        def test_callback(message: EventBusMessage):
            received_messages.append(message)
        
        # Subscribe using convenience function
        from utils.event_bus import subscribe_to_karma_feedback
        subscribe_to_karma_feedback(test_callback)
        
        # Publish using convenience function
        from utils.event_bus import publish_karma_feedback
        payload = {"test": "convenience"}
        message = publish_karma_feedback(payload)
        
        # Verify the message was published and received
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0].payload, payload)
        self.assertEqual(received_messages[0].message_id, message.message_id)

if __name__ == '__main__':
    unittest.main()