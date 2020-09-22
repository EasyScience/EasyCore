__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyExampleLib.model import Model
from easyExampleLib.interface import InterfaceFactory
from dicttoxml import dicttoxml

i = InterfaceFactory()
m = Model(interface_factory=i)

from easyCore import borg
pars = m.get_parameters()

d = []
for par in pars:
    elem = {'id': borg.map.convert_id(par)}
    route = borg.map.reverse_route(elem['id'], borg.map.convert_id(m))
    objs = [getattr(borg.map.get_item_by_key(r), 'name') for r in route]
    objs.reverse()
    elem['route'] = '.'.join(objs[1:])
    elem['id'] = elem['id'].int
    d.append(elem)
xml = dicttoxml(d, attr_type=False)
xml = xml.decode()

print(xml)
