#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np
from easyCore.BayesianAnalysis.Models import Line
from easyCore.BayesianAnalysis.Likelihoods import LogLikeWithGrad, LogLike
from easyCore.BayesianAnalysis.ParameterDistribution import Sampler
from matplotlib import pyplot as plt
import arviz as az

# set up our data
N = 1000  # number of data points
sigma = 1.0  # standard deviation of noise
x_data = np.linspace(0.0, 9.0, N)

mtrue = 0.4  # true gradient
ctrue = 3.0  # true y-intercept

# create our model
l = Line.from_pars(mtrue, ctrue)
# set some limits
l.m.min = -10
l.m.max = 10
l.c.min = -10
l.c.max = 10

# generate some 'real' data
truemodel = l.func(x_data)
# make data
np.random.seed(716742)  # set random seed, so the data is reproducible each time
y_data = sigma * np.random.randn(N) + truemodel

def loglike(y, sigma, model):
    logl = -.5 * np.sum(((y - model)/sigma)**2 + np.log(2*np.pi*sigma**2))
    return logl


if __name__ == '__main__':
    # NO GRADIENT
    # s = Sampler(l, 'func', use_quickset=True)
    # # s.distribution_function = LogLikeWithGrad(s.model, logistic=loglike)
    # s.distribution_function = LogLike(s.model, logistic=loglike)
    #
    # # GRADIENT
    # s = Sampler(l, 'func', use_quickset=True)
    # s.distribution_function = LogLikeWithGrad(s.model, logistic=loglike)

    # NORMAL
    s = Sampler(l, 'func', use_quickset=True, sample_type="NORMAL")
    trace = s.sample(x_data, y_data, sigma, n_chains=4, n_samples=3000, tune=1000)
    s = az.summary(trace)
    print(s)
    az.plot_trace(trace, figsize=(10, 7))
    plt.show()

    # plot the posterior predictive
    plt.plot(x_data, y_data, 'o', label='data')
    plt.plot(x_data, truemodel, 'k', label='true model')
    plt.plot(x_data, l.func(x_data, s['mean']['c'], s['mean']['m']), 'r', label='posterior predictive')
    plt.show()