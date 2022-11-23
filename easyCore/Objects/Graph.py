from __future__ import annotations

#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

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
        # self._store = WeakValueDictionary()
        # self.__graph_dict = {}
        self._G = nx.DiGraph()
        self.__known_types = {"argument", "created", "created_internal", "returned"}

    def reset_graph(self):
        # self._store = WeakValueDictionary()
        # self.__graph_dict = {}
        self._G = nx.DiGraph()

    def nodes(self) -> List[str]:
        """returns the nodes of a graph"""
        return list(self._G.nodes)

    def edges(self) -> List[Tuple[str, str]]:
        """returns the edges of a graph"""
        return list(self._G.edges)

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
        item_id = str(item_id)
        return self._G.nodes.get(item_id, {"object": lambda: None})["object"]()

    def is_known(self, node: BV) -> bool:
        return str(self.convert_id(node).int) in self._G.nodes

    def find_type(self, node: BV) -> List[str]:
        item_id = str(self.convert_id(node).int)
        return self._G.nodes.get(item_id, {"type": []})["type"]

    def reset_type(self, node: BV, default_type: str):
        item_id = str(self.convert_id(node).int)
        self._G.nodes[item_id]["type"] = [default_type]

    def change_type(self, node: BV, new_type: str):
        item_id = str(self.convert_id(node).int)
        if (
            new_type in self.__known_types
            and new_type not in self._G.nodes[item_id]["type"]
        ):
            self._G.nodes[item_id]["type"].append(new_type)

    def add_node(self, node: BV, obj_type: str = None):
        oid = self.convert_id(node).int
        self._G.add_node(str(oid), object=ref(node), type=[obj_type])

    def add_edge(self, start_obj: BV, end_obj: BV):
        node1 = str(self.convert_id(start_obj).int)
        node2 = str(self.convert_id(end_obj).int)
        weight = 0.5
        if hasattr(end_obj, "value"):
            weight = 5
        self._G.add_weighted_edges_from([(node1, node2, weight)])

    def get_edges(self, start_obj: BV) -> List[Tuple[str, str]]:
        node1 = str(self.convert_id(start_obj).int)
        return list(self._G.edges(node1))

    def prune_node_from_edge(self, parent_obj: BV, child_obj: BV):
        vertex1 = str(self.convert_id(parent_obj).int)
        if child_obj is None:
            return
        vertex2 = str(self.convert_id(child_obj).int)
        if (vertex1, vertex2) in self._G.edges:
            self._G.remove_edge(vertex1, vertex2)

    def prune(self, key: int):
        key = str(key)
        if key in self._G.nodes:
            self._G.remove_node(key)

    def find_isolated_nodes(self) -> List[int]:
        """returns a list of isolated nodes."""
        return list(nx.isolates(self._G))

    def find_path(
        self,
        start_obj: Union[BV, int],
        end_obj: Union[BV, int],
        path: Optional[List[str]] = None,
    ) -> List[str]:
        """find a path from start_vertex to end_vertex
        in graph"""
        if path is None:
            path = []
        try:
            start_vertex = self.convert_id(start_obj).int
            end_vertex = self.convert_id(end_obj).int
        except TypeError:
            start_vertex = start_obj
            end_vertex = end_obj
        try:
            return path + nx.shortest_path(self._G, str(start_vertex), str(end_vertex))
        except nx.exception.NetworkXNoPath:
            return path

    def find_all_paths(
        self,
        start_obj: Union[BV, int],
        end_obj: Union[BV, int],
        path: Optional[List[str]] = None,
    ) -> List[List[str]]:
        """find all paths from start_vertex to
        end_vertex in graph"""
        if path is None:
            path = []
        try:
            start_vertex = self.convert_id(start_obj).int
            end_vertex = self.convert_id(end_obj).int
        except TypeError:
            start_vertex = start_obj
            end_vertex = end_obj
        try:
            return path + nx.all_shortest_paths(
                self._G, str(start_vertex), str(end_vertex)
            )
        except nx.exception.NetworkXNoPath:
            return path

    def reverse_route(
        self, end_obj: Union[BV, int], start_obj: Optional[Union[BV, int]] = None
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
        if start_obj is None:
            start_node = str(self.convert_id(end_obj).int)
            nodes = list(
                nx.dag_longest_path(nx.dfs_tree(self._G.reverse(), source=start_node))
            )
            return nodes
        else:
            path = self.find_path(start_obj, end_obj)
            path.reverse()
            return path
        # first_decendent = nx.descendants(reversed_graph, start_node)
        #
        # path_length = sys.maxsize
        # optimum_path = []
        # if start_obj is None:
        #     # We now have to find where to begin.....
        #     for possible_start, nodes in self.__graph_dict.items():
        #         if end_vertex in nodes:
        #             temp_path = self.find_path(possible_start, end_vertex)
        #             if len(temp_path) < path_length:
        #                 path_length = len(temp_path)
        #                 optimum_path = temp_path
        # else:
        #     optimum_path = self.find_path(start_obj, end_obj)
        # optimum_path.reverse()
        # return optimum_path

    # def is_connected(self, nodes_encountered=None, start_vertex=None) -> bool:
    #     """determines if the graph is connected"""
    #     if nodes_encountered is None:
    #         nodes_encountered = set()
    #     graph = self.__graph_dict
    #     nodes = list(graph.keys())
    #     if not start_vertex:
    #         # chose a vertex from graph as a starting point
    #         start_vertex = nodes[0]
    #     nodes_encountered.add(start_vertex)
    #     if len(nodes_encountered) != len(nodes):
    #         for vertex in graph[start_vertex]:
    #             if vertex not in nodes_encountered and self.is_connected(
    #                 nodes_encountered, vertex
    #             ):
    #                 return True
    #     else:
    #         return True
    #     return False

    # def _nested_get(self, obj_type: str) -> List[int]:
    #     """Access a nested object in root by key sequence."""
    #     extracted_list = []
    #     for key, item in self.__graph_dict.items():
    #         if obj_type in item.type:
    #             extracted_list.append(key)
    #     return extracted_list

    @staticmethod
    def convert_id(input_value) -> UUID:
        """Sometimes we're dopy and"""
        if not validate_id(input_value):
            input_value = unique_id(input_value)
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
        start_node_id = str(self.convert_id(node).int)
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
