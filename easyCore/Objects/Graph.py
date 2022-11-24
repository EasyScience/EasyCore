from __future__ import annotations

#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

import warnings
from typing import List, Union, TYPE_CHECKING, Optional, Tuple
from weakref import WeakKeyDictionary, ref
from collections import defaultdict
from uuid import uuid4, UUID
import networkx as nx

if TYPE_CHECKING:
    from easyCore.Utils.typing import BV


class UniqueIdMap(WeakKeyDictionary):
    def __init__(self, this_dict: dict = None):
        super().__init__(self)
        # replace data with a defaultdict to generate uuids
        self.data = defaultdict(uuid4)
        if this_dict is not None:
            self.update(this_dict)


uniqueidmap = UniqueIdMap()


class Graph:
    def __init__(self):
        self._graphs = {
            "base": nx.DiGraph(),
        }
        self.__known_types = {"argument", "created", "created_internal", "returned"}

    def create_synced_graph(self, graph_name: str, graph_type=None):
        if graph_type is None:
            graph_type = nx.DiGraph
        self._graphs[graph_name] = graph_type()
        self._graphs[graph_name].add_nodes_from(self._G.nodes(data=True))

    def remove_synced_graph(self, graph_name: str):
        if graph_name in self._graphs and graph_name != "base":
            self._graphs.pop(graph_name)

    def synced_graph_names(self) -> List[str]:
        return list(self._graphs.keys())

    @property
    def _G(self):
        return self._graphs["base"]

    def reset_graph(self):
        for key in self._graphs.keys():
            self._graphs[key] = nx.DiGraph()

    def nodes(self) -> List[str]:
        """returns the nodes of a graph"""
        return list(self._G.nodes)

    def edges(self, graph: str = "base") -> List[Tuple[str, str]]:
        """returns the edges of a graph"""
        if graph not in self._graphs:
            raise ValueError(f"Graph {graph} not found")
        return list(self._graphs[graph].edges)

    def _query_graph_types(self, created_type):
        return [n for n, d in self._G.nodes(data=True) if created_type in d["type"]]

    @property
    def argument_objs(self) -> List[str]:
        return self._query_graph_types("argument")

    @property
    def created_objs(self) -> List[str]:
        return self._query_graph_types("created")

    @property
    def created_internal(self) -> List[str]:
        return self._query_graph_types("created_internal")

    @property
    def returned_objs(self) -> List[str]:
        return self._query_graph_types("returned")

    def get_item_by_key(self, item_id: str) -> Optional[BV]:
        if item_id not in self._G.nodes:
            item_id = str(item_id)
        if item_id not in self._G.nodes:
            raise ValueError(f"Item {item_id} not found")
        return self._G.nodes.get(item_id, {"object": lambda: None})["object"]()

    def is_known(self, node: BV) -> bool:
        return self.convert_id(node, as_string=True) in self._G.nodes

    def find_type(self, node: BV) -> List[str]:
        item_id = self.convert_id(node, as_string=True)
        return self._G.nodes.get(item_id, {"type": []})["type"]

    def reset_type(self, node: BV, default_type: str):
        item_id = self.convert_id(node, as_string=True)
        self._G.nodes[item_id]["type"] = [default_type]

    def change_type(self, node: BV, new_type: str):
        item_id = self.convert_id(node, as_string=True)
        if (
            new_type in self.__known_types
            and new_type not in self._G.nodes[item_id]["type"]
        ):
            self._G.nodes[item_id]["type"].append(new_type)

    def add_node(self, node: BV, obj_type: str = None):
        oid = self.convert_id(node, as_string=True)
        for graph_key in self._graphs.keys():
            try:
                object_ref = ref(node)
            except TypeError:
                object_ref = lambda: node
            self._graphs[graph_key].add_node(oid, object=object_ref, type=[obj_type])

    def add_edge(
        self,
        start_obj: BV,
        end_obj: BV,
        weight=None,
        graph: str = "base",
        additonal_data: dict = None,
    ):
        if graph not in self._graphs:
            raise ValueError(f"Graph {graph} not found")
        node1 = self.convert_id(start_obj, as_string=True)
        node2 = self.convert_id(end_obj, as_string=True)
        this_weight = 0.5
        if hasattr(end_obj, "value"):
            this_weight = 5
        if weight is None:
            weight = this_weight
        if additonal_data is None:
            additonal_data = {}
        self._graphs[graph].add_weighted_edges_from(
            [(node1, node2, weight)], **additonal_data
        )

    def get_edges(self, start_obj: BV, graph: str = "base") -> List[Tuple[str, str]]:
        if graph not in self._graphs:
            raise ValueError(f"Graph {graph} not found")
        node1 = self.convert_id(start_obj, as_string=True)
        return list(self._graphs[graph].edges(node1))

    def prune_node_from_edge(self, parent_obj: BV, child_obj: BV, graph: str = "base"):
        if graph not in self._graphs:
            raise ValueError(f"Graph {graph} not found")
        vertex1 = self.convert_id(parent_obj, as_string=True)
        if child_obj is None:
            return
        vertex2 = self.convert_id(child_obj, as_string=True)
        if (vertex1, vertex2) in self._G.edges:
            self._graphs[graph].remove_edge(vertex1, vertex2)

    def prune(self, key: int):
        if key not in self._G.nodes:
            key = str(key)
            if key not in self._G.nodes:
                raise ValueError(f"Item {key} not found")
        for graph_key in self._graphs.keys():
            if key in self._graphs[graph_key].nodes:
                self._graphs[graph_key].remove_node(key)

    def find_isolated_nodes(self, graph: str = "base") -> List[int]:
        """returns a list of isolated nodes."""
        if graph not in self._graphs:
            raise ValueError(f"Graph {graph} not found")
        return list(nx.isolates(self._graphs[graph]))

    def find_path(
        self,
        start_obj: Union[BV, int],
        end_obj: Union[BV, int],
        path: Optional[List[str]] = None,
        graph: str = "base",
    ) -> List[str]:
        if graph not in self._graphs:
            raise ValueError(f"Graph {graph} not found")
        """find a path from start_vertex to end_vertex
        in graph"""
        if path is None:
            path = []
        try:
            start_vertex = self.convert_id(start_obj, as_string=True)
            end_vertex = self.convert_id(end_obj, as_string=True)
        except TypeError:
            start_vertex = start_obj
            end_vertex = end_obj
        try:
            return path + nx.shortest_path(
                self._graphs[graph], start_vertex, end_vertex
            )
        except nx.exception.NetworkXNoPath:
            return path

    def find_all_paths(
        self,
        start_obj: Union[BV, int],
        end_obj: Union[BV, int],
        path: Optional[List[str]] = None,
        graph: str = "base",
    ) -> List[List[str]]:
        """find all paths from start_vertex to
        end_vertex in graph"""
        if graph not in self._graphs:
            raise ValueError(f"Graph {graph} not found")
        if path is None:
            path = []
        try:
            start_vertex = self.convert_id(start_obj, as_string=True)
            end_vertex = self.convert_id(end_obj, as_string=True)
        except TypeError:
            start_vertex = start_obj
            end_vertex = end_obj
        try:
            return path + nx.all_shortest_paths(
                self._graphs[graph], start_vertex, end_vertex
            )
        except nx.exception.NetworkXNoPath:
            return path

    def reverse_route(
        self,
        end_obj: Union[BV, int],
        start_obj: Optional[Union[BV, int]] = None,
        graph: str = "base",
    ) -> List[str]:
        """
        In this case we have an object and want to know the connections to get to another in reverse.
        We might not know the start_object. In which case we follow the shortest path to a base vertex.
        :param end_obj:
        :type end_obj:
        :param start_obj:
        :type start_obj:
        :return:
        :rtype:
        """
        if graph not in self._graphs:
            raise ValueError(f"Graph {graph} not found")
        if start_obj is None:
            start_node = self.convert_id(end_obj, as_string=True)
            nodes = list(
                nx.dag_longest_path(
                    nx.dfs_tree(self._graphs[graph].reverse(), source=start_node)
                )
            )
            return nodes
        else:
            path = self.find_path(start_obj, end_obj, graph=graph)
            path.reverse()
            return path

    @staticmethod
    def convert_id(input_value, as_string=False) -> UUID:
        """Sometimes we're dopy and"""
        try:
            if not validate_id(input_value):
                input_value = unique_id(input_value)
        except TypeError:
            warnings.warn(f"Unable to convert {input_value} to UUID")
            return input_value
        if as_string:
            input_value = str(input_value.int)
        return input_value

    @staticmethod
    def convert_id_to_key(input_value: Union[object, UUID]) -> int:
        """Sometimes we're dopy and"""
        if not validate_id(input_value):
            input_value: UUID = unique_id(input_value)
        return input_value.int

    def __repr__(self) -> str:
        return f"Graph object of {len(self._G.nodes)} nodes."

    def plot(
        self, node: BV, layout=nx.layout.shell_layout, with_labels=False, **kwargs
    ):
        from easyCore import GRAPHICS, hv

        if not GRAPHICS:
            raise EnvironmentError(
                "Holoviews needs to be installed in order to use `plot`"
            )
        start_node_id = self.convert_id(node, as_string=True)
        to_add = {
            "name": "name",
            "color": "_color",
        }

        def node_expander(this_G, this_node):
            entry = list(self._G[this_node])
            if len(entry) > 0:
                for new_node in entry:
                    new_obj = self._G.nodes[new_node]["object"]
                    attrs = {
                        name: getattr(new_obj(), value)
                        for name, value in to_add.items()
                    }

                    this_G.add_node(new_node, **attrs)
                    this_G.add_edge(this_node, new_node)
                    node_expander(this_G, new_node)

        H = nx.DiGraph()
        H.add_node(
            start_node_id,
            **{name: getattr(node, value) for name, value in to_add.items()},
        )
        node_expander(H, start_node_id)
        graph = hv.Graph.from_networkx(H, layout, **kwargs).opts(
            node_color="color",
            directed=True,
            node_size=20,
            arrowhead_length=0.035,
            width=400,
            height=400,
            xaxis=None,
            yaxis=None,
            bgcolor="#d3d3d3",
        )
        labels = hv.Labels(graph.nodes, ["x", "y"], "name")
        if with_labels:
            return graph, labels.opts(text_font_size="10pt", text_color="white")
        return graph


def unique_id(obj) -> UUID:
    """Produce a unique integer id for the object.

    Object must me *hashable*. Id is a UUID and should be unique
    across Python invocations.

    """
    return uniqueidmap[obj]


def validate_id(potential_id) -> bool:
    test = True
    try:
        if isinstance(potential_id, UUID):
            UUID(str(potential_id), version=4)
        else:
            UUID(potential_id, version=4)
    except (ValueError, AttributeError):
        test = False
    return test
