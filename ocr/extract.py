import os
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path

# Função para verificar extensões permitidas
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Função para processar texto
def process_text(content):
    # Exemplo de análise básica
    word_count = len(content.split())
    return {
        "word_count": word_count,
        "sample": content[:200],  # Mostra os primeiros 200 caracteres
    }


# Função para extrair texto de ficheiros
def extract_text(file_path):
    extension = file_path.rsplit(".", 1)[-1].lower()

    if extension in {"png", "jpg", "jpeg"}:
        return pytesseract.image_to_string(file_path)
    elif extension == "pdf":
        images = convert_from_path(file_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text
    elif extension == "txt":
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    else:
        raise ValueError("Tipo de ficheiro não suportado.")


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
    # Substituir pelo caminho real do ficheiro
    test_file = "./test_image.png"

    try:
        analysis = analyze_file(test_file)
        print("Resultado da análise:", analysis)
    except Exception as e:
        print("Erro:", e)
