__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from asteval import Interpreter
from numbers import Number

from easyCore import borg
from easyCore.Objects.Base import Parameter


class NumericConstraint:
    _borg = borg

    def __init__(self, obj: Parameter, operator: str, value: Number):
        self.obj: int = self._borg.map.convert_id_to_key(obj)
        self.operator = operator
        self.item = value

    def __call__(self):
        obj: Parameter = self._borg.map.get_item_by_key(self.obj)
        obj.value = self._parse_operator(obj)

    def _parse_operator(self, obj: Parameter) -> float:
        aeval = Interpreter()
        value = obj.raw_value
        aeval.symtable['value1'] = value
        aeval.symtable['value2'] = self.item
        try:
            aeval.eval(f'value3 = value1 {self.operator} value2')
        except Exception as e:
            raise e
        logic = aeval.symtable['value3']
        if bool(logic):
            value = aeval.symtable['value2']
        return value


class SelfConstraint:
    _borg = borg

    def __init__(self, obj: Parameter, operator: str, item: str):
        self.obj: int = self._borg.map.convert_id_to_key(obj)
        self.operator = operator
        self.item = item

    def __call__(self):
        obj: Parameter = self._borg.map.get_item_by_key(self.obj)
        obj.value = self._parse_operator(obj)

    def _parse_operator(self, obj: Parameter) -> float:
        aeval = Interpreter()
        value = obj.raw_value
        aeval.symtable['value1'] = value
        aeval.symtable['value2'] = getattr(obj, self.item)
        try:
            aeval.eval(f'value3 = value1 {self.operator} value2')
        except Exception as e:
            raise e
        logic = aeval.symtable['value3']
        if bool(logic):
            value = aeval.symtable['value2']
        return value


class ObjConstraint:
    _borg = borg

    def __init__(self, obj1: Parameter, operator: str, obj2: Parameter):
        self.obj1 = self._borg.map.convert_id_to_key(obj1)
        self.obj2 = self._borg.map.convert_id_to_key(obj2)
        self.operator = operator

    def __call__(self):
        obj1 = self._borg.map.get_item_by_key(self.obj1)
        obj2 = self._borg.map.get_item_by_key(self.obj2)

        value2 = obj2.raw_value
        obj1.value = self._parse_operator(value2)

    def _parse_operator(self, value: Number):
        aeval = Interpreter()
        aeval.symtable['value1'] = value
        try:
            aeval.eval(f'value2 = {self.operator} value1')
        except Exception as e:
            raise e
        return aeval.symtable['value2']
