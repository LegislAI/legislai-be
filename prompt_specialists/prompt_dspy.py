from config import Config
from evaluator import Evaluator
from generator import RAG
from specialist import SpecialistPrompts

NOTA_FINAL = """Observação: Esta análise é meramente informativa e não substitui o aconselhamento jurídico de um profissional."""


def main(context_rag, user_question, code_rag):
    config = Config()
    metric_lm = config.setup_models()

    rag_class = RAG()
    specialist = SpecialistPrompts()
    # evaluator = Evaluator(metric_lm)

    legal_code = specialist.get_legal_code(code_rag)
    introduction = specialist.INTRODUCTIONS.get(legal_code)
    dictionary = specialist.DICIONARIO.get(legal_code)
    hint = introduction + str(dictionary)

    model_answer = rag_class(context=context_rag, question=user_question, hint=hint)
    # evaluation = evaluator.evaluate(model_answer, model_answer)

    model_answer.answer += f"\n\n{NOTA_FINAL}"
    return model_answer


if __name__ == "__main__":
    main()
