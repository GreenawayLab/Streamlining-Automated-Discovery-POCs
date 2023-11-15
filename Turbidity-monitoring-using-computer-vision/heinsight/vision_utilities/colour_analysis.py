from typing import Tuple, Union, List
import numpy as np
import cv2 as cv


def bgr_to_hsv(*images) -> Union[List[np.ndarray], np.ndarray]:
    """
    Convert a 3d bgr image to an hsv image
    :param image: bgr image loaded in by numpy
    :return:
    """
    if len(images) == 1:
        image = images[0]
        hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    else:
        hsv = [cv.cvtColor(image, cv.COLOR_BGR2HSV) for image in images]
    return hsv


def hsv_to_bgr(*images) -> Union[List[np.ndarray], np.ndarray]:
    """
    Convert a 3d hsv image to a bgr image
    :param image: bgr image loaded in by numpy
    :return:
    """
    if len(images) == 1:
        image = images[0]
        bgr = cv.cvtColor(image, cv.COLOR_HSV2BGR)
    else:
        bgr = [cv.cvtColor(image, cv.COLOR_HSV2BGR)for image in images]
    return bgr


def get_average_h_s_v_1d(*images,
                         ) -> Union[Tuple[np.ndarray, np.ndarray, np.ndarray], List[Tuple[np.ndarray, np.ndarray, np.ndarray]]]:
    """
    Get and return the average hsv values from an hsv image, or a list of average hsv values for multiple images
    :param images: one or more 1d array hsv images
    :return:
    """
    def values(image):
        h = [pixel_hsv[0] for pixel_hsv in image]
        s = [pixel_hsv[1] for pixel_hsv in image]
        v = [pixel_hsv[2] for pixel_hsv in image]
        h = np.mean(h)
        s = np.mean(s)
        v = np.mean(v)
        return (h, s, v)
    if len(images) == 1:
        image = images[0]
        (h, s, v) = values(image)
        return (h, s, v)
    else:
        hsv_list = [values(image) for image in images]
        return hsv_list


def get_average_h_s_v_3d(*images,
                         ) -> Union[Tuple[np.ndarray, np.ndarray, np.ndarray], List[Tuple[np.ndarray, np.ndarray, np.ndarray]]]:
    """
        Get and return the average hsv values from an hsv image
        :param images: one or more 3d array hsv images
        :return:
        """
    def values(image):
        h = image[:, :, 0]
        s = image[:, :, 1]
        v = image[:, :, 2]
        h = np.mean(h)
        s = np.mean(s)
        v = np.mean(v)
        return (h, s, v)
    if len(images) == 1:
        image = images[0]
        (h, s, v) = values(image)
        return (h, s, v)
    else:
        hsv_list = [values(image) for image in images]
        return hsv_list


def get_average_b_g_r_1d(*images,
                         ) -> Union[Tuple[np.ndarray, np.ndarray, np.ndarray], List[Tuple[np.ndarray, np.ndarray, np.ndarray]]]:
    """
    Get and return the average bgr values from brg images, or a list of average hsv values for multiple images
    :param images: one or more 1d array brg images
    :return:
    """
    def values(image):
        b = [pixel_hsv[0] for pixel_hsv in image]
        g = [pixel_hsv[1] for pixel_hsv in image]
        r = [pixel_hsv[2] for pixel_hsv in image]
        b = np.mean(b)
        g = np.mean(g)
        r = np.mean(r)
        return (b, g, r)
    if len(images) == 1:
        image = images[0]
        (b, g, r) = values(image)
        return (b, g, r)
    else:
        bgr_list = [values(image) for image in images]
        return bgr_list


def get_average_b_g_r_3d(*images,
                         ) -> Union[Tuple[np.ndarray, np.ndarray, np.ndarray], List[Tuple[np.ndarray, np.ndarray, np.ndarray]]]:
    """
    Get and return the average bgr values from an hsv image
    :param images: one or more 3d array brg images
    :return:
    """
    def values(image):
        b = image[:, :, 0]
        g = image[:, :, 1]
        r = image[:, :, 2]
        b = np.mean(b)
        g = np.mean(g)
        r = np.mean(r)
        return (b, g, r)
    if len(images) == 1:
        image = images[0]
        (b, g, r) = values(image)
        return (b, g, r)
    else:
        bgr_list = [values(image) for image in images]
        return bgr_list

