#!/usr/bin/env/python3
import hashlib
import logging
import time
from typing import Optional

from DatabaseController import DatabaseController as dbc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("db_controller_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("RAG_INTERFACE")


class Retriever:
    def __init__(self):
        self.databasecontroller = dbc()

    def query(
        self,
        query: Optional[str],
        topk: Optional[int],
        metadata_filter: Optional[dict] = {},
    ):
        start = time.time()
        results = self.databasecontroller.query(
            query=query, top_k=topk, metadata_filter=metadata_filter
        )
        end = time.time()
        LOG.info(f"Results for query:{query} in {end-start} seconds")
        return results


if __name__ == "__main__":
    Retriever()
