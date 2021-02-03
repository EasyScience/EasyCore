__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Callable, Union, TypeVar, List, Tuple

import weakref
import xarray as xr

from easyCore import np, ureg

T_ = TypeVar('T_')


@xr.register_dataset_accessor("easyCore")
class easyCoreDatasetAccessor:
    """
    Accessor to extend an xarray dataset to easyCore. These functions can be accessed by `obj.easyCore.func`.
    """

    def __init__(self, xarray_obj: xr.Dataset):
        self._obj = xarray_obj
        self._core_object = None
        self.__error_mapper = {}
        self.sigma_label_prefix = 's_'
        self._obj.attrs['units'] = {}
        self._obj.attrs['name'] = ''
        self._obj.attrs['description'] = ''
        self._obj.attrs['url'] = ''
        self._obj.attrs['computation'] = {
            'precompute_func':  None,
            'compute_func':     None,
            'postcompute_func': None
        }

    @property
    def name(self) -> str:
        return self._obj.attrs['name']

    @name.setter
    def name(self, value: str):
        self._obj.attrs['name'] = value

    @property
    def description(self) -> str:
        return self._obj.attrs['description']

    @description.setter
    def description(self, value: str):
        self._obj.attrs['description'] = value

    @property
    def url(self) -> str:
        return self._obj.attrs['url']

    @url.setter
    def url(self, value: str):
        self._obj.attrs['url'] = value

    @property
    def core_object(self):
        if self._core_object is None:
            return None
        return self._core_object()

    @core_object.setter
    def core_object(self, new_core_object):
        self._core_object = weakref.ref(new_core_object)

    @property
    def compute_func(self):
        return self._obj.attrs['computation']['compute_func']

    @compute_func.setter
    def compute_func(self, value: Callable):
        self._obj.attrs['computation']['compute_func'] = value

    @property
    def precompute_func(self):
        return self._obj.attrs['computation']['precompute_func']

    @precompute_func.setter
    def precompute_func(self, value: Callable):
        self._obj.attrs['computation']['precompute_func'] = value

    def add_dimension(self, axis_name: str, axis_values: Union[List[T_], np.ndarray], unit=''):
        self._obj.coords[axis_name] = axis_values
        self._obj.attrs['units'][axis_name] = ureg.Unit(unit)

    def remove_dimension(self, axis_name: str):
        # TODO This should check coords and fail if coord is in use
        del self._obj.coords[axis_name]
        del self._obj.attrs['units'][axis_name]

    def add_variable(self, variable_name, variable_dimension: Union[str, List[str]],
                     variable_values: Union[List[T_], np.ndarray], variable_sigma: Union[List[T_], np.ndarray] = None,
                     unit: str = '', auto_sigma: bool = False):

        if isinstance(variable_dimension, str):
            variable_dimension = [variable_dimension]

        if not isinstance(variable_dimension, (list, tuple)):
            raise ValueError

        known_keys = self._obj.coords.keys()
        for dimension in variable_dimension:
            if dimension not in known_keys:
                raise ValueError

        self._obj[variable_name] = (variable_dimension, variable_values)

        if variable_sigma is not None:
            if isinstance(variable_sigma, (Callable, np.ndarray)):
                self.sigma_generator(variable_name, variable_sigma)
            elif isinstance(variable_sigma, list):
                self.sigma_generator(variable_name, np.array(variable_sigma))
        else:
            if auto_sigma:
                self.sigma_generator(variable_name)

        self._obj.attrs['units'][variable_name] = ureg.Unit(unit)
        if unit and variable_sigma is None and auto_sigma:
            self._obj.attrs['units'][self.sigma_label_prefix + variable_name] = ureg.Unit(unit + ' ** 0.5')
        else:
            if auto_sigma:
                self._obj.attrs['units'][self.sigma_label_prefix + variable_name] = ureg.Unit('')

    def remove_variable(self, variable_name: str):
        del self._obj[variable_name]

    def sigma_generator(self, variable_label: str, sigma_func: Callable = np.sqrt, label_prefix: str = 's_'):
        sigma_label = label_prefix + variable_label
        self.__error_mapper[variable_label] = sigma_label
        self._obj[sigma_label] = (list(self._obj[variable_label].coords.keys()), sigma_func(self._obj[variable_label]))

    def sigma_attach(self, variable_label: str, sigma_values, label_prefix: str = None):
        if label_prefix is None:
            label_prefix = self.sigma_label_prefix
        sigma_label = label_prefix + variable_label
        self.__error_mapper[variable_label] = sigma_label
        self._obj[sigma_label] = (list(self._obj[variable_label].coords.keys()), sigma_values)

    def generate_points(self, dimensions) -> xr.DataArray:
        coords = [self._obj.coords[da] for da in dimensions]
        c_array = []
        n_array = []
        for da in xr.broadcast(*coords):
            c_array.append(da)
            n_array.append(da.name)

        f = xr.concat(c_array, dim='fit_dim')
        f = f.stack(all_x=n_array)
        return f


@xr.register_dataarray_accessor("easyCore")
class easyCoreDataarrayAccessor:
    """
    Accessor to extend an xarray dataset to easyCore. These functions can be accessed by `obj.easyCore.func`.
    """

    def __init__(self, xarray_obj: xr.DataArray):
        self._obj = xarray_obj
        self._core_object = None
        self.sigma_label_prefix = 's_'
        if self._obj.attrs.get('computation', None) is None:
            self._obj.attrs['computation'] = {
                'precompute_func':  None,
                'compute_func': None,
                'postcompute_func': None
            }

    def __empty_functional(self) -> Callable:

        def outer():
            def empty_fn(input, *args, **kwargs):
                return input
            return empty_fn

        class wrapper:
            def __init__(obj):
                obj.obj = self
                obj.data = {}
                obj.fn = outer()

            def __call__(self, *args, **kwargs):
                return self.fn(*args, **kwargs)

        return wrapper()

    @property
    def core_object(self):
        if self._core_object is None:
            return None
        return self._core_object()

    @core_object.setter
    def core_object(self, new_core_object):
        self._core_object = weakref.ref(new_core_object)

    @property
    def compute_func(self):
        result = self._obj.attrs['computation']['compute_func']
        if result is None:
            result = self.__empty_functional()
        return result

    @compute_func.setter
    def compute_func(self, value: Callable):
        self._obj.attrs['computation']['compute_func'] = value

    @property
    def precompute_func(self):
        result = self._obj.attrs['computation']['precompute_func']
        if result is None:
            result = self.__empty_functional()
        return result

    @precompute_func.setter
    def precompute_func(self, value: Callable):
        self._obj.attrs['computation']['precompute_func'] = value

    @property
    def postcompute_func(self):
        result = self._obj.attrs['computation']['postcompute_func']
        if result is None:
            result = self.__empty_functional()
        return result

    @postcompute_func.setter
    def postcompute_func(self, value: Callable):
        self._obj.attrs['computation']['postcompute_func'] = value

    def fit_prep(self, func_in, dask_chunks=None):

        coords = [self._obj.coords[da].transpose() for da in self._obj.dims]
        bdims = xr.broadcast(*coords)
        self._obj.attrs['computation']['compute_func'] = func_in

        def func(x, *args, vectorize: bool = False, **kwargs):
            old_shape = x.shape
            if not vectorize:
                xs = [x_new.flatten() for x_new in [x, *args] if isinstance(x_new, np.ndarray)]
                x_new = np.column_stack(xs)
                if len(x_new.shape) > 1 and x_new.shape[1] == 1:
                    x_new = x_new.reshape((-1))
                result = self.compute_func(x_new, **kwargs)
            else:
                result = self.compute_func(*[d for d in [x, args] if isinstance(d, np.ndarray)],
                                 *[d for d in args if not isinstance(d, np.ndarray)],
                                 **kwargs)
            if isinstance(result, np.ndarray):
                result = result.reshape(old_shape)
            result = self.postcompute_func(result)
            return result

        return bdims, func

    def generate_points(self) -> xr.DataArray:
        coords = [self._obj.coords[da] for da in self._obj.dims]
        c_array = []
        n_array = []
        for da in xr.broadcast(*coords):
            c_array.append(da)
            n_array.append(da.name)

        f = xr.concat(c_array, dim='fit_dim')
        f = f.stack(all_x=n_array)
        return f

    def fit(self, fitter, *args, dask: str = 'forbidden', fit_kwargs={}, fn_kwargs={}, vectorize: bool = False, **kwargs):

        old_fit_func = fitter.fit_function

        bdims, f = self.fit_prep(fitter.fit_function)
        dims = self._obj.dims
        if isinstance(dims, dict):
            dims = list(dims.keys())

        def fit_func(x, *args, **kwargs):
            kwargs['vectorize'] = vectorize
            res = xr.apply_ufunc(f, *bdims, *args, dask=dask, kwargs=fn_kwargs, **kwargs)
            if dask != 'forbidden':
                res.compute()
            return res.stack(all_x=dims)

        fitter.initialize(fitter.fit_object, fit_func)
        x_for_fit = xr.concat(bdims, dim='fit_dim')
        x_for_fit = x_for_fit.stack(all_x=[d.name for d in bdims])
        try:
            f_res = fitter.fit(x_for_fit, self._obj.stack(all_x=dims), **fit_kwargs)
        finally:
            fitter.fit_function = old_fit_func
        return f_res
