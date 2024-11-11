import numpy as np

from skew_detect import SkewDetect
from PIL import Image
from skimage.util import img_as_ubyte
from skimage.transform import rotate


class Deskew:
    def __init__(self, image: Image):
        # Initialize with the image and create an instance of SkewDetect
        self.image = image
        self.skew_detector = SkewDetect(image)

    def deskew(self):
        # Process the image with SkewDetect to get skew angle data
        skew_data = self.skew_detector.determine_skew(self.image)
        
        # Extract estimated angle from skew detection data
        estimated_angle = skew_data.get('Estimated Angle', 0)
        
        # Adjust the angle for rotation; counter-rotate the skew
        corrected_angle = -estimated_angle

        # Rotate the image to correct the skew
        image_np = np.array(self.image.convert("L"))  # Convert to grayscale if not already
        rotated_image = rotate(image_np, corrected_angle, resize=True, mode='edge')
        
        # Convert back to PIL Image for consistent output format
        deskewed_image = Image.fromarray(img_as_ubyte(rotated_image))

        return deskewed_image
