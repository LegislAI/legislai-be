import numpy as np
from PIL import Image
from skimage import io, color
from skimage.feature import canny
from skimage.transform import hough_line, hough_line_peaks

class SkewDetect:
    def __init__(self, image: Image, sigma=3.0, num_peaks=20, plot_hough=True):
        self.image = image
        self.sigma = sigma
        self.num_peaks = num_peaks
        self.plot_hough = plot_hough

    def determine_skew(self):
        img_gray = np.array(self.image.convert("L"))
        edges = canny(img_gray, sigma=self.sigma)
        h, theta, d = hough_line(edges)
        accum, angles, dists = hough_line_peaks(h, theta, d, num_peaks=self.num_peaks)
        angles_deg = np.rad2deg(angles)
        skew_angle = self._estimate_skew_angle(angles_deg)
        if self.plot_hough:
            self._display_hough(h, theta, d)

        return {"Estimated Angle": skew_angle}

    def _estimate_skew_angle(self, angles_deg):
        angles_norm = [(angle + 90) % 180 - 90 for angle in angles_deg]

        if len(angles_norm) > 0:
            predominant_angle = np.mean(angles_norm)
        else:
            predominant_angle = 0

        return predominant_angle

    def _display_hough(self, h, theta, d):
        import matplotlib.pyplot as plt
        plt.imshow(np.log(1 + h),
                   extent=[np.rad2deg(theta[-1]), np.rad2deg(theta[0]), d[-1], d[0]],
                   cmap=plt.cm.gray,
                   aspect=1.0 / 90)
        plt.xlabel('Angle (degrees)')
        plt.ylabel('Distance (pixels)')
        plt.title('Hough Transform')
        plt.show()
