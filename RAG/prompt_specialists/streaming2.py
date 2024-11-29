import asyncio
import sys
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Generator
from typing import List

import dspy
from generator import AnswerMarkdown
from generator import GenerateAnswer
from generator import StructuredAnswer
from litellm import completion
from litellm import stream_chunk_builder
from utils.config import Config
from utils.logging import logger

sys.setrecursionlimit(10**9)

#### testes only


config = Config()


@dataclass
class StreamingResponse:
    """Wrapper for streaming response chunks"""

    delta: str


def get_template(predict_module: dspy.Predict, **kwargs) -> str:
    """Get formatted template from predict module."""
    signature = dspy.signatures.ensure_signature(predict_module.signature)
    template = dspy.signatures.signature_to_template(signature)
    demos = predict_module.demos if hasattr(predict_module, "demos") else []
    x = dspy.Example(demos=demos, **kwargs)
    return template(x)


def rstripped(s: str) -> str:
    """Extract the trailing whitespace itself."""
    from itertools import takewhile

    return "".join(reversed(tuple(takewhile(str.isspace, reversed(s)))))


class StreamingRAG(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.ChainOfThoughtWithHint(GenerateAnswer)
        self.markdown = dspy.Predict(AnswerMarkdown)
        self.config = Config()
        self.lm = self.config.setup_models()

    async def stream_complete(
        self, template: str
    ) -> Generator[StreamingResponse, None, None]:
        """Wrapper for DSPy LM streaming"""
        async for chunk in self.stream_complete(template):
            print(chunk)
            if chunk:
                yield StreamingResponse(delta=chunk)

    def forward(
        self, question: str, context: str, hint: str
    ) -> Generator[str, None, None]:
        pred = self.generate_answer(
            context=context, question=question, hint=hint
        ).answer

        markdown_template = self.markdown(
            question=question, answer=pred
        ).answer_markdown

        field = "answer_markdown:"
        before_response = ""
        logger.info(f"markdown answer -> {markdown_template}")
        self.stream_complete(markdown_template)


async def main():
    rag = StreamingRAG()

    question = "Qual é a lei que regula o teletrabalho em Portugal?"
    context = "a lei que regula o teletrabalho é a lei 251 do Código do Trabalho com o url https://diariodarepublica.pt/dr/legislacao-consolidada/lei/2009-34546475"
    hint = "Foca-te nos aspetos importantes do contexto."

    response_generator = rag(question=question, context=context, hint=hint)

    # Process the streamed response
    logger.info("Streaming Response: ")
    async for chunk in response_generator:
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())


# class StreamResponse:
#     """Representa uma resposta parcial do streaming."""
#     delta: str

# class StreamingRAG(dspy.Module):
#     def __init__(self):
#         super().__init__()
#         self.generate_answer = dspy.ChainOfThoughtWithHint(GenerateAnswer)
#         self.markdown = dspy.Predict(AnswerMarkdown, stream=True)
#         self.llm = config.setup_models()

#     def get_template(self, predict_module: dspy.Predict, **kwargs) -> str:
#         signature = dspy.signatures.ensure_signature(predict_module.signature)
#         template = dspy.signatures.signature_to_template(signature)
#         demos = getattr(predict_module, "demos", [])
#         example = dspy.Example(demos=demos, **kwargs)
#         return template(example)

#     def parse_stream(self, template: str) -> Generator[StreamResponse, Any, None]:
#         """Processa o stream de respostas do LLM."""
#         def extract_trailing_whitespace(text: str) -> str:
#             return ''.join(c for c in reversed(text) if c.isspace())[::-1]

#         campo_resposta = "Answer_markdown:"
#         texto_anterior = ""

#         stream = self.llm.stream_complete(template)

#         for chunk in stream:
#             texto_anterior += chunk.delta
#             position = texto_anterior.find(campo_resposta)
#             if position != -1:
#                 content = texto_anterior[position + len(campo_resposta):]
#                 if content.strip():
#                     yield StreamResponse(delta=content.strip())
#                     espacos_final = extract_trailing_whitespace(content)
#                     break

#         for chunk in stream:
#             content = chunk.delta
#             yield StreamResponse(delta=espacos_final + content.rstrip())
#             espacos_final = extract_trailing_whitespace(content)

#     def forward(self, question: str, context: str, hint: str) -> dspy.Prediction:
#         """Processa uma questão e retorna uma resposta estruturada."""
#         initial_response = self.generate_answer(
#             context=context, question=question, hint=hint
#         )
#         template = self.get_template(
#             predict_module=self.markdown,
#             question=question,
#             answer=initial_response.answer.answer
#         )


#         def format_response():
#             for chunk in self.parse_stream(template):
#                 print(chunk)
#                 yield chunk.delta

#         return dspy.Prediction(
#             answer=format_response(),
#             references=initial_response.answer.references
#         )
