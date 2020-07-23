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
        self._original_fit_function = fit_function
        self._cached_pars = {}
        self._cached_model = None
        self._fit_function = None

    @abstractmethod
    def make_model(self, pars=None):
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

    def evaluate(self, x: np.ndarray, parameters: dict = None, **kwargs) -> np.ndarray:
        """
        Evaluate the fit function for values of x. Parameters used are either the latest or user supplied.
        If the parameters are user supplied, it must be in a dictionary of {'parameter_name': parameter_value,...}

        :param x: x values for which the fit function will be evaluated
        :type x:  np.ndarray
        :param parameters: Dictionary of parameters which will be used in the fit function. They must be in a dictionary
         of {'parameter_name': parameter_value,...}
        :type parameters: dict
        :param kwargs: additional arguments
        :return: y values calculated at points x for a set of parameters.
        :rtype: np.ndarray
        """
        if self._fit_function is None:
            # This will also generate self._cached_pars
            self._fit_function = self._generate_fit_function()

        if not isinstance(parameters, (dict, noneType)):
            raise AttributeError

        pars = self._cached_pars
        new_parameters = parameters
        if new_parameters is None:
            new_parameters = {}
        for name, item in pars.items():
            if name not in new_parameters.keys():
                new_parameters[name] = item.raw_value

        return self._fit_function(x, **new_parameters, **kwargs)

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

    @abstractmethod
    def _set_parameter_fit_result(self, fit_result):
        """
        Update parameters to their final values and assign a std error to them.

        :param fit_result: Fit object which contains info on the fit
        :return: None
        :rtype: noneType
        """
        pass

    @abstractmethod
    def _gen_fit_results(self, fit_results, **kwargs) -> 'FitResults':
        """
        Convert fit results into the unified `FitResults` format

        :param fit_result: Fit object which contains info on the fit
        :return: fit results container
        :rtype: FitResults
        """
        pass


class FitResults:
    """
    At the moment this is just a dummy way of unifying the returned fit parameters
    """
    def __init__(self):
        self.success = False
        self.fitting_engine = None
        self.fit_args = {}
        self.p = {}
        self.p0 = {}
        self.x = np.ndarray([])
        self.y_obs = np.ndarray([])
        self.y_calc = np.ndarray([])
        self.goodness_of_fit = np.Inf
        self.residual = np.ndarray([])
        self.engine_result = None

    # def __repr__(self) -> str:
    #     info = ''
    #     return info
    #
    # def fit_report(self) -> str:
    #     info = ''
    #     return info
