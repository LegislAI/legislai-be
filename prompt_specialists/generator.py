import dspy
import pydantic
from typing import List



class References(pydantic.BaseModel):
    article_title: str
    url: str
    date: str

class StructuredAnswer(pydantic.BaseModel):
    answer: str
    references: List[References]

class GenerateAnswer(dspy.Signature):
    context = dspy.InputField(desc="Informação importante para responder à questão")
    question = dspy.InputField()
    answer : StructuredAnswer = dspy.OutputField(desc="Uma resposta detalhada e a lista de referencias utilizadas")

class RAG(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.ChainOfThoughtWithHint(GenerateAnswer)

    def forward(self, question, context, hint):
        pred = self.generate_answer(context=context, question=question, hint=hint).answer
        res = dspy.Prediction(context=context, answer=pred, question=question)
        
        return res