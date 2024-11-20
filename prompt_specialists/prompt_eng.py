import json
import os
from enum import Enum

import numpy as np
from dotenv import load_dotenv
from langchain import PromptTemplate
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain_together import Together

nota_final = """Observação: Esta análise é meramente informativa e não substitui o aconselhamento jurídico de um profissional."""


load_dotenv()
llm = Together(
    model="mistralai/Mistral-7B-Instruct-v0.1",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    max_tokens=1000,
)

embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def text_evaluation(correct_answer, model_answer, trace=None):
    correct_answer_embeddings = embedding.embed_query(correct_answer)
    model_answer_embedding = embedding.embed_query(model_answer)

    similarity = cosine_similarity(model_answer_embedding, correct_answer_embeddings)
    return similarity


class LegalCode(Enum):
    TRABALHO = "Código do Trabalho e Processo do Trabalho"
    PREDIAL = "NRAU e Código do Registo Predial"
    CDADC = "Código dos Direitos de Autor"
    CIRS = "Código IRS"
    CIMI = "Código do IMI e Código do IMT"
    CN = "Código do Notariado"
    ESTRADA = "Código da Estrada"
    CIRE = "Codigo da Insolvencia e da Recuperacao de Empresas"
    CCP = "Codigo Contratos Publicos"


class SpecialistPrompts:
    def __init__(self):
        self.INTRODUCTIONS = {
            LegalCode.TRABALHO: "És um especialista em Direito Laboral português. Tens profundo conhecimento do Código do Trabalho e do Processo do Trabalho, bem como da legislação relativa ao emprego em Portugal.",
            LegalCode.PREDIAL: "És um especialista em legislação de arrendamento e registo predial em Portugal. Dominas o Novo Regime do Arrendamento Urbano (NRAU) e o Código do Registo Predial.",
            LegalCode.CCP: "És um especialista em contratação pública em Portugal. Tens conhecimento aprofundado do Código dos Contratos Públicos e da legislação aplicável aos contratos celebrados por entidades públicas.",
            LegalCode.CDADC: "És um especialista em legislação de propriedade intelectual em Portugal. Tens profundo conhecimento do Código dos Direitos de Autor e Direitos Conexos, com foco na proteção e gestão de obras intelectuais.",
            LegalCode.CIRE: "És um especialista em insolvência e recuperação de empresas em Portugal. Dominas o Código de Insolvência e Recuperação de Empresa e toda a legislação aplicável aos processos de recuperação e falência de empresas.",
            LegalCode.CIRS: "És um especialista sobre o Codigo do IRS - imposto sobre o Rendimsento das Pessoas Singulares. Tens profundo conhecimento do Código do IRS, incluindo as normas e obrigações relacionadas com esse imposto em Portugal.",
            LegalCode.CIMI: "És um especialista em impostos sobre o património imobiliário em Portugal. Dominas o Código do IMI (Imposto Municipal sobre Imóveis) e o Código do IMT (Imposto Municipal sobre as Transmissões Onerosas de Imóveis).",
            LegalCode.CN: "És um especialista em direito notarial em Portugal. Tens profundo conhecimento do Código do Notariado e das normas relativas à autenticação e formalização de atos e documentos legais.",
            LegalCode.ESTRADA: "És um especialista em legislação rodoviária em Portugal. Dominas o Código da Estrada e toda a regulamentação relacionada com a segurança, regras de trânsito e legislação para condutores e veículos.",
        }

        self.SYSTEM_PROMPT = """{intro}
            O teu papel é responder a uma questão EXCLUSIVAMENTE com base nos documentos fornecidos. Por isso, é essencial que sigas estas instruções:
            1. Toda a tua resposta deve ser suportada exclusivamente pelas informações presentes nesses documentos.
            2. Se não encontrares resposta à pergunta nos documentos fornecidos, deves informar que não possuis dados para responder.
            3. Sempre que usares informação de um documento específico, indica a fonte que permita ao leitor saber exatamente de onde veio a informação.

            Alguns exemplos (não deves olhar ao formato da resposta):
            {examples}

            O formato da resposta deve ser em formato JSON:
            {
                "resposta": A tua resposta à pergunta colocada,
                "referências": {
                    "article_name": name,
                    "url": url
                }
            }

            A tua tarefa:
            Documentos: {documents}
            Questão: {question}
        """

    def get_legal_answer(
        self, code: LegalCode, documents: str, query: str, examples
    ) -> dict:
        introduction = self.INTRODUCTIONS.get(code)

        prompt = PromptTemplate(
            template=self.SYSTEM_PROMPT,
            input_variables=["intro", "question", "documents", "examples"],
        )

        llm_chain = llm | prompt
        if isinstance(examples, list):
            examples = "\n".join([str(example) for example in examples])

        try:
            response = llm_chain.invoke(
                {
                    "intro": introduction,
                    "question": query,
                    "documents": documents,
                    "examples": examples,
                }
            )
            return response
        except Exception as e:
            return {
                "resposta": f"Erro ao processar a resposta: {str(e)}",
                "referências": {},
            }


def main():
    with open("examples/codigo_estrada.json", "r") as file:
        context_data = json.load(file)

    with open("examples/qa_estrada.json", "r") as file:
        qa_json = json.load(file)

    specialist = SpecialistPrompts()
    examples = qa_json["train"][:4]

    for qa in qa_json["test"]:
        response = specialist.get_legal_answer(
            code=LegalCode.ESTRADA,
            documentos=context_data,
            query=qa["question"],
            examples=examples,
        )
        print(response)


if __name__ == "__main__":
    main()
