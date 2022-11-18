#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

import weakref
import sys
from typing import List, Union
from weakref import WeakKeyDictionary
from collections import defaultdict
from uuid import uuid4, UUID


class _EntryList(list):
    def __init__(self, *args, my_type=None, **kwargs):
        super(_EntryList, self).__init__(*args, **kwargs)
        self.__known_types = {"argument", "created", "created_internal", "returned"}
        self.finalizer = None
        self._type = []
        if my_type in self.__known_types:
            self._type.append(my_type)

    def __repr__(self) -> str:
        s = "Graph entry of type: "
        if self._type:
            s += ", ".join(self._type)
        else:
            s += "Undefined"
        s += ". With"
        if self.finalizer is None:
            s += "out"
        s += "a finalizer."
        return s

    def __delitem__(self, key):
        super(_EntryList, self).__delitem__(key)

    def remove_type(self, old_type: str):
        if old_type in self.__known_types and old_type in self._type:
            self._type.remove(old_type)

    def reset_type(self, default_type: str = None):
        self._type = []
        self.type = default_type

    @property
    def type(self) -> List[str]:
        return self._type

    @type.setter
    def type(self, value: str):
        if value in self.__known_types and value not in self._type:
            self._type.append(value)

    @property
    def is_argument(self) -> bool:
        return "argument" in self._type

    @property
    def is_created(self) -> bool:
        return "created" in self._type

    @property
    def is_created_internal(self) -> bool:
        return "created_internal" in self._type

    @property
    def is_returned(self) -> bool:
        return "returned" in self._type


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
        self._store = weakref.WeakValueDictionary()
        self.__graph_dict = {}

    def vertices(self) -> List[int]:
        """returns the vertices of a graph"""
        return list(self._store.keys())

    def edges(self):
        """returns the edges of a graph"""
        return self.__generate_edges()

    @property
    def argument_objs(self) -> List[int]:
        return self._nested_get("argument")

    @property
    def created_objs(self) -> List[int]:
        return self._nested_get("created")

    @property
    def created_internal(self) -> List[int]:
        return self._nested_get("created_internal")

    @property
    def returned_objs(self) -> List[int]:
        return self._nested_get("returned")

    def get_item_by_key(self, item_id: int) -> object:
        if item_id in self._store.keys():
            return self._store[item_id]
        raise ValueError

    def is_known(self, vertex: object) -> bool:
        return self.convert_id(vertex).int in self._store.keys()

    def find_type(self, vertex: object) -> List[str]:
        if self.is_known(vertex):
            oid = self.convert_id(vertex)
            return self.__graph_dict[oid].type

    def reset_type(self, obj, default_type: str):
        if self.convert_id(obj).int in self.__graph_dict.keys():
            self.__graph_dict[self.convert_id(obj).int].reset_type(default_type)

    def change_type(self, obj, new_type: str):
        if self.convert_id(obj).int in self.__graph_dict.keys():
            self.__graph_dict[self.convert_id(obj).int].type = new_type

    def add_vertex(self, obj: object, obj_type: str = None):
        oid = self.convert_id(obj).int
        self._store[oid] = obj
        self.__graph_dict[oid] = _EntryList()  # Enhanced list of keys
        self.__graph_dict[oid].finalizer = weakref.finalize(
            self._store[oid], self.prune, oid
        )
        self.__graph_dict[oid].type = obj_type

    def add_edge(self, start_obj: object, end_obj: object):
        vertex1 = self.convert_id(start_obj).int
        vertex2 = self.convert_id(end_obj).int
        if vertex1 in self.__graph_dict.keys():
            self.__graph_dict[vertex1].append(vertex2)
        else:
            raise AttributeError

    def get_edges(self, start_obj) -> List[str]:
        vertex1 = self.convert_id(start_obj).int
        if vertex1 in self.__graph_dict.keys():
            return list(self.__graph_dict[vertex1])
        else:
            raise AttributeError

    def __generate_edges(self) -> list:
        """A static method generating the edges of the
        graph "graph". Edges are represented as sets
        with one (a loop back to the vertex) or two
        vertices
        """
        edges = []
        for vertex in self.__graph_dict:
            for neighbour in self.__graph_dict[vertex]:
                if {neighbour, vertex} not in edges:
                    edges.append({vertex, neighbour})
        return edges

    def prune_vertex_from_edge(self, parent_obj, child_obj):
        vertex1 = self.convert_id(parent_obj).int
        if child_obj is None:
            return
        vertex2 = self.convert_id(child_obj).int

        if (
            vertex1 in self.__graph_dict.keys()
            and vertex2 in self.__graph_dict[vertex1]
        ):
            del self.__graph_dict[vertex1][self.__graph_dict[vertex1].index(vertex2)]

    def prune(self, key: int):
        if key in self.__graph_dict.keys():
            del self.__graph_dict[key]

    def find_isolated_vertices(self) -> list:
        """returns a list of isolated vertices."""
        graph = self.__graph_dict
        isolated = []
        for vertex in graph:
            print(isolated, vertex)
            if not graph[vertex]:
                isolated += [vertex]
        return isolated

    def find_path(self, start_obj, end_obj, path=[]) -> list:
        """find a path from start_vertex to end_vertex
        in graph"""

        try:
            start_vertex = self.convert_id(start_obj).int
            end_vertex = self.convert_id(end_obj).int
        except TypeError:
            start_vertex = start_obj
            end_vertex = end_obj

        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return []
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_path = self.find_path(vertex, end_vertex, path)
                if extended_path:
                    return extended_path
        return []

    def find_all_paths(self, start_obj, end_obj, path=[]) -> list:
        """find all paths from start_vertex to
        end_vertex in graph"""

        start_vertex = self.convert_id(start_obj).int
        end_vertex = self.convert_id(end_obj).int

        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return [path]
        if start_vertex not in graph:
            return []
        paths = []
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_paths = self.find_all_paths(vertex, end_vertex, path)
                for p in extended_paths:
                    paths.append(p)
        return paths

    def reverse_route(self, end_obj, start_obj=None) -> List:
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
        end_vertex = self.convert_id(end_obj).int

        path_length = sys.maxsize
        optimum_path = []
        if start_obj is None:
            # We now have to find where to begin.....
            for possible_start, vertices in self.__graph_dict.items():
                if end_vertex in vertices:
                    temp_path = self.find_path(possible_start, end_vertex)
                    if len(temp_path) < path_length:
                        path_length = len(temp_path)
                        optimum_path = temp_path
        else:
            optimum_path = self.find_path(start_obj, end_obj)
        optimum_path.reverse()
        return optimum_path

    def is_connected(self, vertices_encountered=None, start_vertex=None) -> bool:
        """determines if the graph is connected"""
        if vertices_encountered is None:
            vertices_encountered = set()
        graph = self.__graph_dict
        vertices = list(graph.keys())
        if not start_vertex:
            # chose a vertex from graph as a starting point
            start_vertex = vertices[0]
        vertices_encountered.add(start_vertex)
        if len(vertices_encountered) != len(vertices):
            for vertex in graph[start_vertex]:
                if vertex not in vertices_encountered and self.is_connected(
                    vertices_encountered, vertex
                ):
                    return True
        else:
            return True
        return False

    def _nested_get(self, obj_type: str) -> List[int]:
        """Access a nested object in root by key sequence."""
        extracted_list = []
        for key, item in self.__graph_dict.items():
            if obj_type in item.type:
                extracted_list.append(key)
        return extracted_list

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
        return f"Graph object of {len(self._store)} vertices."


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
