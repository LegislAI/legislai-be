import re
from enum import Enum
from typing import List


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
        self._init_dictionaries()
        self._init_introductions()

    def _init_dictionaries(self):
        self.DICIONARIO = {
            LegalCode.ESTRADA: {
                "buzina": "avisador",
                "acidente": "sinistro",
                "sinal": "pisca",
                "velocípedes": "bicicletas",
                "transito": "fila",
                "veículo de transporte coletivo de passageiros": "autocarros",
                "veículo de transporte coletivo de carga": "camião",
                "contra-ordenação": "multa",
            },
            LegalCode.TRABALHO: {
                "vencimento": "salário",
                "baixa médica": "prescrição médica",
                "empregador": ["funcionário", "empregado"],
                "contra-ordenação": "multa",
                "falecimento": "morte",
            },
        }

    def _init_introductions(self):
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

    def get_legal_code(self, input_string: str) -> LegalCode:
        patterns = {
            LegalCode.TRABALHO: r"\b(trabalho|processo do trabalho)\b",
            LegalCode.PREDIAL: r"\b(nrau|registo predial|predial)\b",
            LegalCode.CDADC: r"\b(direitos de autor|cdadc)\b",
            LegalCode.CIRS: r"\b(cirs|código irs)\b",
            LegalCode.CIMI: r"\b(cimi|código do imi|imt)\b",
            LegalCode.CN: r"\b(código do notariado|notariado|cn)\b",
            LegalCode.ESTRADA: r"\b(código da estrada|estrada)\b",
            LegalCode.CIRE: r"\b(cire|insolvência|recuperação de empresas)\b",
            LegalCode.CCP: r"\b(ccp|código contratos públicos)\b",
        }
        for code, pattern in patterns.items():
            if re.search(pattern, input_string, re.IGNORECASE):
                return code
            return "És um especialista na Legislação Portuguesa, dominas os assuntos legais portugueses. "
