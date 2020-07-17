__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'


def singleton(cls):
    """
    This decorator can be used to create a singleton out of a class.

    Usage::

        @singleton
        class MySingleton():

            def __init__():
                pass
    """

    instances = {}

    def get_instance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return get_instance
