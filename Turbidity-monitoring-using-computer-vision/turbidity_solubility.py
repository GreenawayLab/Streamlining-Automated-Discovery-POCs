import time
from pathlib import Path
import cv2
from heinsight.vision_utilities.camera import Camera
from heinsight.vision.turbidity import TurbidityMonitor
from heinsight.vision_utilities.video_utilities import folder_of_images_to_video
import warnings
from typing import Union
from threading import Thread
import json
import matplotlib
# matplotlib.use('TkAgg')


class mxTurbidityMonitor:
    def __init__(self,
                 parent_path: str,
                 measurements_per_min: int = 12,
                 images_per_measurement: int = 25,
                 **tm_params,
                 ):

        self.tm_parameters = {
            'tm_n_minutes': 1,  # number of minutes the data needs to be stable in order to be determined as stable
            'tm_std_max': 1,
            'tm_sem_max': 1,
            'tm_upper_limit': 1,
            'tm_lower_limit': 10,
            'tm_range_limit': 2,
        }
        if tm_params is not None:
            for key in tm_params:
                self.tm_parameters[key] = tm_params[key]

        self._measurements_per_min = measurements_per_min
        self._time_between_measurements = int(60 / self._measurements_per_min)
        self._images_per_measurement = images_per_measurement

        self._vision_selection_json_path: Union[Path, None] = None
        self._experiment_number: int = 1
        self._parent_path: Path = Path(parent_path)
        self._folder: Union[Path, None] = None
        self._experiment_name: Union[str, None] = None
        self._camera_images_folder: Union[Path, None] = None
        self._graph_path: Union[Path, None] = None
        self._turbidity_save_path: Union[Path, None] = None
        self._info_json_path: Union[Path, None] = None
        self._video_path: Union[Path, None] = None

        self._camera: Union[Camera, None] = None
        self._turbidity_monitor: Union[TurbidityMonitor, None] = None

        self._running: bool = False
        self._pause_monitoring: bool = False
        self._monitor_thread: Union[Thread, None] = None

    def initialise_paths(self):
        self._folder: Path = self._make_experiment_folder()
        self._camera_images_folder: Path = self._folder.joinpath(f'{self._experiment_name}_images')
        self._vision_selection_json_path = str(self._folder.joinpath('vision_selections.json'))
        self._graph_path = self._folder.joinpath(f'{self._experiment_name}_turbidity_graph.png')
        self._turbidity_save_path: Path = self._folder.joinpath('turbidity_data')
        self._info_json_path: Path = self._folder.joinpath(f'{self._experiment_name}')
        self._video_path = self._folder.joinpath(f'{self._experiment_name}_turbidity_video.mp4')

    def select_roi(self):
        tm_n_images_for_dissolved_reference: int = 30
        vision_selection_path = str(self._folder.joinpath('vision_selections'))
        roi_cam = Camera(port=0, save_folder=self._camera_images_folder, datetime_string_format='%Y_%m_%d_%H_%M_%S_%f')
        vision_selection_tm = TurbidityMonitor(turbidity_monitor_data_save_path=vision_selection_path)

        image = roi_cam.take_photo(save_photo=False)
        print('Select normalisation region')
        vision_selection_tm.select_normalization_region(image)
        print('Select monitor region')
        vision_selection_tm.select_monitor_region(image)

        print('Select dissolved reference (taking photos, please wait)')
        dissolve_reference_images = roi_cam.take_photos(n=tm_n_images_for_dissolved_reference, save_photo=False)
        vision_selection_tm.set_dissolved_reference(*dissolve_reference_images, select_region=True)
        vision_selection_tm.turbidity_dissolved_reference *= 1.05  # can be changed to increase or decrease dissolved reference
        print(f'Dissolved reference set to {vision_selection_tm.turbidity_dissolved_reference}')
        vision_selection_tm.save_json_data()

        # save image with selected regions drawn on it
        selected_regions_image = vision_selection_tm.draw_regions(image=roi_cam.last_frame)
        annotated_regions_path = str(self._folder.joinpath(f'vision_selection.png'))
        cv2.imwrite(annotated_regions_path,
                    selected_regions_image,
                    )

        roi_cam.disconnect()
        del vision_selection_tm

    def load_roi_json(self, roi_path: Path):
        vision_selection_path = str(self._folder.joinpath('vision_selections'))
        roi_cam = Camera(port=0, save_folder=self._camera_images_folder, datetime_string_format='%Y_%m_%d_%H_%M_%S_%f')
        vision_selection_tm = TurbidityMonitor(turbidity_monitor_data_save_path=vision_selection_path)
        vision_selection_tm.load_data(json_path=roi_path)
        vision_selection_tm.save_json_data()

        # save annotated photo
        image = roi_cam.take_photo(save_photo=False)
        annotated_regions_path = str(self._folder.joinpath(f'vision_selection.png'))
        selected_regions_image = vision_selection_tm.draw_regions(image=image)
        cv2.imwrite(annotated_regions_path, selected_regions_image)
        roi_cam.disconnect()
        del vision_selection_tm

    def _make_experiment_folder(self) -> Path:
        parent_path = self._parent_path
        self._experiment_name = f'solubility_study_{self._experiment_number}'
        experiment_folder = Path.joinpath(parent_path, self._experiment_name)
        while True:
            if experiment_folder.exists():
                self._experiment_number += 1
                self._experiment_name = f'solubility_study_{self._experiment_number}'
                experiment_folder = Path.joinpath(parent_path, self._experiment_name)
            else:
                Path.mkdir(experiment_folder)
                break
        return experiment_folder

    def _save_current_graph(self):
        try:
            figure = self._turbidity_monitor.make_turbidity_over_time_graph_with_stable_visualization()
            figure.savefig(self._graph_path, bbox_inches='tight')
            time.sleep(0.3)
        except Exception as e:
            print(e)

    def _save_info_json(self):
        info_dict: dict = self.tm_parameters
        info_dict['measurements_per_min'] = self._measurements_per_min
        info_dict['images_per_measurement'] = self._images_per_measurement
        info_dict['final_state'] = self._turbidity_monitor.state
        with open(str(self._info_json_path), 'w') as json_file:
            json.dump(info_dict, json_file)

    @property
    def state(self) -> str:  # 'dissolved', 'saturated', 'stable', 'unstable_state'
        if self._turbidity_monitor is None:
            return 'not monitoring'
        else:
            return self._turbidity_monitor.state

    @property
    def dissolved(self) -> bool:
        if self.state == 'dissolved':
            return True
        else:
            return False

    def get_turbidity_data(self) -> tuple[list[float], list[float]]:
        x, y = self._turbidity_monitor.get_turbidity_data_for_graphing()
        return x, y

    def _monitor_loop(self):
        while self._running:
            time.sleep(self._time_between_measurements)
            if self._pause_monitoring:
                continue

            images = self._camera.take_photos(n=self._images_per_measurement)
            self._turbidity_monitor.add_measurement(*images)
            self._turbidity_monitor.save_data()
            self._save_current_graph()

    def _set_tm_parameters(self):
        if self._turbidity_monitor is None:
            raise RuntimeError('self._turbidity_monitor not created')
        tm_n = self._measurements_per_min * self.tm_parameters['tm_n_minutes']  # don't touch this parameter - no of measurements

        self._turbidity_monitor.std_max = self.tm_parameters['tm_std_max']
        self._turbidity_monitor.sem_max = self.tm_parameters['tm_sem_max']
        self._turbidity_monitor.upper_limit = self.tm_parameters['tm_upper_limit']
        self._turbidity_monitor.lower_limit = self.tm_parameters['tm_lower_limit']
        self._turbidity_monitor.range_limit = self.tm_parameters['tm_range_limit']
        self._turbidity_monitor.n = tm_n

    def start_monitoring(self, roi_path: str = None):
        if self._monitor_thread is not None:
            warnings.warn('Cannot start: monitoring in progress')
        else:
            self.initialise_paths()
            datetime_format = '%Y_%m_%d_%H_%M_%S_%f'
            
            if roi_path is not None:
                self.load_roi_json(Path(roi_path))
            else:
                self.select_roi()
                
            self._camera = Camera(port=0, save_folder=self._camera_images_folder,
                                  datetime_string_format=datetime_format)
            self._turbidity_monitor = TurbidityMonitor(turbidity_monitor_data_save_path=str(self._turbidity_save_path),
                                                       datetime_format=datetime_format)
            self._set_tm_parameters()
            self._save_info_json()

            self._turbidity_monitor.load_data(json_path=self._vision_selection_json_path)

            self._running = True
            self._pause_monitoring = False
            self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
            print(f'Start monitoring: {self._experiment_name}')
            self._monitor_thread.start()

    def stop_monitoring(self):
        if self._monitor_thread is None:
            warnings.warn('Not monitoring')
        else:
            print('Stop monitoring')
            self._running = False
            self._monitor_thread.join()
            self._monitor_thread = None
            
            self._save_info_json()

            print('Generating video...')
            fps = (self._images_per_measurement * self._measurements_per_min) / 60 * 10
            folder_of_images_to_video(str(self._camera_images_folder), str(self._video_path), fps=fps, display_image_name=True)

            self._camera.disconnect()
            self._camera = None
            self._turbidity_monitor = None

