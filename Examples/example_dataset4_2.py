__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np
from easyCore.Datasets.xarray import xr
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting.Fitting import Fitter

import matplotlib.pyplot as plt

d = xr.Dataset()

class Wavey(BaseObj):
    def __init__(self,
                 amplitude: Parameter,
                 phase: Parameter,
                 period: Parameter):
        super(Wavey, self).__init__(amplitude=amplitude, phase=phase, period=period)

    @classmethod
    def from_params(cls, amplitude: float = 1, phase: float = 0, period: float = 2*np.pi):
        amplitude = Parameter('amplitude', amplitude, min=0)
        phase = Parameter('phase', phase)
        period = Parameter('period', period)
        return cls(amplitude, phase, period)

    def fit_fun(self, x, *args, **kwargs):
        # In the real case we would gust call the evaluation fn without reference to the BaseObj
        return self.amplitude.raw_value * np.sin((x + self.phase.raw_value)/self.period.raw_value)

f = Fitter()

f.initialize(b, fit_fun)

nx = 1E3
x_min = 0
x_max = 100

x = np.linspace(x_min, x_max, num=int(nx))
y1 = 2*x - 1 + 5*(np.random.random(size=x.shape) - 0.5)
x2 = x + 20
y2 = 2*x2 - 1 + 5*(np.random.random(size=x2.shape) - 0.5)

d.easyCore.add_dimension('x1', x)
d.easyCore.add_variable('y1', ['x1'], y1, auto_sigma=True)
d.easyCore.add_dimension('x2', x2)
d.easyCore.add_variable('y2', ['x2'], y2, auto_sigma=True)

res = d.easyCore.fit(f, ['y1', 'y2'])

fig, axs = plt.subplots(1, len(res), sharey=True)
for idx, r in enumerate(res):
    r.y_obs.plot(ax=axs[idx])
    r.y_calc.plot(ax=axs[idx])
    axs[idx].set_title(f'Dataset {idx}')
plt.show()

