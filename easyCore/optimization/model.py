#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import concurrent.futures as cf
import functools
import inspect
import warnings

# import dask.array as da

from easyCore import np
from easyCore.Objects.ObjectClasses import BaseObj
from time import perf_counter
from typing import Callable, TypeVar, Iterable, Optional, List, Union, Tuple, Any

T = TypeVar('T', bound=Iterable)


def value_wrapper(value, x):
    return value


def check_model(func):
    def checker(obj, model):
        if not issubclass(model.__class__, Model):
            try:
                model = Model(model)
            except Exception:
                raise TypeError('The model must be a subclass of Model')
        return func(obj, model)
    return checker


class Model:
    def __init__(self, f: Optional[Callable] = None, parameters: Optional[dict] = None):
        if not hasattr(f, '__call__'):
            f = functools.partial(value_wrapper, f)
        self._function = f
        self._parameters = parameters
        s = inspect.signature(f)
        self._idx = sum([isinstance(item.default, type(inspect._empty)) or
                         item.kind == inspect.Parameter.POSITIONAL_ONLY
                         for n, item in s.parameters.items()])
        if parameters is None and f is not None:
            if len(s.parameters) == self._idx:
                self._parameters = {}
            else:
                p = s.parameters
                self._parameters = {
                    p[name].name: p[name].default
                    for name in list(s.parameters.keys())[self._idx::]
                }
        self._count = 0
        self._parameter_history = {}
        self._initialize_parameters()
        self._runtime = []
        self._input_dimensions = 1

    @property
    def evaluation_dimension(self) -> int:
        return self._input_dimensions

    @evaluation_dimension.setter
    def evaluation_dimension(self, value: int):
        self._input_dimensions = value

    def __call__(self, x, *args, **kwargs):
        self._count += 1
        if len(args) == len(self._parameters):
            for name, value in zip(self._parameters.keys(), args):
                self._parameter_history[name].append(value)
        fn = self._function
        if fn is None:
            return None
        start = perf_counter()
        try:
            results = fn(x, *args, **kwargs)
        except Exception:
            warnings.warn('The fn evaluation has failed', ResourceWarning)
            results = np.zeros_like(x)
        finally:
            self._runtime.append(perf_counter() - start)
        return results

    def _initialize_parameters(self, names: Optional[List[str]] = None, values: Optional[List[Any]] = None):
        self.reset_count()
        if names is None or values is None:
            names = list(self._parameter_history.keys())
            values = list(self._parameter_history.values())

        params = [inspect.Parameter('x', inspect.Parameter.POSITIONAL_ONLY, annotation=inspect._empty)] + \
                 [inspect.Parameter(n, inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                    annotation=inspect._empty, default=v[0] ) for n, v in zip(names, values)]
        # Sign the function
        self.__call__.__func__.__signature__ = inspect.Signature(params)

    @property
    def count(self) -> int:
        return self._count

    def reset_count(self):
        names = []
        values = []
        for n, v in self._parameters.items():
            names.append(n)
            values.append(v)
            if hasattr(v, 'value'):
                values[-1] = v.value
                if hasattr(values[-1], 'raw_value'):
                    values[-1] = values[-1].raw_value
        self._count = 0
        self._parameter_history = {n: [v] for n, v in zip(names, values)}
        self._runtime = []

    @property
    def parameter_history(self, parameter_name: Optional[Union[str, List[str]]] = None):
        if not isinstance(parameter_name, list):
            if isinstance(parameter_name, str):
                parameter_name = [parameter_name]
            else:
                parameter_name = list(self._parameter_history.keys())
        return {name: self._parameter_history[name] for name in parameter_name}

    @property
    def parameters(self) -> dict:
        return self._parameters

    @parameters.setter
    def parameters(self, parameters: dict):
        self._parameters = parameters
        self._initialize_parameters()

    @property
    def function(self) -> Callable:
        return self._function

    @function.setter
    def function(self, function: Callable):
        self._function = function
        self.reset_count()

    @property
    def runtime(self) -> float:
        return np.sum(self._runtime)

    @check_model
    def __add__(self, other):
        return CompositeModel(self, other, np.add)

    @check_model
    def __sub__(self, other):
        return CompositeModel(self, other, np.subtract)

    @check_model
    def __mul__(self, other):
        return CompositeModel(self, other, np.multiply)

    @check_model
    def __truediv__(self, other):
        return CompositeModel(self, other, np.divide)


class EasyModel(Model):
    def __init__(self, easy_object, fn_handle):
        function = getattr(easy_object, fn_handle)
        s = inspect.signature(function)
        parameters = easy_object.get_fit_parameters()
        self._cached_parameters = {
            param.name: param
            for param in parameters
        }
        parameters_dict = {
            parameter.name: parameter.raw_value
            for parameter in parameters
        }
        super(EasyModel, self).__init__(function, parameters_dict)

    def __call__(self, x, *args, **kwargs):
        if len(args) == len(self._cached_parameters):
            for name, value in zip(self._cached_parameters.keys(), args):
                self._cached_parameters[name].value = value
        return super(EasyModel, self).__call__(x, *args, **kwargs)


class CompositeModel(Model):
    def __init__(self, left_model, right_model, function, fn_kwargs=None):
        if fn_kwargs is None:
            fn_kwargs = {}
        self._left_model = left_model
        self._right_model = right_model
        lp = left_model.parameters.copy()
        rp = right_model.parameters.copy()
        super(CompositeModel, self).__init__(None, lp.update(rp))
        self._function = function
        self._function_kwargs = fn_kwargs

    def _initialize_parameters(self, names: Optional[List[str]] = None, values: Optional[List[Any]] = None):
        left_names = list(self._left_model.parameters.keys())
        right_names = list(self._right_model.parameters.keys())
        names = left_names + right_names
        values = []
        for n in left_names:
            if hasattr(self._left_model.parameters[n], 'raw_value'):
                values.append([self._left_model.parameters[n].raw_value])
            else:
                values.append([self._left_model.parameters[n]])
        for n in right_names:
            if hasattr(self._right_model.parameters[n], 'raw_value'):
                values.append([self._right_model.parameters[n].raw_value])
            else:
                values.append([self._right_model.parameters[n]])
        super(CompositeModel, self)._initialize_parameters(names=names, values=values)

    def __call__(self, x, *args, **kwargs):
        left = dict.fromkeys(self._left_model.parameters.keys())
        right = dict.fromkeys(self._right_model.parameters.keys())

        if len(args) == len(left) + len(right):
            for name, value in zip(left.keys(), args[:len(left)]):
                left[name] = value
            for name, value in zip(right.keys(), args[len(left):]):
                right[name] = value
        else:
            for key in left.keys():
                if key in kwargs.keys():
                    left[key] = kwargs[key]
            for key in right.keys():
                if key in kwargs.keys():
                    right[key] = kwargs[key]

        return super(CompositeModel, self).__call__(self._left_model(x, **left),
                                                    self._right_model(x, **right), **self._function_kwargs)

#
# class FunctionalContainer:
#     def __init__(self, initial, multi_threaded: bool = False):
#         fn, pars = self._check_other(initial)
#         self._stack = [(fn, pars, None, False)]
#         self._cache = False
#         self._runtime = []
#         self._calls = 0
#         self.__gu = None
#         self._generate_signature()
#         self._multi_threaded = multi_threaded
#         self.fitting = False
#         self._chunks = ()
#         self.__temp_dependent = None
#         self._profile_results = None
#
#     def reset(self):
#         self._runtime = []
#         self._calls = 0
#         for item in self._stack:
#             item[0].reset_count()
#
#     def profile(self, dependent_spacing, dependent_generator, samples, *args, **kwargs):
#         x = {int(N): [int(N)] for N in dependent_spacing}
#         sp = 0
#         ep = 0
#         for item in self._stack:
#             fn, pars, op, use_previous = item
#             ep = ep + len(pars)
#             fp = fnProfiler(fn.function)
#             fp.profile(x, gen_func=dependent_generator, samples=samples, *args[sp:ep], **kwargs)
#             sp = ep
#             print(fp)
#
#     def _check_other(self, other: Callable):
#         if isinstance(other, Functional):
#             return other, other._parameters
#         else:
#             f = Functional(other)
#             return f, f._parameters
#
#     def _generate_signature(self):
#         params = [inspect.Parameter(
#             "x", inspect.Parameter.POSITIONAL_ONLY, annotation=inspect._empty
#         )]
#         for item in self._stack:
#             fn, pars, tmp, _ = item
#             if fn is None:
#                 continue
#             params += [inspect.Parameter(
#                 n, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=inspect._empty, default=v
#             ) for n, v in pars.items()]
#         self.reset()
#         self.__call__.__func__.__signature__ = inspect.Signature(params)
#         self.__gu = da.gufunc(self.__hidden_call, signature=('(),'*len(params))[:-1] + ' -> ()')
#
#     def add(self, other: Callable, use_previous: bool = False):
#         fn, pars = self._check_other(other)
#         self._stack.append((fn, pars, np.add, use_previous))
#         self._generate_signature()
#
#     def subtract(self, other: Callable, use_previous: bool = False):
#         fn, pars = self._check_other(other)
#         self._stack.append((fn, pars, np.subtract, use_previous))
#         self._generate_signature()
#
#     def multiply(self, other: Callable, use_previous: bool = False):
#         fn, pars = self._check_other(other)
#         self._stack.append((fn, pars, np.multiply, use_previous))
#         self._generate_signature()
#
#     def divide(self, other: Callable, use_previous: bool = False):
#         fn, pars = self._check_other(other)
#         self._stack.append((fn, pars, np.divide, use_previous))
#         self._generate_signature()
#
#     def __call__(self, x, *args, **kwargs):
#         x_calc = x
#         if len(self._chunks) > 0:
#             # Check
#             if self.__temp_dependent is None:
#                 self.__temp_dependent = da.from_array(x, chunks=self._chunks)
#             else:
#                 if not self.fitting:
#                     logic = da.all(x_calc == self.__temp_dependent)
#                     if not logic.compute():
#                         self.__temp_dependent = da.from_array(x, chunks=self._chunks)
#             x_calc = self.__temp_dependent
#             return self.__gu(x_calc, *args, **kwargs).compute()
#         else:
#             return self.__hidden_call(x_calc, *args, **kwargs)
#
#     def __hidden_call(self, x, *args, **kwargs):
#         self._calls += 1
#         start = perf_counter()
#         sp = 0
#         if self.multi_threaded:
#             with cf.ProcessPoolExecutor() as executor:
#                 spep = []
#                 ops = []
#                 args = list(args)
#                 ep = 0
#                 futures = {}
#                 for idx, item in enumerate(self._stack):
#                     fn, pars, op, use_previous = item
#                     ep = ep + len(pars)
#                     spep.append((sp, ep))
#                     ops.append(op)
#                     if idx == 0 and len(args) == 0:
#                         args += list(pars.values())
#                     future = executor.submit(fn, x, *args[sp:ep], **kwargs)
#                     sp = ep
#                     futures[future] = idx
#                 results = dict.fromkeys(range(len(self._stack)))
#                 for future in cf.as_completed(futures):
#                     idx = futures[future]
#                     results[idx] = future.result()
#                 result = results[0]
#                 for idx in range(1, len(self._stack)):
#                     result = ops[idx](result, results[idx])
#         else:
#             ep = len(self._stack[0][1])
#             result = self._stack[0][0](x, *args[sp:ep], **kwargs)
#             for item in self._stack[1::]:
#                 fn, pars, op, use_previous = item
#                 sp = ep
#                 ep = ep + len(pars)
#                 result = op(result, fn(x, *args[sp:ep], **kwargs))
#             # if self._calls == 1 and self._multi_threaded:
#             #     timings = [item[0].runtime for item in self._stack]
#                 # if sum(timings)/len(timings)  and  max(timings)/min(timings) > 1.5:
#         self._runtime.append(perf_counter() - start)
#         return result
#
#     def custom_function(self, function: Callable, other: Callable):
#         fn, pars = self._check_other(other)
#         self._stack.append((fn, pars, function, False))
#         self._generate_signature()
#
#     @property
#     def runtime(self) -> float:
#         return sum(self._runtime)
#
#     @property
#     def overhead(self) -> float:
#         return self.runtime - self.functional_runtime
#
#     @property
#     def functional_runtime(self) -> float:
#         return sum([item[0].runtime for item in self._stack])
#
#     @property
#     def calls(self) -> int:
#         return self._calls
#
#     @property
#     def multi_threaded(self) -> bool:
#         return self._multi_threaded
#
#     @multi_threaded.setter
#     def multi_threaded(self, multi_threaded: bool):
#         self._multi_threaded = multi_threaded
#
#     @property
#     def chunks(self):
#         return self._chunks
#
#     @chunks.setter
#     def chunks(self, chunksize:Tuple[int]):
#         self._chunks = chunksize
#
#     @property
#     def default_parameters(self) -> List[float]:
#         pars = []
#         for item in self._stack:
#             pars += list(item[1].values())
#         return pars