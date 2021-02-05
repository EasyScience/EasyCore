__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Callable, Union, TypeVar, List, Tuple

import weakref
import xarray as xr

from easyCore import np, ureg
from easyCore.Fitting.fitting_template import FitResults

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
        if self._obj.attrs.get('name', None) is None:
            self._obj.attrs['name'] = ''
        if self._obj.attrs.get('description', None) is None:
            self._obj.attrs['description'] = ''
        if self._obj.attrs.get('url', None) is None:
            self._obj.attrs['url'] = ''
        if self._obj.attrs.get('units', None) is None:
            self._obj.attrs['units'] = {}

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

    def sigma_generator(self, variable_label: str, sigma_func: Callable = lambda x: np.sqrt(np.abs(x)), label_prefix: str = 's_'):
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

    def fit(self, fitter, data_arrays: list, *args, dask: str = 'forbidden', fit_kwargs=None, fn_kwargs=None, vectorize: bool = False, **kwargs):
        if fn_kwargs is None:
            fn_kwargs = {}
        if fit_kwargs is None:
            fit_kwargs = {}
        if not isinstance(data_arrays, (list, tuple)):
            data_arrays = [data_arrays]

        # In this case we are only fitting 1 dataset
        if len(data_arrays) == 1:
            variable_label = data_arrays[0]
            dataset = self._obj[variable_label]
            if self.__error_mapper.get(variable_label, False):
                # Pull out any sigmas and send them to the fitter.
                temp = self._obj[self.__error_mapper[variable_label]]
                temp[xr.ufuncs.isnan(temp)] = 1e5
                fit_kwargs['weights'] = temp
            # Perform a standard DataArray fit.
            return dataset.easyCore.fit(fitter, *args,
                                        fit_kwargs=fit_kwargs,
                                        fn_kwargs=fn_kwargs,
                                        dask=dask,
                                        vectorize=vectorize,
                                        **kwargs)
        else:
            # In this case we are fitting multiple datasets to the same fn!
            bdim_f = [self._obj[p].easyCore.fit_prep(fitter.fit_function) for p in data_arrays]
            dim_names = [list(self._obj[p].dims.keys()) if isinstance(self._obj[p].dims, dict) else self._obj[p].dims for p in data_arrays]
            bdims = [bdim[0] for bdim in bdim_f]
            fs = [bdim[1] for bdim in bdim_f]
            old_fit_func = fitter.fit_function

            fn_array = []
            y_list = []
            for _idx, d in enumerate(bdims):
                dims = self._obj[data_arrays[_idx]].dims
                if isinstance(dims, dict):
                    dims = list(dims.keys())

                def fit_func(x, *args, idx=None, **kwargs):
                    kwargs['vectorize'] = vectorize
                    res = xr.apply_ufunc(fs[idx], *bdims[idx], *args, dask=dask, kwargs=fn_kwargs, **kwargs)
                    if dask != 'forbidden':
                        res.compute()
                    return res.stack(all_x=dim_names[idx])
                y_list.append(self._obj[data_arrays[_idx]].stack(all_x=dims))
                fn_array.append(fit_func)

            def fit_func(x, *args, **kwargs):
                res = []
                for idx in range(len(fn_array)):
                    res.append(fn_array[idx](x, *args, idx=idx, **kwargs))
                return xr.DataArray(np.concatenate(res, axis=0), coords={'all_x': x}, dims='all_x')

            fitter.initialize(fitter.fit_object, fit_func)
            try:
                if fit_kwargs.get('weights', None) is not None:
                    del fit_kwargs['weights']
                x = xr.DataArray(np.arange(np.sum([y.size for y in y_list])), dims='all_x')
                y = xr.DataArray(np.concatenate(y_list, axis=0), coords={'all_x': x}, dims='all_x')
                f_res = fitter.fit(x, y, **fit_kwargs)
                f_res = check_sanity_multiple(f_res, [self._obj[p] for p in data_arrays])
            finally:
                fitter.fit_function = old_fit_func
            return f_res


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

    def fit_prep(self, func_in, bdims=None, dask_chunks=None):

        if bdims is None:
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
            if fit_kwargs.get('weights', None) is not None:
                fit_kwargs['weights'] = xr.DataArray(
                    np.array(fit_kwargs['weights']),
                    dims=['all_x'],
                    coords={'all_x': x_for_fit.all_x}
                )
            f_res = fitter.fit(x_for_fit, self._obj.stack(all_x=dims), **fit_kwargs)
            f_res = check_sanity_single(f_res)
        finally:
            fitter.fit_function = old_fit_func
        return f_res


def check_sanity_single(fit_results: FitResults):

    items = ['y_obs', 'y_calc', 'residual']

    for item in items:
        array = getattr(fit_results, item)
        if isinstance(array, xr.DataArray):
            array = array.unstack()
            array.name = item
            setattr(fit_results, item, array)

    x_array = fit_results.x
    if isinstance(x_array, xr.DataArray):
        fit_results.x.name = 'axes_broadcast'
        x_array = x_array.unstack()
        x_dataset = xr.Dataset()
        dims = [dims for dims in x_array.dims if dims != 'fit_dim']
        for idx, dim in enumerate(dims):
            x_dataset[dim + '_broadcast'] = x_array[idx]
            x_dataset[dim + '_broadcast'].name = dim + '_broadcast'
        fit_results.x_matrices = x_dataset
    else:
        fit_results.x_matrices = x_array
    return fit_results


def check_sanity_multiple(fit_results: FitResults, originals: List[xr.DataArray]) -> List[FitResults]:

    return_results = []
    offset = 0
    for item in originals:
        current_results = fit_results.__class__()
        # Fill out the basic stuff....
        current_results.engine_result = fit_results.engine_result
        current_results.fitting_engine = fit_results.fitting_engine
        current_results.success = fit_results.success
        current_results.p = fit_results.p
        current_results.p0 = fit_results.p0
        # now the tricky stuff
        current_results.x = item.easyCore.generate_points()
        current_results.y_obs = item.copy()
        current_results.y_obs.name = f'{item.name}_obs'
        current_results.y_calc = xr.DataArray(
            fit_results.y_calc[offset:offset+item.size].data,
            dims=item.dims,
            coords=item.coords,
            name=f'{item.name}_calc'
        )
        offset += item.size
        current_results.residual = current_results.y_calc - current_results.y_obs
        current_results.residual.name = f'{item.name}_residual'
        return_results.append(current_results)
    return return_results
