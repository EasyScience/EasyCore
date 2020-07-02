__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from collections import deque


class Borg:
    __log = []
    __map = []
    __debug = False

    def __init__(self):
        self.log = self.__log
        self.debug = self.__debug
        self.map = self.__map

    def find_shortest_path(self, start, end):
        graph = self.__map
        dist = {start: [start]}
        q = deque(start)
        while len(q):
            at = q.popleft()
            for next in graph[at]:
                if next not in dist:
                    dist[next] = [dist[at], next]
                    q.append(next)
        return dist.get(end)