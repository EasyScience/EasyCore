__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import numpy as np

from abc import ABCMeta, abstractmethod
from typing import Union, Callable, List
from easyCore.Utils.typing import noneType


class FittingTemplate(metaclass=ABCMeta):
    """
    This template class is the basis for all fitting engines in `easyCore`.
    """

    _engines = []
    property_type = None
    name: str = None

    def __init_subclass__(cls, is_abstract: bool = False, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_abstract:
            cls._engines.append(cls)

    def __init__(self, obj, fit_function: Callable):
        self._object = obj
        self._fit_function = fit_function

    @abstractmethod
    def make_model(self):
        """
        Generate an engine model from the supplied `fit_function` and parameters in the base object
        :return: Callable model
        """
        pass

    @abstractmethod
    def _generate_fit_function(self) -> Callable:
        """
        Using the user supplied `fit_function`, wrap it in such a way we can update `Parameter` on
        iterations.
        """
        pass

    @abstractmethod
    def fit(self, x: np.ndarray, y: np.ndarray,
            weights: Union[np.ndarray, noneType] = None, model=None, parameters=None, **kwargs):
        """
        Perform a fit using the  engine.
        :param x: points to be calculated at
        :type x: np.ndarray
        :param y: measured points
        :type y: np.ndarray
        :param weights: Weights for supplied measured points
        :type weights: np.ndarray
        :param model: Optional Model which is being fitted to
        :param parameters: Optional parameters for the fit
        :param kwargs: Additional arguments for the fitting function.
        :return: Fit results
        """
        pass

    @abstractmethod
    def convert_to_pars_obj(self, par_list: Union[list, noneType] = None):
        """
        Create an engine compatible container with the `Parameters` converted from the base object.
        :param par_list: If only a single/selection of parameter is required. Specify as a list
        :type par_list: List[str]
        :return: engine Parameters compatible object
        """
        pass

    @staticmethod
    @abstractmethod
    def convert_to_par_object(obj):
        """
        Convert an `easyCore.Objects.Base.Parameter` object to an engine Parameter object
        """
        pass
