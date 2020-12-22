__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import List

import pytest
from easyCore import np
from easyCore.Elements.Basic.Site import Atoms, Site, _SITE_DETAILS

site_details = [Site.from_pars('Al', 'Al'), Site.from_pars('Fe', 'Fe3+'), Site.from_pars('TEST', 'H')]


def gen_sites() -> List[Site]:
    args = []
    for edx in range(len(site_details)):
        key = f'from_{edx+1}_sites'
        args.append(pytest.param((site_details[0:(edx + 1)]), id=key))
    return args


@pytest.mark.parametrize('sites', gen_sites())
def test_Atoms_creation_args(sites: List[Site]):

    name = 'test'
    atoms = Atoms(name, *sites)
    assert len(atoms) == len(sites)
    assert atoms.name == name


@pytest.mark.parametrize('sites', gen_sites())
def test_Atoms_creation_dict(sites: List[Site]):

    name = 'test'
    d = {}
    for idx, site in enumerate(sites):
        d[str(idx)] = site
    atoms = Atoms(name, **d)
    assert len(atoms) == len(sites)
    assert atoms.name == name


@pytest.mark.parametrize('sites', gen_sites())
def test_Atoms_repr(sites: List[Site]):
    name = 'test'
    atoms = Atoms(name, *sites)
    assert str(atoms) == f'Collection of {len(atoms)} sites.'


@pytest.mark.parametrize('sites', gen_sites())
def test_Atoms_get_item_int(sites: List[Site]):
    name = 'test'
    atoms = Atoms(name, *sites)

    for atom, site in zip(atoms, sites):
        assert atom.label == site.label

    for idx, site in enumerate(sites):
        atom = atoms[idx]
        assert atom.label == site.label


@pytest.mark.parametrize('sites', gen_sites())
def test_Atoms_get_item_str(sites: List[Site]):
    name = 'test'
    atoms = Atoms(name, *sites)

    for site in sites:
        atom = atoms[site.label.raw_value]
        assert atom.label == site.label