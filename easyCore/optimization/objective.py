#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'


class Objective:
    """
    Class to define the objective function.
    """
    def __init__(self, gradient=None, hessian=None, jacobian=None):
        """
        Initialize the objective function.

        :param function: objective function
        :type function: callable
        :param gradient: gradient of the objective function
        :type gradient: callable
        :param hessian: hessian of the objective function
        :type hessian: callable
        :param jacobian: jacobian of the objective function
        :type jacobian: callable
        """
        self.model = None
        self.gradient = gradient
        self.hessian = hessian
        self.jacobian = jacobian
        self._observed = {
            'independent': None,
            'dependent': None,
            'sigma': None,
            'shape': None
        }
        self._use_weights = False

    def evaluate(self):
        return self.model(self._observed['independent'])

    @property
    def use_weights(self) -> bool:
        return self._use_weights

    @use_weights.setter
    def use_weights(self, value: bool):
        self._use_weights = value

    def attach_model(self, model):
        self.model = model

    def attach_data(self, *args, **kwargs):
        """
        Attach data to the objective function.

        :param dependent: dependent data
        :type dependent: numpy.ndarray
        :param independent: independent data
        :type independent: numpy.ndarray
        :param sigma: standard deviation of the data
        :type sigma: numpy.ndarray
        """
        dependent, independent, sigma = self._check_data(*args, **kwargs)
        self._dependent = dependent
        self._independent = independent
        self._sigma = sigma

    def __call__(self, x):
        """
        Evaluate the objective function.

        :param x: point at which to evaluate the objective function
        :type x: numpy.ndarray
        :return: objective function value
        :rtype: float
        """
        return self.model(x)

    def gradient(self, x):
        """
        Evaluate the gradient of the objective function.

        :param x: point at which to evaluate the gradient of the objective function
        :type x: numpy.ndarray
        :return: gradient of the objective function
        :rtype: numpy.ndarray
        """
        if self.gradient is not None:
            return self.gradient(x)
        else:
            raise NotImplementedError('gradient not implemented')

    def hessian(self, x):
        """
        Evaluate the hessian of the objective function.

        :param x: point at which to evaluate the hessian of the objective function
        :type x: numpy.ndarray
        :return: hessian of the objective function
        :rtype: numpy.ndarray
        """
        if self.hessian is not None:
            return self.hessian(x)
        else:
            raise NotImplementedError('hessian not implemented')

    def jacobian(self, x):
        """
        Evaluate the jacobian of the objective function.

        :param x: point at which to evaluate the jacobian of the objective function
        :type x: numpy.ndarray
        :return: jacobian of the objective function
        :rtype: numpy.ndarray
        """
        if self.jacobian is not None:
            return self.jacobian(x)
        else:
            raise NotImplementedError('jacobian not implemented')


    def _check_data(self, *args, **kwargs):
        dependent, independent, sigma = args
        return dependent, independent, sigma