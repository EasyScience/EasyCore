# #  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
# #  SPDX-License-Identifier: BSD-3-Clause
# #  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

# import pytest
# from easyCore import np
# from easyCore.Datasets.scipp import sc


# @pytest.fixture
# def da():
#     N = 5000
#     values = 10 * np.random.rand(N)
#     data = sc.DataArray(
#         data=sc.Variable(dims=['position'], unit=sc.units.counts, values=values, variances=values),
#         coords={
#             'x': sc.Variable(dims=['position'], unit=sc.units.m, values=np.random.rand(N)),
#             'y': sc.Variable(dims=['position'], unit=sc.units.m, values=np.random.rand(N))
#         })
#     data.values *= 1.0 / np.exp(5.0 * data.coords['x'].values)
#     return data


# def test_accessor(da):
#     """
#     Check to see if the accessor has been correctly attached
#     """
#     assert hasattr(da, "easyFitting")
#     assert id(da) == id(da.easyFitting._obj)
#     assert repr(da) == repr(da.easyFitting)




