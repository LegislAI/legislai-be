import asyncio
import json
import traceback

from generator import RAGPrompt
from specialists import SpecialistPrompts
from utils.config import Config
from utils.logging import logger


# def simulate_streaming(text, delay=0.1):
#     """Simulate streaming by yielding words with a delay"""
#     import time

#     words = text.split()
#     for word in words:
#         yield word
#         time.sleep(delay)


class StreamingRAG:
    def __init__(self, rag_class):
        self.rag_class = rag_class

    async def stream_answer(self, context_rag, user_question, code_rag):
        config = Config()
        lm = config.setup_models()

        specialist = SpecialistPrompts()

        if code_rag is None:
            hint = "És um especialista na Legislação Portuguesa e dominas os assuntos legais portugueses. Deves responder em vocabulário simples e sempre em português de Portugal"
        else:
            legal_code = specialist.get_legal_code(code_rag)  # legalcode.
            introduction = specialist.INTRODUCTIONS.get(legal_code)
            dictionary = specialist.DICIONARIO.get(legal_code)
            if dictionary:
                hint = (
                    introduction
                    + " Aqui tens um dicionário de sinónimos com termos utilizados nesse Código: "
                    + str(dictionary)
                )
            else:
                hint = introduction  # no caso de não haver dicionário

        model_answer = self.rag_class(
            context=context_rag, question=user_question, hint=hint
        )

        answer_chunks = model_answer.answer.split()
        for chunk in answer_chunks:
            yield {"type": "answer_chunk", "content": chunk + " "}
            await asyncio.sleep(0.1)

        yield {
            "type": "references",
            "content": json.dumps([ref.dict() for ref in model_answer.references]),
        }
