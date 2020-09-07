__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import dataclasses
import numpy as np
from easyCore.Utils.

@dataclasses.dataclass
class D1:
    x: np.ndarray
    y: np.ndarray

@dataclasses.dataclass
class D2(D1):
    z: np.ndarray

@dataclasses.dataclass
class D3:
