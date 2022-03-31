#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

import inspect
from typing import List, Optional

from easyCore.Fitting.fitting_template import (
    Union,
    Callable,
    FittingTemplate,
    np,
    FitResults,
    NameConverter,
    FitError,
)

# Import bumps specific objects
from bumps.names import Curve, FitProblem
from bumps.parameter import Parameter as bumpsParameter
from bumps.fitters import fit as bumps_fit, FIT_AVAILABLE_IDS


class bumps(FittingTemplate):  # noqa: S101
    """
    This is a wrapper to bumps: https://bumps.readthedocs.io/
    It allows for the bumps fitting engine to use parameters declared in an `easyCore.Objects.Base.BaseObj`.
    """

    property_type = bumpsParameter
    name = "bumps"

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
        self._cached_pars_order = ()
        self.p_0 = {}

    def make_model(
        self, pars: Optional[List[bumpsParameter]] = None
    ) -> Callable:
        """
        Generate a bumps model from the supplied `fit_function` and parameters in the base object.
        Note that this makes a callable as it needs to be initialized with *x*, *y*, *weights*

        :return: Callable to make a bumps Curve model
        :rtype: Callable
        """
        fit_func = self._generate_fit_function()

        def outer(obj):
            def make_func(x, y, weights):
                par = {}
                if not pars:
                    for name, item in obj._cached_pars.items():
                        par["p" + str(name)] = obj.convert_to_par_object(item)
                else:
                    for item in pars:
                        par[
                            "p" + str(NameConverter().get_key(item))
                        ] = obj.convert_to_par_object(item)
                return Curve(fit_func, x, y, dy=weights, **par)

            return make_func

        return outer(self)

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
            for name, value in kwargs.items():
                par_name = int(name[1:])
                if par_name in self._cached_pars.keys():
                    self._cached_pars[par_name].value = value
                    update_fun = self._cached_pars[par_name]._callback.fset
                    if update_fun:
                        update_fun(value)
            # TODO Pre processing here
            for constraint in self.fit_constraints():
                constraint()
            return_data = func(x)
            # TODO Loading or manipulating data here
            return return_data

        # Fake the function signature.
        # This is done as lmfit wants the function to be in the form:
        # f = (x, a=1, b=2)...
        # Where we need to be generic. Note that this won't hold for much outside of this scope.

        self._cached_pars_order = tuple(self._cached_pars.keys())
        params = [
            inspect.Parameter(
                "x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=inspect._empty
            ),
            *[
                inspect.Parameter(
                    "p" + str(name),
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=inspect._empty,
                    default=self._cached_pars[name].raw_value,
                )
                for name in self._cached_pars_order
            ],
        ]
        # Sign the function
        fit_function.__signature__ = inspect.Signature(params)
        self._fit_function = fit_function
        return fit_function

    def fit(
        self,
        x: np.ndarray,
        y: np.ndarray,
        weights: Optional[np.ndarray] = None,
        model: Optional = None,
        parameters: Optional = None,
        method: Optional[str] = None,
        minimizer_kwargs: Optional[dict] = None,
        engine_kwargs: Optional[dict] = None,
        **kwargs,
    ) -> FitResults:
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
            default_method["method"] = method

        if weights is None:
            weights = np.sqrt(np.abs(y))

        if engine_kwargs is None:
            engine_kwargs = {}

        if minimizer_kwargs is None:
            minimizer_kwargs = {}
        # else:
        #     minimizer_kwargs = {"fit_kws": minimizer_kwargs}
        minimizer_kwargs.update(engine_kwargs)

        if model is None:
            model = self.make_model(pars=parameters)
            model = model(x, y, weights)
        self._cached_model = model
        self.p_0 = {
            f"p{key}": self._cached_pars[key].raw_value
            for key in self._cached_pars.keys()
        }
        problem = FitProblem(model)
        # Why do we do this? Because a fitting template has to have borg instantiated outside pre-runtime
        from easyCore import borg

        borg.stack.beginMacro("Fitting routine")
        try:
            model_results = bumps_fit(
                problem, **default_method, **minimizer_kwargs, **kwargs
            )
            self._set_parameter_fit_result(model_results)
            results = self._gen_fit_results(model_results)
        except Exception as e:
            raise FitError(e)
        finally:
            borg.stack.endMacro()
        return results

    def convert_to_pars_obj(
        self, par_list: Optional[List] = None
    ) -> List[bumpsParameter]:
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
        pars_obj = [self.__class__.convert_to_par_object(obj) for obj in par_list]
        return pars_obj

    # For some reason I have to double staticmethod :-/
    @staticmethod
    def convert_to_par_object(obj) -> bumpsParameter:
        """
        Convert an `easyCore.Objects.Base.Parameter` object to a bumps Parameter object

        :return: bumps Parameter compatible object.
        :rtype: bumpsParameter
        """
        return bumpsParameter(
            name="p" + str(NameConverter().get_key(obj)),
            value=obj.raw_value,
            bounds=[obj.min, obj.max],
            fixed=obj.fixed,
        )

    def _set_parameter_fit_result(self, fit_result):
        """
        Update parameters to their final values and assign a std error to them.

        :param fit_result: Fit object which contains info on the fit
        :return: None
        :rtype: noneType
        """
        pars = self._cached_pars
        for index, name in enumerate(self._cached_model._pnames):
            dict_name = int(name[1:])
            pars[dict_name].value = fit_result.x[index]
            pars[dict_name].error = fit_result.dx[index]

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
        results.success = fit_results.success
        pars = self._cached_pars
        item = {}
        for index, name in enumerate(self._cached_model._pnames):
            dict_name = int(name[1:])
            item[name] = pars[dict_name].raw_value
        results.p0 = self.p_0
        results.p = item
        results.x = self._cached_model.x
        results.y_obs = self._cached_model.y
        results.y_calc = self.evaluate(results.x, parameters=results.p)
        results.residual = results.y_obs - results.y_calc
        results.goodness_of_fit = fit_results.fun

        results.fitting_engine = self.__class__
        results.fit_args = None
        results.engine_result = fit_results
        # results.check_sanity()
        return results

    def available_methods(self) -> List[str]:
        return FIT_AVAILABLE_IDS
