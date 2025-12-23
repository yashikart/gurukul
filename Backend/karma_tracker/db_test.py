#!/usr/bin/env python3
"""
Database connection test script
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import database modules
from database import get_db, get_client, rnanubandhan_col, users_col
from utils.rnanubandhan import RnanubandhanManager
from bson import ObjectId

def test_connection():
    print("Testing database connection...")
    try:
        # Test connection
        client = get_client()
        client.admin.command('ping')
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_collections():
    print("\nTesting collections...")
    try:
        # List collections
        db = get_db()
        collections = db.list_collection_names()
        print(f"📚 Available collections: {collections}")
        
        if "rnanubandhan_relationships" in collections:
            print("✅ Rnanubandhan collection exists")
        else:
            print("ℹ️ Rnanubandhan collection does not exist yet")
        
        return True
    except Exception as e:
        print(f"❌ Error checking collections: {e}")
        return False

def test_create_users():
    print("\nTesting user creation...")
    try:
        # Create test users if they don't exist
        user1 = users_col.find_one({"user_id": "test_user_1"})
        user2 = users_col.find_one({"user_id": "test_user_2"})
        
        if not user1:
            result = users_col.insert_one({
                "user_id": "test_user_1",
                "role": "learner",
                "balances": {
                    "DharmaPoints": 50,
                    "SevaPoints": 30,
                    "PunyaTokens": 20
                }
            })
            print(f"✅ Created test_user_1 with ID: {result.inserted_id}")
        else:
            print("✅ test_user_1 already exists")
        
        if not user2:
            result = users_col.insert_one({
                "user_id": "test_user_2",
                "role": "learner",
                "balances": {
                    "DharmaPoints": 40,
                    "SevaPoints": 25,
                    "PunyaTokens": 15
                }
            })
            print(f"✅ Created test_user_2 with ID: {result.inserted_id}")
        else:
            print("✅ test_user_2 already exists")
        
        return True
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        return False

def test_create_relationship():
    print("\nTesting Rnanubandhan relationship creation...")
    try:
        # Create Rnanubandhan relationship
        manager = RnanubandhanManager()
        relationship = manager.create_debt_relationship(
            debtor_id="test_user_1",
            receiver_id="test_user_2",
            action_type="help_action",
            severity="minor",
            amount=10.0,
            description="Helped with a task"
        )
        
        print("✅ Successfully created Rnanubandhan relationship")
        print(f"   Relationship ID: {relationship['_id']}")
        print(f"   Debtor: {relationship['debtor_id']}")
        print(f"   Receiver: {relationship['receiver_id']}")
        print(f"   Amount: {relationship['amount']}")
        
        # Clean up the relationship
        rnanubandhan_col.delete_one({"_id": ObjectId(relationship['_id'])})
        print("🧹 Cleaned up test relationship")
        
        return True
    except Exception as e:
        print(f"❌ Error creating Rnanubandhan relationship: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 Testing Rnanubandhan collection and database connection...")
    print("=" * 60)
    
    # Test database connection
    if not test_connection():
        return
    
    # Test collections
    if not test_collections():
        return
    
    # Test creating users
    if not test_create_users():
        return
    
    # Test creating relationship
    if not test_create_relationship():
        return
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed successfully!")

if __name__ == "__main__":
    main()