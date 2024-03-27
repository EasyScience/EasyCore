#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore

from easyCore.Objects.ObjectClasses import BaseObj
from easyCore.Objects.ObjectClasses import Parameter
from typing import List
from easyCore.Objects.Job.Theory import TheoryBase
from easyCore.Objects.Job.Experiment import ExperimentBase
from easyCore.Objects.Job.Analysis import AnalysisBase


class JobBase(BaseObj):
    """
    This virtual class allows for the creation of technique-specific Job objects.
    """
    def __init__(self, name: str, parameters: List[Parameter], *args, **kwargs):
        super(JobBase, self).__init__(name, *args, **kwargs)
        self.parameters = parameters
        self._theory = None
        self._experiment = None
        self._analysis = None

    """
    JobBase consists of Theory, Experiment, Analysis virtual classes.
    """
    def set_theory(self, theory: TheoryBase):
        # The implementation must include __copy__ and __deepcopy__ methods
        raise NotImplementedError("setTheory not implemented")
    
    def set_experiment(self, experiment: ExperimentBase):
        # We might not have an experiment but this should be dealt with in the specific implementation
        raise NotImplementedError("setExperiment not implemented")
    
    def set_analysis(self, analysis: AnalysisBase):
        raise NotImplementedError("setAnalysis not implemented")

    @property
    def theory(self):
        return self._theory
    
    @property
    def experiment(self):
        return self._experiment
    
    @property
    def analysis(self):
        return self._analysis

    def calculate_model(self, *args, **kwargs):
        raise NotImplementedError("calculateModel not implemented")
    
    def fit(self, *args, **kwargs):
        raise NotImplementedError("fit not implemented")
    