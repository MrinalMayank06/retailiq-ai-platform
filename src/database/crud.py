from datetime import datetime
from typing import Any, Dict, List

from src.database.mongo_client import get_db
from src.common.logger import get_logger

logger = get_logger(__name__)


def insert_one(collection_name: str, document: Dict[str, Any]) -> None:
    db = get_db()
    if db is None:
        return
    payload = dict(document)
    payload["created_at"] = datetime.utcnow()
    db[collection_name].insert_one(payload)


def find_many(collection_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    db = get_db()
    if db is None:
        return []
    return list(db[collection_name].find({}, {"_id": 0}).sort("created_at", -1).limit(limit))


def replace_one(collection_name: str, filter_doc: Dict[str, Any], document: Dict[str, Any]) -> None:
    db = get_db()
    if db is None:
        return
    payload = dict(document)
    payload["updated_at"] = datetime.utcnow()
    db[collection_name].replace_one(filter_doc, payload, upsert=True)
