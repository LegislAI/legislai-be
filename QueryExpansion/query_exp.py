import os
import json
from dotenv import load_dotenv
from langchain_together import Together
from prompt_toolkit import prompt

load_dotenv()

few_shot_examples = [
    {
        "role": "user",
        "content": """
        Query: Quais são os requisitos para o registo predial?
        Expanded Queries: {
            Quais são os documentos necessários para o registo predial em Portugal?,
            O que acontece se o registo predial não for feito dentro do prazo estipulado?,
            Qual é o custo do registo predial e como varia dependendo do tipo de imóvel?,
            Quais os tipos de registo predial existentes e em que situações são aplicáveis?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são os direitos e deveres do proprietário?
        Expanded Queries: {
            Como a legislação portuguesa define o conceito de propriedade?,
            Quais são as obrigações do proprietário em relação à manutenção do imóvel?,
            Em que situações o proprietário pode perder o direito sobre a propriedade?,
            Quais são os direitos do proprietário perante a ocupação ilegal do imóvel?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: O que são servidões administrativas?
        Expanded Queries: {
            Quais são os tipos de servidões administrativas previstas na legislação?,
            Como se estabelece uma servidão administrativa entre propriedades?,
            Quais são as limitações impostas ao proprietário por uma servidão administrativa?,
            Existe possibilidade de recurso para contestar uma servidão administrativa?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são as condições para a concessão de nacionalidade portuguesa?
        Expanded Queries: {
            Quais são os requisitos de residência para obter a nacionalidade portuguesa?,
            Quais documentos são necessários para o processo de concessão de nacionalidade?,
            Como é o processo de naturalização para filhos de cidadãos portugueses nascidos no estrangeiro?,
            Existe algum exame de proficiência em português exigido para a nacionalidade?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Como funciona o processo de legalização de um imóvel?
        Expanded Queries: {
            Quais são os documentos exigidos para a legalização de um imóvel?,
            Quais entidades são responsáveis pela validação da legalização de imóveis?,
            Quais são as multas ou penalidades aplicadas pela falta de legalização?,
            Como realizar o processo de legalização para imóveis em áreas de proteção ambiental?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são os direitos do arrendatário segundo a lei portuguesa?
        Expanded Queries: {
            Em que situações o arrendatário pode rescindir o contrato sem penalidades?,
            Quais são os prazos de aviso prévio para a rescisão do contrato pelo arrendatário?,
            Quais são os direitos do arrendatário em relação às condições de habitabilidade do imóvel?,
            Como a legislação protege o arrendatário contra aumentos abusivos de renda?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: O que constitui assédio laboral segundo a legislação portuguesa?
        Expanded Queries: {
            Quais comportamentos são considerados como assédio laboral pela lei?,
            Quais são as medidas que um trabalhador pode tomar caso sofra assédio laboral?,
            Como a legislação protege os trabalhadores contra represálias após denúncias de assédio?,
            Quais são as penalidades para empregadores condenados por assédio laboral?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são as condições para um cidadão estrangeiro trabalhar em Portugal?
        Expanded Queries: {
            Quais vistos são necessários para cidadãos estrangeiros trabalharem em Portugal?,
            Quais são os requisitos para obter uma autorização de trabalho em Portugal?,
            Existem setores de atividade com requisitos específicos para estrangeiros?,
            Quais são os direitos trabalhistas de um cidadão estrangeiro com contrato em Portugal?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Como funciona o regime de parentalidade na legislação portuguesa?
        Expanded Queries: {
            Quais são os direitos de licença parental para pais e mães em Portugal?,
            Como é o processo de partilha da licença parental entre os pais?,
            Quais são as condições para obter subsídio de parentalidade?,
            Quais são os direitos dos trabalhadores para acompanhar os filhos em consultas?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: O que é o contrato de empreitada e quais são os seus requisitos?
        Expanded Queries: {
            Quais são as responsabilidades das partes em um contrato de empreitada?,
            Como é o processo de resolução de conflitos em contratos de empreitada?,
            Quais são os prazos legais para a execução dos serviços acordados?,
            Como deve ser formalizado o contrato de empreitada de acordo com a lei?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são as regras para a penhora de bens?
        Expanded Queries: {
            Quais bens são impenhoráveis segundo a legislação portuguesa?,
            Como funciona o processo de penhora de bens móveis e imóveis?,
            Quais são os prazos e condições para a execução de uma penhora?,
            Quais são os direitos do devedor durante o processo de penhora?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são os requisitos para obter subsídio de desemprego em Portugal?
        Expanded Queries: {
            Quais são os períodos de contribuição necessários para aceder ao subsídio?,
            Como calcular o valor do subsídio de desemprego segundo a legislação?,
            Quais são as condições para a suspensão do subsídio de desemprego?,
            Quais documentos são exigidos para solicitar o subsídio de desemprego?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Como funciona o processo de adoção segundo a legislação portuguesa?
        Expanded Queries: {
            Quais são os requisitos para se candidatar à adoção em Portugal?,
            Qual é o papel das instituições de acolhimento no processo de adoção?,
            Como é o processo de integração da criança na família adotiva?,
            Quais são os prazos e etapas legais no processo de adoção?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são as regras para o registo de uma sociedade em Portugal?
        Expanded Queries: {
            Quais são os tipos de sociedades que podem ser registadas em Portugal?,
            Quais documentos são necessários para o registo de uma sociedade?,
            Como proceder com a alteração de informações após o registo da sociedade?,
            Quais são os prazos legais para o registo de uma sociedade após sua constituição?
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Como funciona o processo de herança segundo a lei portuguesa?
        Expanded Queries: {
            Como se define a herança legítima e a herança testamentária na legislação?,
            Quais são os direitos dos herdeiros no processo de partilha de bens?,
            Quais são os prazos e condições para a aceitação ou renúncia à herança?,
            Como são aplicadas as taxas de imposto sobre heranças em Portugal?
        }
        """,
    },
]


class QueryExpander:
    def __init__(self):
        self.query_expansion_prompt = """
        És um sistema de informação que processa queries dos utilizadores.
        Expande uma querie dada em 4 queries semelhantes no seu significado.

        Estrutura:
        Segue a estrutura mostrada nos exemplos abaixo para gerar queries expandidas.

        Exemplos:
        1. Exemplo de Consulta 1: "Como funciona o processo de herança segundo a lei portuguesa?"
        Exemplo de queries Expandidas: ["Quais são os direitos dos herdeiros no processo de partilha de bens?",
                                        "Como são aplicadas as taxas de imposto sobre heranças em Portugal?",
                                        "Quais são os prazos e condições para a aceitação ou renúncia à herança?",
                                        "Como se define a herança legítima e a herança testamentária na legislação?"]

        2. Exemplo de Consulta 2: "Quais são as regras para o registo de uma sociedade em Portugal?"
        Exemplo de queries Expandidas: ["Quais são os tipos de sociedades que podem ser registadas em Portugal?",
                                        "Quais documentos são necessários para o registo de uma sociedade?",
                                        "Como proceder com a alteração de informações após o registo da sociedade?",
                                        "Quais são os prazos legais para o registo de uma sociedade após sua constituição?"]

        A tua tarefa:
        Query: "{{query}}"
        Queries Expandidas:
        """
        self.llm = Together(
            model="mistralai/Mistral-7B-Instruct-v0.1",
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            max_tokens=256,
        )

    def expand_query(self, query: str, number: int = 5):
        formatted_prompt = self.query_expansion_prompt.replace(
            "{{query}}", query
        ).replace("{{number}}", str(number))
        messages = few_shot_examples + [{"role": "user", "content": formatted_prompt}]
        response = self.llm.invoke(messages)

        try:
            expanded_queries = response
        except json.JSONDecodeError:
            expanded_queries = query

        return {"queries": expanded_queries}