# utils/db.py
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
    def __init__(self):
        self.db_file = "userbot.db.json"
        self._lock = asyncio.Lock()

    async def _load(self) -> dict:
        async with self._lock:
            if os.path.exists(self.db_file):
                with open(self.db_file, "r") as f:
                    return json.load(f)
            return {}

    async def _save(self, data: dict):
        async with self._lock:
            with open(self.db_file, "w") as f:
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

    async def get_collection(self, collection: str) -> dict:
        data = await self._load()
        return data.get(collection, {})

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

    async def get_collection(self, collection: str) -> dict:
        coll = await self._get_collection(collection)
        result = {}
        async for doc in coll.find():
            result[doc["_id"]] = doc["value"]
        return result

# Decide which backend to use
if MONGO_URI and MONGO_AVAILABLE:
    _db = MongoDatabase(MONGO_URI)
else:
    _db = JSONDatabase()

# Expose the same async interface
async def get(collection: str, key: str, default: Any = None) -> Any:
    return await _db.get(collection, key, default)

async def set(collection: str, key: str, value: Any):
    await _db.set(collection, key, value)

async def delete(collection: str, key: str):
    await _db.delete(collection, key)

async def get_collection(collection: str) -> dict:
    return await _db.get_collection(collection)