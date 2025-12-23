# Real-Time Event Bus Implementation

## Overview

This document describes the implementation of a real-time event bus for KarmaChain to make it multiplayer-ready. The event bus enables asynchronous communication between different components of the system through three dedicated channels.

## Implementation Details

### Channels

The event bus implements three channels as specified:

1. **karma.feedback** - For karmic feedback and influence signals
2. **karma.lifecycle** - For user lifecycle events (birth, death, role changes, etc.)
3. **karma.analytics** - For analytics and reporting events

### Core Components

#### EventBus Class

The main `EventBus` class provides the following functionality:

- **Publish/Subscribe Pattern**: Components can subscribe to channels and receive notifications when messages are published
- **Thread Safety**: Uses locks to ensure thread-safe operations
- **Message History**: Maintains a limited history of messages for debugging
- **Error Handling**: Gracefully handles subscriber errors without affecting other subscribers

#### Message Structure

Messages follow a standardized structure:

```json
{
  "message_id": "string (UUID)",
  "channel": "string",
  "payload": "object",
  "timestamp": "ISO8601 datetime",
  "metadata": "object (optional)"
}
```

### Integration Points

#### Karma Feedback Engine

The karma feedback engine has been updated to publish messages to the `karma.feedback` channel whenever it computes and sends karmic influence signals. This enables real-time monitoring and processing of feedback events.

#### Future Integrations

The event bus is designed to be easily extensible for future integrations:
- Lifecycle engine (Day 3) can publish to `karma.lifecycle`
- Analytics components can publish to `karma.analytics`

### API

#### Publishing Messages

```python
from utils.event_bus import publish_karma_feedback

# Publish a feedback message
message = publish_karma_feedback({
    "user_id": "user-123",
    "type": "karmic_influence",
    "data": {"score": 95.5}
})
```

#### Subscribing to Channels

```python
from utils.event_bus import subscribe_to_karma_feedback

def my_handler(message):
    print(f"Received message: {message.payload}")

subscribe_to_karma_feedback(my_handler)
```

## Testing

The implementation includes comprehensive tests that verify:

- Publishing and subscribing functionality
- Multiple subscribers to the same channel
- Unsubscribing functionality
- Channel isolation
- Message history management
- Convenience functions

All tests pass successfully.

## Schema Definition

The message formats for each channel are documented in `schemas/event_bus.json`, providing clear specifications for:
- Required fields
- Data types
- Example structures

## Benefits

1. **Real-Time Communication**: Enables immediate notification of events across the system
2. **Decoupling**: Components can communicate without direct dependencies
3. **Scalability**: Easy to add new publishers and subscribers
4. **Multiplayer Ready**: Supports concurrent access from multiple users/systems
5. **Debugging**: Built-in message history for troubleshooting

## Future Enhancements

While the current implementation uses an in-memory approach suitable for single-instance deployments, it can be extended to support:

1. **Redis Streams**: For distributed deployments requiring persistence
2. **Apache Kafka**: For high-throughput, enterprise-grade event streaming
3. **WebSocket Integration**: For real-time browser notifications
4. **Message Filtering**: Advanced filtering capabilities for subscribers

The modular design makes it easy to swap the underlying transport mechanism while maintaining the same API.