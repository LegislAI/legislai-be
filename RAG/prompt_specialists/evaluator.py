from datetime import datetime

import dspy


class EvaluateAnswer(dspy.Signature):
    context = dspy.InputField(desc="O contexto necessário para responder à questão")
    question = dspy.InputField(desc="A pergunta perguntada ao sistema")
    model_answer = dspy.InputField(desc="A resposta do sistema que tens de avaliar")
    rating = dspy.OutputField(
        desc="Resultado entre 1 e 5. Apenas responde o número como um `int`, nada mais!"
    )


class Evaluator:
    def __init__(self, metric_lm):
        self.metric_lm = metric_lm

    def evaluate(self, gold, pred, trace=None):
        predicted_answer = pred.answer
        question = gold.question
        context = gold.context

        with dspy.context(lm=self.metric_lm):
            faithful = dspy.ChainOfThought(EvaluateAnswer)(
                context=context, question=question, model_answer=predicted_answer
            )

        return float(faithful.rating)
