#  SPDX-FileCopyrightText: 2022 easyCrystallography contributors  <crystallography@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCrystallography>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import scipp as sc
import numpy as np
from easyCore.Datasets.scipp import register_accessor


@register_accessor('boo', sc.DataArray)
class Boo:
    def __init__(self, obj):
        self._obj = obj

    def pp(self):
        print(self._obj)


N = 5000
values = 10*np.random.rand(N)
data = sc.DataArray(
    data=sc.Variable(dims=['position'], unit=sc.units.counts, values=values, variances=values),
    coords={
        'x':sc.Variable(dims=['position'], unit=sc.units.m, values=np.random.rand(N)),
        'y':sc.Variable(dims=['position'], unit=sc.units.m, values=np.random.rand(N))
    })
data.values *= 1.0/np.exp(5.0*data.coords['x'].values)

data.boo.pp()
print(data)