"""
Image analysis to contain methods used to do simple image analysis on images, and to prepare images for analysis.
Example of preparing an image for analysis is letting the user select an area in an image, and returning that area so
other analyses can be done for just that area
"""

import cv2
import numpy as np
from typing import Union, List
import warnings



def height_width(image):
    """
    Find the height and width of an image, whether it is a grey scale image or not

    :param image: an image, as a numpy array
    :return: int, int: the height and width of an image
    """
    if len(image.shape) == 3:
        image_height, image_width, _ = image.shape
    elif len(image.shape) == 2:
        image_height, image_width = image.shape
    else:
        raise ValueError('Image must be passed as a numpy array and have either 3 or 2 channels')

    return image_height, image_width


def display(image: np.ndarray,
            window_name: str = 'Image',
            ):
    """
    Display a cv2 image. User needs to press any key before anything else will happen. Image will stop being
    displayed when user exits out of the image window

    :param image:
    :param str, window_name:

    :return:
    """
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    height, width = height_width(image=image)
    cv2.resizeWindow(winname=window_name, width=width, height=height)
    cv2.imshow(winname=window_name, mat=image)
    cv2.waitKeyEx(0)


def draw_line(image, left_point, right_point, colour=None, thickness=None):
    """
    Helper function to draw a single line on an image. image origin is the top right corner

    :param image: image to draw the line on
    :param (int, int), left_point: the left point of the line, as (width, height) or equivalently (column, row)
    :param (int, int), right_point: the right point of the line, as (width, height) or equivalently (column, row)
    :param (int, int, int), colour: colour of the line in (b, g, r)
    :param int, thickness: line thickness
    :return: image with line and text drawn on the image
    """
    warnings.warn(
        'use cv2 line method directly',
        DeprecationWarning,
        stacklevel=2,
    )
    image = cv2.line(image,
                     left_point,
                     right_point,
                     colour,
                     thickness)
    return image

