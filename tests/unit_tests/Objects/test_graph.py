__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>
from easyCore import borg
from easyCore.Objects.ObjectClasses import Parameter, Descriptor, BaseObj


def test_load():
    G = borg.map
    G.reset_graph()
    assert len(G.nodes()) == 0
    assert len(G.edges()) == 0


def test_create():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    assert len(G.nodes()) == 1
    assert len(G.edges()) == 0


def test_delete_Par():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    assert len(G.nodes()) == 1
    assert len(G.edges()) == 0
    del p1
    assert len(G.nodes()) == 0
    assert len(G.edges()) == 0


def test_delete_BaseObj():
    G = borg.map
    G.reset_graph()
    p1 = BaseObj("b1")
    assert len(G.nodes()) == 1
    assert len(G.edges()) == 0
    del p1
    assert len(G.nodes()) == 0
    assert len(G.edges()) == 0


def test_delete_BaseObj_Par1():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    b1 = BaseObj("b1", p1=p1)
    assert len(G.nodes()) == 2
    assert len(G.edges()) == 1
    del b1
    assert len(G.nodes()) == 1
    assert len(G.edges()) == 0


def test_delete_BaseObj_Par2():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    b1 = BaseObj("b1", p1=p1)
    assert len(G.nodes()) == 2
    assert len(G.edges()) == 1
    del p1
    assert len(G.nodes()) == 2
    assert len(G.edges()) == 1


def test_get_item_by_key():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    assert len(G.nodes()) == 1
    assert len(G.edges()) == 0
    obj_id = G.nodes()[0]
    assert p1 == G.get_item_by_key(obj_id)


def test_nodes():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p1", 1)
    assert list(G._G.nodes) == G.nodes()


def test_edges():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    b1 = BaseObj("b1", p1=p1)
    assert list(G._G.edges) == G.edges()


def test_type_query():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)

    p1_id = str(G.convert_id_to_key(p1))
    p2_id = str(G.convert_id_to_key(p2))
    b1_id = str(G.convert_id_to_key(b1))

    assert p2_id in G.created_objs
    assert p1_id in G.created_internal
    assert b1_id in G.created_objs


def test_is_known():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    assert G.is_known(p1)


def test_is_type():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    assert "created" in G.find_type(p1)


def test_reset_type():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)
    G.reset_type(p1, "created")
    assert "created" in G.find_type(p1)
    p1_id = str(G.convert_id_to_key(p1))
    assert p1_id not in G.created_internal


def test_get_edges():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)

    p1_id = str(G.convert_id_to_key(p1))
    b1_id = str(G.convert_id_to_key(b1))

    edges = G.get_edges(b1)
    assert edges == [(b1_id, p1_id)]


def test_prune_node_from_edges():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)

    G.prune_node_from_edge(b1, p1)

    edges = G.get_edges(b1)
    assert edges == []


def test_prune_node():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)

    p2_id = str(G.convert_id_to_key(p2))
    G.prune(p2_id)

    assert len(G.nodes()) == 2


def test_find_isolated_nodes():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)

    p2_id = str(G.convert_id_to_key(p2))

    assert p2_id in G.find_isolated_nodes()


def test_find_path():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)
    b2 = BaseObj("b2", b1=b1, p2=p2)

    p1_id = str(G.convert_id_to_key(p1))
    b1_id = str(G.convert_id_to_key(b1))
    b2_id = str(G.convert_id_to_key(b2))

    path = G.find_path(b2, p1)
    assert path == [b2_id, b1_id, p1_id]


def test_reverse_route1():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)
    b2 = BaseObj("b2", b1=b1, p2=p2)

    p1_id = str(G.convert_id_to_key(p1))
    b1_id = str(G.convert_id_to_key(b1))
    b2_id = str(G.convert_id_to_key(b2))

    path = G.reverse_route(p1, b2)
    assert path == [p1_id, b1_id, b2_id]


def test_reverse_route2():
    G = borg.map
    G.reset_graph()
    p1 = Parameter("p1", 1)
    p2 = Parameter("p2", 1)
    b1 = BaseObj("b1", p1=p1)
    b2 = BaseObj("b2", b1=b1, p2=p2)

    p1_id = str(G.convert_id_to_key(p1))
    b1_id = str(G.convert_id_to_key(b1))
    b2_id = str(G.convert_id_to_key(b2))

    path = G.reverse_route(p1)
    assert path == [p1_id, b1_id, b2_id]
