__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from .xarray import xr, easyCoreAccessor
from easyCore.Datasets.Dataset import Dataset


@xr.register_dataset_accessor("neutron")
class NeutronAccessor(easyCoreAccessor):
    def __init__(self, xarray_obj):
        super(NeutronAccessor, self).__init__(xarray_obj)
        self.state = 0

    @property
    def current_state(self):
        return self.state


class NeutronDataset(Dataset):
    def __init__(self, *args, **kwargs):
        super(NeutronDataset, self).__init__(*args, **kwargs)

    @property
    def neutron(self) -> xr.Dataset:
        return self._data.neutron
