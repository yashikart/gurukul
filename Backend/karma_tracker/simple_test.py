import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "karma-chain")

print(f"MONGO_URI: {MONGO_URI}")
print(f"DB_NAME: {DB_NAME}")

try:
    from pymongo import MongoClient
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Test connection
    client.admin.command('ping')
    print("✅ Database connection successful")
    
    # List collections
    collections = db.list_collection_names()
    print(f"📚 Available collections: {collections}")
    
    if "rnanubandhan_relationships" in collections:
        print("✅ Rnanubandhan collection exists")
    else:
        print("ℹ️ Rnanubandhan collection does not exist yet")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()