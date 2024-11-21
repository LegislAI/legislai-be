from typing import List

import dspy
import pydantic


class References(pydantic.BaseModel):
    article_title: str
    article_name: str
    url: str

class StructuredAnswer(pydantic.BaseModel):
    answer: str
    references: List[References]

class AnswerMarkdown(dspy.Signature):
    """Vais receber uma resposta do sistema e uma questão e a tua tarefa é fazer markdown da mesma, ou seja, sublinhares os aspetos mais importantes da resposta (com **), dar nova linha (\n), e bullet points (-)"""
    question = dspy.InputField()
    answer = dspy.InputField(desc="Resposta do sistema")
    answer_markdown = dspy.OutputField(desc="resposta com markdown")

class GenerateAnswer(dspy.Signature):
    """Sendo tu um especialista da legislação portuguesa, responde à questão baseado EXCLUSIVAMENTE no contexto fornecido. Por isso, é essencial que sigas estas instruções:
        1. Toda a tua resposta deve ser suportada exclusivamente pelas informações presentes nesses documentos.
        2. Se não encontrares resposta à pergunta nos documentos fornecidos, deves informar que não possuis dados para responder.
        3. A tua resposta deve ser detalhada, bem estruturada e conter vocabulário simples.
    """
    context = dspy.InputField(desc="Informação importante para responder à questão")
    question = dspy.InputField()
    answer : StructuredAnswer = dspy.OutputField(desc="Uma resposta detalhada com vocabulário simples e a lista de referencias utilizadas")

class RAG(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.ChainOfThoughtWithHint(GenerateAnswer)
        self.markdown = dspy.Predict(AnswerMarkdown)
    def forward(self, question, context, hint):
        pred = self.generate_answer(context=context, question=question, hint=hint).answer
        final_res = self.markdown(question = question, answer=pred).answer_markdown
        return dspy.Prediction(answer=final_res, references = pred.references)
