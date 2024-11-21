import base64
import os
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path


ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_text(content):
    word_count = len(content.split())
    return {
        "word_count": word_count,
        "sample": content,
    }


# Função para extrair texto de ficheiros
def extract_text(file_path):
    images = convert_from_path(file_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image)
    return text


def file_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def base64_to_file(base64_string, output_path):
    with open(output_path, "wb") as file:
        file.write(base64.b64decode(base64_string))


# Função principal para analisar o ficheiro
def analyze_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O ficheiro {file_path} não existe.")
    if not allowed_file(file_path):
        raise ValueError(f"Extensão do ficheiro {file_path} não é suportada.")

    # Extrair texto
    content = extract_text(file_path)

    # Processar texto
    return process_text(content)


# Exemplo de utilização
if __name__ == "__main__":
    test_file = "./teste.pdf"
    # base64_output_path = "./decoded_test.pdf"

    try:
        # Converter para Base64
        # base64_string = file_to_base64(test_file)
        # print("Ficheiro em Base64 (primeiros 100 caracteres):")
        # print(base64_string[:100], "...")

        # Decodificar Base64 para o formato original
        # base64_to_file(base64_string, base64_output_path)
        # print(f"Ficheiro reconstruído salvo em: {base64_output_path}")

        # analysis = analyze_file(base64_output_path)
        analysis = analyze_file(test_file)
        print("Resultado da análise:")
        print(f"Número de palavras: {analysis['word_count']}")
        print("\nTexto completo extraído:")
        print(analysis["sample"])
    except Exception as e:
        print("Erro:", e)
