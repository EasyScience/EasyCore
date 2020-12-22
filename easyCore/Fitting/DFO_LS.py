__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import inspect
from typing import List
from numbers import Number

from easyCore.Fitting.fitting_template import noneType, Union, Callable, \
    FittingTemplate, np, FitResults, NameConverter, FitError

# Import dfols specific objects
import dfols


class DFO_LS(FittingTemplate):  # noqa: S101
    """
    This is a wrapper to Derivative free optimisation: https://numericalalgorithmsgroup.github.io/dfols/
    """

    property_type = Number
    name = 'DFO_LS'

    def __init__(self, obj, fit_function: Callable):
        """
        Initialize the fitting engine with a `BaseObj` and an arbitrary fitting function.

        :param obj: Object containing elements of the `Parameter` class
        :type obj: BaseObj
        :param fit_function: function that when called returns y values. 'x' must be the first
                            and only positional argument. Additional values can be supplied by
                            keyword/value pairs
        :type fit_function: Callable
        """
        super().__init__(obj, fit_function)

    def make_model(self, pars: Union[noneType, List[float]] = None) -> Callable:
        """
        Generate a bumps model from the supplied `fit_function` and parameters in the base object.
        Note that this makes a callable as it needs to be initialized with *x*, *y*, *weights*

        :return: Callable to make a bumps Curve model
        :rtype: Callable
        """
        fit_func = self._generate_fit_function()

        def residuals(x0):
            return (fit_func(x, x0) - y)/weights
        
        residuals.x = x
        residuals.y = y
        residuals.weights = weights
        return residuals

    def _generate_fit_function(self) -> Callable:
        """
        Using the user supplied `fit_function`, wrap it in such a way we can update `Parameter` on
        iterations.

        :return: a fit function which is compatible with bumps models
        :rtype: Callable
        """
        # Original fit function
        func = self._original_fit_function
        # Get a list of `Parameters`
        self._cached_pars = {}
        for parameter in self._object.get_fit_parameters():
            self._cached_pars[NameConverter().get_key(parameter)] = parameter

        # Make a new fit function
        def fit_function(x: np.ndarray, **kwargs):
            """
            Wrapped fit function which now has a bumps compatible form

            :param x: array of data points to be calculated
            :type x: np.ndarray
            :param kwargs: key word arguments
            :return: points calculated at `x`
            :rtype: np.ndarray
            """
            # Update the `Parameter` values and the callback if needed
            # TODO THIS IS NOT THREAD SAFE :-(
            for name, value in kwargs.items():
                par_name = int(name[1:])
                if par_name in self._cached_pars.keys():
                    # This will take in to account constraints
                    self._cached_pars[par_name].value = value
                    # Since we are calling the parameter fset will be called.
            # TODO Pre processing here
            for constraint in self.fit_constraints():
                constraint()
            return_data = func(x)
            # TODO Loading or manipulating data here
            return return_data

        self._fit_function = fit_function
        return fit_function

    def fit(self, x: np.ndarray, y: np.ndarray, weights: Union[np.ndarray, noneType] = None,
            model=None, parameters=None, method: str = None, xtol: float = 1e-6, ftol: float = 1e-8, **kwargs) -> FitResults:
        """
        Perform a fit using the lmfit engine.

        :param x: points to be calculated at
        :type x: np.ndarray
        :param y: measured points
        :type y: np.ndarray
        :param weights: Weights for supplied measured points * Not really optional*
        :type weights: np.ndarray
        :param model: Optional Model which is being fitted to
        :type model: lmModel
        :param parameters: Optional parameters for the fit
        :type parameters: List[bumpsParameter]
        :param kwargs: Additional arguments for the fitting function.
        :param method: Method for minimization
        :type method: str
        :return: Fit results
        :rtype: ModelResult
        """

        default_method = {}
        if method is not None and method in self.available_methods():
            default_method['method'] = method

        if weights is None:
            weights = np.sqrt(y)

        if model is None:
            model = self.make_model(x, y, weights)
        self._cached_model = model

        # Why do we do this? Because a fitting template has to have borg instantiated outside pre-runtime
        from easyCore import borg
        borg.stack.beginMacro('Fitting routine')
        try:
            model_results = self.dfols_fit(model, **kwargs)
            self._set_parameter_fit_result(model_results)
        except Exception as e:
            raise FitError(e)
        finally:
            borg.stack.endMacro()
        return self._gen_fit_results(model_results)

    def convert_to_pars_obj(self, par_list: Union[list, noneType] = None) -> List[bumpsParameter]:
        """
        Create a container with the `Parameters` converted from the base object.

        :param par_list: If only a single/selection of parameter is required. Specify as a list
        :type par_list: List[str]
        :return: bumps Parameters list
        :rtype: List[bumpsParameter]
        """
        if par_list is None:
            # Assume that we have a BaseObj for which we can obtain a list
            par_list = self._object.get_fit_parameters()
        pars_obj = ([self.__class__.convert_to_par_object(obj) for obj in par_list])
        return pars_obj

    # For some reason I have to double staticmethod :-/
    @staticmethod
    def convert_to_par_object(obj) -> None:
        """
        Convert an `easyCore.Objects.Base.Parameter` object to a bumps Parameter object

        :return: bumps Parameter compatible object.
        :rtype: bumpsParameter
        """
        pass

    def _set_parameter_fit_result(self, fit_result):
        """
        Update parameters to their final values and assign a std error to them.

        :param fit_result: Fit object which contains info on the fit
        :return: None
        :rtype: noneType
        """
        pars = self._cached_pars
        for index, parameter in enumerate(self._cached_model):
            pars[index].value = fit_result.x[index]
            pars[index].error = fit_result.resid[index]

    def _gen_fit_results(self, fit_results, **kwargs) -> FitResults:
        """
        Convert fit results into the unified `FitResults` format

        :param fit_result: Fit object which contains info on the fit
        :return: fit results container
        :rtype: FitResults
        """

        results = FitResults()
        for name, value in kwargs.items():
            if getattr(results, name, False):
                setattr(results, name, value)
        results.success = fit_results.flag
        pars = self._cached_pars
        item = {}
        for par in pars:
            item[f'p{NameConverter().get_key(par)}'] = par.raw_value
        results.p = item
        results.x = self._cached_model.x
        results.y_obs = self._cached_model.y
        results.y_calc = self.evaluate(results.x, parameters=results.p)
        results.residual = results.y_obs - results.y_calc
        results.goodness_of_fit = fit_results.fun

        results.fitting_engine = self.__class__
        results.fit_args = None

        return results

    def available_methods(self) -> List[str]:
        return ['leastsq']

    def dfols_fit(self, model, **kwargs):
        x0 = [par.raw_value for par in self._cached_pars]
        bounds = ([par.min for par in self._cached_pars], [par.max for par in self._cached_pars])
        results = dfols.solve(model, x0, bounds=bounds, **kwargs)
        return results
