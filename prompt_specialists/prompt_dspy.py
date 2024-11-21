from config import Config
from evaluator import Evaluator
from generator import RAG
from specialists import SpecialistPrompts
import json
from datetime import datetime


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
    if dictionary:
        hint = introduction + " Aqui tens um dicionário de sinónimos com termos utilizados no Código: " + str(dictionary)
    else:
        hint = introduction  # Fallback no caso de não haver dicionário.

    
    model_answer = rag_class(context=context_rag, question=user_question, hint=hint)
    # evaluation = evaluator.evaluate(model_answer, model_answer)

    model_answer.answer += f"\n\n{NOTA_FINAL}"
    return model_answer


if __name__ == "__main__":
    with open('examples/codigo_estrada.json', 'r') as file:
        context_data = json.load(file)

    with open('examples/qa_estrada.json', 'r') as file:
        qa_json = json.load(file)

    init_time = datetime.now()
    context_rag = context_data
    user_question = qa_json['test'][2]['question']
    code_rag = "estrada"

    result = main(context_rag, user_question, code_rag)
    
    final_time = datetime.now()
    print(f"Time passed: {final_time - init_time}")
    print(result)
