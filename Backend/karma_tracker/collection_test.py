import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

try:
    # Import database modules
    from database import db, rnanubandhan_col, users_col
    
    print("Testing Rnanubandhan collection creation...")
    
    # Test connection
    client = db.client
    client.admin.command('ping')
    print("✅ Database connection successful")
    
    # List collections before
    collections_before = db.list_collection_names()
    print(f"📚 Collections before: {collections_before}")
    
    # Try to insert a document to force collection creation
    test_doc = {
        "test_field": "test_value",
        "created_at": "2023-01-01"
    }
    
    result = rnanubandhan_col.insert_one(test_doc)
    print(f"✅ Inserted test document with ID: {result.inserted_id}")
    
    # List collections after
    collections_after = db.list_collection_names()
    print(f"📚 Collections after: {collections_after}")
    
    # Check if Rnanubandhan collection exists now
    if "rnanubandhan_relationships" in collections_after:
        print("✅ Rnanubandhan collection exists")
    else:
        print("❌ Rnanubandhan collection still doesn't exist")
    
    # Clean up
    rnanubandhan_col.delete_one({"_id": result.inserted_id})
    print("🧹 Cleaned up test document")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()