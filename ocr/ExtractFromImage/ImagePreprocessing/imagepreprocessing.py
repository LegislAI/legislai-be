import base64

import cv2
import matplotlib.pyplot as plt
import numpy as np


class ImagePreprocessing:
    # Image comes from the frontend as a base64 string, so we need to decode it into a numpy array
    # We will automatically load the image as grayscale for the preprocessing
    # image = self.__load_image(image)
    # We want to remove speckles (i.e dust) from the image without loosing text sharpness since this is what we want to extract
    # We will enhance the image by binarizing it, enhance sharpness and then denoising it with a low pass filter
    # transformed_image = self.__deskew_image(image)
    # transformed_image = self.__binarize_image(transformed_image)
    # transformed_image = self.__enhance_image(transformed_image)
    # TODO ROI, Edge detection
    # transformed_image = self.__adjust_contrast(transformed_image)
    # resizing at the end. TODO alter for dynamic resizing based on original image size
    # Minimum: 200x200
    # Maximum: 4000x4000

    def pre_process(self, image, actions="all", plot=False) -> np.ndarray:
        transforms = {
            "deskew": self.__deskew_image,
            "binarize": self.__binarize_image,
            "enhance": self.__enhance_image,
            "contrast": self.__adjust_contrast,
            "resize": self.__resize_image,
        }

        if actions == "all":
            actions = transforms.keys()

        transformed_image = self.__load_image(image)
        for action in actions:
            if action in transforms:
                transformed_image = transforms[action](transformed_image)
            else:
                raise ValueError(f"Invalid action: {action}")

        if plot:
            self.__plot_image([image, transformed_image])

        transformed_image = cv2.cvtColor(transformed_image, cv2.COLOR_GRAY2RGB)
        transformed_image = np.uint8(transformed_image)

        return transformed_image

    def __resize_image(self, image, size=(800, 800)):
        return cv2.resize(image, size)

    def __adjust_contrast(self, image):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_image = clahe.apply(image)
        return contrast_image

    def __load_image(self, image):
        encoded_data = image.split(",")[1]
        nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        return image

    def __deskew_image(self, image):
        # rotated_image = self.__rotate_image(cropped_image, angle[-1])
        imOTSU = cv2.threshold(image, 0, 1, cv2.THRESH_OTSU + cv2.THRESH_BINARY_INV)[
            1
        ]  # get threshold with positive pixels as text
        coords = np.column_stack(
            np.where(imOTSU > 0)
        )  # get coordinates of positive pixels (text)
        angle = cv2.minAreaRect(coords)[-1]  # get a minAreaRect angle
        THRESHOLD = 1
        image = self.__rotate_image(image, angle) if angle > THRESHOLD else image
        return image

    def __rotate_image(self, image, angle):
        angle = -(90 + angle) if angle < -45 else -angle
        (h, w) = image.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )

    def __enhance_image(self, image):
        # We will enhance the image by sharpening it
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened_image = cv2.filter2D(image, -1, kernel)
        return sharpened_image

    def __denoise_image(self, image):
        kernel = np.ones((2, 2), np.uint8)
        denoised_image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        return denoised_image

    def __binarize_image(self, image):
        # hsl_image = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
        _, binary_image = cv2.threshold(
            image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return binary_image

    def __plot_image(self, images):
        # We can receive multiple images to plot, divide the images into subplots of len(images)
        _, ax = plt.subplots(1, len(images))
        for i in range(len(images)):
            ax[i].imshow(images[i])
            ax[i].axis("off")
        plt.show()
