
from ImageProcessing.image_processing import ImageProcessing
from PIL import Image

test_image_path = "ImageTextRecognition/test_image.png"

class ImageTextRecognition():
    def __init__(self):
        image_processor = ImageProcessing()
        test_image = Image.open(test_image_path)
        image_processor.process_document_image(test_image)

ImageTextRecognition()
