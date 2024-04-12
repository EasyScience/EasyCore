#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore


from easyCore.Objects.ObjectClasses import BaseObj


class AnalysisBase(BaseObj):
    """
    This virtual class allows for the creation of technique-specific Analysis objects.
    """
    def __init__(self, name: str, *args, **kwargs):
        super(AnalysisBase, self).__init__(name, *args, **kwargs)
        self.name = name

    # required dunder methods
    def __str__(self):
        return f"Analysis: {self.name}"
    
    