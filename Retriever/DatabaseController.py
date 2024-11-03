#!/usr/bin/env/python3
import json
import logging
from typing import List
from typing import Optional

from bin.Models import EmbeddingDocument
from bin.utils import EmbeddingModel
from DatabaseModels.FAISSDatabase import FAISSDatabase as FAISS
from DatabaseModels.PineconeDatabase import PineconeDatabase as Pinecone
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("db_controller_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("DB_CONTROLLER")


class DatabaseController:
    def __init__(self):
        load_dotenv()
        self.embeddings = EmbeddingModel()
        self.pinecone_db = Pinecone()
        # self.faiss_db = FAISS()

    def insert_many_into_databases(self, payload: List[EmbeddingDocument]):
        LOG.info("Inserting many documents into databases")
        try:
            self.pinecone_db.insert_many_into_databases(payload)
            # self.faiss_db.insert_many_into_databases(payload)
        except Exception as e:
            LOG.error(f"Error inserting payload into database: {e}")

    def insert_into_databases(self, payload: EmbeddingDocument):
        try:
            self.pinecone_db.insert_into_database(payload)
            # self.faiss_db.insert_into_database(payload)
        except Exception as e:
            LOG.error(f"Error inserting payload into database: {e}")

    def query(
        self, query: str, metadata_filter: Optional[dict] = {}, top_k: Optional[int] = 5
    ):
        try:
            pinecone_results = self.pinecone_db.query(query, metadata_filter, top_k)
            # faiss_results = self.faiss_db.query(query, metadata_filter, top_k)
            return pinecone_results
        except Exception as e:
            LOG.error(f"Error querying database: {e}, query: {query}")
            return
