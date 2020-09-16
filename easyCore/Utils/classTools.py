__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Utils.Hugger.Property import LoggedProperty


def addLoggedProp(inst, name, *args, **kwargs):
    cls = type(inst)
    if not hasattr(cls, '__perinstance'):
        cls = type(cls.__name__, (cls,), {})
        cls.__perinstance = True
        inst.__old_class__ = inst.__class__
        inst.__class__ = cls
    setattr(cls, name, LoggedProperty(*args, **kwargs))


def addProp(inst, name, *args, **kwargs):
    cls = type(inst)
    if not hasattr(cls, '__perinstance'):
        cls = type(cls.__name__, (cls,), {})
        cls.__perinstance = True
        inst.__old_class__ = inst.__class__
        inst.__class__ = cls
    setattr(cls, name, property(*args, **kwargs))