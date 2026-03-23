# utils/mongo.py
import json
import os
import asyncio
from typing import Any, Optional

# MongoDB support (optional)
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

MONGO_URI = os.getenv("MONGO_URI", "")

class JSONDatabase:
    def __init__(self, filename="userbot.db.json"):
        self.filename = filename
        self._lock = asyncio.Lock()

    async def _load(self) -> dict:
        async with self._lock:
            if os.path.exists(self.filename):
                with open(self.filename, "r") as f:
                    return json.load(f)
            return {}

    async def _save(self, data: dict):
        async with self._lock:
            with open(self.filename, "w") as f:
                json.dump(data, f, indent=2)

    async def get(self, collection: str, key: str, default: Any = None) -> Any:
        data = await self._load()
        return data.get(collection, {}).get(key, default)

    async def set(self, collection: str, key: str, value: Any):
        data = await self._load()
        if collection not in data:
            data[collection] = {}
        data[collection][key] = value
        await self._save(data)

    async def delete(self, collection: str, key: str):
        data = await self._load()
        if collection in data and key in data[collection]:
            del data[collection][key]
            await self._save(data)

    async def keys(self, collection: str) -> list:
        data = await self._load()
        return list(data.get(collection, {}).keys())

class MongoDatabase:
    def __init__(self, uri: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client.get_default_database()
        self.collections = {}

    async def _get_collection(self, name: str):
        if name not in self.collections:
            self.collections[name] = self.db[name]
        return self.collections[name]

    async def get(self, collection: str, key: str, default: Any = None) -> Any:
        coll = await self._get_collection(collection)
        doc = await coll.find_one({"_id": key})
        return doc["value"] if doc else default

    async def set(self, collection: str, key: str, value: Any):
        coll = await self._get_collection(collection)
        await coll.update_one({"_id": key}, {"$set": {"value": value}}, upsert=True)

    async def delete(self, collection: str, key: str):
        coll = await self._get_collection(collection)
        await coll.delete_one({"_id": key})

    async def keys(self, collection: str) -> list:
        coll = await self._get_collection(collection)
        return [doc["_id"] async for doc in coll.find()]

# Choose backend
if MONGO_URI and MONGO_AVAILABLE:
    _db = MongoDatabase(MONGO_URI)
else:
    _db = JSONDatabase()

# Expose async interface
async def mget(collection: str, key: str, default: Any = None) -> Any:
    return await _db.get(collection, key, default)

async def mset(collection: str, key: str, value: Any):
    await _db.set(collection, key, value)

async def mdelete(collection: str, key: str):
    await _db.delete(collection, key)

async def mkeys(collection: str) -> list:
    return await _db.keys(collection)

# Convenience variable for your collection name
store_col = "stored_data"   # you can import this directly