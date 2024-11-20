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
            }
        }

    def _init_introductions(self):
        self.INTRODUCTIONS = {
            LegalCode.TRABALHO: "És um especialista em Direito Laboral português...",
            LegalCode.PREDIAL: "És um especialista em legislação de arrendamento...",
            LegalCode.CCP: "És um especialista em contratação pública...",
            LegalCode.CDADC: "És um especialista em legislação de propriedade intelectual...",
            LegalCode.CIRE: "És um especialista em insolvência e recuperação...",
            LegalCode.CIRS: "És um especialista sobre o Codigo do IRS...",
            LegalCode.CIMI: "És um especialista em impostos sobre o património...",
            LegalCode.CN: "És um especialista em direito notarial...",
            LegalCode.ESTRADA: "És um especialista em legislação rodoviária...",
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
        return None
