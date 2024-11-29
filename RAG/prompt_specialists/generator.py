import os
from datetime import datetime
from typing import List
from typing import Optional

import dspy
import pydantic
from dotenv import load_dotenv
from utils.logging import logger

NOTA_FINAL = """**Observação:** Esta análise é meramente informativa e não substitui o aconselhamento jurídico de um profissional."""


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
    question = dspy.InputField(desc="Pedido que deves responder")
    answer: StructuredAnswer = dspy.OutputField(
        desc="Uma resposta detalhada e abrangente com vocabulário simples e a lista de referencias utilizadas"
    )


class RAGPrompt(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.ChainOfThoughtWithHint(GenerateAnswer)
        self.markdown = dspy.Predict(AnswerMarkdown)

    def forward(self, question, context, hint):
        init_time = datetime.now()
        pred = self.generate_answer(context=context, question=question, hint=hint)
        ans_markdown = self.markdown(question=question, answer=pred.answer.answer)
        final_res = ans_markdown.answer_markdown
        final_res = final_res + f"\n\n{NOTA_FINAL}"
        final_time = datetime.now()
        logger.info(f"Time passed in RAGPrompt: {final_time - init_time}")

        return dspy.Prediction(answer=final_res, references=pred.answer.references)
