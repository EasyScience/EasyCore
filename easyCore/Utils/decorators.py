#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

import collections.abc
import functools
import sys
from time import time
import warnings
from typing import Callable

from easyCore import borg


class memoized:
    """
    Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.abc.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        value = self.func(*args)
        self.cache[args] = value
        return value

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)


def counted(func):
    """
    Counts how many times a function has been called and adds a `func.calls` to it's properties
    :param func: Function to be counted
    :return: Results from function call
    """

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        wrapped.n_calls += 1
        return func(*args, **kwargs)

    wrapped.n_calls = 0
    return wrapped


def time_it(func):
    """
    Times a function and reports the time either to the class' log or the base logger
    :param func: function to be timed
    :return: callable function with timer
    """
    name = func.__module__ + "." + func.__name__
    time_logger = borg.log.getLogger("timer." + name)

    @functools.wraps(func)
    def _time_it(*args, **kwargs):
        start = int(round(time() * 1000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1000)) - start
            time_logger.debug(
                f"\033[1;34;49mExecution time: {end_ if end_ > 0 else 0} ms\033[0m"
            )

    return _time_it


def minimum_version(
    major: int = 3, minor: int = 7, fallback: Callable = None
) -> Callable:
    """
    This decorator checks if the current python version is greater than or equal to the specified version. If not,
    the decorated function is called with the specified fallback.

    :param major: Major version to check (3)
    :type major: int
    :param minor: Minor version to check (7)
    :type minor: int
    :param fallback: Function which will be returned if version is not greater than or equal to the specified version.
    :type fallback: typing.Callable
    :return: Decorated function or fallback function
    :rtype: typing.Callable
    """

    if sys.version_info < (major, minor):
        if fallback is None:
            raise RuntimeError(
                f"This function requires Python {major}.{minor} or higher"
            )
        else:
            warnings.warn(
                f"This function requires Python {major}.{minor} or higher, using fallback function"
            )
            return fallback
    else:

        @functools.wraps
        def wrapper(func):
            return func

        return wrapper
