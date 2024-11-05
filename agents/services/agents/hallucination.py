from langchain_core.prompts import ChatPromptTemplate
from agents.utils.state import GraphState
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Literal

MAX_RETRIES = 3

class HallucinationsOutput(BaseModel):  # structured output
    """Binary score for hallucination present in generation answer."""
    binary_score: str = Field(description="Answer is grounded in the facts, 'sim' or 'nao'")


class HallucinationEvaluator:
    """Evaluator class for determining whether a generation answer is grounded in the legal facts provided."""

    PROMPT_SYSTEM = """
        És um perito encarregado de verificar se uma resposta gerada por um modelo de linguagem para uma questão jurídica está fundamentada e completamente suportada por um conjunto de factos jurídicos, como leis, estatutos e jurisprudência.
        Fornece uma classificação binária, 'sim' ou 'nao':
            - 'sim' significa que a resposta está totalmente fundamentada no conjunto de factos jurídicos fornecidos.
            - 'nao' significa que a resposta inclui informações ou afirmações não suportadas pelos factos fornecidos.

        Requisitos:
        - Se a resposta se refere a leis, estatutos, números de casos ou outras fontes legais específicas, assegura-te de que estas referências estão explicitamente presentes no conjunto de factos. Caso contrário, devolve 'nao'.
        - Se a resposta inclui exemplos de texto ou frases jurídicas (por exemplo, citações de estatutos ou jurisprudência), verifica se esses exemplos correspondem ao conjunto de factos. Se não, devolve 'nao'.
        - Se a resposta inclui interpretação ou análise jurídica, garante que esta está alinhada com os factos jurídicos fornecidos sem introduzir informações não suportadas.
        
        Lembra-te, a tarefa principal é determinar se a resposta está firmemente baseada nos factos e referências legais fornecidos.
    """

    def __init__(self, max_retries: int = MAX_RETRIES):
        self.max_retries = max_retries

    def create_prompt(self, documents: str, question: str, pred_answer: str) -> ChatPromptTemplate:
        """Generates a prompt template using the provided documents, question, and predicted answer."""
        return ChatPromptTemplate.from_messages(
            [
                ("system", self.PROMPT_SYSTEM),
                ("human", f"Documentos: \n {documents} \n\n Pergunta: {question}\n\n Resposta da LLM : {pred_answer}"),
            ]
        )

    def evaluate(self, state: GraphState) -> Literal["rag_coordinator", "end"]:
        """
        Evaluates if the LLM answer is grounded in the provided facts.

        Args:
            state (GraphState): The current graph state containing the question, documents, and predicted answer.
            config (dict): Configuration settings, including max_retries.

        Returns:
            Literal["rag_coordinator", "end"]: The next step in the workflow.
        """
        # Retrieve inputs from state
        question = state["question"]
        documents = state["documents"]
        pred_answer = state["model_answer"]
        retries = state.get("retries", -1)

        prompt = self.create_prompt(documents=documents, question=question, pred_answer=pred_answer)
        hallucination_llm = prompt | llm.with_structured_output(HallucinationsOutput) 
        hallucination_grade: HallucinationsOutput = hallucination_llm.invoke(
            {"documents": documents, "question": question, "pred_answer": pred_answer}
        )

        # Check hallucination result
        if hallucination_grade.binary_score == "nao":
            return "rag_coordinator" if retries < self.max_retries else "end"
        else:
            return "end"


# HOW TO USE
# evaluator = HallucinationEvaluator(max_retries=3)
# next_step = evaluator.evaluate(state=graph_state)
