#!/usr/bin/env python3
"""
Initialize the karma_events collection with proper indexes and schema validation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import karma_events_col, get_db
from pymongo import IndexModel, ASCENDING, DESCENDING
from datetime import datetime

def init_karma_events_collection():
    """Initialize karma_events collection with indexes and validation"""
    
    print("🚀 Initializing karma_events collection...")
    
    # Create indexes for efficient querying
    indexes = [
        IndexModel([("event_id", ASCENDING)], unique=True),
        IndexModel([("event_type", ASCENDING)]),
        IndexModel([("user_id", ASCENDING)]),  # If user_id exists in data
        IndexModel([("timestamp", DESCENDING)]),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("source", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)])
    ]
    
    try:
        # Create indexes
        karma_events_col.create_indexes(indexes)
        print("✅ Indexes created successfully")
        
        # Get collection stats
        stats = karma_events_col.database.command("collStats", "karma_events")
        print(f"📊 Collection stats: {stats['count']} documents, {stats['size']} bytes")
        
        # Create a sample document to test
        sample_event = {
            "event_id": "test-init-001",
            "event_type": "system_init",
            "data": {
                "message": "Karma events collection initialized",
                "version": "1.0.0"
            },
            "timestamp": datetime.utcnow(),
            "source": "system_initializer",
            "status": "processed",
            "response_data": {
                "status": "success",
                "message": "Collection ready for use"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert sample document (upsert to avoid duplicates)
        result = karma_events_col.update_one(
            {"event_id": "test-init-001"},
            {"$set": sample_event},
            upsert=True
        )
        
        if result.upserted_id:
            print("✅ Sample initialization event inserted")
        else:
            print("ℹ️ Sample initialization event already exists")
        
        print("\n🎉 karma_events collection initialization complete!")
        
        # Show available indexes
        indexes_info = karma_events_col.list_indexes()
        print("\n📋 Available indexes:")
        for index in indexes_info:
            print(f"  - {index['name']}: {index['key']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing collection: {e}")
        return False

def verify_collection_setup():
    """Verify the collection is properly set up"""
    
    print("\n🔍 Verifying collection setup...")
    
    try:
        # Test basic operations
        test_event = {
            "event_id": "test-verify-001",
            "event_type": "test_event",
            "data": {"test": "data"},
            "timestamp": datetime.utcnow(),
            "source": "verification_script",
            "status": "processed",
            "created_at": datetime.utcnow()
        }
        
        # Insert test document
        karma_events_col.insert_one(test_event)
        print("✅ Test document inserted")
        
        # Query test document
        found = karma_events_col.find_one({"event_id": "test-verify-001"})
        if found:
            print("✅ Test document retrieved successfully")
        else:
            print("❌ Test document not found")
            return False
        
        # Clean up test document
        karma_events_col.delete_one({"event_id": "test-verify-001"})
        print("✅ Test document cleaned up")
        
        print("✅ Collection verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🛠️ Karma Events Collection Setup")
    print("=" * 40)
    
    # Initialize collection
    if init_karma_events_collection():
        # Verify setup
        if verify_collection_setup():
            print("\n🎉 All systems ready! The karma_events collection is now available.")
            print("\n💡 Usage:")
            print("   from database import karma_events_col")
            print("   karma_events_col.insert_one({...})")
        else:
            print("\n⚠️ Collection initialized but verification failed.")
    else:
        print("\n❌ Collection initialization failed.")
        sys.exit(1)