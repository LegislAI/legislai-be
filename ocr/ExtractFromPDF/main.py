import base64
import subprocess
from typing import List

import pytesseract
from pdf2image import convert_from_path

DEFAULT_TEMP_FILE_PATH = "./temp.pdf"


class PDFProcessor:
    def __base64_to_file(base64_string, output_path):
        with open(output_path, "wb") as file:
            file.write(base64.b64decode(base64_string))

    def extract_from_pdf(self, payload: str) -> dict:
        # convert from base 64 to pdf file
        # store in temporary path
        # extract text from pdf file
        # delete temp file
        # return extracted text
        encoded_data = payload.split(",")[1]
        self.__base64_to_file(encoded_data, DEFAULT_TEMP_FILE_PATH)

        # Conversão de PDF para imagens (uma imagem por página)
        images = convert_from_path(DEFAULT_TEMP_FILE_PATH)
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

        subprocess.run(f"rm {DEFAULT_TEMP_FILE_PATH}", shell=True)

        return complete_document
