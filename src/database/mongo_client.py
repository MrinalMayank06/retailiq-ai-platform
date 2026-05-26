from pymongo import MongoClient
from pymongo.errors import PyMongoError

from src.common.settings import get_settings
from src.common.logger import get_logger

logger = get_logger(__name__)

_client = None


def get_db():
    global _client
    settings = get_settings()
    if _client is None:
        try:
            _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
            _client.admin.command("ping")
            logger.info("Connected to MongoDB")
        except PyMongoError as exc:
            logger.warning("MongoDB connection unavailable: %s", exc)
            return None
    return _client[settings.mongodb_db]
