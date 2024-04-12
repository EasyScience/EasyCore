#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore

from abc import abstractmethod

from easyCore.Objects.Job.Analysis import AnalysisBase
from easyCore.Objects.Job.Experiment import ExperimentBase
from easyCore.Objects.Job.Theory import TheoryBase
from easyCore.Objects.ObjectClasses import BaseObj

# from easyCore.Objects.ObjectClasses import Parameter


class JobBase(BaseObj):
    """
    This virtual class allows for the creation of technique-specific Job objects.
    """
    def __init__(self, name: str, *args, **kwargs):
        super(JobBase, self).__init__(name, *args, **kwargs)
        self.name = name
        self._theory = None
        self._experiment = None
        self._analysis = None
        self._summary = None
        self._info = None

    """
    JobBase consists of Theory, Experiment, Analysis virtual classes.
    Additionally, Summary and Info classes are included to store additional information.
    """
    @abstractmethod
    def set_theory(self, theory: TheoryBase):
        # The implementation must include __copy__ and __deepcopy__ methods
        raise NotImplementedError("setTheory not implemented")
    
    @abstractmethod
    def set_experiment(self, experiment: ExperimentBase):
        # We might not have an experiment but this should be dealt with in the specific implementation
        raise NotImplementedError("setExperiment not implemented")

    @abstractmethod
    def set_analysis(self, analysis: AnalysisBase):
        raise NotImplementedError("setAnalysis not implemented")

    @abstractmethod
    def set_summary(self, summary: BaseObj):
        raise NotImplementedError("setSummary not implemented")

    @abstractmethod
    def set_info(self, info: BaseObj):
        raise NotImplementedError("setInfo not implemented")

    @property
    def theory(self):
        return self._theory
    
    @property
    def experiment(self):
        return self._experiment
    
    @property
    def analysis(self):
        return self._analysis

    @property
    def summary(self):
        return self._summary
    
    @property
    def info(self):
        return self._info

    @abstractmethod
    def calculate_model(self, *args, **kwargs):
        #raise NotImplementedError("calculateModel not implemented")
        pass

    @abstractmethod
    def fit(self, *args, **kwargs):
        #raise NotImplementedError("fit not implemented")
        pass
    