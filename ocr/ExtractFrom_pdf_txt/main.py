import os

import pytesseract
from pdf2image import convert_from_path


class PDFProcessor:
    @staticmethod
    def extract_text_from_file(file_path: str) -> dict:
        """
        Converte páginas do PDF em imagens e extrai texto usando OCR, retornando formato json.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"O ficheiro {file_path} não existe.")

        # Conversão de PDF para imagens (uma imagem por página)
        images = convert_from_path(file_path)
        complete_document = {}

        page_num = 0

        for image in images:
            # Extrai texto da página atual usando OCR
            page_text = pytesseract.image_to_string(image)

            # Organiza por blocos e linhas para simular a estrutura do JSON
            complete_document.setdefault("page", {})
            complete_document["page"].setdefault(page_num, {"paragraph": {}})

            paragraph_num = 0
            for block in page_text.split("\n\n"):
                block_text = block.strip()
                if block_text:
                    paragraph_num += 1
                    complete_document["page"][page_num]["paragraph"][
                        paragraph_num
                    ] = block_text

            page_num += 1

        return complete_document


test_file = "./teste.pdf"
processor = PDFProcessor()
result = processor.extract_text_from_file(test_file)
print(result)
