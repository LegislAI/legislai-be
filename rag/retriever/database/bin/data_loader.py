import hashlib
import json
import logging
import os
from argparse import ArgumentParser
from typing import List

from RAG.Retriever.database.bin.models import EmbeddingDocument
from RAG.Retriever.database.DatabaseController import DatabaseController as dbc

database_controller = dbc()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("db_controller_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger("RAG_INTERFACE")


def process_updates(updates: List[dict]) -> List[dict]:
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


def hash_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def load_data(data_path):
    LOG.info(f"Loading data from {data_path}")
    for path in os.listdir(data_path):
        temp_path = os.path.join(data_path, path)
        json_files_name = os.listdir(temp_path)
        for json_file_name in json_files_name:
            LOG.info(f"Loading {json_file_name}")
            with open(
                os.path.join(temp_path, json_file_name), "r", encoding="utf-8"
            ) as json_file:
                data = json.load(json_file)
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
                    doc_id = hash_id(section_key)

                    metadata = {
                        **base_metadata,
                        "title": title,
                        "epigrafe": section.get("epigrafe", "Unknown"),
                        "text": text,
                        "chapter": section.get("chapter", "Unknown"),
                        "book_number": section.get("book_number", ""),
                        "book_title": section.get("book_title", ""),
                        "updates": process_updates(section.get("updates", [])),
                        "previous_iterations": section.get("previous_iterations", []),
                    }

                    document = EmbeddingDocument(doc_id=doc_id, metadata=metadata)
                    LOG.info(f"Processed document ID: {doc_id}, Title: {title}")
                    database_controller.insert_into_databases(document)
                LOG.info(f"Processed all documents in file: {json_file_name}")


def main():
    parser = ArgumentParser()
    parser.add_argument("--data_path", type=str, default="data")
    args = parser.parse_args()

    load_data(args.data_path)


if __name__ == "__main__":
    main()
