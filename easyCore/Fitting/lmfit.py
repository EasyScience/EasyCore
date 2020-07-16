__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Union
import inspect
from lmfit import Parameter as lmParameter, Parameters as lmParameters, Model as lmModel
from lmfit.model import ModelResult

from easyCore.Fitting.fitting_template import FittingTemplate
from easyCore.Utils.typing import noneType


class lmfit(FittingTemplate):
    property_type = lmParameter
    name = 'lmfit'

    def __init__(self, obj, fit_function):
        super().__init__(obj, fit_function)
        self._cached_pars = {}
        self._cached_model = None

    def make_model(self):
        fit_func = self._generate_fit_function()
        model = lmModel(fit_func, independent_vars=['x'], param_names=list(self._cached_pars.keys()))
        for name, item in self._cached_pars.items():
            model.set_param_hint(name, value=item.raw_value, min=item.min, max=item.max)
        self._cached_model = model
        return model

    def _generate_fit_function(self):
        func = self._fit_function
        for parameter in self._object.get_fittables():
            self._cached_pars[parameter.name] = parameter

        def fit_function(x, **kwargs):
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

        # Fake the fun signature
        params = [inspect.Parameter('x',
                                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                    annotation=inspect._empty), *[inspect.Parameter(name,
                                                                                   inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                                                                   annotation=inspect._empty,
                                                                                   default=parameter.raw_value)
                                                                 for name, parameter in self._cached_pars.items()]]
        fit_function.__signature__ = inspect.Signature(params)
        return fit_function

    def fit(self, x, y, weights=None, model=None, parameters=None, **kwargs) -> ModelResult:
        if not model:
            model = self.make_model()
        model_results = model.fit(y, x=x, weights=weights, **kwargs)
        # TODO post process model results
        return model_results

    def convert_to_pars_obj(self, par_list: Union[list, noneType] = None):
        if par_list is None:
            # Assume that we have a BaseObj for which we can obtain a list
            par_list = self._object.get_fittables()
        pars_obj = lmParameters().add_many([self.__class__.convert_to_par_object(obj) for obj in par_list])
        return pars_obj

    def convert_to_par_object(obj):
        return lmParameter(obj.name, value=obj.raw_value, vary=~obj.fixed,
                           min=obj.min, max=obj.max, expr=None, brute_step=None
                           )
