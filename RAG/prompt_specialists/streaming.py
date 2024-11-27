from rag.prompt_specialists.generator import RAGPrompt
from rag.prompt_specialists.specialists import SpecialistPrompts
from rag.prompt_specialists.utils.config import Config
from rag.prompt_specialists.utils.logging import logger


class StreamingRAG:
    def __init__(self):
        self.rag_class = RAGPrompt()

    def stream_answer(self, context_rag, user_question, code_rag):
        config = Config()
        lm = config.setup_models()

        specialist = SpecialistPrompts()

        if code_rag is None:
            hint = "És um especialista na Legislação Portuguesa e dominas os assuntos legais portugueses. Deves responder em vocabulário simples e sempre em português de Portugal"
        else:
            legal_code = specialist.get_legal_code(code_rag)
            introduction = specialist.INTRODUCTIONS.get(legal_code)
            dictionary = specialist.DICIONARIO.get(legal_code)
            if dictionary:
                hint = (
                    introduction
                    + " Aqui tens um dicionário de sinónimos com termos utilizados nesse Código: "
                    + str(dictionary)
                )
            else:
                hint = introduction

        model_answer = self.rag_class(
            context=context_rag, question=user_question, hint=hint
        )

        return model_answer
