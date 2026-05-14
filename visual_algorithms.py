import heapq
from collections import deque

from graph import Graph


def edge_weight(graph, weight):
    if not graph.weighted:
        return 1
    if weight is None:
        raise ValueError("у каждого ребра взвешенного графа должен быть вес.")
    return weight


def path_result(source, target, distance, path, negative_cycle=False):
    return {
        "source": source,
        "target": target,
        "distance": distance,
        "path": path,
        "negativeCycle": negative_cycle
    }


def build_path(source, target, next_vertices):
    path = [source]
    current = source
    while current != target:
        current = next_vertices.get(current)
        if current is None:
            return None
        path.append(current)
    return path


def out_greater_in_visual(graph):
    if not graph.directed:
        raise ValueError("по условию задачи требуется орграф.")

    result = []
    steps = []
    for vertex in graph._adj:
        out_degree = len(graph._adj[vertex])
        in_degree = len(graph._rev_adj[vertex])
        selected = out_degree > in_degree
        if selected:
            result.append(vertex)
        steps.append({
            "type": "degree_check",
            "title": f"проверяем вершину {vertex}",
            "activeVertices": [vertex],
            "message": f"исходящих рёбер: {out_degree}, входящих рёбер: {in_degree}",
            "table": {"out": out_degree, "in": in_degree, "selected": selected}
        })

    return {
        "summary": f"вершины: {", ".join(result) if result else "нет"}",
        "result": {"vertices": result},
        "steps": steps
    }


def non_adjacent_visual(graph, vertex):
    if not graph.directed:
        raise ValueError("по условию задачи требуется орграф.")
    if vertex not in graph._adj:
        raise KeyError(f"вершина {vertex} не найдена в графе.")

    adjacent = set(graph._adj[vertex]) | set(graph._rev_adj[vertex])
    result = [v for v in graph._adj if v != vertex and v not in adjacent]
    edges = [[vertex, v] for v in graph._adj[vertex]] + [[v, vertex] for v in graph._rev_adj[vertex]]
    steps = [
        {
            "type": "adjacent_collect",
            "title": f"собираем смежные вершины для {vertex}",
            "activeVertices": [vertex],
            "activeEdges": edges,
            "message": f"смежные вершины: {", ".join(sorted(adjacent, key=str)) if adjacent else "нет"}"
        },
        {
            "type": "non_adjacent_result",
            "title": "получено множество несмежных вершин",
            "activeVertices": result,
            "message": f"несмежные вершины: {", ".join(result) if result else "нет"}"
        }
    ]

    return {
        "summary": f"несмежные вершины: {", ".join(result) if result else "нет"}",
        "result": {"vertices": result},
        "steps": steps
    }


def scc_visual(graph):
    if not graph.directed:
        raise ValueError("по условию задачи требуется орграф.")

    visited = set()
    order = []
    steps = []

    def first_pass(start):
        stack = [(start, False)]
        while stack:
            vertex, processed = stack.pop()
            if processed:
                order.append(vertex)
                steps.append({
                    "type": "finish",
                    "title": f"вершина {vertex} завершена",
                    "activeVertices": [vertex],
                    "message": f"добавляем {vertex} в порядок выхода"
                })
                continue
            if vertex in visited:
                continue
            visited.add(vertex)
            steps.append({
                "type": "visit",
                "title": f"первый проход: посещаем {vertex}",
                "activeVertices": [vertex],
                "message": "идём по исходным рёбрам"
            })
            stack.append((vertex, True))
            for to in graph._adj[vertex]:
                if to not in visited:
                    stack.append((to, False))

    for start in graph._adj:
        if start not in visited:
            first_pass(start)

    visited.clear()
    components = []

    for start in reversed(order):
        if start in visited:
            continue
        component = []
        stack = [start]
        visited.add(start)
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            for to in graph._rev_adj[vertex]:
                if to not in visited:
                    visited.add(to)
                    stack.append(to)
        components.append(component)
        steps.append({
            "type": "component",
            "title": f"найдена компонента {len(components)}",
            "activeVertices": component,
            "message": f"компонента: {", ".join(component)}"
        })

    return {
        "summary": f"количество сильно связных компонент: {len(components)}",
        "result": {"count": len(components), "components": components},
        "steps": steps
    }


def radius_visual(graph):
    if not graph._adj:
        return {
            "summary": "радиус пустого графа не определён",
            "result": {"radius": None, "eccentricities": {}},
            "steps": []
        }

    eccentricities = {}
    steps = []

    for target in graph._adj:
        distances = {target: 0}
        queue = deque([target])
        steps.append({
            "type": "bfs_start",
            "title": f"считаем эксцентриситет вершины {target}",
            "activeVertices": [target],
            "message": "запускаем BFS по обратным рёбрам"
        })
        while queue:
            vertex = queue.popleft()
            for to in graph._rev_adj[vertex]:
                if to not in distances:
                    distances[to] = distances[vertex] + 1
                    queue.append(to)
                    steps.append({
                        "type": "distance",
                        "title": f"расстояние от {to} до {target}",
                        "activeVertices": [to, target],
                        "activeEdges": [[to, vertex]],
                        "message": f"расстояние: {distances[to]}",
                        "distances": dict(distances)
                    })
        eccentricity = float("inf") if len(distances) != len(graph._adj) else max(distances.values())
        eccentricities[target] = eccentricity
        steps.append({
            "type": "eccentricity",
            "title": f"эксцентриситет {target}",
            "activeVertices": [target],
            "message": f"значение: {format_number(eccentricity)}"
        })

    radius = min(eccentricities.values())
    centers = [v for v, value in eccentricities.items() if value == radius]
    steps.append({
        "type": "radius",
        "title": "радиус графа найден",
        "activeVertices": centers,
        "message": f"радиус: {format_number(radius)}, центры: {", ".join(centers)}"
    })

    return {
        "summary": f"радиус: {format_number(radius)}",
        "result": {"radius": radius, "eccentricities": eccentricities, "centers": centers},
        "steps": steps
    }


def prim_visual(graph):
    tree, total_weight = graph.get_minimum_spanning_tree_prim()
    visited = set()
    steps = []
    if not graph._adj:
        return {
            "summary": "каркас пустого графа имеет вес 0",
            "result": {"weight": 0, "edges": []},
            "steps": []
        }

    start = next(iter(graph._adj))
    visited.add(start)
    heap = []
    index = 0
    for to, weight in graph._adj[start].items():
        if to != start:
            heapq.heappush(heap, (weight, index, start, to))
            index += 1

    steps.append({
        "type": "prim_start",
        "title": f"начинаем с вершины {start}",
        "activeVertices": [start],
        "message": "добавляем исходящие рёбра в очередь кандидатов"
    })

    chosen_edges = []
    while heap and len(visited) < len(graph._adj):
        weight, _, u, v = heapq.heappop(heap)
        if v in visited:
            steps.append({
                "type": "prim_skip",
                "title": f"ребро {u} -> {v} пропущено",
                "activeEdges": [[u, v]],
                "message": "оно ведёт в уже выбранную вершину"
            })
            continue
        visited.add(v)
        chosen_edges.append((u, v, weight))
        steps.append({
            "type": "prim_take",
            "title": f"берём ребро {u} -> {v}",
            "activeVertices": list(visited),
            "activeEdges": [[a, b] for a, b, _ in chosen_edges],
            "message": f"вес ребра: {weight}"
        })
        for to, next_weight in graph._adj[v].items():
            if to not in visited and to != v:
                heapq.heappush(heap, (next_weight, index, v, to))
                index += 1

    return {
        "summary": f"вес каркаса: {total_weight}",
        "result": {"weight": total_weight, "edges": tree.get_edge_list()},
        "steps": steps
    }


def dijkstra_to_target_visual(graph, target, max_distance):
    vertices = graph.get_vertices_with_distance_to_target_at_most_dijkstra(target, max_distance)
    distances = {target: 0}
    heap = [(0, target)]
    steps = [{
        "type": "dijkstra_start",
        "title": f"старт из {target} по обратному графу",
        "activeVertices": [target],
        "message": "так мы считаем расстояния до заданной вершины"
    }]

    while heap:
        distance, vertex = heapq.heappop(heap)
        if distance != distances[vertex]:
            continue
        steps.append({
            "type": "dijkstra_vertex",
            "title": f"выбрана вершина {vertex}",
            "activeVertices": [vertex],
            "message": f"текущее расстояние: {distance}",
            "distances": dict(distances)
        })
        if distance > max_distance:
            continue
        for to, weight in graph._rev_adj[vertex].items():
            next_distance = distance + edge_weight(graph, weight)
            if next_distance < distances.get(to, float("inf")):
                distances[to] = next_distance
                heapq.heappush(heap, (next_distance, to))
                steps.append({
                    "type": "dijkstra_relax",
                    "title": f"улучшаем расстояние для {to}",
                    "activeVertices": [to, vertex],
                    "activeEdges": [[to, vertex]],
                    "message": f"новое расстояние: {next_distance}",
                    "distances": dict(distances)
                })

    return {
        "summary": f"подходящие вершины: {", ".join(vertices) if vertices else "нет"}",
        "result": {"vertices": vertices, "distances": distances},
        "steps": steps
    }


def bellman_ford_visual(graph, u1, u2, target):
    result = graph.get_shortest_paths_from_two_vertices_to_target_bellman_ford(u1, u2, target)
    distances = {v: float("inf") for v in graph._adj}
    next_vertices = {v: None for v in graph._adj}
    distances[target] = 0
    edges = [(v, u, edge_weight(graph, weight)) for u in graph._adj for v, weight in graph._adj[u].items()]
    steps = [{
        "type": "bellman_start",
        "title": f"старт от стока {target} по обратным рёбрам",
        "activeVertices": [target],
        "message": "так сразу получаем пути до стока из разных вершин"
    }]

    for iteration in range(max(0, len(graph._adj) - 1)):
        changed = False
        for u, v, weight in edges:
            if distances[u] == float("inf"):
                continue
            next_distance = distances[u] + weight
            if next_distance < distances[v]:
                distances[v] = next_distance
                next_vertices[v] = u
                changed = True
                steps.append({
                    "type": "bellman_relax",
                    "title": f"проход {iteration + 1}: релаксация {v} -> {u}",
                    "activeVertices": [v, u],
                    "activeEdges": [[v, u]],
                    "message": f"новое расстояние для {v}: {next_distance}",
                    "distances": dict(distances)
                })
        if not changed:
            steps.append({
                "type": "bellman_stop",
                "title": "изменений больше нет",
                "message": "алгоритм завершён досрочно"
            })
            break

    steps.append({
        "type": "paths",
        "title": "пути восстановлены",
        "activeEdges": path_edges(result[u1]["path"]) + path_edges(result[u2]["path"]),
        "message": "используем массив следующих вершин"
    })

    return {
        "summary": "пути Беллмана-Форда построены",
        "result": result,
        "steps": steps
    }


def floyd_visual(graph, source, v1, v2):
    result = graph.get_shortest_paths_with_possible_negative_cycles_floyd(source, v1, v2)
    vertices = list(graph._adj.keys())
    distances = {u: {v: float("inf") for v in vertices} for u in vertices}
    steps = []

    for v in vertices:
        distances[v][v] = 0
    for u in graph._adj:
        for v, weight in graph._adj[u].items():
            distances[u][v] = min(distances[u][v], edge_weight(graph, weight))

    for k in vertices:
        steps.append({
            "type": "floyd_middle",
            "title": f"промежуточная вершина {k}",
            "activeVertices": [k],
            "message": "проверяем, можно ли улучшить пути через неё"
        })
        for i in vertices:
            if distances[i][k] == float("inf"):
                continue
            for j in vertices:
                if distances[k][j] == float("inf"):
                    continue
                next_distance = distances[i][k] + distances[k][j]
                if next_distance < distances[i][j]:
                    distances[i][j] = next_distance
                    steps.append({
                        "type": "floyd_update",
                        "title": f"обновляем путь {i} -> {j}",
                        "activeVertices": [i, k, j],
                        "message": f"новая длина через {k}: {next_distance}",
                        "matrix": serializable_matrix(distances)
                    })

    steps.append({
        "type": "floyd_result",
        "title": "результат для выбранных путей",
        "activeEdges": path_edges(result[v1]["path"]) + path_edges(result[v2]["path"]),
        "message": "если на маршруте есть отрицательный цикл, путь не определён"
    })

    return {
        "summary": "расчёт Флойда-Уоршелла завершён",
        "result": result,
        "steps": steps
    }


def max_flow_visual(graph, source, sink):
    if not graph.directed:
        raise ValueError("максимальный поток ищется в ориентированной сети.")
    if not graph.weighted:
        raise ValueError("для максимального потока нужен взвешенный граф с пропускными способностями.")
    if source not in graph._adj:
        raise KeyError(f"вершина {source} не найдена в графе.")
    if sink not in graph._adj:
        raise KeyError(f"вершина {sink} не найдена в графе.")
    if source == sink:
        raise ValueError("источник и сток должны быть разными вершинами.")

    residual = {v: {} for v in graph._adj}
    original_edges = []
    for u in graph._adj:
        for v, weight in graph._adj[u].items():
            capacity = edge_weight(graph, weight)
            if capacity < 0:
                raise ValueError("пропускные способности не могут быть отрицательными.")
            residual[u][v] = residual[u].get(v, 0) + capacity
            residual[v].setdefault(u, 0)
            original_edges.append((u, v, capacity))

    max_flow = 0
    steps = []
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
            steps.append({
                "type": "flow_stop",
                "title": "увеличивающих путей больше нет",
                "message": f"максимальный поток: {max_flow}"
            })
            break

        path = []
        path_flow = float("inf")
        current = sink
        while current != source:
            previous = parent[current]
            path.append((previous, current))
            path_flow = min(path_flow, residual[previous][current])
            current = previous
        path.reverse()

        steps.append({
            "type": "augmenting_path",
            "title": "найден увеличивающий путь",
            "activeVertices": [source, sink],
            "activeEdges": [[u, v] for u, v in path],
            "message": f"бутылочное горлышко: {path_flow}"
        })

        current = sink
        while current != source:
            previous = parent[current]
            residual[previous][current] -= path_flow
            residual[current][previous] = residual[current].get(previous, 0) + path_flow
            current = previous

        max_flow += path_flow
        steps.append({
            "type": "flow_update",
            "title": "остаточная сеть обновлена",
            "activeEdges": [[u, v] for u, v in path],
            "message": f"текущий поток: {max_flow}",
            "flows": current_flows(original_edges, residual)
        })

    flows = current_flows(original_edges, residual)
    return {
        "summary": f"максимальный поток: {max_flow}",
        "result": {"value": max_flow, "flows": flows},
        "steps": steps
    }


def path_edges(path):
    if not path:
        return []
    return [[path[i], path[i + 1]] for i in range(len(path) - 1)]


def current_flows(original_edges, residual):
    flows = []
    for u, v, capacity in original_edges:
        flow = capacity - residual[u].get(v, 0)
        flows.append({
            "from": u,
            "to": v,
            "flow": flow,
            "capacity": capacity
        })
    return flows


def serializable_matrix(distances):
    return {
        u: {v: format_number(value) for v, value in row.items()}
        for u, row in distances.items()
    }


def format_number(value):
    if value == float("inf"):
        return "бесконечность"
    if value == float("-inf"):
        return "минус бесконечность"
    return value
