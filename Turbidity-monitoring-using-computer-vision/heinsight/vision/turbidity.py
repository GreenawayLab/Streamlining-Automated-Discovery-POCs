import os
import json
from copy import copy, deepcopy
from typing import Union, Dict, List, Tuple
from datetime import timedelta
from datetime import datetime
import numpy as np
import pandas as pd
import cv2
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns
from scipy import stats
from heinsight.heinsight_utilities.data_analysis_visualization import stable_against_known, stable_against_unknown, \
    find_stable_against_unknown_custom_one_window, find_stable_against_known_custom_one_window, plot_plateau, \
    plot_axes, _colour_10_rgb, _colour_4_rgb
from hein_utilities.datetime_utilities import datetimeManager
from hein_utilities.json_utilities import create_json_file
from heinsight.vision_utilities.roi import ROIManager, PolygonROI, RectangleROI, ROI
from heinsight.vision_utilities.colour_analysis import bgr_to_hsv, get_average_h_s_v_1d, get_average_h_s_v_3d
import warnings
from heinsight.vision_utilities.camera import Camera




sns.set(palette='colorblind')
sns.set_context(
    'notebook',
    rc={},
)
sns.set_style(
    style="ticks",
    rc={
        'axes.spines.right': False,
        'axes.spines.top': False,
    },
)
_colour_palette = sns.color_palette()

_ls_solid = '-'
_ls_dash_dot = '-.'
_ls_dash = '--'
_ls_dot = ':'


class TurbidityMonitor:
    _unit_seconds = datetimeManager._unit_seconds
    _unit_minutes = datetimeManager._unit_minutes
    _unit_hours = datetimeManager._unit_hours
    _default_datetime_format = datetimeManager._default_datetime_format

    dissolved_state = 'dissolved'
    saturated_state = 'saturated'
    stable_state = 'stable'
    #stable_state = 'not_dissolved'
    unstable_state = 'unstable_state'

    monitor_region = 'monitor region'
    normalization_region = 'normalization region'
    dissolved_region = 'dissolved region'
    arbitrary_region = 'arbitrary region'
    saturated_region = 'saturated region'

    states = [dissolved_state, saturated_state, stable_state, unstable_state]

    def __init__(self,
                 turbidity_monitor_data_save_path: str,
                 datetime_format: str = _default_datetime_format,
                 ):
        """
        Class to monitor turbidity measurements

        :param str, turbidity_monitor_data_save_path: if provided, will be the location to save a any files produced
            by this class; the files that can be saved are a json file of the turbidity data collected or jpg of a
            turbidity over time graph. There should not be a file type associated
        :param str, datetime_format: format the the stamps for when a turbidity measurement was made
        """
        self._turbidity_monitor_data: Dict[Union[str: Dict]] = {}  # todo, add other meta data other than turbidity data?
        self.raw_turbidity_data: Dict[str: float] = {}  # dictionary of {time stamp: turbidity measurement} before
        # 'normalizing' the data with a reference region
        self.turbidity_data: Dict[str: float] = {}  # dictionary of {time stamp: turbidity measurement} after
        # normalizing with reference region
        self.turbidity_monitoring_start_time: datetime = datetime.now()

        # turbidity measurements for calibration/relative measurements
        self._turbidity_dissolved_reference: float = None
        self._turbidity_arbitrary_reference: float = None
        self._turbidity_saturated_reference: float = None
        self._state = self.unstable_state  # one of self.states
        self._last_state = None

        self._turbidity_monitor_data_save_path: str = turbidity_monitor_data_save_path
        self._turbidity_monitor_data_json_save_path: str = create_json_file(turbidity_monitor_data_save_path)

        self._datetime_format: str = datetime_format

        self._roi_manager: ROIManager = ROIManager()

        self._n: int = 40
        self._std_max: float = 0.05
        self._sem_max: float = 0.05
        self._relative_limits: bool = False
        self._upper_limit: float = 5
        self._lower_limit: float = 5
        self._range_limit: float = 0.1

        self.figure, self.axes = plt.subplots(nrows=1, ncols=1)
        # plt.close()
        self.x_axis_units = self._unit_minutes
        self._stable_plateau_points:  List[Tuple] = []  # The tuples are (x_ax_value_1, x_ax_value_2),
        # where x_ax_value_1 is the first value along the x axis where some stable region starts, and the second
        # value is where it ends

    @property
    def turbidity_monitor_data(self):
        return self._turbidity_monitor_data

    @turbidity_monitor_data.setter
    def turbidity_monitor_data(self,
                               value,
                               ):
        self._turbidity_monitor_data = value

    @property
    def roi_manager(self) -> ROIManager:
        return self._roi_manager

    @property
    def n(self) -> int:
        return self._n

    @n.setter
    def n(self,
          value: int,
          ):
        if isinstance(value, int) is False:
            raise TypeError('value must be of type int')
        self._n = value

    @property
    def std_max(self) -> float:
        return self._std_max

    @std_max.setter
    def std_max(self,
                value: float,
                ):
        self._std_max = value

    @property
    def sem_max(self) -> float:
        return self._sem_max

    @sem_max.setter
    def sem_max(self,
                value: float,
                ):
        self._sem_max = value

    @property
    def relative_limits(self) -> bool:
        return self._relative_limits

    @relative_limits.setter
    def relative_limits(self,
                        value: bool,
                        ):
        self._relative_limits = value

    @property
    def upper_limit(self) -> float:
        return self._upper_limit

    @upper_limit.setter
    def upper_limit(self,
                    value: float,
                    ):
        self._upper_limit = value

    @property
    def lower_limit(self) -> float:
        return self._lower_limit

    @lower_limit.setter
    def lower_limit(self,
                    value: float,
                    ):
        self._lower_limit = value

    @property
    def range_limit(self) -> float:
        return self._range_limit

    @range_limit.setter
    def range_limit(self,
                    value: float,
                    ):
        self._range_limit = value

    @property
    def datetime_format(self):
        return self._datetime_format

    @datetime_format.setter
    def datetime_format(self,
                        value: str):
        self._datetime_format = value

    @property
    def turbidity_dissolved_reference(self) -> float:
        return self._turbidity_dissolved_reference

    @turbidity_dissolved_reference.setter
    def turbidity_dissolved_reference(self,
                                      value: float,
                                      ):
        self._turbidity_dissolved_reference = value

    @turbidity_dissolved_reference.deleter
    def turbidity_dissolved_reference(self) -> None:
        self._turbidity_dissolved_reference = None

    @property
    def turbidity_arbitrary_reference(self) -> float:
        return self._turbidity_arbitrary_reference

    @turbidity_arbitrary_reference.setter
    def turbidity_arbitrary_reference(self,
                                      value: float,
                                      ):
        self._turbidity_arbitrary_reference = value

    @turbidity_arbitrary_reference.deleter
    def turbidity_arbitrary_reference(self) -> None:
        self._turbidity_arbitrary_reference = None

    @property
    def turbidity_saturated_reference(self) -> float:
        return self._turbidity_saturated_reference

    @turbidity_saturated_reference.setter
    def turbidity_saturated_reference(self,
                                      value: float,
                                      ):
        self._turbidity_saturated_reference = value

    @turbidity_saturated_reference.deleter
    def turbidity_saturated_reference(self) -> None:
        self._turbidity_saturated_reference = None

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self,
              value: str,
              ):
        if value not in self.states:
            raise TypeError(f'value must be one of: {self.states}')
        self._state = value

    @property
    def last_state(self) -> str:
        return self._last_state

    @last_state.setter
    def last_state(self,
                   value: str,
                   ):
        if value not in self.states:
            raise TypeError(f'value must be one of: {self.states}')
        self._last_state = value

    @property
    def stable_plateau_points(self) -> List[Tuple]:
        return self._stable_plateau_points

    @stable_plateau_points.setter
    def stable_plateau_points(self,
                              value: List[Tuple],
                              ):
        self._stable_plateau_points = value

    def state_changed_to_stable(self) -> bool:
        """
        Return True if the state changed to stable
        :return:
        """
        if self.state_changed() and self.state == self.stable_state and len(self.stable_plateau_points) == 1:
            return True
        if self.state_changed() and self.state == self.stable_state and len(self.stable_plateau_points) >= 2:
            second_last_plateau_point = self.stable_plateau_points[-2]
            second_last_plateau_start, second_last_plateau_stop = second_last_plateau_point
            last_plateau_point = self.stable_plateau_points[-1]
            last_plateau_point_start, _ = last_plateau_point
            if second_last_plateau_start < last_plateau_point_start <= second_last_plateau_stop:
                # this check is to make sure that the state is actually changing, and is not 'maintaining' stability;
                # maintaining because it is still within the stable regime of the previous plateau point
                return False
            else:
                return True
        else:
            return False

    def state_changed_to_unstable(self) -> bool:
        """
        Return True if the state changed to unstable
        :return:
        """
        if self.state_changed() and self.state == self.unstable_state and len(self.stable_plateau_points) > 0:
            last_plateau_point = self.stable_plateau_points[-1]
            _, last_plateau_point_stop = last_plateau_point
            x_values, _ = self.get_turbidity_data_for_graphing()
            last_x_value = x_values[-1]
            if last_plateau_point_stop < last_x_value:
                # this check is to make sure that the state is actually out of the the entire window of the last time
                # the graph was found to be stable
                return True
            else:
                return False
        else:
            return False

    def state_changed_to_dissolved(self,) -> bool:
        """
        Return True if the state changed to dissolved
        :return:
        """
        if self.state_changed() and self.state == self.dissolved_state:
            return True
        else:
            return False

    def state_changed_to_saturated(self) -> bool:
        """
        Return True if the state changed to saturated
        :return:
        """
        if self.state_changed() and self.state == self.saturated_state:
            return True
        else:
            return False

    def state_changed(self) -> bool:
        """
        True if the current state and the last state are difference
        :return:
        """
        if self.state != self.last_state:
            return True
        else:
            return False

    def update_state(self,
                     n: int = None,
                     std_max: float = None,
                     sem_max: float = None,
                     relative_limits: bool = None,
                     upper_limit: float = None,
                     lower_limit: float = None,
                     range_limit: float = None,
                     ):
        if n is None:
            n = self.n
        if std_max is None:
            std_max = self.std_max
        if sem_max is None:
            sem_max = self.sem_max
        if relative_limits is None:
            relative_limits = self.relative_limits
        if upper_limit is None:
            upper_limit = self.upper_limit
        if lower_limit is None:
            lower_limit = self.lower_limit
        if range_limit is None:
            range_limit = self.range_limit

        x_values, y_values = self.get_turbidity_data_for_graphing()
        if upper_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            upper_limit = upper_limit * total_range
        if lower_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            lower_limit = lower_limit * total_range
        if range_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            range_limit = range_limit * total_range

        self.last_state = deepcopy(self.state)
        current_state = self.check_state(n=n,
                                         std_max=std_max,
                                         sem_max=sem_max,
                                         upper_limit=upper_limit,
                                         lower_limit=lower_limit,
                                         range_limit=range_limit,
                                         )
        self.state = current_state

    def check_state(self,
                    n: int = None,
                    std_max: float = None,
                    sem_max: float = None,
                    relative_limits: bool = None,
                    upper_limit: float = None,
                    lower_limit: float = None,
                    range_limit: float = None,
                    ) -> str:
        """
        Check what state the system is in

        :param n: number of most recent turbidity measurements to use
        :param float, std_max: maximum standard deviation the data can have to be determined as stable
        :param float, sem_max: maximum standard error the data can have to be determined as stable
        :param bool, relative_limits: if true, then the upper, lower, and range limits, if their values are 0 < x < 1,
            will be relative to the range of all measurements so far
        :param float, upper_limit: if relative limits is False, it is the absolute turbidity measurement that the mean
            and mode of the data is allowed to be above the known reference (dissolved or saturated),
            for determining if the data has stabilized when checking against the dissolved or saturated reference.
            if the value is above 0 and less than 1 and relative limits is True, it is the percent of the range of all
            the turbidity data gathered so far (range = max - min turbidity value) that will be converted into
            absolute turbidity for use in this function
        :param float, lower_limit: if relative limits is False, it is the absolute turbidity measurement that the mean
            and mode of the data is allowed to be below the known reference (dissolved or saturated),
            for determining if the data has stabilized when checking against the dissolved or saturated reference.
            if the value is below 0 and less than 1 and relative limits is True, it is the percent of the range of all
            the turbidity data gathered so far (range = max - min turbidity value) that will be converted into
            absolute turbidity for use in this function
        :param float, range_limit: if relative limits is False, it is the absolute difference in
            terms ot the turbidity measurement, that the mode and mean of the data can have to be determined as
            stable, and the maximum allowed range the data can have, when checking for stability without some
            reference (dissolved or saturated) to compare to
            if the value is above 0 and less than 1 and relative limits is True, it is the percent of the range of
            all the turbidity data gathered so far (range = max - min turbidity value) that will be converted into
            absolute turbidity for use in this function
        :return: string representing the state of the system
        """
        if n is None:
            n = self.n
        if std_max is None:
            std_max = self.std_max
        if sem_max is None:
            sem_max = self.sem_max
        if relative_limits is None:
            relative_limits = self.relative_limits
        if upper_limit is None:
            upper_limit = self.upper_limit
        if lower_limit is None:
            lower_limit = self.lower_limit
        if range_limit is None:
            range_limit = self.range_limit

        x_values, y_values = self.get_turbidity_data_for_graphing()
        if upper_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            upper_limit = upper_limit * total_range
        if lower_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            lower_limit = lower_limit * total_range
        if range_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            range_limit = range_limit * total_range

        if self.dissolved(n=n,
                          std_max=std_max,
                          sem_max=sem_max,
                          upper_limit=upper_limit,
                          lower_limit=lower_limit,
                          ):
            state = self.dissolved_state
        elif self.saturated(n=n,
                            std_max=std_max,
                            sem_max=sem_max,
                            upper_limit=upper_limit,
                            lower_limit=lower_limit,
                            ):
            state = self.saturated_state
        elif self.stable(n=n,
                         range_limit=range_limit,
                         std_max=std_max,
                         sem_max=sem_max,
                         ):
            self.stable_plateau_points = self.get_stable_plateau_points(n=n,
                                                                        std_max=std_max,
                                                                        sem_max=sem_max,
                                                                        range_limit=range_limit,
                                                                        )
            state = self.stable_state
        else:
            state = self.unstable_state
        return state

    def get_stable_plateau_points(self,
                                  n: int = None,
                                  std_max: float = None,
                                  sem_max: float = None,
                                  relative_limits: bool = None,
                                  range_limit: float = None,
                                  r_min=None,
                                  slope_upper_limit=None,
                                  slope_lower_limit=None,
                                  ):
        x_values, y_values = self.get_turbidity_data_for_graphing()
        if relative_limits is None:
            relative_limits = self.relative_limits
        if range_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            range_limit = range_limit * total_range

        stable_plateau_points = find_stable_against_unknown_custom_one_window(
            x=x_values,
            y=y_values,
            window_size=n,
            range_limit=range_limit,
            std_max=std_max,
            sem_max=sem_max,
            r_min=r_min,
            slope_upper_limit=slope_upper_limit,
            slope_lower_limit=slope_lower_limit,
        )
        return stable_plateau_points

    def dissolved(self,
                  n: int = None,
                  std_max: float = None,
                  sem_max: float = None,
                  relative_limits: bool = None,
                  upper_limit: float = None,
                  lower_limit: float = None,
                  ) -> bool:
        """
        Check if the last n measurements mean and mode fall within dissolved reference - lower_limit and
        dissolved reference + upper limit, and if the standard deviation is les than std_max. If so, return True to
        indicate that the system is dissolved, and an sem less than sem_max

        :param n: number of most recent turbidity measurements to use
        :param float, std_max: maximum standard deviation the data can have to be determined as stable
        :param float, sem_max: maximum standard error the data can have to be determined as stable
        :param bool, relative_limits: if true, then the upper and lower limits, if their values are 0 < x < 1,
            will be relative to the range of all measurements so far
        :param float, upper_limit: if relative limits is False, it is the absolute turbidity measurement that the mean
            and mode of the data is allowed to be above the known reference (dissolved or saturated),
            for determining if the data has stabilized when checking against the dissolved or saturated reference.
            if the value is above 0 and less than 1 and relative limits is True, it is the percent of the range of all
            the turbidity data gathered so far (range = max - min turbidity value) that will be converted into
            absolute turbidity for use in this function
        :param float, lower_limit: if relative limits is False, it is the absolute turbidity measurement that the mean
            and mode of the data is allowed to be below the known reference (dissolved or saturated),
            for determining if the data has stabilized when checking against the dissolved or saturated reference.
            if the value is below 0 and less than 1 and relative limits is True, it is the percent of the range of all
            the turbidity data gathered so far (range = max - min turbidity value) that will be converted into
            absolute turbidity for use in this function
        :return:
        """
        if n is None:
            n = self.n
        if std_max is None:
            std_max = self.std_max
        if sem_max is None:
            sem_max = self.sem_max
        if relative_limits is None:
            relative_limits = self.relative_limits
        if upper_limit is None:
            upper_limit = self.upper_limit
        if lower_limit is None:
            lower_limit = self.lower_limit

        if len(list(self.turbidity_data.values())) < n or self.turbidity_dissolved_reference is None:
            return False
        x_values, y_values = self.get_turbidity_data_for_graphing()
        if upper_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            upper_limit = upper_limit * total_range
        if lower_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            lower_limit = lower_limit * total_range
        last_n_x_values = x_values[-n:]
        last_n_y_values = y_values[-n:]

        dissolved_reference = self.turbidity_dissolved_reference
        at_dissolved: bool = stable_against_known(x=last_n_x_values,
                                                  y=last_n_y_values,
                                                  known=dissolved_reference,
                                                  upper_limit=upper_limit,
                                                  lower_limit=lower_limit,
                                                  std_max=std_max,
                                                  sem_max=sem_max,
                                                  )

        stable: bool = stable_against_unknown(x=last_n_x_values,
                                              y=last_n_y_values,
                                              range_limit=upper_limit+lower_limit,
                                              std_max=std_max,
                                              sem_max=sem_max,
                                              )
        y_mean = np.mean(last_n_y_values)
        y_mode = stats.mode(last_n_y_values, keepdims=True)
        y_mode = y_mode.mode[0]
        if stable and y_mean < dissolved_reference and y_mode < dissolved_reference:
            below_dissolved = True
        else:
            below_dissolved = False

        return at_dissolved or below_dissolved

    def saturated(self,
                  n: int = None,
                  std_max: float = None,
                  sem_max: float = None,
                  relative_limits: bool = None,
                  upper_limit: float = None,
                  lower_limit: float = None,
                  ) -> bool:
        """
        Check if the last n measurements mean and mode fall within saturated reference - lower_limit and
        saturated reference + upper limit, and if the standard deviation is les than std_max. If so, return True to
        indicate that the system is saturated, and an sem less than sem_max

        :param n: number of most recent turbidity measurements to use
        :param float, std_max: maximum standard deviation the data can have to be determined as stable
        :param float, sem_max: maximum standard error the data can have to be determined as stable
        :param bool, relative_limits: if true, then the upper, and lower limits, if their values are 0 < x < 1,
            will be relative to the range of all measurements so far
        :param float, upper_limit: if relative limits is False, it is the absolute turbidity measurement that the mean
            and mode of the data is allowed to be above the known reference (dissolved or saturated),
            for determining if the data has stabilized when checking against the dissolved or saturated reference.
            if the value is above 0 and less than 1 and relative limits is True, it is the percent of the range of all
            the turbidity data gathered so far (range = max - min turbidity value) that will be converted into
            absolute turbidity for use in this function
        :param float, lower_limit: if relative limits is False, it is the absolute turbidity measurement that the mean
            and mode of the data is allowed to be below the known reference (dissolved or saturated),
            for determining if the data has stabilized when checking against the dissolved or saturated reference.
            if the value is below 0 and less than 1 and relative limits is True, it is the percent of the range of all
            the turbidity data gathered so far (range = max - min turbidity value) that will be converted into
            absolute turbidity for use in this function
        :return:
        """
        if n is None:
            n = self.n
        if std_max is None:
            std_max = self.std_max
        if sem_max is None:
            sem_max = self.sem_max
        if relative_limits is None:
            relative_limits = self.relative_limits
        if upper_limit is None:
            upper_limit = self.upper_limit
        if lower_limit is None:
            lower_limit = self.lower_limit

        if len(list(self.turbidity_data.values())) < n or self.turbidity_saturated_reference is None:
            return False
        x_values, y_values = self.get_turbidity_data_for_graphing()
        if upper_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            upper_limit = upper_limit * total_range
        if lower_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            lower_limit = lower_limit * total_range
        last_n_x_values = x_values[-n:]
        last_n_y_values = y_values[-n:]

        saturated_reference = self.turbidity_saturated_reference
        at_saturated: bool = stable_against_known(x=last_n_x_values,
                                                  y=last_n_y_values,
                                                  known=saturated_reference,
                                                  upper_limit=upper_limit,
                                                  lower_limit=lower_limit,
                                                  std_max=std_max,
                                                  sem_max=sem_max,
                                                  )
        stable: bool = stable_against_unknown(x=last_n_x_values,
                                              y=last_n_y_values,
                                              range_limit=upper_limit + lower_limit,
                                              std_max=std_max,
                                              sem_max=sem_max,
                                              )
        y_mean = np.mean(last_n_y_values)
        #y_mode = stats.mode(last_n_y_values)
        y_mode = stats.mode(last_n_y_values, keepdims=False)
        y_mode = y_mode.mode[0]
        if stable and y_mean > saturated_reference and y_mode > saturated_reference:
            above_sautrated = True
        else:
            above_sautrated = False

        return at_saturated or above_sautrated

    def stable(self,
               n: int = None,
               range_limit: float = None,
               relative_limits: bool = None,
               std_max: float = None,
               sem_max: float = None,
               ) -> bool:
        """

        :param n: number of most recent turbidity measurements to use
        :param bool, relative_limits: if true, then the range limit, if the value is 0 < x < 1,  will be relative to
        the range of all measurements so far
        :param float, range_limit: if the value is equal to or greater than 1, it is the absolute difference in
            terms ot the turbidity measurement, that the mode and mean of the data can have to be determined as
            stable, and the maximum allowed range the data can have, when checking for stability (any staility,
            not specifically at the point of dissolution or saturation). if the value is above 0 and less
            than 1, it is the percent of the range of all the turbidity data gathered so far (range = max - min
            turbidity value) that will be converted into absolute turbidity for use in this function
        :return: string representing the state of the system
        :param float, std_max: maximum standard deviation the data can have to be determined as stable
        :param float, sem_max: maximum standard error the data can have to be determined as stable
        :return:
        """
        if n is None:
            n = self.n
        if std_max is None:
            std_max = self.std_max
        if sem_max is None:
            sem_max = self.sem_max
        if relative_limits is None:
            relative_limits = self.relative_limits
        if range_limit is None:
            range_limit = self.range_limit

        if len(list(self.turbidity_data.values())) < n:
            return False
        x_values, y_values = self.get_turbidity_data_for_graphing()
        if range_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            range_limit = range_limit * total_range
        last_n_x_values = x_values[-n:]
        last_n_y_values = y_values[-n:]
        stable: bool = stable_against_unknown(x=last_n_x_values,
                                              y=last_n_y_values,
                                              range_limit=range_limit,
                                              std_max=std_max,
                                              sem_max=sem_max,
                                              )
        return stable

    def set_up_turbidity_monitor_data(self) -> None:
        self.turbidity_monitor_data = {
            'raw_turbidity_data': self.raw_turbidity_data,  # dictionary of {time stamp: turbidity measurement}
            'turbidity_data': self.turbidity_data,  # dictionary of {time stamp: turbidity measurement}
            'roi_manager': self.roi_manager.data,
            'turbidity_dissolved_reference': self.turbidity_dissolved_reference,  # float
            'turbidity_arbitrary_reference': self.turbidity_arbitrary_reference,  # float
            'turbidity_saturated_reference': self.turbidity_saturated_reference,  # float
        }

    def update_turbidity_monitor_data(self):
        self.set_up_turbidity_monitor_data()

    def reset_collected_turbidity_data(self) -> None:
        self.turbidity_data: Dict[str: float] = {}
        self.raw_turbidity_data: Dict[str: float] = {}

    def select_region_of_interest(self,
                                  image: np.ndarray,
                                  ) -> None:
        warnings.warn(
            'use select_monitor_region instead',
            DeprecationWarning,
        )
        self.select_monitor_region(image)

    def select_monitor_region(self,
                              image: np.ndarray,
                              ) -> None:
        """
        Let the user select a region of interest on an image that will be used for all the future turbidity
        measurements

        :param numpy.ndarray, image: numpy array that represents a 3 (bgr) channel/colour image
        :return:
        """
        window_name = 'Select region to track turbidity. Press "space bar" to choose, "r" to reset'
        self.roi_manager.add_roi(roi_type=ROI.polygon_roi,
                                 name=self.monitor_region,
                                 image=image,
                                 window_name=window_name,
                                 )

    def select_reference_region(self,
                                image: np.ndarray,
                                ) -> None:
        warnings.warn(
            'use select_normalization_region instead',
            DeprecationWarning,
        )
        self.select_normalization_region(image)

    def select_normalization_region(self,
                                    image: np.ndarray,
                                    ) -> None:
        """
        Let the user select a region on an image that will be used to 'normalize', in a way, all future turbidity
        measurements. The use of the normalization region is to account for changes in the images collected that
        affect the entire image, i.e. automatic changes in exposure and brightness of the entire image.

        :param numpy.ndarray, image: numpy array that represents a 3 channel/colour image
        :return:
        """
        window_name = 'Select region of to normalize turbidity measurements.  Press "space bar" to choose, "r" to reset'
        self.roi_manager.add_roi(roi_type=ROI.polygon_roi,
                                 name=self.normalization_region,
                                 image=image,
                                 window_name=window_name,
                                 )

    def reset_region_of_interest(self):
        warnings.warn(
            'use reset_monitor_region instead',
            DeprecationWarning,
        )
        self.reset_monitor_region()

    def reset_monitor_region(self) -> None:
        """
        Reset the region of interest selection

        :return:
        """
        self.roi_manager.roi(self.monitor_region).clear()

    def reset_reference_region(self):
        warnings.warn(
            'use reset_normalization_region instead',
            DeprecationWarning,
        )
        self.reset_normalization_region()

    def reset_normalization_region(self) -> None:
        """
        Reset the reference region selection

        :return:
        """
        self.roi_manager.roi(self.normalization_region).clear()

    def add_measurement(self,
                        *images: np.ndarray,
                        time: str = None,
                        ) -> None:
        """
        Make and add the turbidity measurement value for a given colour image/images into the turbidity monitor data
        attribute

        :param images: one or more numpy.ndarray arrays can be passed into this function that represent a 3
            channel/colour images (bgr)
        :param str, time: a string of when images was taken to be passed if the add_measurement function is being
            called retroactively/not in real time; the format of the string must be identical to
            self._datetime_format. If left as None, the time when this function is called, formatted following
            self._datetime_format is used (Leave as None if making measurements in real time)
        :return:
        """
        if time is None:
            t = datetime.now()
            t_str: str = t.strftime(self._datetime_format)
        if len(images) == 1:
            images = [images]
        if len(self.raw_turbidity_data.keys()) == 0:
            t = datetime.strptime(t_str, self._datetime_format)
            self.turbidity_monitoring_start_time = t
        raw_turbidity, turbidity = self.turbidity_measurement(*images, roi_name=self.monitor_region)
        self.update_raw_turbidity_data(turbidity_measurement=raw_turbidity, time=t_str)
        self.update_turbidity_data(turbidity_measurement=turbidity, time=t_str)
        self.update_state()

    def turbidity_measurement(self,
                              *images: np.ndarray,
                              roi_name: str,
                              ) -> (float, float):
        """
        Convert a 3d bgr image/images into a 3d hsv image/images then measure turbidity; in this case turbidity is
        taken as the average v value from an hsv image, within a region specified by the user. First blur the image
        as a pre-processing step
        If more than one images was passed into the function, take the average value of all those images and return a
        single result

        If there is a specific region is based on the roi name passed in.

        :param images: one or more numpy.ndarray arrays can be passed into this function that represent a 3
            channel/colour images (bgr)
        :param roi_name: one of self.monitor_region, normalization_region, dissolved_region, arbitrary_region,
            or saturated_region

        :return: (float, float), where the first float is the un-normalized turbidity measurement, and the second
            float is the normalized turbidity measurement
        """
        blur_kernel = (3, 3)
        def measure(*images) -> Union[List[np.ndarray], np.ndarray]:
            images = [cv2.GaussianBlur(image, blur_kernel, 0) for image in images]
            images = bgr_to_hsv(*images)
            if type(images) is not list:
                images = [images]
            hsv_for_images = get_average_h_s_v_3d(*images)
            if type(hsv_for_images) is not list:
                hsv_for_images = [hsv_for_images]
            v = [v for (h, s, v) in hsv_for_images]
            if len(v) == 1:
                return v[0]
            else:
                return v

        normalization_roi = self.roi_manager.roi(self.normalization_region)
        if normalization_roi.rectangle is None:
            raise Exception('A normalization region needs to be selected before a measurement can be made')
        roi = self.roi_manager.roi(roi_name)
        if roi.rectangle is None:
            raise Exception(f'A region for the {roi_name} has not been selected yet')
        if len(images) == 1:
            image = images[0]
            extracted_roi_rectangles = [roi.extract_rectangle(*image)]
            extracted_normalization_rectangles = [normalization_roi.extract_rectangle(*image)]
        else:
            extracted_roi_rectangles = roi.extract_rectangle(*images)
            extracted_normalization_rectangles = normalization_roi.extract_rectangle(*images)
        _roi_measurement = measure(*extracted_roi_rectangles)  # not normalized
        normalization_measurement = measure(*extracted_normalization_rectangles)

        if type(_roi_measurement) is list:
            roi_measurement = [(_roi/normalization) * 100 for _roi, normalization in zip(_roi_measurement, normalization_measurement)]
            turbidity = np.mean(roi_measurement)
            _turbidity = np.mean(_roi_measurement)
        else:
            turbidity = (_roi_measurement / normalization_measurement) * 100
            _turbidity = _roi_measurement
        return _turbidity, turbidity

    def set_arbitrary_reference(self,
                                *images: np.ndarray,
                                select_region: bool = True,
                                ):
        """
        Take an image/images, make a turbidity measurement on it, and set it as the arbitrary turbidity reference

        :param images: one or more numpy.ndarray arrays can be passed into this function that represent a 3
            channel/colour image (bgr)
        :return:
        """
        raise NotImplementedError

    def set_dissolved_reference(self,
                                *images: np.ndarray,
                                select_region: bool = True,
                                ):
        """
        Take an image/images, make a turbidity measurement on it, and set it as the dissolved turbidity reference

        :param images: one or more numpy.ndarray arrays can be passed into this function that represent a 3
            channel/colour images (bgr)
        :param bool, select_region: if True, the user must select a region on an image to use for setting the
            dissolved state reference

        :return:
        """
        if select_region is True:
            image = images[0]
            self.select_dissolved_reference_region(image=image)
        rois = list(self.roi_manager.rois.keys())
        if self.dissolved_region in rois:
            roi_name = self.dissolved_region
        else:
            # a region wasn't just selected or previously selected, then use the same region as the monitor region
            roi_name = self.monitor_region
        if len(images) == 1:
            images = [images]
        _, turbidity = self.turbidity_measurement(*images, roi_name=roi_name)
        self.turbidity_dissolved_reference = turbidity

    def select_dissolved_reference_region(self,
                                          image: np.ndarray,
                                          ) -> None:
        """
        Let the user select a region of interest on an image that will be used for determining the turbidity
        measurement for the dissolved reference

        :param numpy.ndarray, image: numpy array that represents a 3 (bgr) channel/colour image
        :return:
        """
        window_name = 'Select region to measure a dissolved reference. Press "space bar" to choose, "r" to reset'
        self.roi_manager.add_roi(roi_type=ROI.polygon_roi,
                                 name=self.dissolved_region,
                                 image=image,
                                 window_name=window_name,
                                 )

    def set_saturated_reference(self,
                                *images: np.ndarray,
                                select_region: bool = True,
                                ):
        """
        Take an image/images, make a turbidity measurement on it, and set it as the saturated turbidity reference

        :param images: one or more numpy.ndarray arrays can be passed into this function that represent a 3
            channel/colour images (bgr)
        :param bool, select_region: if True, the user must select a region on an image to use for setting the
            saturated state reference

        :return:
        """
        if select_region is True:
            image = images[0]
            self.select_saturated_reference_region(image=image)
        rois = list(self.roi_manager.rois.keys())
        if self.saturated_region in rois:
            roi_name = self.saturated_region
        else:
            # a region wasn't just selected or previously selected, then use the same region as the monitor region
            roi_name = self.monitor_region
        if len(images) == 1:
            images = [images]
        _, turbidity = self.turbidity_measurement(*images, roi_name=roi_name)
        self.turbidity_saturated_reference = turbidity

    def select_saturated_reference_region(self,
                                          image: np.ndarray,
                                          ) -> None:
        """
        Let the user select a region of interest on an image that will be used for determining the turbidity
        measurement for the saturated reference

        :param numpy.ndarray, image: numpy array that represents a 3 (bgr) channel/colour image
        :return:
        """
        window_name = 'Select region to measure a saturated reference. Press "space bar" to choose, "r" to reset'
        self.roi_manager.add_roi(roi_type=ROI.polygon_roi,
                                 name=self.saturated_region,
                                 image=image,
                                 window_name=window_name,
                                 )

    def draw_regions(self,
                     image,
                     roi: Union[str, List[str]] = None,
                     annotate=True):
        """
        Draw on an image all the rois that have been selected so far if roi is none, otherwise, draw only the
        specified rois. Optionally, also label the polygons

        :param numpy.ndarray, image: numpy array that represents a 3 (bgr) channel/colour image
        :param bool, annotate: if True, label all the polygons that are drawn
        :return:
        """
        if roi is None:
            roi = self.roi_manager.names
        if type(roi) == str:
            roi = [roi]
        if self.normalization_region in roi:
            image = self.draw_normalization_region(image, annotate)
        if self.dissolved_region in roi:
            image = self.draw_dissolved_region(image, annotate)
        if self.saturated_region in roi:
            image = self.draw_saturated_region(image, annotate)
        if self.monitor_region in roi:
            image = self.draw_monitor_region(image, annotate)
        return image

    def draw_monitor_region(self, image, annotate: bool = False):
        return self.draw_region(image, annotate, self.monitor_region)

    def draw_normalization_region(self, image, annotate: bool = False):
        return self.draw_region(image, annotate, self.normalization_region)

    def draw_dissolved_region(self, image, annotate: bool = False):
        return self.draw_region(image, annotate, self.dissolved_region)

    def draw_saturated_region(self, image, annotate: bool = False):
        return self.draw_region(image, annotate, self.saturated_region)

    def draw_region(self, image, annotate, region_name: str):
        image_copy = image.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        colour = (0, 255, 0)  # green
        rois = self.roi_manager.names
        if region_name in rois:
            roi = self.roi_manager.roi(region_name)
            if roi.rectangle is not None:  # roi has been set
                roi_name = roi.name
                image_copy = roi.roi(image_copy)
                if annotate is True:
                    (x, y, width, height) = roi.rectangle
                    middle = int(x + (width / 2))
                    text_position = (middle, y - 20)
                    cv2.putText(image_copy, roi_name, text_position, font, font_scale, colour)
        return image_copy

    def update_raw_turbidity_data(self,
                                  turbidity_measurement: float,
                                  time: str,
                                  ) -> None:
        """
        Add the turbidity measurement into the raw turbidity data dictionary attribute

        :param float, turbidity_measurement: a single turbidity measurement
        :param str, time: a string of when an image was analyzed in format of self._datetime_format

        :return:
        """
        self.raw_turbidity_data[time] = turbidity_measurement

    def update_turbidity_data(self,
                              turbidity_measurement: float,
                              time: str,
                              ) -> None:
        """
        Add the turbidity measurement into the turbidity data dictionary attribute

        :param float, turbidity_measurement: a single turbidity measurement
        :param str, time: a string of when an image was analyzed in format of self._datetime_format

        :return:

        """
        self.turbidity_data[time] = turbidity_measurement

    def save_data(self):
        self.save_json_data()
        self.save_csv_data()

    def save_json_file(self):
        warnings.warn(
            'save_json_file has been deprecated, use save_json_data instead',
            DeprecationWarning,
            stacklevel=2,
        )
        self.save_json_data()

    def save_json_data(self) -> None:
        """
        Saves the turbidity monitor data to a json file

        :return:
        """
        self.set_up_turbidity_monitor_data()
        data_to_save = self.turbidity_monitor_data.copy()
        if self._turbidity_monitor_data_json_save_path is not None:
            try:
                with open(self._turbidity_monitor_data_json_save_path, 'w') as file:
                    json.dump(data_to_save, file)
            except PermissionError as e:
                pass
        else:
            raise AttributeError('turbidity_monitor_data_json_save_path has not been specified')

    def load_data(self, json_path):
        """
        Loads the turbidity monitor data from a json file

        :return:
        """
        with open(json_path) as file:
            data = json.load(file)
            self.roi_manager.data = data['roi_manager']
            self.raw_turbidity_data = data['raw_turbidity_data']
            self.turbidity_data = data['turbidity_data']
            self.turbidity_dissolved_reference = data['turbidity_dissolved_reference']
            self.turbidity_arbitrary_reference = data['turbidity_arbitrary_reference']
            self.turbidity_saturated_reference = data['turbidity_saturated_reference']

            self.update_turbidity_monitor_data()

    def save_csv_file(self, rounding=None):
        warnings.warn(
            'save_csv_data has been deprecated, use save_csv_data instead',
            DeprecationWarning,
            stacklevel=2,
        )
        self.save_csv_data(rounding)
        print('csv file saved')

    def save_csv_data(self, rounding=None):
        csv_path = self._turbidity_monitor_data_save_path + '.csv'
        timestamp_string = list(self.turbidity_data.keys())
        timestamp_datetime = datetimeManager.str_to_datetime(*timestamp_string, datetime_format=self._datetime_format)
        time_s = datetimeManager.relative_datetime(timestamp_datetime, datetimeManager._unit_seconds, rounding)
        time_min = datetimeManager.relative_datetime(timestamp_datetime, datetimeManager._unit_minutes, rounding)
        time_hour = datetimeManager.relative_datetime(timestamp_datetime, datetimeManager._unit_hours, rounding)
        turbidity_data = list(self.turbidity_data.values())
        df = pd.DataFrame(data=[timestamp_string, time_s, time_min, time_hour, turbidity_data]).T
        df.columns = ['Timestamp', 'Time (s)', 'Time (min)', 'Time (hour)', 'Turbidity']
        try:
            df.to_csv(csv_path, sep=',', index=False)
        except PermissionError as e:
            pass

    def get_turbidity_data_for_graphing(self,
                                        x_axis_units: Union[_unit_seconds, _unit_minutes, _unit_hours] = None,
                                        ) -> List[List[float]]:
        if x_axis_units is None:
            x_axis_units = self.x_axis_units

        self.set_up_turbidity_monitor_data()

        datetime_format = self._datetime_format

        # getting the x values
        turbidity_data: Dict[str: float] = self.turbidity_data
        turbidity_time_data: Union[List[str], List[float]] = list(turbidity_data.keys())  # if data gets loaded in,
        # then it is possible that the data might already be in float form (loading in a previous turbidity monitor data
        # from the csv that gets when TurbidityMonitor.save_data() gets called)

        if type(turbidity_time_data[0]) is not float and type(turbidity_time_data[0]) is not int:
            # if in this block, then the data is in str format, and needs to be converted into float time values that
            # are relative to the first time point
            turbidity_time_data_as_datetime_objects: List[datetime] = datetimeManager.str_to_datetime(
                *turbidity_time_data,
                datetime_format=datetime_format,
            )

            # transform the time data so it is all relative to the first time point
            turbidity_time_data_relative: List[timedelta] = datetimeManager.relative_datetime(
                datetime_objects=turbidity_time_data_as_datetime_objects,
                units=x_axis_units,
            )
        else:
            # if in float format already, the the data must have been loaded in instead of taken in real time (which
            # is the case if the turbidity analysis is being done retroactively on a csv file from a previous
            # run), and it might not be necessary to do the conversion to relative time step because that time data
            # saved in the csv data file also gets saved in relative time, and can just loaded
            turbidity_time_data_relative = turbidity_time_data

        x_values: List[float] = turbidity_time_data_relative

        # getting the y values
        turbidity_measurement_data: List[float] = list(turbidity_data.values())
        y_values: List[float] = turbidity_measurement_data

        return x_values, y_values

    def make_and_save_turbidity_over_time_graph(self,
                                                x_axis_units: Union[_unit_seconds, _unit_minutes, _unit_hours] = None,
                                                scatter: bool = False,
                                                ) -> None:
        """
        Make and save a graph of turbidity data over time, with the x_axis being times relative to the first time
        point. Save the graph as a jpg file

        :param Union[_unit_seconds, _unit_minutes, _unit_hours], x_axis_units: the units that the x_axis should be
            in
        :param bool, scatter: whether to make a scatter plot or not
        :return:
        """
        x_values, y_values = self.get_turbidity_data_for_graphing()
        print(x_values, y_values)

        graph = self.make_turbidity_over_time_graph(
            x_values=x_values,
            y_values=y_values,
            x_axis_units=x_axis_units,
            scatter=scatter,
        )
        self.figure = graph
        self.save_graph(
        )
        return  graph

    def make_turbidity_over_time_graph(self,
                                       x_values: Union[List[datetime], List[timedelta]],
                                       y_values: List[float],
                                       x_axis_units: Union[_unit_seconds, _unit_minutes, _unit_hours] = None,
                                       scatter: bool = False,
                                       line: bool = True,
                                       ) -> Figure:
        """
        Make a graph of turbidity data over time, with the x_axis being times relative to the first time point

        :param List[datetime], x_axis_units: list of x values
        :param List[datetime], y_values: list of y values
        :param Union[_unit_seconds, _unit_minutes, _unit_hours], x_axis_units: the units that the x_axis should be in
        :param bool, scatter: whether to graph scatter points or not
        :param bool, line: whether to graph a line or not
        :return: matplotlib.figure.Figure, graph of turbidity over time as a matplotlib figure
        """
        if x_axis_units is None:
            x_axis_units = self.x_axis_units

        figure_title = 'Turbidity over time'

        # axis names
        x_axis_name = None
        if x_axis_units == self._unit_seconds:
            x_axis_name = 'Relative time (seconds)'
        elif x_axis_units == self._unit_minutes:
            x_axis_name = 'Relative time (minutes)'
        elif x_axis_units == self._unit_hours:
            x_axis_name = 'Relative time (hours)'

        y_axis_name = 'Turbidity'  # normalized turbidity technically

        axes = self.axes
        axes.clear()
        figure = self.figure
        figure.suptitle(figure_title)
        axes = plot_axes(axes=axes,
                         x=x_values,
                         y=y_values,
                         x_axis_label=x_axis_name,
                         y_axis_label=y_axis_name,
                         scatter=scatter,
                         line=line,
                         line_colour=_colour_10_rgb,
                         )

        return figure

    def make_turbidity_over_time_graph_with_stable_visualization(
            self,
            x_axis_units: Union[_unit_seconds, _unit_minutes, _unit_hours] = None,
            scatter=False,
            n: int = None,
            std_max: float = None,
            sem_max: float = None,
            relative_limits: bool = None,
            upper_limit: float = None,
            lower_limit: float = None,
            range_limit: float = None,
            r_min=None,
            slope_upper_limit=None,
            slope_lower_limit=None,
    ):
        if n is None:
            n = self.n
        if std_max is None:
            std_max = self.std_max
        if sem_max is None:
            sem_max = self.sem_max
        if relative_limits is None:
            relative_limits = self.relative_limits
        if upper_limit is None:
            upper_limit = self.upper_limit
        if lower_limit is None:
            lower_limit = self.lower_limit
        if range_limit is None:
            range_limit = self.range_limit

        x_values, y_values = self.get_turbidity_data_for_graphing()

        figure = self.make_turbidity_over_time_graph(
            x_values=x_values,
            y_values=y_values,
            x_axis_units=x_axis_units,
            scatter=scatter,
        )

        axes = figure.axes[0]

        y_max = max(y_values)
        y_min = min(y_values)

        if upper_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            upper_limit = upper_limit * total_range
        if lower_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            lower_limit = lower_limit * total_range
        if range_limit < 1 and relative_limits is True:
            total_range = max(y_values) - min(y_values)
            range_limit = range_limit * total_range

        # plateau_points are a set, of (start_x, end_x), used to know how to fill in the background of
        #a figure of
        # where the regions have stabilized/reached a plateau
        plateau_points_stable: List[Tuple] = find_stable_against_unknown_custom_one_window(
            x=x_values,
            y=y_values,
            window_size=n,
            range_limit=range_limit,
            std_max=std_max,
            sem_max=sem_max,
            r_min=r_min,
            slope_upper_limit=slope_upper_limit,
            slope_lower_limit=slope_lower_limit,
        )
        axes = plot_plateau(
            axes=axes,
            plateau_points=plateau_points_stable,
            y_min=y_min,
            y_max=y_max,
        )

        if self.turbidity_dissolved_reference is not None:
            plateau_points_dissolved: List[Tuple] = find_stable_against_known_custom_one_window(
                x=x_values,
                y=y_values,
                window_size=n,
                known=self.turbidity_dissolved_reference,
                upper_limit=upper_limit,
                lower_limit=lower_limit,
                std_max=std_max,
                sem_max=sem_max,
                r_min=r_min,
                slope_upper_limit=slope_upper_limit,
                slope_lower_limit=slope_lower_limit,
            )
            axes = plot_plateau(
                axes=axes,
                plateau_points=plateau_points_dissolved,
                y_min=y_min,
                y_max=y_max
            )

            axes.axhline(self.turbidity_dissolved_reference,
                         ls=_ls_dash,
                         color=_colour_4_rgb,
                         label='Dissolved reference',
                         )

        if self.turbidity_saturated_reference is not None:
            plateau_points_saturated: List[Tuple] = find_stable_against_known_custom_one_window(
                x=x_values,
                y=y_values,
                window_size=n,
                known=self.turbidity_saturated_reference,
                upper_limit=upper_limit,
                lower_limit=lower_limit,
                std_max=std_max,
                sem_max=sem_max,
                r_min=r_min,
                slope_upper_limit=slope_upper_limit,
                slope_lower_limit=slope_lower_limit,
            )
            axes = plot_plateau(
                axes=axes,
                plateau_points=plateau_points_saturated,
                y_min=y_min,
                y_max=y_max
            )

            axes.axhline(self.turbidity_saturated_reference,
                         ls=_ls_dash,
                         color=_colour_4_rgb,
                         label='Saturated reference',
                         )

        if self.turbidity_dissolved_reference is not None or self.turbidity_saturated_reference is not None:
            axes.legend(bbox_to_anchor=(1.04, 0.5), loc="center left")

        return figure

    def save_graph(self,
                   graph: Figure = None,
                   ) -> None:
        """
        Save the graph as a jpg, with the file name and location the same as the json data file

        :param matplotlib.figure.Figure, graph:
        :return:
        """
        if graph is None:
            graph = self.figure

        graph_save_path: str = self._turbidity_monitor_data_save_path
        graph_save_path = graph_save_path + '.png'

        try:
            graph.savefig(f'{graph_save_path}', bbox_inches='tight')
        except PermissionError as e:
            print('permission error')
            pass



