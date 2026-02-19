import copy
import os


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
        header = f"{'Ориентированный' if self.directed else 'Неориентированный'} "
        header += f"{'взвешенный' if self.weighted else 'невзвешенный'} граф"
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
    def from_copy(cls, other: 'Graph'):
        new = cls(directed=other.directed, weighted=other.weighted)
        new._adj = copy.deepcopy(other._adj)
        new._rev_adj = copy.deepcopy(other._rev_adj)
        return new

    @classmethod
    def from_file(cls, filename: str) -> 'Graph':
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Файл {filename} не найден.")

        with open(filename, 'r', encoding='utf-8') as f:
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
                if '|' not in line:
                    u = line.strip()
                    graph.add_vertex(u)
                    continue

                parts = line.split('|')
                u = parts[0].strip()
                graph.add_vertex(u)

                raw_edges = parts[1].strip()
                if not raw_edges:
                    continue

                edge_entries = [e.strip() for e in raw_edges.split(',') if e.strip()]

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
