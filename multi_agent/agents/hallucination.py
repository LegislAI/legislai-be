import os
import re
from typing import Literal

from agents.utils.state import GraphState
from dotenv import load_dotenv
from langchain import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.pydantic_v1 import Field
from langchain_together import ChatTogether

MAX_RETRIES = 3
load_dotenv()

# NOT DONE


def get_few_shots(fs_examples):
    fs_examples_shuffled = fs_examples.sample(frac=1).reset_index(drop=True)
    few_shot_examples = fs_examples_shuffled.iloc[2:5]

    # Construct template from each row
    examples = []
    for _, row in few_shot_examples.iterrows():
        example = f"""
        Pergunta: {row['question']}
        Resposta do Modelo: {row['answer']}
        Feedback: {row['feedback']}
        Score Total: {row['human_score']}
        """
        examples.append(example.strip())

    template_fs_examples = "\n\n".join(examples)
    return template_fs_examples


class HallucinationsOutput(BaseModel):  # structured output
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'sim' or 'nao'"
    )


class HallucinationEvaluator:
    """Evaluator class for determining whether a generation answer is grounded in the legal facts provided."""

    def __init__(self):
        self.JUDGE_PROMPT = """
            Será fornecido uma questão de um utilizador e uma resposta do sistema.
            A tua tarefa que é providenciar um 'score total' para avaliar quão bem o sistema respondeu à questão.
            O teu score total tem de estar na escala de 1 a 5, onde 1 significa que a resposta não ajuda nada e não responde corretamente à questão, e 5 significa que a resposta do sistema ajuda e responde completamente à questão.

            Aqui está a escala necessária para construires o teu feedback:
            1: A resposta_do_sistema é terrível: completamente irrelevante para a pergunta ou muito insuficiente.
            2: A resposta_do_sistema é pouco útil: cobre alguns pontos, mas falha em aspetos importantes da pergunta.
            3: A resposta_do_sistema é parcialmente útil: aborda a pergunta, mas ainda carece de detalhes ou precisão.
            4: A resposta_do_sistema é boa: é útil, direta e cobre a maior parte dos aspetos da pergunta, mas poderia ser aprimorada.
            5: A resposta_do_sistema é excelente: totalmente relevante, detalhada, precisa e responde plenamente a todas as preocupações da pergunta.

            Aqui estão alguns exemplos para seguires:
            {examples}
            Fornece o teu feedback da seguinte forma:
            Feedback:::
            Avaliação: (o teu raciocinio para o score final, em texto)
            Score total: (o teu score final, em número entre 1 a 5)

            DEVES fornecer valores para "Avaliação:" e "Score total:" na sua resposta.

            Agora, aqui está a pergunta e a resposta do sistema.
            Questão: {question}
            Resposta do modelo: {answer}

            Feedback:::"""
        self.llm = ChatTogether(
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        )

    def __init__(self, max_retries: int = MAX_RETRIES):
        self.max_retries = max_retries

    def _create_chain(self):
        chat_prompt = PromptTemplate(
            template=self.JUDGE_PROMPT,
            input_variables=["question", "answer", "examples"],
        )
        llm_chain = chat_prompt | llm
        return llm_chain

    def _extract_judge_score(answer: str, split_str: str = "Score total:") -> int:

        try:
            if split_str in answer.content:
                rating = answer.content.split(split_str)[1]
            else:
                rating = answer.content
            digit_groups = [el.strip() for el in re.findall(r"\d+(?:\.\d+)?", rating)]
            return float(digit_groups[0])
        except Exception as e:
            print(e)
            return None

    def _evaluate(self, state: GraphState) -> Literal["rag_coordinator", "end"]:
        """
        Evaluates if the LLM answer is grounded in the provided facts.
        """
        # Retrieve inputs from state
        llm_chain = self._create_chain()
        result = llm_chain.invoke(
            {
                "question": state["question"],
                "answer": state["model_answer"],
                "examples": get_few_shots(),
            }
        )
        retries = state.get("retries", -1)
        llm_score = self._extract_judge_score(result)

        # Check hallucination result
        if int(llm_score) < 3:
            return "rag_coordinator" if retries < self.max_retries else "default_answer"
        else:
            return "end"


# HOW TO USEfrom langchain import PromptTemplate
# evaluator = HallucinationEvaluator(max_retries=3)
# next_step = evaluator.evaluate(state=graph_state)
