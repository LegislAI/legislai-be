#!/usr/bin/env/python3
import hashlib
import json
import logging
import os
import time
from typing import List
from typing import Optional

from bin.Models import EmbeddingDocument
from DatabaseController import DatabaseController as dbc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("db_controller_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("RAG_INTERFACE")


class RAG:
    def __init__(self):
        self.databasecontroller = dbc()
        # self.load_data()
        # self.query()

    def query(self):
        query = input("Query: ")
        topk = int(input("Topk: "))
        while query != "exit":
            start = time.time()
            results = self.databasecontroller.query(query, topk)
            end = time.time()
            LOG.info(f"Results: {results} in {end-start} seconds")
            query = input("Query: ")
            topk = int(input("Topk: "))

    def hash_id(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def process_updates(self, updates: List[dict]) -> List[dict]:
        processed_updates = []
        for update in updates:
            processed_updates.append(
                json.dumps(
                    {
                        "article": update.get("text", "Unknown"),
                        "active_from": update.get("active_from", "Unknown"),
                        "url": update.get("url", "Unknown"),
                    },
                    ensure_ascii=False,
                )
            )
        return processed_updates

    def load_data(self, data_path: str = "data/", force: Optional[bool] = True):
        documents = []
        for doc_type in os.listdir(data_path):
            type_path = os.path.join(data_path, doc_type)
            for file in os.listdir(type_path):
                file_path = os.path.join(type_path, file)
                with open(file_path) as f:
                    data = json.load(f)
                    base_metadata = {
                        "document_name": data.get("document_name", "Unknown"),
                        "law_name": data.get("law_name", "Unknown"),
                        "dr_document": data.get("dr_document", "Unknown"),
                        "link": data.get("link", "Unknown"),
                        "date_of_fetch": data.get("date_of_fetch", "Unknown"),
                        "theme": data.get("theme", "Unknown"),
                    }

                    sections = data.get("sections", {})
                    for section_key, section in sections.items():
                        title = section.get("title", "Unknown")
                        text = section.get("text", "")
                        doc_id = self.hash_id(section_key)

                        metadata = {
                            **base_metadata,
                            "title": title,
                            "epigrafe": section.get("epigrafe", "Unknown"),
                            "text": text,
                            "chapter": section.get("chapter", "Unknown"),
                            "book_number": section.get("book_number", ""),
                            "book_title": section.get("book_title", ""),
                            "updates": self.process_updates(section.get("updates", [])),
                            "previous_iterations": section.get(
                                "previous_iterations", []
                            ),
                        }

                        document = EmbeddingDocument(doc_id=doc_id, metadata=metadata)
                        documents.append(document)
                        LOG.info(f"Processed document ID: {doc_id}, Title: {title}")
                        self.databasecontroller.insert_into_databases(document)
        # self.databasecontroller.insert_many_into_databases(documents)
        LOG.info("Processed all documents")

        return documents


if __name__ == "__main__":
    rag = RAG()
