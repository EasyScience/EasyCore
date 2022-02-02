#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import numpy as np
import pymc3 as pm
import theano
import theano.tensor as tt
from .likelihoods import LogLikeWithGrad, _LogLikeWithGrad
from easyCore.Utils.classTools import NameConverter


class Wrapper:
    def __init__(self, model, function_name, use_quickset=False):
        self.model = model
        self.fit_function = function_name
        self._quickset = use_quickset
        self._cached_pars = {id(self.model): self.model.get_fit_parameters()}

    @property
    def fit_function(self):
        """
        Function of the model which will be called to generate the data.
        """
        return self._fit_function

    @fit_function.setter
    def fit_function(self, value):
        """
        Set the function of the model which will be called to generate the data.
        """
        self._fit_function = getattr(self.model, value)

    @property
    def cached_pars(self):
        """
        Return a list of the parameters that are currently cached.
        A dict is used due to pymc3 using threading, we need each parameter to be associated with the correct model.
        """
        if id(self.model) in self._cached_pars.keys():
            pars = self._cached_pars[id(self.model)]
        else:
            pars = self.model.get_fit_parameters()
            self._cached_pars[id(self.model)] = pars
        return pars

    def __call__(self, theta, x):
        """
        Update parameters and call the underlying model.
        """
        pars = self.cached_pars
        quickset = self._quickset
        for p, v in zip(pars, theta):
            if quickset:
                p._quick_set(v)
            else:
                # This is the slow bottleneck. :-(
                p.value = v
        #  Call model
        return self.fit_function(x)


class Sampler:

    supported_sampling = ["DENSITY", "NORMAL"]

    def __init__(
        self, easy_model, fit_function=None, sample_type="DENSITY", use_quickset=False
    ):
        self._sampling = None
        self.sampling = sample_type
        self._use_quickset = None
        self._fit_function = None
        self.base_model = None
        if self.sampling == "NORMAL":
            return
        self.base_model = easy_model
        self.fit_function = fit_function
        self.model = Wrapper(easy_model, fit_function, use_quickset)
        self._distribution_function = LogLikeWithGrad(self.model)
        self.use_quickset = use_quickset

    @property
    def sampling(self):
        return self._sampling

    @sampling.setter
    def sampling(self, sample_type):
        sample_type = sample_type.upper()
        if sample_type not in self.supported_sampling:
            raise AttributeError(
                "Sampling type not supported. Supported types are: {}".format(
                    self.supported_sampling
                )
            )
        self._sampling = sample_type

    @property
    def distribution_function(self):
        return self._distribution_function

    @distribution_function.setter
    def distribution_function(self, value):
        self._distribution_function = value

    @property
    def use_quickset(self) -> bool:
        """
        Should we use the quickset feature. This speeds up the setting of parameters, but in reality this might not
        be the bottleneck. Use with caution.
        """
        return self._use_quickset

    @use_quickset.setter
    def use_quickset(self, value: bool):
        """
        Should we use the quickset feature. This speeds up the setting of parameters, but in reality this might not
        be the bottleneck. Use with caution.
        """
        self._use_quickset = value
        self.model._quickset = value

    def sample(self, x_data, y_data, sigma, n_samples=1000, n_chains=4, tune=1000):

        n_conv = NameConverter()

        if self.sampling == "DENSITY":
            # create our Op
            dist = self.distribution_function
            dist.initialize(x_data, y_data, sigma)
            pars = self.base_model.get_fit_parameters()
            wrapped_pars = []
            # use PyMC3 to sampler from log-likelihood
            with pm.Model():
                # Get fit parameters

                # Define priors# uniform priors on m and c
                for par in pars:
                    name = str(n_conv.get_key(par))
                    p = _to_pymc3_distribution(name, par)
                    wrapped_pars.append(p)
                priors = [*wrapped_pars]
                # convert m and c to a tensor vector
                theta = tt.as_tensor_variable(priors)

                # use a DensityDist (use a lamdba function to "call" the Op)
                pm.DensityDist("likelihood", lambda v: dist(v), observed={"v": theta})
                trace = pm.sample(
                    n_samples,
                    tune=tune,
                    chains=n_chains,
                    discard_tuned_samples=True,
                    return_inferencedata=True,
                    idata_kwargs={"density_dist_obs": False},
                )
        elif self.sampling == "NORMAL":
            raise NotImplementedError("Sampling type is not yet implemented")
            # # create our Op
            # try:
            #     model = pymc3_model(self.base_model, self.fit_function,
            #                         x_data, y_data, sigma)
            #     with model:
            #         trace = pm.sample(n_samples, tune=tune, chains=n_chains)
            # except Exception:
            #     old_sampling = self.sampling
            #     self.sampling = "DENSITY"
            #     trace = self.sample(x_data, y_data, sigma, n_samples=n_samples, n_chains=n_chains, tune=tune)
            #     self.sampling = old_sampling
        else:
            raise ValueError(
                "Sampling type not supported. Supported types are: {}".format(
                    self.supported_sampling
                )
            )

        return trace


# def pymc3_model(objective, fit_function = None, x = None, y = None, sigma = None):
#
#     basic_model = pm.Model()
#     if not isinstance(objective, Objective):
#         objective = Objective(objective, fit_function, x, y, sigma)
#
#     n_conv = NameConverter()
#     pars = objective.model.get_fit_parameters()
#     wrapped_pars = []
#     with basic_model:
#         # Priors for unknown model parameters
#         for par in pars:
#             name = str(n_conv.get_key(par))
#             p = _to_pymc3_distribution(name, par)
#             wrapped_pars.append(p)
#
#         # Expected value of outcome
#         # try:
#             # Likelihood (sampling distribution) of observations
#         pm.Normal(
#             "y_obs",
#             mu=pm.Flat("y_pred"),
#             sigma=objective.data['sigma'],
#             observed=objective.data['y'],
#         )
#     return basic_model


def _to_pymc3_distribution(name, par):
    """
    Create a pymc3 continuous distribution from a Bounds object.
    Parameters
    ----------
    name : str
        Name of parameter
    par : refnx.analysis.Parameter
        The parameter to wrap
    Returns
    -------
    d : pymc3.Distribution
        The pymc3 distribution
    """
    import pymc3 as pm

    # interval and both lb, ub are finite
    if np.isfinite([par.min, par.max]).all():
        return pm.Uniform(name, par.min, par.max)
    # no bounds
    elif np.isneginf(par.min) and np.isinf(par.max):
        return pm.Flat(name)
    # half open uniform
    elif not np.isfinite(par.min):
        return par.max - pm.HalfFlat(name)
    # half open uniform
    elif not np.isfinite(par.max):
        return par.min + pm.HalfFlat(name)
