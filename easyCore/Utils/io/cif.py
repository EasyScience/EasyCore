__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Utils.io.CIF_HEADERS import CIF_DICT, ADP_DICT
from easyCore.Utils.io.star import StarHeader, StarCollection, StarLoop, StarEntry, StarSection
from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Atoms, Site
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup
from easyCore.Elements.Basic.AtomicDisplacement import AtomicDisplacement

_CRYSTAL = [SpaceGroup, Cell, Atoms]


class CrystalCif:
    def __init__(self, name: str, *args):
        self.name = name
        self._items: list = list(args)
        self.blocks = self._create_cif_obj()

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items
        self.blocks = self._create_cif_obj()

    def _create_cif_obj(self):
        blocks = [StarHeader(self.name)]
        for idx, entry_item in enumerate(self._items):
            in_there = [isinstance(entry_item, c) for c in _CRYSTAL]
            if not any(in_there):
                raise AttributeError
            mro = self.items[idx].__class__.mro()
            idx2 = sum([ob.__module__ == 'easyCore.Utils.classTools' for ob in mro])
            qualified_class = mro[idx2].__module__ + '.' + mro[idx2].__name__
            block = self.items[idx].to_star()
            if isinstance(block, list):
                # Block 0 should be positions..
                labels = [details['output'] for details in CIF_DICT['easyCore.Elements.Basic.Site.Site']]
                if 'adp_type' in block[0].labels:
                    # We also have iso adp
                    labels.extend(
                        [CIF_DICT['easyCore.Elements.Basic.AtomicDisplacement.AtomicDisplacement'][0]['output'],
                         ADP_DICT['iso'][block[0].labels[-1]]])
                block[0].labels = labels
                if len(block) > 1:
                    for this_block in block[1:]:
                        if 'adp_type' in this_block.labels:
                            # ani adp are in the form of 'label, type, Pars'
                            labels = [CIF_DICT['easyCore.Elements.Basic.AtomicDisplacement.AtomicDisplacement'][0][
                                          'additional'][0][1],
                                      CIF_DICT['easyCore.Elements.Basic.AtomicDisplacement.AtomicDisplacement'][0][
                                          'output']]
                            labels.extend(ADP_DICT['ani'][this_block.data[0]._kwargs['adp_type'].raw_value])
                            this_block.labels = labels
                blocks.extend(block)
            else:
                if qualified_class in CIF_DICT.keys():
                    if hasattr(block, 'labels'):
                        block.labels = [details['output'] for details in CIF_DICT[qualified_class]]
                    elif hasattr(block, 'name'):
                        block.name = CIF_DICT[qualified_class][0]['output']
                blocks.append(block)
        return StarCollection(*blocks)

    def __str__(self) -> str:
        return str(self.blocks)

    @classmethod
    def from_cif_str(cls, in_str: str):
        # Get the string into a star format
        star_items = StarCollection.from_string(in_str)
        # Extract out the header
        header = [item for item in star_items if isinstance(item, StarHeader)]
        header = header[0].name
        # Convert the rest to entries and use set to do name checking
        entry_dict = {item.name: item for item in star_items if isinstance(item, StarEntry)}
        entry_name_set = set(entry_dict.keys())
        # Get the spacegroup
        qualified_class = SpaceGroup.__module__ + '.' + SpaceGroup.__name__
        if CIF_DICT[qualified_class][0]['output'] in entry_name_set:
            space_group = entry_dict[CIF_DICT[qualified_class][0]['output']].to_class(SpaceGroup,
                                                                                   name_conversion=
                                                                                   CIF_DICT[qualified_class][0][
                                                                                       'internal'])
        else:
            # This is where you would check loops for sgOPTS and build a custom space-group
            raise AttributeError
        # Get the cell parameters
        qualified_class = Cell.__module__ + '.' + Cell.__name__

        cell_cif_names = set([item['output'] for item in CIF_DICT[qualified_class]])
        if entry_name_set.issuperset(cell_cif_names):
            cell_star = StarSection.from_StarEntries([entry_dict[key] for key in cell_cif_names],
                                                     [item['internal'] for item in CIF_DICT[qualified_class]])
            cell = cell_star.to_class(Cell)
        else:
            raise AttributeError
        # Search the loops for atoms
        qualified_class = Site.__module__ + '.' + Site.__name__
        atom_cif_names = set([item['output'] for item in CIF_DICT[qualified_class]])
        loops = [item for item in star_items if isinstance(item, StarLoop)]
        found = False
        for loop in loops:
            if set(loop.labels).issuperset(atom_cif_names):
                found = True
                atoms = loop.to_class(Atoms, Site, [[item['internal'], item['output']] for item in CIF_DICT[qualified_class]])
                break
        if not found:
            raise AttributeError
        # Search for ADP entries and then add them to the corresponding atoms
        mini_adp = [CIF_DICT[k] for k in CIF_DICT.keys() if 'AtomicDisplacement.' in k][1:]
        for idx, adp_key in enumerate([i[0]['output'] for i in mini_adp]):
            for loop in loops:
                if adp_key in loop.labels:
                    items_CIF = [item['output'] for item in mini_adp[0]]
                    items_STAR = [item['internal'] for item in mini_adp[0]]
                    loop.to_StarSections()
                    adp_atoms, adp_objs = AtomicDisplacement.from_pars(mini_adp[idx]['internal'], )
                    for idx, atom_key in enumerate(adp_atoms):
                        if atom_key in atoms.atom_labels:
                            idx2 = atoms.atom_labels.index(atom_key)
                            atoms[idx2].add_adp(adp_objs[idx2])
                        else:
                            raise AttributeError
        # Finally, create a CrystalCif object!
        return cls(header, space_group, cell, atoms)
