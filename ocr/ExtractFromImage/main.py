import subprocess

import cv2
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from ocr.ExtractFromImage.ImagePreprocessing.imagepreprocessing import Processor


class ImageProcessor:
    def __init__(self):

        self.image_processor = Processor()
        self.model = ocr_predictor(
            "db_resnet50",
            "crnn_vgg16_bn",
            pretrained=True,
            assume_straight_pages=False,
            disable_crop_orientation=True,
            resolve_lines=True,
            resolve_blocks=True,
        )

    def extract_from_image(self, image: str) -> dict:
        transformed_image = self.image_processor.pre_process(
            image=image, actions="all", plot=False
        )

        temp_image_path = "./temp_image.png"
        cv2.imwrite(temp_image_path, transformed_image)
        image = DocumentFile.from_images(temp_image_path)

        result = self.model(image)

        json_output = result.export()

        complete_document = {}

        page_num = 0
        paragraph_num = 0

        for page in json_output.get("pages", []):
            complete_document.setdefault("page", {})
            complete_document["page"].setdefault(page_num, {"paragraph": {}})

            for block in page.get("blocks", []):
                block_text = ""
                for line in block.get("lines", []):
                    for word in line.get("words", []):
                        block_text += f"{word.get('value', '')} "

                paragraph_num += 1
                complete_document["page"][page_num]["paragraph"][
                    paragraph_num
                ] = block_text.strip()

            page_num += 1
            paragraph_num = 0

        subprocess.run("rm ./temp_image.png", shell=True, capture_output=True)
        return complete_document
