import json
from pathlib import Path
from typing import Dict, List, Union, Tuple
import uuid
import numpy as np
from heinsight.vision_utilities.colour_analysis import get_average_h_s_v_1d
from heinsight.vision_utilities.image_analysis import height_width
from heinsight.vision_utilities.roi import ROIManager, ROI
from heinsight.heinsight_utilities.reference import Reference, ReferenceManager


class HSVReference:
    def __init__(self, name: str = None):
        self._name = name
        if self.name is None:
            self.name = uuid.uuid4().hex
        self._h = None  # h reference value for the image
        self._h_ul = 5  # ul stands for upper limit; how much above the
        self._h_ll = 5  # ll stands for lower limit
        self._s = None
        self._s_ul = 5
        self._s_ll = 5
        self._v = None
        self._v_ul = 5
        self._v_ll = 5
        self._image = None  # hsv image captured/read in by opencv
        self._channels = ['h', 's', 'v']

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,
             value: str):
        self._name = value

    @property
    def h(self):
        return self._h

    @h.setter
    def h(self, value):
        self._h = value

    @property
    def h_ul(self):
        return self._h_ul

    @h_ul.setter
    def h_ul(self, value):
        self._h_ul = value

    @property
    def h_ll(self):
        return self._h_ll

    @h_ll.setter
    def h_ll(self, value):
        self._h_ll = value

    @property
    def s(self):
        return self._s

    @s.setter
    def s(self, value):
        self._s = value

    @property
    def s_ul(self):
        return self._s_ul

    @s_ul.setter
    def s_ul(self, value):
        self._s_ul = value

    @property
    def s_ll(self):
        return self._s_ll

    @s_ll.setter
    def s_ll(self, value):
        self._s_ll = value

    @property
    def v(self):
        return self._v

    @v.setter
    def v(self, value):
        self._v = value

    @property
    def v_ul(self):
        return self._v_ul

    @v_ul.setter
    def v_ul(self, value):
        self._v_ul = value

    @property
    def v_ll(self):
        return self._v_ll

    @v_ll.setter
    def v_ll(self, value):
        self._v_ll = value

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, value):
        """
        By setting the image, this sets the reference hsv values
        :param value: 1d array of an hsv image
        :return:
        """
        self._image = value
        self.h, self.s, self.v = get_average_h_s_v_1d(value)

    def good(self, *images, channel=None) -> Union[bool, List[bool]]:
        """
        Check whether, for the channel specified, if the average channel value for 1/more images lies within the
        upper and lower bounds set for that channel

        :param images: one more more 1d array of an hsv image
        :param str, channel: one of the values in self._channels
        :return:
        """
        if channel not in [*self._channels, None]:
            raise Exception("channel must be one of 'h', 's', v', or None")
        def h_good(h) -> bool:
            # print(h)
            return self.h - self.h_ll <= h <= self.h + self.h_ul
        def s_good(s) -> bool:
            return self.s - self.s_ll <= s <= self.s + self.s_ul
        def v_good(v) -> bool:
            return self.v - self.v_ll <= v <= self.v + self.v_ul
        def all_good(h, s, v):
            return h_good(h) and s_good(s) and v_good(v)
        good_list = []
        for image in images:
            h, s, v = get_average_h_s_v_1d(image)
            if channel == 'h':
                good_list.append(h_good(h))
            elif channel == 's':
                good_list.append(s_good(s))
            elif channel == 'v':
                good_list.append(v_good(v))
            elif channel is None:
                good_list.append(all_good(h, s, v))
        if len(good_list) == 1:
            return good_list[0]
        else:
            return good_list


class HSVReferenceManager:
    def __init__(self):
        self._hsv_references: Dict[str, HSVReference] = {}
        self._data: Dict[str, Dict] = {}

    @property
    def hsv_references(self) -> Dict[str, HSVReference]:
        """Dictionary, where the key is the name of the reference, and the value is the HSVReference object"""
        return self._hsv_references

    @hsv_references.setter
    def hsv_references(self,
                       value: Dict[str, Dict]):
        self._hsv_references = value

    @property
    def names(self) -> List[str]:
        """Return a list of all the names of all the hsv references"""
        names = list(self.hsv_references.keys())
        return names

    @property
    def data(self) -> Dict[str, Dict]:
        """Nested dictionary that contains the necessary data to be able to save and set an hsv reference manager
        object"""
        data = {'hsv_references': {},
                }
        data_hsv_references = {}
        hsv_references = list(self.hsv_references.values())
        for index, hsv_reference in enumerate(hsv_references):
            name = hsv_reference.name
            add_data = {'name': name,
                        'h': hsv_reference.h,
                        'h_ul': hsv_reference.h_ul,
                        'h_ll': hsv_reference.h_ll,
                        's': hsv_reference.s,
                        's_ul': hsv_reference.s_ul,
                        's_ll': hsv_reference.s_ll,
                        'v': hsv_reference.v,
                        'v_ul': hsv_reference.v_ul,
                        'v_ll': hsv_reference.v_ll,
                        'image': hsv_reference.image.tolist(),  # since image is a numpy array and is not
                        # json-serializable
                        }
            data_hsv_references[name] = add_data
        data['hsv_references'] = data_hsv_references
        self._data = data
        return self._data

    @data.setter
    def data(self,
             value: Dict[str, Dict]):
        hsv_reference_data = list(value['hsv_references'].values())
        for index, data in enumerate(hsv_reference_data):
            name = data['name']
            image = np.asarray(data['image'])
            hsv_reference = HSVReference(name=name)
            hsv_reference.h = data['h']
            hsv_reference.h_ul = data['h_ul']
            hsv_reference.h_ll = data['h_ll']
            hsv_reference.s = data['s']
            hsv_reference.s_ul = data['s_ul']
            hsv_reference.s_ll = data['s_ll']
            hsv_reference.v = data['v']
            hsv_reference.v_ul = data['v_ul']
            hsv_reference.v_ll = data['v_ll']
            hsv_reference.image = image

            self.hsv_references[name] = hsv_reference

            value['hsv_references'][name]['image'] = image

    def add_reference(self,
                      name: str,
                      image: np.ndarray,
                      h_ul: float = None,
                      h_ll: float = None,
                      s_ul: float = None,
                      s_ll: float = None,
                      v_ul: float = None,
                      v_ll: float = None,
                      ) -> HSVReference:
        reference = HSVReference(name=name)
        reference.image = image
        if h_ul is not None:
            reference.h_ul = h_ul
        if h_ll is not None:
            reference.h_ll = h_ll
        if s_ul is not None:
            reference.s_ul = s_ul
        if s_ll is not None:
            reference.s_ll = s_ll
        if v_ul is not None:
            reference.v_ul = v_ul
        if v_ll is not None:
            reference.v_ll = v_ll
        self.hsv_references[name] = reference
        return reference

    def remove_references(self,
                          *reference_names: str,
                          ) -> Union[HSVReference, Dict[str, HSVReference]]:
        references = {}
        for reference_name in reference_names:
            reference = self.hsv_references.pop(reference_name)
            references[reference_name] = reference

        if len(references) == 1:
            reference_name, reference = references.popitem()
            return reference
        else:
            return references

    def update_reference(self,
                         name: str,
                         image: np.ndarray = None,
                         h: float = None,
                         h_ul: float = None,
                         h_ll: float = None,
                         s: float = None,
                         s_ul: float = None,
                         s_ll: float = None,
                         v: float = None,
                         v_ul: float = None,
                         v_ll: float = None,
                         ) -> HSVReference:
        reference = self.hsv_references[name]
        if image is not None:
            reference.image = image
        if h is not None:
            reference.h = h
        if h_ul is not None:
            reference.h_ul = h_ul
        if h_ll is not None:
            reference.h_ll = h_ll
        if s is not None:
            reference.s = s
        if s_ul is not None:
            reference.s_ul = s_ul
        if v is not None:
            reference.v = v
        if s_ll is not None:
            reference.s_ll = s_ll
        if v_ul is not None:
            reference.v_ul = v_ul
        if v_ll is not None:
            reference.v_ll = v_ll
        self.hsv_references[name] = reference
        return reference


class HSVMatcher:
    def __init__(self):
        """
        There is one hsv associated with each roi
        """
        self._roi_manager = ROIManager()
        self._select_height: int = None
        self._select_width: int = None
        self._reference_image: np.ndarray = None
        self._hsv_reference_manager: HSVReferenceManager = HSVReferenceManager()

        self._save_path: Path = None

    @property
    def roi_manager(self) -> ROIManager:
        return self._roi_manager

    @property
    def reference_image(self) -> np.ndarray:
        """reference image to set the reference values for the hsv references"""
        return self._reference_image

    @reference_image.setter
    def reference_image(self,
                        value: np.ndarray):
        if self.select_width is not None:
            height, width = height_width(value)
            if height != self.select_height or width != self.select_width:
                raise Exception('Cannot update a new reference image if it doesnt have the same dimensions as the '
                                'previously set reference image')

        reference_names = self.hsv_reference_manager.names
        for reference_name in reference_names:
            roi = self.roi_manager.rois[reference_name]
            image_roi_rectangle = roi.extract_rectangle(value)
            self.hsv_reference_manager.update_reference(reference_name, image=image_roi_rectangle)
        self._reference_image = value

    @property
    def select_height(self) -> int:
        """height of the image used to select the roi(s)"""
        return self._select_height

    @select_height.setter
    def select_height(self,
                      value: int):
        self._select_height = value

    @property
    def select_width(self) -> int:
        """width of the image used to select the roi(s)"""
        return self._select_width

    @select_width.setter
    def select_width(self,
                     value: int):
        self._select_width = value

    @property
    def hsv_reference_manager(self):
        return self._hsv_reference_manager

    @property
    def save_path(self) -> Path:
        """Path to save the data as a json file"""
        return self._save_path

    @save_path.setter
    def save_path(self,
                  value: Path):
        file_name = value.name
        if file_name[-5:] != '.json':
            value = value.with_name(f'{file_name}.json')
        self._save_path = value

    def add_roi(self,
                roi_type: str,
                name: str,
                window_name: str = None,
                ) -> ROI:
        """

        :param str, roi_type: one of roi_types to create and add, one of roi_types
        :param str, name: name to give an roi to create and add
        :param window_name: str to give specific instructions to select the roi
        :return:
        """
        image = self.reference_image
        roi = self.roi_manager.add_roi(roi_type=roi_type,
                                       name=name,
                                       image=image,
                                       window_name=window_name,
                                       )
        self.select_height = roi.select_height
        self.select_width = roi.select_width
        image_roi_rectangle = roi.extract_rectangle(image)
        self.hsv_reference_manager.add_reference(name=name,
                                                 image=image_roi_rectangle)
        return roi

    def remove_rois(self,
                    *roi_names: str,
                    ) -> None:
        roi_names_to_remove: Tuple[str] = roi_names
        self.roi_manager.remove_rois(*roi_names_to_remove)
        self.hsv_reference_manager.remove_references(*roi_names_to_remove)

    def good(self,
             *images: np.ndarray,
             roi_name: str,
             channel: Union[str, None] = None
             ) -> Union[bool, List[bool]]:
        """
        Given an image, the same size as self.reference_image, check only in a rectangle that encompasses
        the roi to see if the hsv values are within the upper and lower limits of the corresponding hsv reference
        (corresponding meaning the roi and hsv reference share the same name)

        Return true if within the roi, the given image has an average hsv value for one or all channels within the
        upper and lower limits of the hsv reference

        :param roi_name:
        :param images: one or more images
        :param channel: 'h', 's', 'v', or None; if None, check if all h, s, and v are within the limits to be
            considered good
        :return:
        """
        roi = self.roi_manager.rois[roi_name]
        if type(images) is not list:
            images = list(images)
        image_roi_rectangles = roi.extract_rectangle(*images)
        hsv_reference: HSVReference = self.hsv_reference_manager.hsv_references[roi_name]
        if type(image_roi_rectangles) is not list:
            image_roi_rectangles = [image_roi_rectangles]
        matches = hsv_reference.good(*image_roi_rectangles,
                                     channel=channel)
        return matches

    def save_data(self, file_path=None):
        data = {'roi_manager': self.roi_manager.data,
                'select_height': self.select_height,
                'select_width': self.select_width,
                'reference_image': self.reference_image.tolist(),
                'hsv_reference_manager': self.hsv_reference_manager.data,
                'save_path': str(self.save_path),
                }
        if file_path is None:
            file_path = self.save_path
        else:
            if file_path[-5:] != '.json':
                file_path += '.json'
        try:
            with open(file_path, 'w') as file:
                json.dump(data, file)
        except PermissionError as e:
            pass

    def load_data(self, file_path):
        with open(file_path) as file:
            data = json.load(file)
        self.roi_manager.data = data['roi_manager']
        self.select_height = data['select_height']
        self.select_width = data['select_width']
        self.reference_image = np.asarray(data['reference_image'])
        self.hsv_reference_manager.data = data['hsv_reference_manager']
        self.save_path = Path(data['save_path'])