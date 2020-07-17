__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import inspect

from easyCore.Fitting.fitting_template import noneType, Union, Callable, FittingTemplate, np

from lmfit import Parameter as lmParameter, Parameters as lmParameters, Model as lmModel
from lmfit.model import ModelResult


class lmfit(FittingTemplate):  # noqa: S101
    """
    This is a wrapper to lmfit: https://lmfit.github.io/
    It allows for the lmfit fitting engine to use parameters declared in an `easyCore.Objects.Base.BaseObj`.
    """
    property_type = lmParameter
    name = 'lmfit'

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
        self._cached_pars = {}
        self._cached_model = None

    def make_model(self) -> lmModel:
        """
        Generate a lmfit model from the supplied `fit_function` and parameters in the base object
        :return: Callable lmfit model
        :rtype: lmModel
        """
        # Generate the fitting function
        fit_func = self._generate_fit_function()
        # Create the model
        model = lmModel(fit_func, independent_vars=['x'], param_names=list(self._cached_pars.keys()))
        # Assign values from the `Parameter` to the model
        for name, item in self._cached_pars.items():
            model.set_param_hint(name, value=item.raw_value, min=item.min, max=item.max)
        # Cache the model for later reference
        self._cached_model = model
        return model

    def _generate_fit_function(self) -> Callable:
        """
        Using the user supplied `fit_function`, wrap it in such a way we can update `Parameter` on
        iterations.
        :return: a fit function which is compatible with lmfit models
        :rtype: Callable
        """
        # Original fit function
        func = self._fit_function
        # Get a list of `Parameters`
        for parameter in self._object.get_parameters():
            self._cached_pars[parameter.name] = parameter

        # Make a new fit function
        def fit_function(x: np.ndarray, **kwargs):
            """
            Wrapped fit function which now has a lmfit compatible form
            :param x: array of data points to be calculated
            :type x: np.ndarray
            :param kwargs: key word arguments
            :return: points calculated at `x`
            :rtype: np.ndarray
            """
            # Update the `Parameter` values and the callback if needed
            for name, value in kwargs.items():
                if name in self._cached_pars.keys():
                    self._cached_pars[name].value = value
                    update_fun = self._cached_pars[name]._callback.fset
                    if update_fun:
                        update_fun(value)
            # TODO Pre processing here
            return_data = func(x)
            # TODO Loading or manipulating data here
            return return_data

        # Fake the function signature.
        # This is done as lmfit wants the function to be in the form:
        # f = (x, a=1, b=2)...
        # Where we need to be generic. Note that this won't hold for much outside of this scope.
        params = [inspect.Parameter('x',
                                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                    annotation=inspect._empty), *[inspect.Parameter(name,
                                                                                   inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                                                                   annotation=inspect._empty,
                                                                                   default=parameter.raw_value)
                                                                 for name, parameter in self._cached_pars.items()]]
        # Sign the function
        fit_function.__signature__ = inspect.Signature(params)
        return fit_function

    def fit(self, x: np.ndarray, y: np.ndarray,
            weights: Union[np.ndarray, noneType] = None, model: Union[lmModel, noneType] = None,
            parameters: Union[lmParameters, noneType] = None, **kwargs) -> ModelResult:
        """
        Perform a fit using the lmfit engine.
        :param x: points to be calculated at
        :type x: np.ndarray
        :param y: measured points
        :type y: np.ndarray
        :param weights: Weights for supplied measured points
        :type weights: np.ndarray
        :param model: Optional Model which is being fitted to
        :type model: lmModel
        :param parameters: Optional parameters for the fit
        :type parameters: lmParameters
        :param kwargs: Additional arguments for the fitting function.
        :return: Fit results
        :rtype: ModelResult
        """
        if not model:
            model = self.make_model()
        model_results = model.fit(y, x=x, weights=weights, **kwargs)
        # TODO post process model results
        # TODO update parameter with fit sigma.
        return model_results

    def convert_to_pars_obj(self, par_list: Union[list, noneType] = None) -> lmParameters:
        """
        Create an lmfit compatible container with the `Parameters` converted from the base object.
        :param par_list: If only a single/selection of parameter is required. Specify as a list
        :type par_list: List[str]
        :return: lmfit Parameters compatible object
        :rtype: lmParameters
        """
        if par_list is None:
            # Assume that we have a BaseObj for which we can obtain a list
            par_list = self._object.get_parameters()
        pars_obj = lmParameters().add_many([self.__class__.convert_to_par_object(obj) for obj in par_list])
        return pars_obj

    # Note that this is an implementation of a abstract static method. My IDE can't cope with this.
    def convert_to_par_object(obj) -> lmParameter:
        """
        Convert an `easyCore.Objects.Base.Parameter` object to a lmfit Parameter object
        :return: lmfit Parameter compatible object.
        :rtype: lmParameter
        """
        return lmParameter(obj.name, value=obj.raw_value, vary=~obj.fixed,
                           min=obj.min, max=obj.max, expr=None, brute_step=None
                           )
