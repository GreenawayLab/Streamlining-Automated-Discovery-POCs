from typing import Tuple, Union
from pathlib import Path
import time
from datetime import datetime
import threading
import numpy as np
import cv2
import warnings
from hein_utilities.runnable import Runnable
import logging
import atexit


_cv = {  # controlled variables for adjusting camera values
    'frame_width': 3,
    'frame_height': 4,
    'brightness': 10,
    'contrast': 11,
    'saturation': 12,
    'exposure': 15,
}


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Camera(Runnable):
    """
    Way to control a laptop webcam or usb webcam
    """
    def __init__(self,
                 cam=None,  # leave in for backwards compatibility
                 port=0,
                 save_folder: Path = None,
                 save_folder_location: str = None,  # leave in for backwards compatibility
                 datetime_string_format: str = '%Y_%m_%d_%H_%M_%S_%f',
                 ):
        """
        :param cam: left in for backwards compatibility, use port instead
        :param save_folder_location: left in for backwards compatibility, use save_folder instead
        :param int, port: 0, or 1 (or a higher number depending on the number of cameras connected). The camera you
            want to use to take a picture with. 0 if its the only camera, 1 if it is a secondary camera.
        :param Path, save_folder: location to a folder to save all images to. Will be created if it doesnt exist
        :param str, datetime_string_format: datetime format to name all images captured and saved. note that if
            multiple images are saved with the same file path they will be overwritten, so you may need to alter the
            granularity of the time format to suit your needs
        """
        """ warnings.warn(
            'the input parameters cam and save_folder_location are no longer used, use port and save_folder instead',
            FutureWarning,
        )"""
        Runnable.__init__(self, logger=logger)
        self._lock = threading.Lock()
        if cam is not None:
            port = cam  # todo left in for backwards compatibility
        self.port = port  # int, the camera to use
        self.vc = None
        self.connect()
        self.image_width = self.vc.get(3)  # float
        self.image_height = self.vc.get(4)  # float
        

        self._last_frame = None
        self._last_photo: Tuple[str, np.ndarray] = (None, None)  # date_time image was taken, image

        self.save_recording_photos: bool = False  # flag whether, when running the camera in the background, images should be
        # saved or not
        self.time_interval: float = 0  # time interval to wait between capturing images when recording (the run fn)
        # in seconds

        self.video_writer = None
        self.video_writer_path: str = None  # path to save a video of the camera stream

        # create folder to save all images if it doesnt already exist
        if save_folder_location is not None and save_folder is None:
            save_folder = save_folder_location  # todo left in for backwards compatibility, should remove later
        if save_folder is not None:
            if type(save_folder) is str:
                save_folder = Path(save_folder)
            if save_folder.exists() is False:
                save_folder.mkdir()
        self.save_folder: Path = save_folder  # folder to save images to

        self.datetime_string_format = datetime_string_format

        atexit.register(self.stop_recording)

        self.take_photos(n=3, save_photo=False)

    @property
    def last_photo(self) -> Tuple[str, np.ndarray]:
        return self._last_photo

    @last_photo.setter
    def last_photo(self, value: Tuple[str, np.ndarray]):
        self._last_photo = value

    @property
    def last_frame(self) -> np.ndarray:
        return self._last_frame

    @last_frame.setter
    def last_frame(self, value) -> np.ndarray:
        self._last_frame = value

    def connect(self):
        try:
            self.vc = cv2.VideoCapture(self.port)
            #self.vc = cv2.VideoCapture(self.port, cv2.CAP_DSHOW)

            self.vc.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # turn auto-exposure off
            self.vc.set(cv2.CAP_PROP_EXPOSURE, 10)

            # https://github.com/opencv/opencv/issues/9738 - 0.25 for off, 0.75 for on, after turning it off,
            # exposure needs to be manually set - https://github.com/yuripourre/v4l2-ctl-opencv/issues/6
            #self.vc.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # turn off autofocus

        except:
            print(f'could not connect to camera')

    def disconnect(self):
        self.vc.release()
        self.vc = None

    def reset(self):
        warnings.warn(
            'reset doesnt do anything anymore',
            DeprecationWarning,
        )
        pass

    def make_video_writer(self,
                          video_path: str,
                          fps=30):
        self.video_writer = None
        if video_path[-4:] != '.mp4':
            video_path = video_path + '.mp4'
        self.video_writer_path = video_path
        width = int(self.image_width)
        height = int(self.image_height)
        fourcc = 0x00000021  # mp4
        self.video_writer = cv2.VideoWriter(video_path,
                                            fourcc,
                                            fps,
                                            (width, height), True)
        return self.video_writer

    def release_video_writer(self):
        if self.video_writer is not None:
            self.video_writer.release()
        video_path = str(self.video_writer_path)
        self.video_writer_path = None
        self.video_writer = None
        return video_path

    def frame(self):
        with self._lock:
            _, frame = self.vc.read()
            _, frame = self.vc.read()
            self.last_frame = frame
        return frame

    def take_photo(self,
                   save_photo=True,
                   name: Union[str, Path] = None):
        """
        Take a picture with the camera. If save photo is true and no name is given, save the photo taken with the
        time as the file name in the objects save folder path if one is set. If name is of type string and the save
        folder path is set, save the photo with the specified name in the save folder path. If name is of type path,
        save the photo at the specified path

        :param save_photo: if a folder to save the photos was set, then if this parameter is true,
            save the photo to the folder
        :param name: if name is a path, save the image at the specified path, if name is a string save image at the
            save folder with the specified name (name must have file type specified for both options). If name is a
            string, save_photo must be true

        :return: frame is a numpy.ndarray, the image taken by the camera as a BGR image
        """
        frame = None
        while frame is None:
            # take a picture with a camera
            frame = self.frame()
            if frame is None:
                self.disconnect()
                self.connect()
        curr_time = datetime.now()
        time_as_str = curr_time.strftime(self.datetime_string_format)
        self.last_photo = (time_as_str, frame)

        if (self.save_folder is not None and save_photo is True) or (self.save_folder is not None and name is not None) or type(name) == type(Path()):
            if name is None:
                name = f'{time_as_str}.png'
            if type(name) == str:
                path_to_save_image = str(self.save_folder.joinpath(name))
            if type(name) == type(Path()):
                path_to_save_image = str(name)
            cv2.imwrite(path_to_save_image, frame)
            #cv2.imwrite(path_to_save_image, frame)
        
        return frame

    def take_picture(self, save_photo=True):
        warnings.warn(
            'take_picture has been deprecated, use take_photo instead',
            DeprecationWarning,
            stacklevel=2,
        )
        frame = self.take_photo(save_photo=save_photo)
        return frame

    def take_photos(self,
                    n: int = 1,
                    save_photo: bool = True):
        """
        Take n number of photos and return a list of the photos

        :param int, n: number of photos to take
        :param bool, save_photo: whether or not to save the photos to disk

        :return: list of the photos taken
        """
        for i in range(n):
            if i == 0:
                images = [self.take_photo(save_photo=save_photo)]
            else:
                images.append(self.take_photo(save_photo=save_photo))
        return images

    def view(self):
        self.disconnect()
        # stream what the video sees
        video_capture = cv2.VideoCapture(self.port)
        #video_capture = cv2.VideoCapture(self.port, cv2.CAP_DSHOW)

        video_capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # turn the autofocus off

        while True:
            
            # capture frame-by-frame
            _, frame = video_capture.read()
            #frame = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)

            cv2.imshow('Live video - press q button to exit', frame)
            # if press the q button exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
        self.connect()

    def run(self):
        """
        Since the Camera class is a Runnable, this run function will run the camera in the background so it
        continuously captures frames
        :return:
        """
        while self.running:
            if self.time_interval > 0:
                time.sleep(self.time_interval)
            frame = self.take_photo(save_photo=self.save_recording_photos)
            if self.video_writer is not None:
                self.video_writer.write(frame)

    def start_recording(self,
                        video_path: str = None,
                        save_photos: bool = False,
                        ):
        """
        Start running the camera in the background, optionally save images captured by the camera to the save folder, or
        :param video_path: str, path to save a video of the stream. if left as none, no video will be created or saved
        :param save_photos: bool, whether to save the images taken to a folder or not
        :return:
        """
        if video_path is not None:
            self.make_video_writer(video_path=video_path)
        self.save_recording_photos = save_photos
        self.start()

    def stop_recording(self):
        if self.video_writer is not None:
            self.release_video_writer()
        self.stop()

