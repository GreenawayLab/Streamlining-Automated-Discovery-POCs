from typing import Dict, Union, List
import uuid
import json
from pathlib import Path


class Reference:
    def __init__(self,
                 value: float = 0,
                 relative_lower: float = None,
                 relative_upper: float = None,
                 name: str = None,
                 lower: float = None,
                 upper: float = None,
                 ):
        """
        Dont pass in both relative_lower and lower
        Dont pass in both relative_upper and upper

        :param value: some value that will be the reference
        :param relative_lower: some value that is the relative lower limit of what is considered still "good",
            relative to the value
        :param relative_upper: some value that is the relative upper limit of what is considered still "good",
            relative to the value
        :param lower: some value that is the lower limit of what is considered still "good", absolute value
        :param name:
        """
        if name is None:
            name = uuid.uuid4().hex

        if relative_lower is not None and lower is not None:
            raise Exception('Must only pass in one of relative_lower or lower')
        if relative_upper is not None and upper is not None:
            raise Exception('Must only pass in one of relative_upper or upper')
        if relative_lower is None and lower is None:
            raise Exception('Must only pass in one of relative_lower or lower')
        if relative_upper is None and upper is None:
            raise Exception('Must only pass in one of relative_upper or upper')

        if value is None:
            value = 0
        self._value = value

        self._relative_lower = None
        self._relative_upper = None
        self._lower = None
        self._upper = None

        if relative_lower is not None:
            self.relative_lower = relative_lower
        if relative_upper is not None:
            self.relative_upper = relative_upper
        if lower is not None:
            self.lower = lower
        if upper is not None:
            self.upper = upper
        self._name = name

    def good(self, *values) -> Union[bool, List[bool]]:
        good = []
        for value in values:
            good.append(self.value - self.relative_lower <= value <= self.value + self.relative_upper)
        if len(good) == 1:
            return good[0]
        else:
            return good

    @property
    def data(self) -> Dict:
        data = {'name': self.name,
                'value': self.value,
                'relative_lower': self.relative_lower,
                'relative_upper': self.relative_upper,
                }
        return data

    @data.setter
    def data(self,
             value,
             ):
        self.name = value['name']
        self.value = value['value']
        self.relative_lower = value['relative_lower']
        self.relative_upper = value['relative_upper']
        self.lower = value['lower']
        self.upper = value['upper']

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,
             value: str):
        self._name = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self,
              value: float):
        self._value = value

    @property
    def relative_upper(self):
        return self._relative_upper

    @relative_upper.setter
    def relative_upper(self,
                       value: float):
        self._relative_upper = value
        self._upper = self.value + value

    @property
    def relative_lower(self):
        return self._relative_lower

    @relative_lower.setter
    def relative_lower(self,
                       value: float):
        self._relative_lower = value
        self._lower = self.value - value

    @property
    def upper(self):
        return self._upper

    @upper.setter
    def upper(self,
              value: float):
        self._upper = value
        self._relative_upper = value - self.value

    @property
    def lower(self):
        return self._lower

    @lower.setter
    def lower(self,
              value: float):
        self._lower = value
        self._relative_lower = self.value - value

    # todo add check to make sure upper >= value and lower <= value before setting values


class ReferenceManager:
    def __init__(self):
        self._references: Dict[str, Reference] = {}
        self._data: Dict[str, Union[Dict, float]] = {}

    def good(self,
             *values: float,
             reference_name: str,
             ) -> Union[bool, List[bool]]:
        reference = self.reference(reference_name)
        return reference.good(*values)

    def reference(self, reference_name: str) -> Reference:
        if reference_name not in self.names:
            return None
        reference = self.references[reference_name]
        return reference

    def add_reference(self,
                      value: float = None,
                      relative_lower: float = None,
                      relative_upper: float = None,
                      name: str = None,
                      upper: float = None,
                      lower: float = None,
                      ) -> Reference:
        """
        :return:
        """
        reference = Reference(value, relative_lower, relative_upper, name, lower, upper)
        name = reference.name
        self.references[name] = reference
        return reference

    def remove_reference(self,
                         *reference_names: str
                         ) -> Union[Reference, Dict[str, Reference]]:
        references_removed = {}
        for reference_name in reference_names:
            if reference_name not in self.names:
                raise ValueError(f'{reference_name} not in reference manager')
            reference = self.references.pop(reference_name)
            references_removed[reference_name] = reference
        if len(references_removed) == 1:
            reference_name, reference = references_removed.popitem()
            return reference
        else:
            return references_removed

    def update_reference(self,
                         reference_name: str,
                         value: float = None,
                         relative_lower: float = None,
                         relative_upper: float = None,

                         upper: float = None,
                         lower: float = None,
                         name: str = None,
                         ) -> Reference:
        if reference_name not in self.names:
            raise ValueError(f'{reference_name} not in reference manager')
        reference = self.remove_reference(reference_name)
        if value is None:
            value = reference.value
        if relative_lower is None:
            relative_lower = reference.relative_lower
        if relative_upper is None:
            relative_upper = reference.relative_upper
        if name is None:
            name = reference.name
        if lower is None:
            lower = reference.lower
        if upper is None:
            upper = reference.upper
        reference = self.add_reference(value, relative_lower, relative_upper, name, lower, upper)
        return reference

    @property
    def references(self) -> Dict[str, Reference]:
        """Dictionary of reference names: reference object"""
        return self._references

    @references.setter
    def references(self,
                   value):
        self._references = value

    @property
    def names(self) -> List[str]:
        """Return a list of all the names of all the references"""
        names = list(self.references.keys())
        return names

    @property
    def data(self) -> Dict[str, Dict[str, Union[str, float]]]:
        """Nested dictionary that contains the necessary data to be able to save and set a reference manager and all its
        references"""
        data = {'references': {},
                }
        data_references = {}
        references = list(self.references.values())
        for reference in references:
            name = reference.name
            add_data = {'name': name,
                        'value': reference.value,
                        'relative_lower': reference.relative_lower,
                        'relative_upper': reference.relative_upper,
                        'lower': reference.lower,
                        'upper': reference.upper,
                        }
            data_references[name] = add_data
        data['references'] = data_references
        self._data = data
        return self._data

    @data.setter
    def data(self,
             value: Dict[str, Dict[str, Union[str, float]]]
             ):
        self.references = {}
        reference_data = list(value['references'].values())
        for data in reference_data:
            name = data['name']
            reference_value = data['value']
            relative_lower = data['relative_lower']
            relative_upper = data['relative_upper']
            reference = Reference(reference_value, relative_upper, relative_lower, name)
            self.references[name] = reference

    def save_data(self, file_path: Path):
        """Save data to a json file"""
        data = {'reference_manager': self.data}
        with open(str(file_path), 'w') as file:
            json.dump(data, file)

    def load_data(self, file_path: Path):
        with open(str(file_path)) as file:
            data = json.load(file)
        self.data = data['reference_manager']
