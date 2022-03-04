#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import scipp as sc

from typing import Callable, Union, TypeVar, List, Tuple, Any, Iterable, TYPE_CHECKING

import weakref
from easyCore import np
from .extensions.scipp_accessors import register_accessor
from easyCore.Fitting.fitting_template import FitResults

T_ = TypeVar("T_")

if TYPE_CHECKING:
    from easyCore.Fitting.Fitting import Fitter


@register_accessor("easyCore", sc.DataArray)
class easyCoreDataarrayAccessor:
    """
    Accessor to extend an xarray DataArray to easyCore. These functions can be accessed by `obj.easyCore.func`.

    """

    def __init__(self, xarray_obj: sc.DataArray):
        self._obj = xarray_obj
        self._core_object = None
        self.sigma_label_prefix = "s_"
        self._compute_func = None

    @property
    def core_object(self):
        """
        Get the core object associated to a DataArray. Note that this is called from a weakref. If the easyCore obj is
        garbage collected, None will be returned.

        :return: easyCore object associated with the DataArray
        :rtype: Any
        """
        if self._core_object is None:
            return None
        return self._core_object()

    @core_object.setter
    def core_object(self, new_core_object: Any):
        """
        Set the core object associated to a dataset

        :param new_core_object: easyCore object to be associated with the DataArray
        :type new_core_object: Any
        :return: None
        :rtype: None
        """
        self._core_object = weakref.ref(new_core_object)

    def fit_prep(
        self, func_in: Callable, bdims=None, dask_chunks=None
    ) -> Tuple[sc.DataArray, Callable]:
        """
        Generate boradcasted coordinates for fitting and reform the fitting function into one which can handle xarrays

        :param func_in: Function to be wrapped and made xarray fitting compatable.
        :type func_in: Callable
        :param bdims: Optional precomputed broadcasted dimensions.
        :type bdims: xarray.DataArray
        :param dask_chunks: How to split to broadcasted dimensions for dask.
        :type dask_chunks: Tuple[int..]
        :return: Tuple of broadcasted fit arrays and wrapped fit function.
        :rtype: xarray.DataArray, Callable
        """

        if bdims is None:
            coords = [self._obj.coords[da].transpose() for da in self._obj.dims]
            bdims = [
                sc.broadcast(a, self._obj.data.dims, self._obj.data.shape)
                for a in coords
            ]
        self._compute_func = func_in

        def func(x, *args, vectorize: bool = False, **kwargs):
            old_shape = x.shape
            if not vectorize:
                xs = [
                    x_new.flatten()
                    for x_new in [x, *args]
                    if isinstance(x_new, np.ndarray)
                ]
                x_new = np.column_stack(xs)
                if len(x_new.shape) > 1 and x_new.shape[1] == 1:
                    x_new = x_new.reshape((-1))
                result = self._compute_func(x_new, **kwargs)
            else:
                result = self._compute_func(
                    *[d for d in [x, args] if isinstance(d, np.ndarray)],
                    *[d for d in args if not isinstance(d, np.ndarray)],
                    **kwargs,
                )
            if isinstance(result, np.ndarray):
                result = result.reshape(old_shape)
            return result

        return bdims, func

    def generate_points(self) -> sc.DataArray:
        """
        Generate an expanded DataArray of points which corresponds to broadcasted dimensions (`all_x`) which have been
        concatenated along the second axis (`fit_dim`).

        :return: Broadcasted and concatenated coordinates
        :rtype: xarray.DataArray
        """

        coords = [self._obj.coords[da] for da in self._obj.dims]
        c_array = []
        n_array = []
        for da in sc.broadcast(*coords):
            c_array.append(da)
            n_array.append(da.name)

        f = sc.concat(c_array, dim="fit_dim")
        f = f.stack(all_x=n_array)
        return f

    def fit(
        self,
        fitter,
        *args,
        fit_kwargs: dict = None,
        fn_kwargs: dict = None,
        vectorize: bool = False,
        dask: str = "forbidden",
        **kwargs,
    ) -> FitResults:
        """
        Perform a fit on the given DataArray. This fit utilises a given fitter from `easyCore.Fitting.Fitter`, though
        there are a few differences to a standard easyCore fit. In particular, key-word arguments to control the
        optimisation algorithm go in the `fit_kwargs` dictionary, fit function key-word arguments go in the `fn_kwargs`
        and given key-word arguments control the `xarray.apply_ufunc` function.

        :param fitter: Fitting object which controls the fitting
        :type fitter: easyCore.Fitting.Fitter
        :param args: Arguments to go to the fit function
        :type args: Any
        :param dask: Dask control string. See `xarray.apply_ufunc` documentation
        :type dask: str
        :param fit_kwargs: Dictionary of key-word arguments to be supplied to the Fitting control
        :type fit_kwargs: dict
        :param fn_kwargs: Dictionary of key-words to be supplied to the fit function
        :type fn_kwargs: dict
        :param vectorize: Should the fit function be given dependents in a single object or split
        :type vectorize: bool
        :param kwargs: Key-word arguments for `xarray.apply_ufunc`. See `xarray.apply_ufunc` documentation
        :type kwargs: Any
        :return: Results of the fit
        :rtype: FitResults
        """

        # Deal with any kwargs which has been given
        if fn_kwargs is None:
            fn_kwargs = {}
        if fit_kwargs is None:
            fit_kwargs = {}
        old_fit_func = fitter.fit_function

        # Wrap and broadcast
        bdims, f = self.fit_prep(fitter.fit_function)
        dims = self._obj.dims

        # Find which coords we need
        if isinstance(dims, dict):
            dims = list(dims.keys())

        # # Wrap the wrap in a callable
        # def local_fit_func(x, *args, **kwargs):
        #     """
        #     Function which will be called by the fitter. This will deal with sending the function the correct data.
        #     """
        #     kwargs["vectorize"] = vectorize
        #     fn_kwargs["vectorize"] = vectorize
        #     res = xr.apply_ufunc(
        #         f, *bdims, *args, dask=dask, kwargs=fn_kwargs, **kwargs
        #     )
        #     if dask != "forbidden":
        #         res.compute()
        #     return res.stack(all_x=dims)

        # Set the new callable to the fitter and initialize
        fitter.initialize(fitter.fit_object, f)
        # Make easyCore.Fitting.Fitter compatible `x`
        x_for_fit = sc.concat(bdims, dim="fit_dim")
        x_for_fit = sc.flatten(x_for_fit, to="all_x")
        # x_for_fit = x_for_fit.stack(all_x=[d.name for d in bdims])
        try:
            # Deal with any sigmas if supplied
            if fit_kwargs.get("weights", None) is not None:
                fit_kwargs["weights"] = sc.DataArray(
                    np.array(fit_kwargs["weights"]),
                    dims=["all_x"],
                    coords={"all_x": x_for_fit.all_x},
                )
            # Try to perform a fit
            f_res = fitter.fit(
                x_for_fit.values, sc.flatten(self._obj, to="all_x").values, **fit_kwargs
            )
            f_res = check_sanity_single(f_res)
        finally:
            # Reset the fit function on the fitter to the old fit function.
            fitter.fit_function = old_fit_func
        return f_res


def check_sanity_single(fit_results: FitResults) -> FitResults:
    """
    Convert the FitResults from a fitter compatible state to a recognizable DataArray state.

    :param fit_results: Results of a fit to be modified
    :type fit_results: FitResults
    :return: Modified fit results
    :rtype: FitResults
    """
    items = ["y_obs", "y_calc", "residual"]

    for item in items:
        array = getattr(fit_results, item)
        if isinstance(array, sc.DataArray):
            array = array.unstack()
            array.name = item
            setattr(fit_results, item, array)

    x_array = fit_results.x
    if isinstance(x_array, sc.DataArray):
        fit_results.x.name = "axes_broadcast"
        x_array = x_array.unstack()
        x_dataset = sc.Dataset()
        dims = [dims for dims in x_array.dims if dims != "fit_dim"]
        for idx, dim in enumerate(dims):
            x_dataset[dim + "_broadcast"] = x_array[idx]
            x_dataset[dim + "_broadcast"].name = dim + "_broadcast"
        fit_results.x_matrices = x_dataset
    else:
        fit_results.x_matrices = x_array
    return fit_results
