__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from abc import abstractmethod, ABCMeta

from asteval import Interpreter
from numbers import Number
from typing import List, Union, Callable, TypeVar

from easyCore import borg
from easyCore.Utils.typing import noneType
from easyCore.Utils.json import MSONable

Descriptor = TypeVar("Descriptor")
Parameter = TypeVar("Parameter")


class ConstraintBase(MSONable, metaclass=ABCMeta):
    """
    A base class used to describe a constraint to be applied to easyCore base objects.
    """
    _borg = borg

    def __init__(self, dependent_obj: Union[Descriptor, Parameter],
                 independent_obj: Union[Parameter, Descriptor, List[Union[Descriptor, Parameter]], noneType] = None,
                 operator=None, value=None):
        self.aeval = Interpreter()
        self.dependent_obj_ids = self.get_key(dependent_obj)
        self.independent_obj_ids = None
        self.enabled = True
        if independent_obj is not None:
            if isinstance(independent_obj, list):
                self.independent_obj_ids = [self.get_key(obj) for obj in independent_obj]
            else:
                self.independent_obj_ids = self.get_key(independent_obj)
            # Test if dependent is a parameter or a descriptor.
            # We can not import `Parameter`, so......
            if dependent_obj.__class__.__name__ == 'Parameter':
                print(f'Dependent variable {dependent_obj}. It should be a `Descriptor`.'
                      f'Setting to fixed')
                dependent_obj.fixed = True

        self.operator = operator
        self.value = value

    def __call__(self, *args, no_set=False, **kwargs):
        """
        Method which applies the constraint

        :return: None
        """
        if not self.enabled:
            if no_set:
                return None
            return
        independent_objs = None
        if isinstance(self.dependent_obj_ids, int):
            dependent_obj = self.get_obj(self.dependent_obj_ids)
        else:
            raise AttributeError
        if isinstance(self.independent_obj_ids, int):
            independent_objs = self.get_obj(self.independent_obj_ids)
        elif isinstance(self.independent_obj_ids, list):
            independent_objs = [self.get_obj(obj_id) for obj_id in self.independent_obj_ids]
        if independent_objs is not None:
            value = self._parse_operator(independent_objs, *args, **kwargs)
        else:
            value = self._parse_operator(dependent_obj, *args, **kwargs)

        if no_set:
            return value
        else:
            dependent_obj.value = value

    @abstractmethod
    def _parse_operator(self, obj: Union[Descriptor, Parameter], *args, **kwargs) -> Number:
        """
        Abstract method which contains the constraint logic

        :param obj: The object/objects which the constraint will use
        :return: A numeric result of the constraint logic
        """
        pass

    @abstractmethod
    def __repr__(self):
        pass

    def get_key(self, obj) -> int:
        """
        Get the unique key of a easyCore object

        :param obj: easyCore object
        :return: key for easyCore object
        """
        return self._borg.map.convert_id_to_key(obj)

    def get_obj(self, key: int) -> Union[Descriptor, Parameter]:
        """
        Get an easyCore object from its unique key

        :param key: an easyCore objects unique key
        :return: easyCore object
        """
        return self._borg.map.get_item_by_key(key)


class NumericConstraint(ConstraintBase):
    """
    A `NumericConstraint` is a constraint whereby a dependent parameters value is something of an independent parameters
    value
    """

    def __init__(self, dependent_obj: Union[Descriptor, Parameter], operator: str, value: Number):
        """


        :param dependent_obj:
        :type dependent_obj:
        :param operator:
        :type operator:
        :param value:
        :type value:
        """
        super(NumericConstraint, self).__init__(dependent_obj, operator=operator, value=value)

    def _parse_operator(self, obj: Union[Descriptor, Parameter], *args, **kwargs) -> Number:
        value = obj.raw_value
        self.aeval.symtable['value1'] = value
        self.aeval.symtable['value2'] = self.value
        try:
            self.aeval.eval(f'value3 = value1 {self.operator} value2')
            logic = self.aeval.symtable['value3']
            if not logic:
                value = self.aeval.symtable['value2']
        except Exception as e:
            raise e
        finally:
            self.aeval.symtable.clear()
        return value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} with `value` {self.operator} {self.value}'


class SelfConstraint(ConstraintBase):

    def __init__(self, dependent_obj: Union[Descriptor, Parameter], operator: str, value: str):
        super(SelfConstraint, self).__init__(dependent_obj, operator=operator, value=value)

    def _parse_operator(self, obj: Union[Descriptor, Parameter], *args, **kwargs) -> Number:
        value = obj.raw_value
        self.aeval.symtable['value1'] = value
        self.aeval.symtable['value2'] = getattr(obj, self.value)
        try:
            self.aeval.eval(f'value3 = value1 {self.operator} value2')
            logic = self.aeval.symtable['value3']
            if not logic:
                value = self.aeval.symtable['value2']
        except Exception as e:
            raise e
        finally:
            self.aeval.symtable.clear()
        return value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} with `value` {self.operator} obj.{self.value}'


class ObjConstraint(ConstraintBase):

    def __init__(self, dependent_obj: Parameter, operator: str, independent_obj: Parameter):
        super(ObjConstraint, self).__init__(dependent_obj, independent_obj=independent_obj, operator=operator)

    def _parse_operator(self, obj: Union[Descriptor, Parameter], *args, **kwargs) -> Number:
        value = obj.raw_value
        self.aeval.symtable['value1'] = value
        try:
            self.aeval.eval(f'value2 = {self.operator} value1')
            value = self.aeval.symtable['value2']
        except Exception as e:
            raise e
        finally:
            self.aeval.symtable.clear()
        return value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} with `dependent_obj` = {self.operator} `independent_obj`'


class MultiObjConstraint(ConstraintBase):

    def __init__(self, independent_objs: List[Union[Descriptor, Parameter]],
                 operator: List[str], dependent_obj: Union[Descriptor, Parameter],
                 value: Number):
        super(MultiObjConstraint, self).__init__(dependent_obj, independent_obj=independent_objs,
                                                 operator=operator, value=value)

    def _parse_operator(self, independent_objs: List[Union[Descriptor, Parameter]], *args, **kwargs) -> Number:
        in_str = ''
        value = None
        for idx, obj in enumerate(independent_objs):
            self.aeval.symtable['p' + str(self.independent_obj_ids[idx])] = obj.raw_value
            in_str += ' p' + str(self.independent_obj_ids[idx])
            if idx < len(self.operator):
                in_str += ' ' + self.operator[idx]
        try:
            self.aeval.eval(f'final_value = {self.value} - ({in_str})')
            value = self.aeval.symtable['final_value']
        except Exception as e:
            raise e
        finally:
            self.aeval.symtable.clear()
        return value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


class FunctionalConstraint(ConstraintBase):

    def __init__(self, dependent_obj: Union[Descriptor, Parameter], func: Callable,
                 independent_objs=None):
        super(FunctionalConstraint, self).__init__(dependent_obj, independent_obj=independent_objs)
        self.function = func

    def _parse_operator(self, obj: Union[Descriptor, Parameter], *args, **kwargs) -> Number:
        return self.function(obj.raw_value, *args, **kwargs)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'
