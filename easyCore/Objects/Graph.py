__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import weakref
from typing import List


class _EntryList(list):
    def __init__(self, *args, **kwargs):
        super(_EntryList, self).__init__(*args, **kwargs)
        self.var_type = ''
        self.finalizer = None


class Graph:

    def __init__(self):
        self._store = weakref.WeakValueDictionary()
        self.__graph_dict = {}

    def vertices(self) -> List[int]:
        """ returns the vertices of a graph """
        return list(self._store.keys())

    def edges(self):
        """ returns the edges of a graph """
        return self.__generate_edges()

    @property
    def argument_objs(self) -> List[int]:
        return self._nested_get('argument')

    @property
    def created_objs(self) -> List[int]:
        return self._nested_get('created')

    @property
    def returned_objs(self) -> List[int]:
        return self._nested_get('returned')

    def get_item_by_id(self, item_id: int) -> object:
        if item_id in self._store.keys():
            return self._store[item_id]
        else:
            raise ValueError

    def is_known(self, vertex: object):
        return id(vertex) in self._store.keys()

    def find_type(self, vertex: object):
        if self.is_known(vertex):
            oid = id(vertex)
            return self.__graph_dict[oid].var_type

    def add_vertex(self, obj: object, obj_type: str = ''):
        oid = id(obj)
        self._store[oid] = obj
        self.__graph_dict[oid] = _EntryList()
        self.__graph_dict[oid].finalizer = weakref.finalize(self._store[oid], self.prune, oid)
        self.__graph_dict[oid].var_type = obj_type

    def add_edge(self, start_obj: object, end_obj: object):
        vertex1 = id(start_obj)
        vertex2 = id(end_obj)
        if vertex1 in self.__graph_dict:
            self.__graph_dict[vertex1].append(vertex2)
        else:
            raise AttributeError

    def __generate_edges(self) -> list:
        """ A static method generating the edges of the
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

    def prune(self, key: int):
        if key in self.__graph_dict.keys():
            del self.__graph_dict[key]

    def find_isolated_vertices(self) -> list:
        """ returns a list of isolated vertices. """
        graph = self.__graph_dict
        isolated = []
        for vertex in graph:
            print(isolated, vertex)
            if not graph[vertex]:
                isolated += [vertex]
        return isolated

    def find_path(self, start_obj, end_obj, path=[]):
        """ find a path from start_vertex to end_vertex
            in graph """

        start_vertex = id(start_obj)
        end_vertex = id(end_obj)

        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return None
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_path = self.find_path(vertex,
                                               end_vertex,
                                               path)
                if extended_path:
                    return extended_path
        return None

    def find_all_paths(self, start_obj, end_obj, path=[]):
        """ find all paths from start_vertex to
            end_vertex in graph """

        start_vertex = id(start_obj)
        end_vertex = id(end_obj)

        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return [path]
        if start_vertex not in graph:
            return []
        paths = []
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_paths = self.find_all_paths(vertex,
                                                     end_vertex,
                                                     path)
                for p in extended_paths:
                    paths.append(p)
        return paths

    def is_connected(self,
                     vertices_encountered=None,
                     start_vertex=None) -> bool:
        """ determines if the graph is connected """
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
                if vertex not in vertices_encountered and self.is_connected(vertices_encountered, vertex):
                    return True
        else:
            return True
        return False

    def _nested_get(self, obj_type: str) -> List[int]:
        """Access a nested object in root by key sequence."""
        extracted_list = []
        for key, item in self.__graph_dict.items():
            if item.var_type is obj_type:
                extracted_list.append(key)
        return extracted_list
