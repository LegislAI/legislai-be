#!/usr/bin/env/python3
import json
import logging
from typing import List
from typing import Optional

from database.bin.models import EmbeddingDocument
from database.bin.utils import EmbeddingModel
from database.models.PineconeDatabase import PineconeDatabase as Pinecone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/db_controller_log.log"),
        logging.StreamHandler(),
    ],
)
LOG = logging.getLogger("DB_CONTROLLER")


class DatabaseController:
    def __init__(self):
        self.embeddings = EmbeddingModel()
        self.pinecone_db = Pinecone()

    def insert_many_into_databases(self, payload: List[EmbeddingDocument]):
        LOG.info("Inserting many documents into databases")
        try:
            self.pinecone_db.insert_many_into_databases(payload)
        except Exception as e:
            LOG.error(f"Error inserting payload into database: {e}")

    def insert_into_databases(self, payload: EmbeddingDocument):
        try:
            self.pinecone_db.insert_into_database(payload)
        except Exception as e:
            LOG.error(f"Error inserting payload into database: {e}")

    def query(
        self, query: str, metadata_filter: Optional[dict] = {}, top_k: Optional[int] = 5
    ):
        try:
            pinecone_results = self.pinecone_db.query(query, metadata_filter, top_k)
            return pinecone_results
        except Exception as e:
            LOG.error(f"Error querying database: {e}, query: {query}")
            return
