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
        LOG.info(f"Received query: {query} with filters: {metadata_filter}")
        start = time.time()
        results = self.databasecontroller.query(
            query=query, top_k=topk, metadata_filter=metadata_filter
        )
        results = self.rerank_results(results, query)
        end = time.time()
        LOG.info(f"Results for query:{query} in {end-start} seconds")
        return results

    def rerank_results(self, results, query):
        pass


if __name__ == "__main__":
    retriever = Retriever()
