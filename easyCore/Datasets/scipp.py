#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import scipp as sc

from easyCore import np
from .extensions import register_accessor
from easyCore.Fitting.fitting_template import FitResults


@register_accessor('easyFitting', sc.DataArray)
class easyFitting:
    def __init__(self, scipp_obj=None):
        self._obj = scipp_obj
        self.fit_function = None

    def __repr__(self):
        return repr(self._obj)

    def fit(self, fitter, *args,
            fit_kwargs: dict = None,
            fn_kwargs: dict = None) -> FitResults:
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
        pass


def check_sanity_single(fit_results: FitResults) -> FitResults:
    """
    Convert the FitResults from a fitter compatible state to a recognizable DataArray state.

    :param fit_results: Results of a fit to be modified
    :type fit_results: FitResults
    :return: Modified fit results
    :rtype: FitResults
    """
    items = ['y_obs', 'y_calc', 'residual']

    for item in items:
        array = getattr(fit_results, item)
        if isinstance(array, sc.DataArray):
            array = array.unstack()
            array.name = item
            setattr(fit_results, item, array)

    x_array = fit_results.x
    if isinstance(x_array, sc.DataArray):
        fit_results.x.name = 'axes_broadcast'
        x_array = x_array.unstack()
        x_dataset = sc.Dataset()
        dims = [dims for dims in x_array.dims if dims != 'fit_dim']
        for idx, dim in enumerate(dims):
            x_dataset[dim + '_broadcast'] = x_array[idx]
            x_dataset[dim + '_broadcast'].name = dim + '_broadcast'
        fit_results.x_matrices = x_dataset
    else:
        fit_results.x_matrices = x_array
    return fit_results
