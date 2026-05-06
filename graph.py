import copy
import heapq
import os
from collections import deque


class Graph:
    def __init__(self, directed=False, weighted=False):
        self._adj = {}
        self._rev_adj = {}
        self.directed = directed
        self.weighted = weighted

    def __str__(self):
        if not self._adj:
            return "Граф пуст."

        lines = []
        graph_type = "Ориентированный" if self.directed else "Неориентированный"
        weight_type = "взвешенный" if self.weighted else "невзвешенный"
        header = f"{graph_type} {weight_type} граф"
        lines.append(header)
        lines.append("-" * len(header))

        for u in sorted(self._adj.keys()):
            neighbors = []
            for v, weight in self._adj[u].items():
                if self.weighted:
                    neighbors.append(f"{v}({weight})")
                else:
                    neighbors.append(str(v))

            neighbors_str = ", ".join(neighbors) if neighbors else "изолированная вершина"
            lines.append(f"{u} | {neighbors_str}")

        return "\n".join(lines)

    @classmethod
    def from_copy(cls, other: "Graph"):
        new = cls(directed=other.directed, weighted=other.weighted)
        new._adj = copy.deepcopy(other._adj)
        new._rev_adj = copy.deepcopy(other._rev_adj)
        return new

    @classmethod
    def from_file(cls, filename: str) -> "Graph":
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Файл {filename} не найден.")

        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

            if len(lines) < 2:
                raise ValueError("Некорректный формат файла.")

            try:
                is_directed = bool(int(lines[0]))
                is_weighted = bool(int(lines[1]))
            except ValueError:
                raise ValueError("Флаги должны быть 0 или 1.")

            graph = cls(directed=is_directed, weighted=is_weighted)

            for line_idx, line in enumerate(lines[2:], start=3):
                if "|" not in line:
                    u = line.strip()
                    graph.add_vertex(u)
                    continue

                parts = line.split("|")
                u = parts[0].strip()
                graph.add_vertex(u)

                raw_edges = parts[1].strip()
                if not raw_edges:
                    continue

                edge_entries = [e.strip() for e in raw_edges.split(",") if e.strip()]

                for entry in edge_entries:
                    data = entry.split()
                    v = data[0]

                    if is_weighted:
                        if len(data) < 2:
                            raise ValueError(f"Нет веса в строке {line_idx}")
                        try:
                            weight = float(data[1])
                        except ValueError:
                            raise ValueError(f"Вес не число в строке {line_idx}")
                        graph.add_edge(u, v, weight=weight)
                    else:
                        graph.add_edge(u, v)

            return graph

    def save_to_file(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"{int(self.directed)}\n")
            f.write(f"{int(self.weighted)}\n")

            for u in sorted(self._adj.keys()):
                edges = []
                for v, weight in self._adj[u].items():
                    if self.weighted:
                        edges.append(f"{v} {weight}")
                    else:
                        edges.append(f"{v}")

                if edges:
                    edges_str = ", ".join(edges)
                    f.write(f"{u} | {edges_str}\n")
                else:
                    f.write(f"{u}\n")

    def add_vertex(self, v):
        if v not in self._adj:
            self._adj[v] = {}
            self._rev_adj[v] = {}

    def add_edge(self, u, v, weight=None):
        self.add_vertex(u)
        self.add_vertex(v)
        self._adj[u][v] = weight
        self._rev_adj[v][u] = weight
        if not self.directed:
            self._adj[v][u] = weight
            self._rev_adj[u][v] = weight

    def remove_edge(self, u, v):
        if u not in self._adj:
            raise KeyError(f"Вершина {u} не найдена в графе.")
        if v not in self._adj:
            raise KeyError(f"Вершина {v} не найдена в графе.")

        if v not in self._adj[u]:
            raise ValueError(f"Ребро ({u}, {v}) не существует.")

        del self._adj[u][v]
        del self._rev_adj[v][u]

        if not self.directed:
            if u in self._adj[v]:
                del self._adj[v][u]
                del self._rev_adj[u][v]

    def remove_vertex(self, v):
        if v not in self._adj:
            raise KeyError(f"Вершина {v} не найдена в графе.")

        neighbors = list(self._adj[v].keys())
        for neighbor in neighbors:
            self.remove_edge(v, neighbor)

        if self.directed:
            predecessors = list(self._rev_adj[v].keys())
            for pred in predecessors:
                del self._adj[pred][v]
                del self._rev_adj[v][pred]

        del self._adj[v]
        del self._rev_adj[v]

    def get_edge_list(self):
        edges = []
        seen_undirected = set()

        for u in self._adj:
            for v, weight in self._adj[u].items():
                if not self.directed:
                    edge_id = tuple(sorted((str(u), str(v))))
                    if edge_id in seen_undirected:
                        continue
                    seen_undirected.add(edge_id)

                if self.weighted:
                    edges.append((u, v, weight))
                else:
                    edges.append((u, v))
        return edges

    def count_strongly_connected_components(self):
        if not self.directed:
            raise ValueError("по условию задачи требуется орграф.")

        visited = set()
        order = []

        for start in self._adj:
            if start in visited:
                continue

            stack = [(start, False)]
            while stack:
                v, processed = stack.pop()
                if processed:
                    order.append(v)
                    continue
                if v in visited:
                    continue

                visited.add(v)
                stack.append((v, True))
                for to in self._adj[v]:
                    if to not in visited:
                        stack.append((to, False))

        visited.clear()
        count = 0

        for start in reversed(order):
            if start in visited:
                continue

            count += 1
            stack = [start]
            visited.add(start)

            while stack:
                v = stack.pop()
                for to in self._rev_adj[v]:
                    if to not in visited:
                        visited.add(to)
                        stack.append(to)

        return count

    def get_eccentricity_to_vertex(self, target):
        if target not in self._adj:
            raise KeyError(f"вершина {target} не найдена в графе.")

        distances = {target: 0}
        queue = deque([target])

        while queue:
            v = queue.popleft()
            for to in self._rev_adj[v]:
                if to not in distances:
                    distances[to] = distances[v] + 1
                    queue.append(to)

        if len(distances) != len(self._adj):
            return float("inf")

        return max(distances.values())

    def get_radius(self):
        if not self._adj:
            return None

        return min(self.get_eccentricity_to_vertex(v) for v in self._adj)

    def get_eccentricities_to_vertices(self):
        return {v: self.get_eccentricity_to_vertex(v) for v in self._adj}

    def get_minimum_spanning_tree_prim(self):
        if self.directed:
            raise ValueError("алгоритм Прима применяется к неориентированному графу.")
        if not self.weighted:
            raise ValueError("алгоритм Прима требует взвешенный граф.")
        for u in self._adj:
            for v, weight in self._adj[u].items():
                if u != v and weight is None:
                    raise ValueError("у каждого ребра взвешенного графа должен быть вес.")

        result = Graph(directed=False, weighted=True)
        for v in self._adj:
            result.add_vertex(v)

        if not self._adj:
            return result, 0

        start = next(iter(self._adj))
        visited = {start}
        heap = []
        step = 0
        total_weight = 0

        for to, weight in self._adj[start].items():
            if to != start:
                heapq.heappush(heap, (weight, step, start, to))
                step += 1

        while heap and len(visited) < len(self._adj):
            weight, _, u, v = heapq.heappop(heap)
            if v in visited:
                continue

            visited.add(v)
            result.add_edge(u, v, weight)
            total_weight += weight

            for to, next_weight in self._adj[v].items():
                if to not in visited and to != v:
                    heapq.heappush(heap, (next_weight, step, v, to))
                    step += 1

        if len(visited) != len(self._adj):
            raise ValueError("каркас минимального веса существует только для связного графа.")

        return result, total_weight

    def get_vertices_with_distance_to_target_at_most_dijkstra(self, target, max_distance):
        if not self.directed:
            raise ValueError("по условию задачи требуется орграф.")
        if target not in self._adj:
            raise KeyError(f"вершина {target} не найдена в графе.")
        if self._has_negative_edges():
            raise ValueError("в графе есть рёбра отрицательного веса.")

        distances = {target: 0}
        heap = [(0, target)]

        while heap:
            distance, v = heapq.heappop(heap)
            if distance != distances[v]:
                continue
            if distance > max_distance:
                continue

            for to, weight in self._rev_adj[v].items():
                next_distance = distance + self._edge_weight(weight)
                if next_distance < distances.get(to, float("inf")):
                    distances[to] = next_distance
                    heapq.heappush(heap, (next_distance, to))

        result = [v for v in self._adj if distances.get(v, float("inf")) <= max_distance]
        return sorted(result, key=str)

    def get_shortest_paths_from_two_vertices_to_target_bellman_ford(self, u1, u2, target):
        if not self.directed:
            raise ValueError("по условию задачи требуется орграф.")
        for v in (u1, u2, target):
            if v not in self._adj:
                raise KeyError(f"вершина {v} не найдена в графе.")
        if self._has_negative_cycle_bellman_ford():
            raise ValueError("в графе есть цикл отрицательного веса.")

        distances, next_vertices = self._bellman_ford_to_target(target)
        return {
            u1: self._build_path_result(u1, target, distances, next_vertices),
            u2: self._build_path_result(u2, target, distances, next_vertices)
        }

    def get_shortest_paths_with_possible_negative_cycles_floyd(self, source, v1, v2):
        if not self.directed:
            raise ValueError("по условию задачи требуется орграф.")
        for v in (source, v1, v2):
            if v not in self._adj:
                raise KeyError(f"вершина {v} не найдена в графе.")

        vertices = list(self._adj.keys())
        distances = {u: {v: float("inf") for v in vertices} for u in vertices}
        next_vertices = {u: {v: None for v in vertices} for u in vertices}

        for v in vertices:
            distances[v][v] = 0
            next_vertices[v][v] = v

        for u in self._adj:
            for v, weight in self._adj[u].items():
                edge_weight = self._edge_weight(weight)
                if edge_weight < distances[u][v]:
                    distances[u][v] = edge_weight
                    next_vertices[u][v] = v

        for k in vertices:
            for i in vertices:
                if distances[i][k] == float("inf"):
                    continue
                for j in vertices:
                    if distances[k][j] == float("inf"):
                        continue
                    next_distance = distances[i][k] + distances[k][j]
                    if next_distance < distances[i][j]:
                        distances[i][j] = next_distance
                        next_vertices[i][j] = next_vertices[i][k]

        result = {}
        for target in (v1, v2):
            has_negative_cycle = any(
                distances[source][middle] != float("inf")
                and distances[middle][middle] < 0
                and distances[middle][target] != float("inf")
                for middle in vertices
            )
            if has_negative_cycle:
                result[target] = {
                    "distance": float("-inf"),
                    "path": None,
                    "negative_cycle": True
                }
            else:
                result[target] = self._build_floyd_path_result(source, target, distances, next_vertices)

        return result

    def get_maximum_flow_edmonds_karp(self, source, sink):
        if not self.directed:
            raise ValueError("максимальный поток ищется в ориентированной сети.")
        if not self.weighted:
            raise ValueError("для максимального потока нужен взвешенный граф с пропускными способностями.")
        if source not in self._adj:
            raise KeyError(f"вершина {source} не найдена в графе.")
        if sink not in self._adj:
            raise KeyError(f"вершина {sink} не найдена в графе.")
        if source == sink:
            raise ValueError("источник и сток должны быть разными вершинами.")

        residual = {v: {} for v in self._adj}
        original_edges = []

        for u in self._adj:
            for v, weight in self._adj[u].items():
                capacity = self._edge_weight(weight)
                if capacity < 0:
                    raise ValueError("пропускные способности не могут быть отрицательными.")
                residual[u][v] = residual[u].get(v, 0) + capacity
                residual[v].setdefault(u, 0)
                original_edges.append((u, v, capacity))

        max_flow = 0

        while True:
            parent = {source: None}
            queue = deque([source])

            while queue and sink not in parent:
                u = queue.popleft()
                for v, capacity in residual[u].items():
                    if v not in parent and capacity > 0:
                        parent[v] = u
                        queue.append(v)

            if sink not in parent:
                break

            path_flow = float("inf")
            current = sink
            while current != source:
                previous = parent[current]
                path_flow = min(path_flow, residual[previous][current])
                current = previous

            current = sink
            while current != source:
                previous = parent[current]
                residual[previous][current] -= path_flow
                residual[current][previous] = residual[current].get(previous, 0) + path_flow
                current = previous

            max_flow += path_flow

        flows = []
        for u, v, capacity in original_edges:
            flow = capacity - residual[u].get(v, 0)
            if flow > 0:
                flows.append((u, v, flow, capacity))

        return {
            "value": max_flow,
            "flows": flows
        }

    def _bellman_ford_to_target(self, target):
        distances = {v: float("inf") for v in self._adj}
        next_vertices = {v: None for v in self._adj}
        distances[target] = 0
        edges = []

        for u in self._adj:
            for v, weight in self._adj[u].items():
                edges.append((v, u, self._edge_weight(weight)))

        for _ in range(max(0, len(self._adj) - 1)):
            changed = False
            for u, v, weight in edges:
                if distances[u] == float("inf"):
                    continue
                next_distance = distances[u] + weight
                if next_distance < distances[v]:
                    distances[v] = next_distance
                    next_vertices[v] = u
                    changed = True
            if not changed:
                break

        return distances, next_vertices

    def _build_path_result(self, source, target, distances, next_vertices):
        if distances[source] == float("inf"):
            return {
                "distance": float("inf"),
                "path": None,
                "negative_cycle": False
            }

        path = [source]
        current = source
        while current != target:
            current = next_vertices[current]
            if current is None:
                return {
                    "distance": float("inf"),
                    "path": None,
                    "negative_cycle": False
                }
            path.append(current)

        return {
            "distance": distances[source],
            "path": path,
            "negative_cycle": False
        }

    def _build_floyd_path_result(self, source, target, distances, next_vertices):
        if distances[source][target] == float("inf"):
            return {
                "distance": float("inf"),
                "path": None,
                "negative_cycle": False
            }

        path = [source]
        current = source
        while current != target:
            current = next_vertices[current][target]
            if current is None:
                return {
                    "distance": float("inf"),
                    "path": None,
                    "negative_cycle": False
                }
            path.append(current)

        return {
            "distance": distances[source][target],
            "path": path,
            "negative_cycle": False
        }

    def _has_negative_edges(self):
        return any(
            self._edge_weight(weight) < 0
            for u in self._adj
            for weight in self._adj[u].values()
        )

    def _has_negative_cycle_bellman_ford(self):
        distances = {v: 0 for v in self._adj}
        edges = [
            (u, v, self._edge_weight(weight))
            for u in self._adj
            for v, weight in self._adj[u].items()
        ]

        for _ in range(max(0, len(self._adj) - 1)):
            changed = False
            for u, v, weight in edges:
                next_distance = distances[u] + weight
                if next_distance < distances[v]:
                    distances[v] = next_distance
                    changed = True
            if not changed:
                return False

        return any(distances[u] + weight < distances[v] for u, v, weight in edges)

    def _edge_weight(self, weight):
        if not self.weighted:
            return 1
        if weight is None:
            raise ValueError("у каждого ребра взвешенного графа должен быть вес.")
        return weight

    def get_out_greater_in_vertices(self):
        """
        Возвращает список вершин, у которых полустепень исхода
        (исходящие рёбра) строго больше полустепени захода (входящие рёбра).
        """
        if not self.directed:
            return []

        result = []
        for v in self._adj:
            out_degree = len(self._adj[v])  # Полустепень исхода
            in_degree = len(self._rev_adj[v])  # Полустепень захода

            if out_degree > in_degree:
                result.append(v)

        return result

    def get_non_adjacent_vertices(self, v):
        """
        Возвращает список вершин орграфа, не смежных с вершиной v.
        Смежными считаются вершины, соединенные с v ребром в любом направлении.
        """
        if not self.directed:
            raise ValueError("По условию задачи требуется орграф. Текущий граф неориентированный.")

        if v not in self._adj:
            raise KeyError(f"Вершина \"{v}\" не найдена в графе.")

        adjacent = set(self._adj[v].keys()).union(set(self._rev_adj[v].keys()))

        non_adjacent = []
        for u in self._adj:
            if u != v and u not in adjacent:
                non_adjacent.append(u)

        return non_adjacent

    @staticmethod
    def symmetric_difference(g1: "Graph", g2: "Graph") -> "Graph":
        if g1.directed != g2.directed:
            raise ValueError("Графы должны быть одного типа ориентированности.")

        res = Graph(directed=g1.directed, weighted=g1.weighted or g2.weighted)

        all_v = set(g1._adj.keys()) | set(g2._adj.keys())
        for v in all_v:
            res.add_vertex(v)

        edges1 = g1.get_edge_list()
        edges2 = g2.get_edge_list()

        def has_edge(g, u, v):
            return u in g._adj and v in g._adj[u]

        for e in edges1:
            u, v = e[0], e[1]
            if not has_edge(g2, u, v):
                w = e[2] if len(e) == 3 else None
                res.add_edge(u, v, weight=w)

        for e in edges2:
            u, v = e[0], e[1]
            if not has_edge(g1, u, v):
                w = e[2] if len(e) == 3 else None
                res.add_edge(u, v, weight=w)

        return res
