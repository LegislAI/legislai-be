import json
from datetime import datetime

from streaming import stream_answer
from utils.logging import logger


# HOW TO USE
if __name__ == "__main__":
    code_rag = "estrada"
    with open("prompt_specialists/testing/codigo_trabalho.json", "r") as file:
        context_json = json.load(file)
    context_rag = str(context_json)
    with open("prompt_specialists/testing/qa_trabalho.json", "r") as file:
        qa_json = json.load(file)

    user_question = qa_json["test"][0]["question"]

    init_time = datetime.now()
    stream_answer(context_rag, user_question, code_rag)

    final_time = datetime.now()
    logger.info(f"Time passed: {final_time - init_time}")
