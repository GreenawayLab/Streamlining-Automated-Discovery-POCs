from typing import List, Union, Dict
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

_unit_seconds = 'seconds'
_unit_minutes = 'minutes'
_unit_hours = 'hours'


class TemporalData:
    time_s_column_heading = 'Time (s)'
    time_min_column_heading = 'Time (min)'
    time_hour_column_heading = 'Time (hour)'

    def __init__(self,
                 save_path: Path = Path.cwd().joinpath('temporal data'),
                 ):
        self._datetime_format = '%Y_%m_%d_%H_%M_%S_%f'
        self._data = pd.DataFrame(columns=[self.time_heading,
                                           self.time_s_column_heading,
                                           self.time_min_column_heading,
                                           self.time_hour_column_heading])
        if save_path.is_dir():
            save_path = save_path.joinpath('temporal data')
        self.save_path: Path = save_path

    @property
    def columns(self) -> List[str]:
        return self.data.columns.values.tolist()

    @property
    def data(self) -> pd.DataFrame:
        return self._data

    @data.setter
    def data(self,
             value: pd.DataFrame):
        self._data = value

    @property
    def datetime_format(self) -> str:
        return self._datetime_format

    @datetime_format.setter
    def datetime_format(self,
                        value: str):
        self._datetime_format = value

    # todo add a way so that when the datetime format is changed, all previous measurements datetime format are also
    #  changed

    @property
    def save_path(self) -> Path:
        return self._save_path

    @save_path.setter
    def save_path(self,
                  value: Path):
        self._save_path = value

    @property
    def csv_path(self) -> Path:
        file_name = self.save_path.name
        return self.save_path.with_name(f'{file_name}.csv')

    @property
    def time_heading(self) -> str:
        return f'Time ({self.datetime_format})'

    def save_csv(self, file_path: str = None):
        if file_path is None:
            file_path = self.csv_path
        try:
            self.data.to_csv(file_path, sep=',', index=False, mode='w')
        except PermissionError as e:
            print(f'failed to save {self.csv_path.absolute()}')

    def head(self,
             n: int,
             column: str = None) -> Union[pd.DataFrame, pd.Series]:
        """
        Return the first n rows of data

        :param n:
        :param column: str, column name
        :return:
        """
        data = self.data.head(n)
        if column is not None:
            data = data[column]
        return data

    def tail(self,
             n: int,
             column: str = None) -> Union[pd.DataFrame, pd.Series]:
        """
        Return the last n rows of data

        :param n:
        :param column: str, column name
        :return:
        """
        data = self.data.tail(n)
        if column is not None:
            data = data[column]
        return data

    def drop_tail(self,
                  n,
                  ):
        """Drop the last n rows of data"""
        self.data.drop(self.data.tail(n).index, inplace=True)

    def add_data(self,
                 data: Dict,
                 t: Union[None, str, datetime, int, float] = None,
                 units: Union[_unit_seconds, _unit_minutes, _unit_hours] = None,
                 ):
        """
        Add data to the data property at a specific time point. Either the time point for the data is in data
        dictionary for a key that is identical to this object's time_heading property, or t must be passed in (None
        is also a valid value for t)

        If t is None, then the time is the current time
        If t is a string, use that as it is; note that it should be in the same datetime format as this object's
        datetime_format property
        If t is given as a datetime object, it is formatted into a string based on the object's datetime_format property
        If t is a float, then units must be given. In this case, t is the number of units since the previous time
        point. The other time columns will be calculated accordingly. If this data will be the first row in
        the object's data property (if it is the first piece of data added), then the current time is used as the
        time point although

        :param dict, data: dictionary to be added into this object's data property (a Pandas dataframe)
        :param t: datetime or string formatted datetime or float
        :param units: if t is a float, units is the units for the time since the last time point
        :return:
        """
        n_rows = len(self.data)
        last_row_index = n_rows - 1
        first_row = self.head(1)
        last_row = self.tail(1)
        # add time to the data to be added dictionary
        if type(t) == float or type(t) == int:
            if units is None:
                raise ValueError('If a relative time (float value) is given, units must be too')
            if n_rows == 0:
                data[self.time_heading] = now_string(self.datetime_format)
            else:
                last_time: str = last_row[self.time_heading][last_row_index]
                last_time: datetime = str_to_datetime(last_time, datetime_format=self.datetime_format)
                if units == _unit_seconds:
                    s_since_last_time = t
                elif units == _unit_minutes:
                    s_since_last_time = t * 60.0
                elif units == _unit_hours:
                    s_since_last_time = t * 3600.0
                else:
                    raise ValueError('Units value not valid')
                data[self.time_heading] = (last_time + timedelta(seconds=s_since_last_time)).strftime(self.datetime_format)
        if self.time_heading not in data:
            if t is None:
                t = now_string(self.datetime_format)
            if type(t) is not str:
                t = t.strftime(self.datetime_format)
            data[self.time_heading] = t

        # at this point the data to be added should have a key that is identical to this object's time_heading
        # property and next is to figure out the values for the seconds, minutes, and hours columns
        if n_rows == 0:
            data[self.time_s_column_heading] = 0
            data[self.time_min_column_heading] = 0
            data[self.time_hour_column_heading] = 0
        else:
            first_time: str = first_row[self.time_heading][0]
            first_time: datetime = str_to_datetime(first_time, datetime_format=self.datetime_format)
            last_time: str = last_row[self.time_heading][last_row_index]
            data_time: str = data[self.time_heading]
            if last_time == data_time:
                return
            data_time: datetime = str_to_datetime(data_time, datetime_format=self.datetime_format)
            times = [first_time, data_time]
            relative_s = relative_datetime(*times, units=_unit_seconds, rounding=3)
            relative_min = relative_datetime(*times, units=_unit_minutes, rounding=3)
            relative_hour = relative_datetime(*times, units=_unit_hours, rounding=3)
            data[self.time_s_column_heading] = relative_s
            data[self.time_min_column_heading] = relative_min
            data[self.time_hour_column_heading] = relative_hour

        self.data = self.data.append(data, ignore_index=True)


def now_string(string_format) -> str:
    """
    Get the current time from datetime.now() formatted as as a string according to the string_format property
    :return:
    """
    return datetime.now().strftime(string_format)


def str_to_datetime(*string_values: str,
                    datetime_format: str = None,
                    ) -> Union[datetime, List[datetime]]:
    """
    Convert a list of string values, back into datetime objects with a specific format; in this case, the string has
    to have been a datetime object that was converted into a string with the datetime_format that is passed in this
    function.

    Main use has previously been when files where timestamped, and when the file names need to be converted back
    into datetime objects in order to do calculations

    :param string_values: one or more (a list) of strings that can be converted into datetime objects
    :param str, datetime_format: a string to represent the datetime format the string should be converted into; it
        should also have been the format that the strings already are in
    :return:
    """
    if len(string_values) == 1:
        return datetime.strptime(string_values[0], datetime_format)
    else:
        return [datetime.strptime(value, datetime_format) for value in string_values]


def relative_datetime(*datetime_objects: datetime,
                      units: Union[_unit_seconds, _unit_minutes, _unit_hours] = _unit_seconds,
                      rounding: int = None,
                      ) -> Union[float, List[float]]:
    """
    Convert an array of datetime objects that are absolute times, and return an array where all the times in the
    array are relative to the first time in the array. The relativity can be in seconds, minutes, or hours.
    If only one time is given, return 0.
    If two times are given, return a single float that is the time difference between the two value
    If more than two times are given, the list returned has the same length as the input

    :param datetime_objects: a list of datetime objects
    :param units: one of _unit_seconds, _unit_minutes, or _unit_hours
    :param int, rounding: the number of decimal places to round to
    :return:
    """
    if units not in [_unit_seconds, _unit_minutes, _unit_hours]:
        raise ValueError('units passed in is not valid')

    # takes a list of datetime objects, and makes all the values relative to the first object in the list

    if len(datetime_objects) == 1:
        return 0

    # make an array of timedelta objects where each value is the difference between the actual time relative to
    # the first time point
    array_of_datetime_timedelta = [datetime_value - datetime_objects[0] for datetime_value in
                                   datetime_objects]

    # convert the relative timedeltas to floats, where the float number is the number of seconds since the first
    # time point
    array_of_relative_x_in_seconds = [array_of_datetime_timedelta[index].total_seconds() for index
                                      in range(len(array_of_datetime_timedelta))]

    if units == _unit_seconds:
        array_of_relative_datetime_objects = array_of_relative_x_in_seconds
    elif units == _unit_minutes:
        array_of_relative_x_in_minutes = [array_of_relative_x_in_seconds[index] / 60.0 for index in
                                          range(len(array_of_relative_x_in_seconds))]
        array_of_relative_datetime_objects = array_of_relative_x_in_minutes
    elif units == _unit_hours:
        array_of_relative_x_in_hours = [array_of_relative_x_in_seconds[index] / 3600.0 for index in
                                        range(len(array_of_relative_x_in_seconds))]
        array_of_relative_datetime_objects = array_of_relative_x_in_hours

    if rounding is not None:
        array_of_relative_datetime_objects = [round(datetime_obj, rounding) for datetime_obj in
                                              array_of_relative_datetime_objects]

    if len(array_of_relative_datetime_objects) == 2:
        return array_of_relative_datetime_objects[1]
    else:
        return array_of_relative_datetime_objects
