from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, HttpUrl
from typing import List

system_prompt = """
És um assistente jurídico encarregado de fornecer respostas baseadas exclusivamente na informação contida nos documentos fornecidos. O teu objetivo principal é garantir respostas precisas, fundamentadas no contexto, com citações específicas de quaisquer fontes referenciadas na resposta.
"""

prompt_template = """
Com base no documento fornecido responde à seguinte pergunta. 
Responde à pergunta apenas se tiveres 100% de certeza com base na informação disponibilizada nos documentos. Se a resposta não puder ser encontrada nos documentos, responde educadamente que não sabes.
Deves incluir todas as citações e referências do contexto para apoiar todos os pontos mencionados na resposta.

Documento: {document}
Pergunta: {question}
"""

class Citation(BaseModel):
    content: str = Field(..., description="Official document title or reference")
    designation: str = Field(..., description="Title of the document's purpose")
    url: HttpUrl = Field(..., description="Direct link to the official document")

class StructuredResponse(BaseModel):
    answer: str = Field(..., description="The answer based on the provided context.")
    citations: List[Citation] = Field(description="List of citations or references that support the answer.")


output_parser = PydanticOutputParser(pydantic_model=StructuredResponse)

prompt = PromptTemplate(
    input_variables=["question", "document"],
    template=prompt_template,
    output_parser=output_parser,
    system_prompt=system_prompt
)
chain = prompt | llm | output_parser
# chain.invoke({"question": .., "document": ..})



# how to use
# parsed_output = output_parser.parse(
#     prompt.format(question=question, document=context)
# )

