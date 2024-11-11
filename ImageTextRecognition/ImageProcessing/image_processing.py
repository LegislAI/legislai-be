import numpy as np
from ImageProcessing.bin.skew_detect import SkewDetect
from PIL import Image
from matplotlib 

class ImageProcessing():
    def __init__(self):
        pass

    def process_document_image(self, image: Image)-> Image:
        img = self._normalize_image(Image)
        # skew_correction = SkewCorrection(img)
        noise_corrected_image = self._correct_noise(img)
        # skew_detector = SkewDetect(image)
        # skew_data = skew_detector.determine_skew()
        # print(skew_data)

    def _normalize_image(self, image: Image)-> np.array: 
        img_as_arr = np.array(image)
        minval = img_as_arr.min()
        maxval = img_as_arr.max()

        if minval!=maxval:
            img_as_arr-=minval
            img_as_arr*=(255/(maxval-minval))


    def _correct_noise(self, image: np.array) -> np.array:
        