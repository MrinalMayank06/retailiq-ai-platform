from __future__ import annotations

import json

from src.agents.support_agent.vector_store import rebuild_product_knowledge_store
from src.common.logger import get_logger

logger = get_logger(__name__)


def main():
    try:
        result = rebuild_product_knowledge_store()
        logger.info("Azure embedding local vector store rebuilt successfully")
        print(json.dumps(result, indent=4))
    except Exception as exc:
        logger.exception("Failed to rebuild Azure embedding local vector store: %s", exc)
        raise


if __name__ == "__main__":
    main()