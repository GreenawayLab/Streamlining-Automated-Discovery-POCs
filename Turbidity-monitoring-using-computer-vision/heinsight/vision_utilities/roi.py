from typing import Tuple, List, Union, Dict
import json
from pathlib import Path
import numpy as np
import cv2
import uuid
from heinsight.vision_utilities.image_analysis import display, height_width
from heinsight.heinsight_utilities import colour_palette

_rectangle_roi = 'rectangle'
_polygon_roi = 'polygon'
_roi_types = [_rectangle_roi,
              _polygon_roi,
              ]
_roi_colour = colour_palette._colour_9_bgr


class ROI:
    rectangle_roi = _rectangle_roi
    polygon_roi = _polygon_roi
    roi_types = _roi_types

    def __init__(self,
                 name: str,
                 roi_type: str,
                 ):
        """

        :param name:
        :param roi_type: one of roi_types
        """
        if name is None:
            name = uuid.uuid4().hex
        self._name = name
        self._roi_type = roi_type
        self._rectangle: Tuple[int, int, int, int] = None
        self._mask = None
        self._x: int = None  # starting/left x point of the roi
        self._y: int = None  # starting/top y point of the roi
        self._width: int = None  # width of the roi
        self._height: int = None  # height of the roi
        self._points: List[List[int]] = None  # points (vertices)] to create the roi [[x1, y1], [x2, y2]... [xn, yn]]
        self._select_width: int = None  # width of the image used to select the roi
        self._select_height: int = None  # height of the image used to select the roi
        self._data: Dict = {}

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,
             value: str):
        self._name = value

    @property
    def roi_type(self):
        return self._roi_type

    @roi_type.setter
    def roi_type(self,
                 value: str):
        self._roi_type = value

    @property
    def rectangle(self) -> Tuple[int, int, int, int]:
        """Points for the upright rectangle that contain the roi in the form (x, y, width, height) where x and y are
        the x and y coordinates for the top left corner of the rectangle, with the image origin in the top left
        corner"""
        return self._rectangle

    @rectangle.setter
    def rectangle(self,
                  value: Tuple[int, int, int, int]):
        (x, y, width, height) = value
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._rectangle = value

    @property
    def mask(self):
        """mask (black pixels everywhere, but the roi is in white)that contains the roi with dimensions of the image
        used to select the roi"""
        height = self.select_height
        width = self.select_width
        points = self.points
        white = (255)
        if height is None or width is None or points is None:
            raise Exception('no roi has been selected yet')
        mask = ROI.blank_mask(height=height, width=width)
        mask = cv2.fillPoly(img=mask,
                            pts=np.array([points]),
                            color=white,
                            )  # fills the area bound by the points with white
        self._mask = mask
        return self._mask

    @property
    def x(self) -> int:
        """starting/left x point of the roi"""
        return self._x

    @x.setter
    def x(self,
          value: int):
        self._x = value

    @property
    def y(self) -> int:
        """starting/top y point of the roi"""
        return self._y

    @y.setter
    def y(self,
          value: int):
        self._y = value

    @property
    def width(self) -> int:
        """width of the roi"""
        return self._width

    @width.setter
    def width(self,
              value: int):
        self._width = value

    @property
    def height(self) -> int:
        """height of the roi"""
        return self._height

    @height.setter
    def height(self,
               value: int):
        self._height = value

    @property
    def points(self) -> List[List[int]]:
        """points (vertices) to create the roi [[x1, y1], [x2, y2]... [xn, yn]]"""
        return self._points

    @points.setter
    def points(self,
               value: List[List[int]]):
        self._points = value

    @property
    def select_width(self) -> int:
        """width of the image used to select the roi"""
        return self._select_width

    @select_width.setter
    def select_width(self,
                     value: int):
        self._select_width = value

    @property
    def select_height(self) -> int:
        """height of the image used to select the roi"""
        return self._select_height

    @select_height.setter
    def select_height(self,
                      value: int):
        self._select_height = value

    @property
    def data(self) -> Dict:
        """necessary data to be able to save and load an ROI"""
        data = {'name': self.name,
                'points': self.points,
                'rectangle': self.rectangle,
                'select_height': self.select_height,
                'select_width': self.select_width,
                }
        self._data = data
        return self._data

    @data.setter
    def data(self,
             value: Dict):
        self.name = value['name']
        self.points = value['points']
        self.rectangle = value['rectangle']
        self.select_height = value['select_height']
        self.select_width = value['select_width']

    @staticmethod
    def blank_mask(height: int,
                   width: int,
                   ) -> np.ndarray:
        """create a 1d image with only black pixels of a specific height and width"""
        blank_mask = np.zeros(shape=(height, width),
                              dtype=np.uint8)  # blank mask, all black pixels
        return blank_mask

    @staticmethod
    def full_3d_mask(height: int,
                     width: int,
                     ) -> np.ndarray:
        """create a 3d image with only white pixels of a specific height and width"""
        full_3d = np.full(shape=(height, width, 3),
                          fill_value=255,
                          dtype=np.uint8)  # full mask, all white pixels
        return full_3d

    @staticmethod
    def blank_3d_mask(height: int,
                      width: int,
                      ) -> np.ndarray:
        """create a 3d image with only black pixels of a specific height and width"""
        blank_3d = np.zeros(shape=(height, width, 3),
                            dtype=np.uint8)  # blank mask, all black pixels
        return blank_3d

    def clear(self):
        """Reset everything back to default value except the name of the roi and the type of the roi"""
        self.rectangle = None
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.points = None
        self.select_width = None
        self.select_height = None
        self.data = None

    def select(self,
               image,
               window_name: str = None,
               ):
        """interactively select an roi on an image"""
        raise NotImplementedError

    def rectangle_image(self,
                        image: np.ndarray = None) -> np.ndarray:
        """draw a rectangle containing the roi on an image"""
        white = (255)
        if self.rectangle is not None:
            if image is None:
                clone = ROI.blank_3d_mask(height=self.select_height,
                                          width=self.select_width)
                colour = white
            else:
                clone = image.copy()
                colour = _roi_colour
            (x, y, width, height) = self.rectangle
            top_left = (x, y)
            bottom_right = (x + width, y + height)
            image_w_rectangle = cv2.rectangle(img=clone,
                                              pt1=top_left,
                                              pt2=bottom_right,
                                              color=colour,
                                              thickness=2,
                                              )
            return image_w_rectangle
        else:
            raise Exception('no roi has been selected yet')

    def show_rectangle(self,
                       image: np.ndarray = None) -> np.ndarray:
        """draw and display a rectangle containing the roi on an image"""
        rectangle_image = self.rectangle_image(image=image)
        display(image=rectangle_image, window_name=f'{self.name} rectangle')
        return rectangle_image

    def extract_rectangle(self,
                          *images: np.ndarray,
                          ) -> Union[List[np.ndarray], np.ndarray]:
        """Extract a rectangle from an image that contains the roi; essentially crop and return a cropped
        rectangular image that contains the roi"""
        (x, y, width, height) = self.rectangle
        if len(images) == 1:
            image = images[0]
            extracted_rectangle = image[y:y + height, x:x + width]
            return extracted_rectangle
        extracted_rectangles = []
        for image in images:
            extracted_rectangle = image[y:y+height, x:x+width]
            extracted_rectangles.append(extracted_rectangle)
        return extracted_rectangles

    def roi(self,
            image: np.ndarray = None) -> np.ndarray:
        """draw the roi on an image"""
        points = self.points
        white = (255)
        if points is not None:
            if image is None:
                clone = ROI.blank_3d_mask(height=self.select_height,
                                          width=self.select_width)
                colour = white
            else:
                clone = image.copy()
                colour = _roi_colour
            points = np.array([points])
            roi = cv2.polylines(img=clone,
                                pts=[points],
                                isClosed=True,
                                color=colour,
                                thickness=2,
                                )
            return roi
        else:
            raise Exception('no roi has been selected yet')

    def show_roi(self,
                 image: np.ndarray = None) -> np.ndarray:
        """draw and display the roi on an image"""
        roi_image = self.roi(image=image)
        display(image=roi_image, window_name=f'{self.name} roi')
        return roi_image

    def mask_image(self,
                   image: np.ndarray = None) -> np.ndarray:
        """
        Return an image where the mask has been applied to it; all pixels outside of the mask are black. The mask is
        created based on the roi

        :param image:
        :return:
        """
        if self.mask is not None:
            if image is None:
                clone = ROI.blank_mask(height=self.select_height,
                                       width=self.select_width)
                masked_image = cv2.bitwise_or(src1=clone,
                                              src2=self.mask)
                masked_image = np.dstack([masked_image, masked_image, masked_image])
            else:
                clone = image.copy()
                masked_image = cv2.bitwise_or(src1=clone,
                                              src2=clone,
                                              mask=self.mask)
            return masked_image
        else:
            raise Exception('no roi has been selected yet')

    def show_mask(self,
                  image: np.ndarray = None) -> np.ndarray:
        """Create and display an image with a mask of the roi on it"""
        mask_image = self.mask_image(image=image)
        display(image=mask_image, window_name=f'{self.name} mask')
        return mask_image

    def save_data(self, file_path: Path):
        """Save data to a json file"""
        data = {'roi': self.data}
        with open(str(file_path), 'w') as file:
            json.dump(data, file)

    def load_data(self, file_path: Path):
        with open(str(file_path)) as file:
            data = json.load(file)
        self.data = data['roi']


class RectangleROI(ROI):
    def __init__(self,
                 name: str,
                 ):
        super().__init__(name=name,
                         roi_type=self.rectangle_roi)

    def select(self,
               image,
               window_name: str = None,
               ) -> List[List[int]]:
        """
        Press space bar to confirm selection

        :param image:
        :param str, window_name:
        :return:
        """
        window_name = window_name if window_name is not None else 'Select rectangular ROI. Space bar to select.'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        rectangle = cv2.selectROI(windowName=window_name,
                                  img=image,
                                  fromCenter=False,
                                  showCrosshair=True)
        (x, y, width, height) = rectangle
        self.rectangle = rectangle
        win_height, win_width = height_width(image=image)
        p1 = [x, y]
        p2 = [x, y + height]
        p3 = [x + width, y + height]
        p4 = [x + width, y]
        points = [p1, p2, p3, p4]
        self.points = points
        self.select_height = win_height
        self.select_width = win_width
        cv2.destroyWindow(window_name)
        return points


class PolygonROI(ROI):
    def __init__(self,
                 name: str,
                 ):
        super().__init__(name=name,
                         roi_type=self.polygon_roi)

    def select(self,
               image,
               window_name: str = None,
               ):
        # todo
        """
        Press space bar to confirm selection

        :param image:
        :param str, window_name:
        :return:
        """
        window_name = window_name if window_name is not None else """Select polygonal ROI. Space bar to select. R to \
                                                                  reset points"""
        image = image.copy()
        clone = image.copy()
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        roi_colour = _roi_colour
        line_width = 2
        points_tuple = []
        def mouse_click(event, x, y, flags, param):
            # if left mouse button clicked, record the starting(x, y) coordinates
            if event is cv2.EVENT_LBUTTONDOWN:
                points_tuple.append((x, y))
            if event is cv2.EVENT_LBUTTONUP:
                if len(points_tuple) >= 2:
                    # if there are a total of two or more clicks made on the image, draw a line to connect the dots
                    # to easily visualize the region of interest that has been created so far
                    pt_1 = points_tuple[-2]
                    pt_2 = points_tuple[-1]
                    cv2.line(image, pt_1, pt_2, roi_colour, line_width)
            if len(points_tuple) > 0:
                # if only a single click has occurred so far, to still draw a single line that starts and ends at the
                # position (aka a dot) to allow visualization of where the user just clicked
                pt = points_tuple[-1]
                cv2.line(image, pt, pt, roi_colour, line_width)
                cv2.imshow(window_name, image)
        cv2.setMouseCallback(window_name, mouse_click)
        # loop until space bar is clicked
        while True:
            # display image, wait for a keypress
            cv2.imshow(window_name, image)
            key = cv2.waitKey(1) & 0xFF
            # if 'r' key is pressed, reset the roi
            if key == ord('r'):
                image = clone.copy()
                points_tuple = []
            # if 'space bar' key pressed break from while True loop
            elif key == ord(' '):
                cv2.destroyWindow(window_name)
                cv2.waitKey(500)
                break
        self.points = [[x, y] for (x, y) in points_tuple]  # convert list of tuple points to self.points format and set
        (x, y, width, height) = cv2.boundingRect(np.asarray(self.points))
        self.rectangle = (x, y, width, height)
        win_height, win_width = height_width(image=image)
        self.select_height = win_height
        self.select_width = win_width
        return self.points


class ROIManager:
    roi_types = ROI.roi_types

    def __init__(self):
        self._rois: Dict[str, ROI] = {}
        self._select_width: int = None  # width of the image used to select the roi
        self._select_height: int = None  # height of the image used to select the roi
        self._data: Dict[str, Union[Dict, int]] = {}

    @property
    def rois(self) -> Dict[str, ROI]:
        """Dictionary of roi names: ROI object"""
        return self._rois

    @rois.setter
    def rois(self,
             value):
        self._rois = value

    @property
    def names(self) -> List[str]:
        """Return a list of all the names of all the rois"""
        names = list(self.rois.keys())
        return names

    @property
    def select_width(self) -> int:
        """width of the image used to select the roi"""
        return self._select_width

    @select_width.setter
    def select_width(self,
                     value: int):
        self._select_width = value

    @property
    def select_height(self) -> int:
        """height of the image used to select the roi"""
        return self._select_height

    @select_height.setter
    def select_height(self,
                      value: int):
        self._select_height = value

    @property
    def data(self) -> Dict[str, Union[Dict, int]]:
        """Nested dictionary that contains the necessary data to be able to save and set an ROI manager and all its
        selected ROIs"""
        data = {'rois': {},
                'select_height': self.select_height,
                'select_width': self.select_width,
                }
        data_rois = {}
        rois = list(self.rois.values())
        for roi in rois:
            name = roi.name
            add_data = {'name': name,
                        'roi_type': roi.roi_type,
                        'points': roi.points,
                        'rectangle': roi.rectangle,
                        'select_height': roi.select_height,
                        'select_width': roi.select_width,
                        }
            data_rois[name] = add_data
        data['rois'] = data_rois
        self._data = data
        return self._data

    @data.setter
    def data(self,
             value: Dict[str, Union[Dict, int]]):
        self.rois = {}
        self.select_height = value['select_height']
        self.select_width = value['select_width']
        roi_data = list(value['rois'].values())
        for index, data in enumerate(roi_data):
            name = data['name']
            roi_type = data['roi_type']
            roi = ROI(name=name, roi_type=roi_type)
            roi.points = data['points']
            roi.rectangle = data['rectangle']
            roi.select_height = data['select_height']
            roi.select_width = data['select_width']

            self.rois[name] = roi

    def roi(self, roi_name) -> ROI:
        if roi_name not in self.names:
            return None
        roi = self.rois[roi_name]
        return roi

    def add_roi(self,
                image=None,
                roi_type: str = None,
                name: str = None,
                window_name: str = None,
                roi: ROI = None,
                ) -> ROI:
        """
        If roi is None, show an image and make the user interactively select where the roi is and give the roi
        the passed in name. If roi is not None, add that roi into the rois property

        :param str, roi_type: one of roi_types to create and add, one of roi_types
        :param str, name: name to give an roi to create and add
        :param image: image used to interactively select the roi
        :param window_name: str to give specific instructions to select the roi
        :param roi: ROI instance
        :return:
        """
        if roi is None:
            if image is None or roi_type is None or name is None:
                raise ValueError('Must provide image, roi_type, and name if roi is not given')
            if roi_type == _rectangle_roi:
                roi = RectangleROI(name=name)
            elif roi_type == _polygon_roi:
                roi = PolygonROI(name=name)
            roi.select(image=image, window_name=window_name)
            self.rois[name] = roi
        else:
            self.rois[roi.name] = roi
        self.select_height = roi.select_height
        self.select_width = roi.select_width
        return roi

    def remove_rois(self,
                    *roi_names: str
                    ) -> Union[ROI, Dict[str, ROI]]:
        rois = {}
        for roi_name in roi_names:
            roi = self.rois.pop(roi_name)
            rois[roi_name] = roi

        if len(rois) == 1:
            roi_name, roi = rois.popitem()
            return roi
        else:
            return rois

    def rois_image(self,
                   image: np.ndarray = None) -> np.ndarray:
        """Return an image with all the rois drawn on the image"""
        if image is None:
            height = self.select_height
            width = self.select_width
            if height is None:
                raise Exception('no roi has been selected yet')
            clone = ROI.blank_3d_mask(height=height, width=width)
        else:
            clone = image.copy()
        rois = list(self.rois.values())
        rois_image = clone
        for roi in rois:
            rois_image = roi.roi(image=rois_image)
        return rois_image

    def show_rois(self,
                  image: np.ndarray = None) -> np.ndarray:
        """Return and show a image with all the rois drawn on the image"""
        rois_image = self.rois_image(image)
        display(image=rois_image, window_name=f'rois')
        return rois_image

    def mask_image(self,
                   image: np.ndarray = None) -> np.ndarray:
        """Return an image where a mask has been applied to it; all pixels outside of the mask are black. The mask
        will only show areas of the image that are encapsulated by an roi"""
        rois = list(self.rois.values())
        height = self.select_height
        width = self.select_width
        mask_image = ROI.blank_3d_mask(height=height, width=width)
        if image is None:
            full_mask = ROI.full_3d_mask(height=height, width=width)
            image = full_mask
        clone = image.copy()
        for roi in rois:
            roi_mask_image = roi.mask_image(image=clone)
            mask_image = cv2.bitwise_or(src1=mask_image,
                                        src2=roi_mask_image,
                                        )
        return mask_image

    def show_mask(self,
                  image: np.ndarray = None) -> np.ndarray:
        """Return and show an image where a mask has been applied to it; all pixels outside of the mask are black. The
        mask will only show areas of the image that are encapsulated by an roi"""
        mask_image = self.mask_image(image)
        display(image=mask_image, window_name=f'mask')
        return mask_image

    def save_data(self, file_path: Path):
        """Save data to a json file"""
        data = {'roi_manager': self.data}
        with open(str(file_path), 'w') as file:
            json.dump(data, file)

    def load_data(self, file_path: Path):
        with open(str(file_path)) as file:
            data = json.load(file)
        self.data = data['roi_manager']

