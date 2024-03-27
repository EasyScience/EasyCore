#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore

from easyCore.Objects.ObjectClasses import BaseObj
from easyCore.Objects.ObjectClasses import Parameter
from typing import Any, List

class AnalysisBase(BaseObj):
    """
    This virtual class allows for the creation of technique-specific Analysis objects.
    """
    def __init__(self, name: str, parameters: List[Parameter], *args, **kwargs):
        super(AnalysisBase, self).__init__(name, *args, **kwargs)
        self.parameters = parameters


    # required dunder methods
    def __str__(self):
        return f"Analysis: {self.name}"
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return super().__call__(*args, **kwds)
    
    def __copy__(self) -> 'AnalysisBase':
        raise NotImplementedError("Copy not implemented")
        #return super().__copy__()
    
    def __deepcopy__(self, memo: Any) -> 'AnalysisBase':
        raise NotImplementedError("Deepcopy not implemented")
        #return super().__deepcopy__(memo)
    
    def __eq__(self, other: Any) -> bool:
        raise NotImplementedError("Equality not implemented")
        #return super().__eq__(other)
    