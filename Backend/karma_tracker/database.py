import os
import threading
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

_client_lock = threading.Lock()
_client: MongoClient = None
_db = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                max_pool = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
                min_pool = int(os.getenv("MONGO_MIN_POOL_SIZE", "0"))
                server_sel_timeout = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
                connect_timeout = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
                _client = MongoClient(
                    MONGO_URI,
                    maxPoolSize=max_pool,
                    minPoolSize=min_pool,
                    serverSelectionTimeoutMS=server_sel_timeout,
                    connectTimeoutMS=connect_timeout,
                )
    return _client

def get_db():
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db

# Define separate collections for each data type
users_col = get_db()["users"]
transactions_col = get_db()["transactions"]
qtable_col = get_db()["q_table"]
appeals_col = get_db()["appeals"]
atonements_col = get_db()["atonements"]
death_events_col = get_db()["death_events"]
karma_events_col = get_db()["karma_events"]  # New collection for unified events
rnanubandhan_col = get_db()["rnanubandhan_relationships"]  # Collection for Rnanubandhan relationships

def close_client():
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None