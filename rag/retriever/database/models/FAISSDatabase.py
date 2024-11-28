#!/usr/bin/env python3
import logging
import os
import time
from typing import List

import faiss
import numpy as np
from bin.models import EmbeddingDocument
from dotenv import load_dotenv
from Retriever.database.bin.utils import EmbeddingModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("faiss_db_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("FAISS")

DATABASE_PATH = ".database/FAISS"
DATABASE_NAME = "legislai"


class FAISSDatabase:
    def __init__(self, force: bool = False):
        LOG.info("Initializing FAISS Instance")
        load_dotenv()

        self.embeddings = EmbeddingModel()
        self.db = self.init_database(database_name=DATABASE_NAME, force=force)

        LOG.info(f"Number of embeddings in database: {self.get_embedding_count()}")
        self.test_insert()

    def test_insert(self):
        LOG.info("Testing insert")
        test_encoding = np.array(
            self.embeddings.embed_query("test"), dtype="float32"
        ).reshape(1, -1)
        self.db.add(test_encoding)
        init_time = time.time()
        result = self.query("teste", top_k=1)
        LOG.info(f"Query time: {time.time() - init_time} seconds")
        for res, score in result:
            LOG.info(f"Test insert result: {res}, score: {score}")
        LOG.info(
            f"Number of embeddings after test insert: {self.get_embedding_count()}"
        )

    def init_database(self, database_name, force: bool = False) -> faiss.IndexHNSWFlat:
        LOG.info("Initializing database")
        index_path = f"{DATABASE_PATH}/{database_name}.index"
        if force or not os.path.exists(index_path):
            os.makedirs(DATABASE_PATH, exist_ok=True)
            index = faiss.IndexHNSWFlat(self.get_embedding_model_size(), 32)
            index.hnsw.efConstruction = 128
            index.hnsw.efSearch = 128
            LOG.info(
                f"Creating new database with efConstruction = {index.hnsw.efConstruction}"
            )
            faiss.write_index(index, index_path)
            return index
        else:
            LOG.info("Loading database from disk")
            index = faiss.read_index(index_path)
            return index

    def query(self, query: str, top_k: int = 5):
        query_vector = np.array(
            self.embeddings.embed_query(query), dtype="float32"
        ).reshape(1, -1)
        distances, indices = self.db.search(query_vector, top_k)
        return [(index, distance) for index, distance in zip(indices[0], distances[0])]

    def insert_many_into_database(self, payloads: List[EmbeddingDocument]):
        try:
            embeddings = [
                np.array(
                    self.embeddings.embed_query(payload.metadata["text"]),
                    dtype="float32",
                )
                for payload in payloads
            ]
            embeddings = np.vstack(embeddings)
            self.db.add(embeddings)
            LOG.info(f"Inserted {len(payloads)} documents into database")
            LOG.info(
                f"Number of embeddings after insertion: {self.get_embedding_count()}"
            )
            self.save_database()
        except Exception as e:
            LOG.error(f"Error inserting payload into database: {e}")

    def insert_into_database(self, payload: EmbeddingDocument):
        try:
            embedding = np.array(
                self.embeddings.embed_query(payload.metadata["text"]), dtype="float32"
            ).reshape(1, -1)
            self.db.add(embedding)
            LOG.info(f"Inserted document into database with ID: {payload.id}")
            LOG.info(
                f"Number of embeddings after single insert: {self.get_embedding_count()}"
            )
            self.save_database()
        except Exception as e:
            LOG.error(f"Error inserting payload into database: {e}")

    def save_database(self):
        index_path = f"{DATABASE_PATH}/{DATABASE_NAME}.index"
        faiss.write_index(self.db, index_path)
        LOG.info(f"Database saved to {index_path}")

    def get_embedding_count(self) -> int:
        return self.db.ntotal

    def get_embedding_model_size(self) -> int:
        return len(self.embeddings.embed_query("test"))


if __name__ == "__main__":
    FAISSDatabase(force=True)
