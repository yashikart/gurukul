#!/usr/bin/env python3
"""
Test script to check database connection and Rnanubandhan collection creation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from database import get_db, get_client, rnanubandhan_col, users_col
from utils.rnanubandhan import RnanubandhanManager

def test_database_connection():
    """Test database connection"""
    try:
        # Test connection
        client = get_client()
        client.admin.command('ping')
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_collection_exists():
    """Test if Rnanubandhan collection exists"""
    try:
        # List collections
        db = get_db()
        collections = db.list_collection_names()
        print(f"📚 Available collections: {collections}")
        
        if "rnanubandhan_relationships" in collections:
            print("✅ Rnanubandhan collection exists")
            return True
        else:
            print("⚠️ Rnanubandhan collection does not exist yet (will be created on first insert)")
            return True
    except Exception as e:
        print(f"❌ Error checking collections: {e}")
        return False

def test_create_sample_relationship():
    """Test creating a sample Rnanubandhan relationship"""
    try:
        # First create test users if they don't exist
        from database import users_col
        
        # Check if test users exist
        user1 = users_col.find_one({"user_id": "test_user_1"})
        user2 = users_col.find_one({"user_id": "test_user_2"})
        
        if not user1:
            users_col.insert_one({
                "user_id": "test_user_1",
                "role": "learner",
                "balances": {
                    "DharmaPoints": 50,
                    "SevaPoints": 30,
                    "PunyaTokens": 20
                }
            })
            print("👤 Created test_user_1")
        
        if not user2:
            users_col.insert_one({
                "user_id": "test_user_2",
                "role": "learner",
                "balances": {
                    "DharmaPoints": 40,
                    "SevaPoints": 25,
                    "PunyaTokens": 15
                }
            })
            print("👤 Created test_user_2")
        
        # Create Rnanubandhan manager
        manager = RnanubandhanManager()
        
        # Create a sample relationship
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
        
        # Clean up - delete the test relationship
        from bson import ObjectId
        rnanubandhan_col.delete_one({"_id": ObjectId(relationship['_id'])})
        print("🧹 Cleaned up test relationship")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating Rnanubandhan relationship: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Testing Rnanubandhan collection and database connection...")
    print("=" * 60)
    
    # Test database connection
    if not test_database_connection():
        return
    
    # Test collection existence
    if not test_collection_exists():
        return
    
    # Test creating a relationship
    if not test_create_sample_relationship():
        return
    
    print("=" * 60)
    print("🎉 All tests completed successfully!")

if __name__ == "__main__":
    main()