from datetime import datetime
from together import Together
from dotenv import load_dotenv
import os

data_atual = datetime.now()

data_formatada = data_atual.strftime("%d%m%Y")

load_dotenv()

API_KEY = os.getenv("API_KEY")
client = Together(api_key=API_KEY)


few_shot_examples = [
    {
        "role": "user",
        "content": """
        Query: Quais são os requisitos para o registo predial?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '03112024',
            'summary': 'Resumo: Condições e requisitos para o registo predial segundo a legislação atual.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais foram os prazos de arrendamento previstos no NRAU em 2022?\n\n
        Metadata: {
            'legislation_date': '2022',
            'question_date': '03112024',
            'summary': 'Resumo: Prazos de arrendamento estipulados pelo Novo Regime do Arrendamento Urbano.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são os direitos dos arrendatários no NRAU em Lisboa?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '03112024',
            'summary': 'Resumo: Direitos e deveres dos arrendatários segundo o Novo Regime do Arrendamento Urbano.',
            'region': 'Lisboa'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Que direitos tenho ao fazer um contrato de trabalho?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '03112024',
            'summary': 'Resumo: Principais direitos ao estabelecer um contrato de trabalho.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são os direitos de indemnização em caso de despedimento no Porto?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '03112024',
            'region': 'Porto',
            'summary': 'Resumo: Regras de indemnização em caso de despedimento na região do Porto.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são os direitos de segurança e saúde no trabalho?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '03112024',
            'summary': 'Resumo: Disposições sobre segurança e saúde no trabalho segundo o Código do Trabalho.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são os meus direitos laborais em Lisboa no caso de rescisão de contrato em 2024?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '03112024',
            'region': 'Lisboa',
            'summary': 'Resumo: Direitos laborais aplicáveis na região de Lisboa sobre rescisão de contrato em 2024.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: O que diz a legislação atual sobre o pagamento de horas extras?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'summary': 'Resumo: Regras sobre pagamento de horas extras segundo a legislação atual.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Como funciona o processo de herança em Portugal?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'summary': 'Resumo: Procedimentos legais para partilha de herança em Portugal.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são os direitos dos trabalhadores em teletrabalho em 2023?\n\n
        Metadata: {
            'legislation_date': '2023',
            'question_date': '04112024',
            'summary': 'Resumo: Direitos e deveres dos trabalhadores em regime de teletrabalho em 2023.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Existe um limite máximo para a duração dos contratos de arrendamento em Lisboa?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'region': 'Lisboa',
            'summary': 'Resumo: Limites para duração de contratos de arrendamento em Lisboa.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Como é calculado o subsídio de desemprego em Portugal?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'summary': 'Resumo: Métodos de cálculo do subsídio de desemprego segundo a legislação portuguesa.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Que direitos tem o pai aquando do nascimento de um filho?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'summary': 'Resumo: Direitos de licença parental para o pai na altura do nascimento do filho.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Como funciona a isenção de IMT na primeira compra de habitação?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'summary': 'Resumo: Requisitos e benefícios para a isenção do IMT na primeira compra de habitação.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Quais são as regras para o contrato de estágio em 2024?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'summary': 'Resumo: Condições e direitos associados a contratos de estágio segundo a legislação de 2024.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: Como se processa o licenciamento para obras em prédios históricos?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'summary': 'Resumo: Procedimento de licenciamento para obras em património histórico.'
        }
        """,
    },
    {
        "role": "user",
        "content": """
        Query: O que está previsto na lei sobre o trabalho noturno?\n\n
        Metadata: {
            'legislation_date': '2024',
            'question_date': '04112024',
            'summary': 'Resumo: Normas e direitos relativos ao trabalho noturno.'
        }
        """,
    },
]


f = open("queries.txt", "r")
for line in f:
    # print(line)
    user_query = f"""
    {line}\n\n Dá me apenas os metadados que tiraste desta querie\n\n
    Se não for indicado um ano em concreto, deves assumir o ano atual como 'legislation_date'\n\n
    Hoje é dia {data_formatada}
    """

    messages = few_shot_examples + [{"role": "user", "content": user_query}]

    response = client.chat.completions.create(
        model="meta-llama/Llama-Vision-Free",
        messages=messages,
    )

    # print(response.choices[0].message.content)
    # print("-" * 100)
