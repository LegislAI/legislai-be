import logging
import os
import time
from typing import List
from typing import Optional
from uuid import uuid4

from bin.Models import EmbeddingDocument
from bin.utils import EmbeddingModel
from dotenv import load_dotenv
from pinecone import Pinecone
from pinecone import ServerlessSpec

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("pinecone_db_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("PINECONE")


class PineconeDatabase:
    def __init__(self):
        load_dotenv()
        self.embeddings = EmbeddingModel()
        self.db = self.init_database(database_name="legislai")
        self.test_insert()

    def init_database(self, database_name) -> Pinecone:
        LOG.info("Initializing Pinecone database")
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        database = Pinecone(api_key=pinecone_api_key)
        self.create_database(database_name=database_name, database=database)
        return database.Index(database_name)

    def insert_many_into_databases(self, payload: List[EmbeddingDocument]):
        try:
            payload = [
                (
                    doc.id,
                    self.embeddings.embed_query(doc.metadata["text"]),
                    doc.metadata,
                )
                for doc in payload
            ]
            self.db.upsert(vectors=payload)
            LOG.info(f"Inserted {len(payload)} documents into database")
        except Exception as e:
            LOG.error(f"Error inserting documents into database: {e}")

    def insert_into_database(self, payload: EmbeddingDocument):
        try:
            embedded_text = self.embeddings.embed_query(payload.metadata["text"])
            self.db.upsert(vectors=[(payload.id, embedded_text, payload.metadata)])
            LOG.info("Inserted payload into database")
        except Exception as e:
            LOG.error(f"Error inserting payload: {payload} into database: {e}")

    def test_insert(self):
        LOG.info("Testing insert")
        test_encoding = self.embeddings.embed_query("test")
        test_id = str(uuid4())
        self.db.upsert(vectors=[(test_id, test_encoding, {"text": "teste"})])
        init_time = time.time()
        _ = self.query("teste", top_k=1)
        LOG.info(f"Query time: {time.time() - init_time} seconds")

    def query(self, query: str, metadata_filter: dict = {}, top_k: int = 5):
        try:
            embedding = self.embeddings.embed_query(query)
            results = self.db.query(
                vector=embedding,
                top_k=top_k,
                filter=metadata_filter,
                include_metadata=True,
                include_values=True,
            )
            return results
        except Exception as e:
            LOG.error(f"Error querying database: {e}, query: {query}")
            return

    def create_database(
        self,
        database_name: str,
        database: Pinecone,
        database_spec: Optional[dict] = None,
    ):
        if database_name not in database.list_indexes().names():
            try:
                LOG.info(f"Database does not exist, creating database {database_name}")
                embedding_vector_dimension = (
                    self.get_embedding_model_size()
                    if database_spec is None
                    else database_spec["dimension"]
                )
                metric = "cosine" if database_spec is None else database_spec["metric"]
                database.create_index(
                    name=database_name,
                    dimension=embedding_vector_dimension,
                    metric=metric,
                    spec=ServerlessSpec(cloud="aws", region="eu-west-1")
                    if database_spec is None
                    else database_spec["spec"],
                )
                LOG.info(
                    f"Created Database with name {database_name}\n"
                    f"Dimension: {embedding_vector_dimension}\n"
                    f"Metric: {metric}"
                )
            except Exception as e:
                LOG.error(f"Error creating database {database_name}: {e}")

    def get_embedding_model_size(self) -> int:
        return len(self.embeddings.embed_query("teste"))
