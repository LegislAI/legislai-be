import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import List

import pandas as pd
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.pydantic_v1 import Field
from langchain_ollama.llms import OllamaLLM


class QueriesFormat(BaseModel):
    queries: List[str] = Field(
        description="List of queries to be generated by the model"
    )
    theme: str = Field(description="Theme of the queries")


json_parser = JsonOutputParser(pydantic_object=QueriesFormat)


class LegalCodes(str, Enum):
    CCP = "Codigo Contratos Publicos"
    PREDIAL = "Codigo do Registo Predial"  # + NRAU
    CDADC = "Codigo Direitos de Autor e dos Direitos Conexos"
    CIRS = "Codigo sobre o Imposto sobre o Rendimento das Pessoas Singulares"
    CN = "Codigo do Notariado"
    CIMI = "Codigo do Imposto Municipal sobre Imoveis"
    CIRE = "Codigo da Insolvencia e da Recuperacao de Empresas"


@dataclass
class ThemeExamples:
    theme: LegalCodes
    description: str
    example_queries: List[str]


def carregar_diploma(tema):
    nome_arquivo = f"{tema}.txt"
    try:
        with open(nome_arquivo, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Descrição padrão: arquivo não encontrado."


class QueryGenerator:
    def __init__(self, llm):
        self.llm = llm
        self.themes = self._initialize_theme_examples()
        self._setup_prompt_template()

    def _initialize_theme_examples(self) -> Dict[LegalCodes, ThemeExamples]:
        return {
            LegalCodes.CCP: ThemeExamples(
                theme=LegalCodes.CCP,
                description=carregar_diploma("CCP"),
                example_queries=[
                    "O que é um certificado digital?",
                    "O que é o relatório preliminar?",
                ],
            ),
            LegalCodes.PREDIAL: ThemeExamples(
                theme=LegalCodes.PREDIAL,
                description="diploma",
                example_queries=[
                    "O meu município tem cadastro predial. Como posso fazer a georreferenciação?",
                    "Como verifico se a propriedade está registada?",
                ],
            ),
            LegalCodes.CDADC: ThemeExamples(
                theme=LegalCodes.CDADC,
                description="diploma",
                example_queries=[
                    "Posso fazer a descarga da internet de uma obra protegida por direito de autor e é relevante qual seja a tecnologia usada, e se eu fizer apenas a descarga de algumas partes da obra?",
                    "Os professores podem tirar fotocópias ou digitalizar páginas de livros ou jornais para os seus alunos?",
                ],
            ),
            LegalCodes.CIRS: ThemeExamples(
                theme=LegalCodes.CIRS,
                description="diploma",
                example_queries=[
                    "Sou solteira e tenho um filho menor que vive comigo, posso beneficiar da declaração automática de IRS?",
                    "Como funciona o sistema de residência parcial?",
                ],
            ),
            LegalCodes.CN: ThemeExamples(
                theme=LegalCodes.CN,
                description="diploma",
                example_queries=[
                    "Qual a diferença entre um projeto de lei, uma proposta de lei, uma lei e um decreto-lei?",
                    "Quais as regras aplicáveis relativamente ao tratamento de dados pessoais?",
                ],
            ),
            LegalCodes.CIMI: ThemeExamples(
                theme=LegalCodes.CIMI,
                description="diploma",
                example_queries=[
                    "Como saber qual a taxa praticada em cada município?",
                    "Quais são as taxas de IMI?",
                ],
            ),
            LegalCodes.CIRE: ThemeExamples(
                theme=LegalCodes.CIRE,
                description="diploma",
                example_queries=[
                    "Quem decide se a opção é liquidar ou recuperar?",
                    "Como se inicia o processo de insolvência?",
                ],
            ),
        }

    def _setup_prompt_template(self):
        print("setup_prompt")
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Age como um especialista em direito português, treinado para gerar perguntas jurídicas realistas baseado na descrição do Tema.
                O objetivo é criar perguntas para colocar num exame de Direito, que façam sentido com a descrição fornecida. Usa os exemplos fornecidos como referência para gerar novas perguntas-
                Mantem  as perguntas:
                1. Realistas e específicas
                2. Em português correto e com terminologia jurídica apropriada

                O output final deve seguir o formato, de acordo com o numero de perguntas geradas:
                  "queries": ["perguntas aqui", "perguntas aqui"]""",
                ),
                (
                    "user",
                    """Tema: {theme}
                Descrição: {description}

                Exemplos:
                {examples}

                Gere {num_queries} novas perguntas seguindo estes exemplos.""",
                ),
            ]
        )

    def generate_queries(self, theme: LegalCodes, num_queries) -> List[str]:
        theme_info = self.themes[theme]

        examples_str = "\n".join(theme_info.example_queries)

        prompt = self.prompt_template.format(
            theme=theme.value,
            description=theme_info.description,
            examples=examples_str,
            num_queries=num_queries,
        )

        response = self.llm.invoke(prompt)
        print(f"response -> {response}\n")
        # try:
        #     queries = json.loads(f"[{response.content.strip()}]")
        #     return self._validate_queries(queries, theme)
        # except json.JSONDecodeError:
        # If JSON parsing fails, try to extract queries using string manipulation
        return self._extract_queries(response, theme.value)

    def _is_valid_query(self, query: Dict) -> bool:
        required_fields = {"query", "key_elements"}
        if not all(field in query for field in required_fields):
            return False

        # Check if query is in Portuguese
        if not any(char in "áéíóúãõâêîôûàèìòùç" for char in query["query"].lower()):
            return False

        if len(query["query"]) < 10:
            return False

        return True

    def _extract_queries(self, content: str, theme: str) -> List[Dict]:
        regex = r'"queries": \[*\s*(?P<queries>.*?)\s*\]*'
        matches = re.search(regex, content, re.DOTALL)
        result_list = []

        if matches:
            print(f"match {theme}\n")
            queries_str = matches.group("queries")
            queries = re.findall(r'"(.*?)"', queries_str)

            for query in queries:
                result_list.append({"query": query, "theme": theme})

        return result_list

    def _result_list_to_dataframe(self, result_list: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(result_list, columns=["query", "theme"])
        return df

    def generate_training_dataset(self, queries_per_theme) -> pd.DataFrame:
        all_queries = []

        for theme in LegalCodes:
            print(f"\nGenerating queries for {theme.value}...")
            queries = self.generate_queries(theme, queries_per_theme)
            all_queries.extend(queries)
        df = self._result_list_to_dataframe(all_queries)
        return df


model = OllamaLLM(model="llama3.2:1b-instruct-q8_0")
generator = QueryGenerator(model)

# penal_queries = generator.generate_queries(LegalCodes.CCP, num_queries=3)
# print("CCP Law Queries:")
# print(penal_queries)
queries_df = generator.generate_training_dataset(queries_per_theme=5)

queries_df.to_csv("queries2.csv", index=False)
