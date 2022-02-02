#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from abc import abstractmethod

import numpy as np
import theano
import theano.tensor as tt

# import pyximport; pyximport.install()
# from .Gradient import gradients
from scipy.stats import multivariate_normal
from scipy.optimize._numdiff import approx_derivative


class LogBase(tt.Op):
    itypes = [tt.dvector]  # expects a vector of parameter values when called
    otypes = [tt.dscalar]  # outputs a single scalar value (the log likelihood)

    def __init__(self, model, logistic=None):
        """
        Initialise with various things that the function requires. Below
        are the things that are needed in this particular example.

        Parameters
        ----------
        loglike:
            The log-likelihood (or whatever) function we've defined
        data:
            The "observed" data that our log-likelihood function takes in
        x:
            The dependent variable (aka 'x') that our model requires
        sigma:
            The noise standard deviation that out function requires.
        """

        # add inputs as class attributes
        self.model = model
        self.log = logistic
        self._logl = None
        self.data = None
        self.x = None
        self.sigma = None

    def initialize(self, x, data, sigma):
        self.data = data
        self.x = x
        self.sigma = sigma
        if self.log is None:
            if not isinstance(sigma, np.ndarray):
                sigma = sigma * np.ones_like(data)
            self._logl = multivariate_normal(data, np.diag(sigma))
            self.log = self._default_caller

    def _default_caller(self, a, b, model):
        return self._logl.logpdf(model)

    # define your really-complicated likelihood function that uses loads of external codes
    def outer_loglike(self, theta, x, data, sigma):
        """
        A Gaussian log-likelihood function for a model with parameters given in theta
        """
        # Call the underlying wrapped model
        model = self.model(theta, x)
        return self.log(data, sigma, model)

    @abstractmethod
    def perform(self, node, inputs, outputs):
        pass


# define a theano Op for our likelihood function
class LogLike(LogBase):
    itypes = [tt.dvector]  # expects a vector of parameter values when called
    otypes = [tt.dscalar]  # outputs a single scalar value (the log likelihood)
    """
    Specify what type of object will be passed and returned to the Op when it is
    called. In our case we will be passing it a vector of values (the parameters
    that define our model) and returning a single "scalar" value (the
    log-likelihood)
    """

    def __init__(self, model, logistic=None):
        super(LogLike, self).__init__(model, logistic)

    def perform(self, node, inputs, outputs):
        """
        Perform the calculation of the log-likelihood.
        """
        # the method that is used when calling the Op
        (theta,) = inputs  # this will contain my variables
        # call the log-likelihood function
        logl = self.outer_loglike(theta, self.x, self.data, self.sigma)
        # output the log-likelihood
        outputs[0][0] = np.array(logl)


# define a theano Op for our likelihood function
class LogLikeWithGrad(LogBase):
    itypes = [tt.dvector]  # expects a vector of parameter values when called
    otypes = [tt.dscalar]  # outputs a single scalar value (the log likelihood)

    def __init__(self, model, logistic=None):
        """
        Initialise with various things that the function requires. Below
        are the things that are needed in this particular example.

        Parameters
        ----------
        loglike:
            The log-likelihood (or whatever) function we've defined
        data:
            The "observed" data that our log-likelihood function takes in
        x:
            The dependent variable (aka 'x') that our model requires
        sigma:
            The noise standard deviation that out function requires.
        """

        super(LogLikeWithGrad, self).__init__(model, logistic)

    def initialize(self, x, data, sigma):
        super(LogLikeWithGrad, self).initialize(x, data, sigma)
        # initialise the gradient Op (below)
        self.logpgrad = LogLikeGrad(self.model, self.log, self.data, self.x, self.sigma)
        self.logpgrad.log = self.log

    def perform(self, node, inputs, outputs):
        # the method that is used when calling the Op
        (theta,) = inputs  # this will contain my variables
        # call the log-likelihood function
        logl = self.outer_loglike(theta, self.x, self.data, self.sigma)
        outputs[0][0] = np.array(logl)  # output the log-likelihood

    def grad(self, inputs, g):
        # the method that calculates the gradients - it actually returns the
        # vector-Jacobian product - g[0] is a vector of parameter values
        (theta,) = inputs  # our parameters
        return [g[0] * self.logpgrad(theta)]


#
# class LogLikeGrad(LogBase):
#     itypes = [tt.dvector]  # expects a vector of parameter values when called
#     otypes = [tt.dscalar]  # outputs a single scalar value (the log likelihood)
#     """
#     This Op will be called with a vector of values and also return a vector of
#     values - the gradients in each dimension.
#     """
#
#     def __init__(self, model, logistic=None):
#         """
#         Initialise with various things that the function requires. Below
#         are the things that are needed in this particular example.
#
#         Parameters
#         ----------
#         loglike:
#             The log-likelihood (or whatever) function we've defined
#         data:
#             The "observed" data that our log-likelihood function takes in
#         x:
#             The dependent variable (aka 'x') that our model requires
#         sigma:
#             The noise standard deviation that out function requires.
#         """
#
#         # add inputs as class attributes
#         super(LogLikeGrad, self).__init__(model, logistic)
#
#     def perform(self, node, inputs, outputs):
#         (theta,) = inputs
#
#         # define version of likelihood function to pass to derivative function
#         def lnlike(values):
#             return self.outer_loglike(values, self.x, self.data, self.sigma)
#
#         # calculate gradients
#         wiggle = 1E-5
#         eps_array = np.abs(np.array(theta)) * wiggle
#         factor = np.finfo(float).eps*1E5
#         eps_array[eps_array < factor] = factor    # avoid zero-wiggles
#         grads = gradients(theta, lnlike, eps_array)
#         outputs[0][0] = grads


class LogLikeGrad(tt.Op):

    """
    This Op will be called with a vector of values and also return a vector of
    values - the gradients in each dimension.
    """

    itypes = [tt.dvector]
    otypes = [tt.dvector]

    def __init__(self, model, loglike, data, x, sigma):
        """
        Initialise with various things that the function requires. Below
        are the things that are needed in this particular example.

        Parameters
        ----------
        loglike:
            The log-likelihood (or whatever) function we've defined
        data:
            The "observed" data that our log-likelihood function takes in
        x:
            The dependent variable (aka 'x') that our model requires
        sigma:
            The noise standard deviation that out function requires.
        """

        # add inputs as class attributes
        self.model = model
        self.data = data
        self.x = x
        self.sigma = sigma
        self.log = loglike

    def outer_loglike(self, theta, x, data, sigma):
        """
        A Gaussian log-likelihood function for a model with parameters given in theta
        """
        # Call the underlying wrapped model
        model = self.model(theta, x)
        return self.log(data, sigma, model)

    def perform(self, node, inputs, outputs):
        (theta,) = inputs

        # define version of likelihood function to pass to derivative function
        def lnlike(values):
            return self.outer_loglike(values, self.x, self.data, self.sigma)

        # calculate gradients
        grads = approx_derivative(lnlike, theta, method="2-point")
        outputs[0][0] = grads


class _LogLikeWithGrad(tt.Op):
    # Theano op for calculating a log-likelihood

    itypes = [tt.dvector]  # expects a vector of parameter values when called
    otypes = [tt.dscalar]  # outputs a single scalar value (the log likelihood)

    def __init__(self, loglike):
        # add inputs as class attributes
        self.likelihood = loglike

        # initialise the gradient Op (below)
        self.logpgrad = _LogLikeGrad(self.likelihood)

    def perform(self, node, inputs, outputs):
        # the method that is used when calling the Op
        (theta,) = inputs  # this will contain my variables

        # call the log-likelihood function
        logl = self.likelihood(theta)

        outputs[0][0] = np.array(logl)  # output the log-likelihood

    def grad(self, inputs, g):
        # the method that calculates the gradients - it actually returns the
        # vector-Jacobian product - g[0] is a vector of parameter values
        (theta,) = inputs  # our parameters

        return [g[0] * self.logpgrad(theta)]


class _LogLikeGrad(tt.Op):
    # Theano op for calculating the gradient of a log-likelihood
    itypes = [tt.dvector]
    otypes = [tt.dvector]

    def __init__(self, loglike):
        # add inputs as class attributes
        self.likelihood = loglike

    def perform(self, node, inputs, outputs):
        (theta,) = inputs

        # define version of likelihood function to pass to derivative function
        def logl(values):
            return self.likelihood(values)

        # calculate gradients
        grads = approx_derivative(logl, theta, method="2-point")

        outputs[0][0] = grads
