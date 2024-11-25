import json
import traceback

from generator import RAGPrompt
from specialists import SpecialistPrompts
from utils.config import Config
from utils.logging import logger


def simulate_streaming(text, delay=0.2):
    """Simulate streaming by yielding words with a delay"""
    import time

    words = text.split()
    for word in words:
        yield word
        time.sleep(delay)


def stream_answer(context_rag, user_question, code_rag):
    config = Config()
    lm = config.setup_models()

    specialist = SpecialistPrompts()

    if code_rag is None:
        hint = "És um especialista na Legislação Portuguesa e dominas os assuntos legais portugueses."
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
    try:
        rag = RAGPrompt()

        response = rag(context=context_rag, question=user_question, hint=hint)

        for chunk in simulate_streaming(response.answer):
            print(chunk, end=" ", flush=True)

        print("\n\nReferences:")
        for ref in response.references:
            print(json.dumps(ref.dict(), indent=2))

    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()
