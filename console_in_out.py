from graph import Graph


class GraphManager:
    def __init__(self):
        self.graphs = {}
        self.current_key = None

    @property
    def current(self):
        if self.current_key:
            return self.graphs[self.current_key]
        return None

    def run(self):
        print("--- менеджер графов ---")
        self._show_help()
        while True:
            current_name = self.current_key or "нет графа"
            cmd = input(f"\n[{current_name}] > ").strip().split()
            if not cmd:
                continue

            try:
                if cmd[0] == "exit":
                    break
                elif cmd[0] == "help":
                    self._show_help()
                elif cmd[0] == "list":
                    self._list_graphs()
                elif cmd[0] == "create":
                    self._create_graph(cmd[1:])
                elif cmd[0] == "load":
                    self._load_graph(cmd[1:])
                elif cmd[0] == "save":
                    self._save_graph(cmd[1:])
                elif cmd[0] == "copy":
                    self._copy_graph(cmd[1:])
                elif cmd[0] == "switch":
                    self._switch_graph(cmd[1:])
                elif cmd[0] == "add_v":
                    self._add_vertex(cmd[1:])
                elif cmd[0] == "add_e":
                    self._add_edge(cmd[1:])
                elif cmd[0] == "del_v":
                    self._del_vertex(cmd[1:])
                elif cmd[0] == "del_e":
                    self._del_edge(cmd[1:])
                elif cmd[0] == "edges":
                    self._show_edges()
                elif cmd[0] == "show":
                    self._show_current()
                elif cmd[0] == "task1":
                    self._task1_out_greater_in()
                elif cmd[0] == "task2":
                    self._task2_non_adjacent(cmd[1:])
                elif cmd[0] == "scc":
                    self._count_strongly_connected_components()
                elif cmd[0] == "radius":
                    self._show_radius()
                elif cmd[0] == "prim":
                    self._prim(cmd[1:])
                elif cmd[0] == "within_n":
                    self._vertices_with_distance_to_target_at_most(cmd[1:])
                elif cmd[0] == "bf_paths":
                    self._bellman_ford_paths(cmd[1:])
                elif cmd[0] == "floyd_paths":
                    self._floyd_paths(cmd[1:])
                elif cmd[0] == "max_flow":
                    self._max_flow(cmd[1:])
                elif cmd[0] == "sym_diff":
                    self._symmetric_difference(cmd[1:])
                else:
                    print("неизвестная команда. введите \"help\".")
            except Exception as e:
                print(f"ошибка: {e}")

    def _show_help(self):
        print("""
                команды:
                  create <name> <dir:0/1> <weight:0/1> - новый граф
                  load <name> <filename>              - загрузить из файла
                  save <filename>                     - сохранить граф в файл
                  copy <new_name>                     - клонировать текущий граф
                  list                                - список всех графов в памяти
                  switch <name>                       - переключиться на граф
                  show                                - вывести текущий граф (__str__)
                  edges                               - вывести плоский список рёбер
                  add_v <v>                           - добавить вершину
                  add_e <u> <v> [w]                   - добавить ребро
                  del_v <v>                           - удалить вершину
                  del_e <u> <v>                       - удалить ребро
                  task1                               - вершины, где исходов > заходов
                  task2 <v>                           - вершины орграфа, не смежные с <v>
                  scc                                 - количество сильно связных компонент орграфа
                  radius                              - радиус графа
                  prim <new_name>                     - каркас минимального веса алгоритмом Прима
                  within_n <v> <n>                    - вершины, от которых расстояние до <v> не более n
                  bf_paths <u1> <u2> <v>              - кратчайшие пути из u1 и u2 до v
                  floyd_paths <u> <v1> <v2>           - кратчайшие пути из u до v1 и v2
                  max_flow <source> <sink>            - максимальный поток из source в sink
                  sym_diff <g1> <g2> <new_res>        - симметрическая разность
                  exit                                - выход
        """)

    def _copy_graph(self, args):
        if not self.current:
            print("нет активного графа для копирования.")
            return
        if not args:
            print("укажите имя копии. пример: copy graph_copy")
            return
        new_name = args[0]
        if new_name in self.graphs:
            print(f"граф \"{new_name}\" уже существует.")
            return
        self.graphs[new_name] = Graph.from_copy(self.current)
        print(f"граф \"{self.current_key}\" скопирован в \"{new_name}\".")

    def _show_edges(self):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        edges = self.current.get_edge_list()
        connector = "-->" if self.current.directed else "---"
        if not edges:
            print("граф не содержит рёбер.")
            return

        print(f"--- список рёбер ({self.current_key}) ---")
        for edge in edges:
            if len(edge) == 3:
                print(f"{edge[0]} ---({edge[2]}){connector} {edge[1]}")
            else:
                print(f"{edge[0]} {connector} {edge[1]}")

    def _create_graph(self, args):
        if len(args) < 3:
            print("укажите имя графа, ориентированность и взвешенность. пример: create g 1 0")
            return
        name = args[0]
        try:
            d = int(args[1])
            w = int(args[2])
        except ValueError:
            print("флаги ориентированности и взвешенности должны быть 0 или 1.")
            return
        if name in self.graphs:
            print(f"граф \"{name}\" уже существует.")
            return
        if d not in (0, 1) or w not in (0, 1):
            print("флаги ориентированности и взвешенности должны быть 0 или 1.")
            return
        self.graphs[name] = Graph(directed=bool(d), weighted=bool(w))
        self.current_key = name
        print(f"граф \"{name}\" создан.")

    def _load_graph(self, args):
        if len(args) < 2:
            print("укажите имя графа и файл. пример: load g data/directed_weighted.txt")
            return
        name, path = args[0], args[1]
        if name in self.graphs:
            print(f"граф \"{name}\" уже существует.")
            return
        self.graphs[name] = Graph.from_file(path)
        self.current_key = name
        print(f"граф \"{name}\" загружен из {path}.")

    def _save_graph(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return
        if not args:
            print("укажите имя файла. пример: save my_graph.txt")
            return

        path = args[0]
        try:
            self.current.save_to_file(path)
            print(f"граф \"{self.current_key}\" успешно сохранен в файл {path}.")
        except Exception as e:
            print(f"ошибка при сохранении: {e}")

    def _switch_graph(self, args):
        if not args:
            print("укажите имя графа. пример: switch g")
            return
        if args[0] in self.graphs:
            self.current_key = args[0]
            print(f"переключено на \"{args[0]}\".")
        else:
            print("граф не найден.")

    def _list_graphs(self):
        print("графы в памяти:", ", ".join(self.graphs.keys()) or "пусто")

    def _add_vertex(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return
        if not args:
            print("укажите вершину. пример: add_v A")
            return
        vertex = args[0]
        if vertex in self.current._adj:
            print(f"вершина \"{vertex}\" уже существует.")
            return
        self.current.add_vertex(vertex)
        print(f"вершина \"{vertex}\" добавлена.")

    def _add_edge(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return
        if len(args) < 2:
            print("укажите две вершины ребра. пример: add_e A B")
            return
        u, v = args[0], args[1]
        if v in self.current._adj.get(u, {}):
            print(f"ребро ({u}, {v}) уже существует.")
            return
        if not self.current.directed and u in self.current._adj.get(v, {}):
            print(f"ребро ({u}, {v}) уже существует.")
            return
        if self.current.weighted and len(args) < 3:
            print("для взвешенного графа укажите вес. пример: add_e A B 3")
            return
        if not self.current.weighted and len(args) > 2:
            print("для невзвешенного графа вес указывать не нужно.")
            return
        if self.current.weighted:
            try:
                w = float(args[2])
            except ValueError:
                print("вес должен быть числом.")
                return
        else:
            w = None
        self.current.add_edge(u, v, weight=w)
        print(f"ребро ({u}, {v}) добавлено.")

    def _del_vertex(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return
        if not args:
            print("укажите вершину. пример: del_v A")
            return
        self.current.remove_vertex(args[0])
        print(f"вершина \"{args[0]}\" удалена.")

    def _del_edge(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return
        if len(args) < 2:
            print("укажите две вершины ребра. пример: del_e A B")
            return
        self.current.remove_edge(args[0], args[1])
        print(f"ребро ({args[0]}, {args[1]}) удалено.")

    def _show_current(self):
        if self.current:
            print(self.current)
        else:
            print("сначала выберите или создайте граф.")

    def _task1_out_greater_in(self):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        vertices = self.current.get_out_greater_in_vertices()

        if vertices:
            vertices_str = ", ".join(vertices)
            print(f"вершины, у которых полустепень исхода > полустепени захода: {vertices_str}")
        else:
            print("таких вершин нет (у всех полустепень исхода <= полустепени захода).")

    def _task2_non_adjacent(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        if not args:
            print("укажите вершину. пример: task2 A")
            return

        v = args[0]
        try:
            result = self.current.get_non_adjacent_vertices(v)

            if result:
                result_str = ", ".join(result)
                print(f"вершины, не смежные с \"{v}\": {result_str}")
            else:
                print(f"все остальные вершины графа смежны с \"{v}\".")

        except ValueError as ve:
            print(f"ошибка логики: {ve}")
        except KeyError as ke:
            print(f"ошибка ввода: {ke}")
        except Exception as e:
            print(f"неожиданная ошибка: {e}")

    def _count_strongly_connected_components(self):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        count = self.current.count_strongly_connected_components()
        print(f"количество сильно связных компонент: {count}")

    def _show_radius(self):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        radius = self.current.get_radius()
        eccentricities = self.current.get_eccentricities_to_vertices()

        if radius is None:
            print("радиус пустого графа не определён.")
            return

        print(f"радиус графа: {self._format_distance(radius)}")
        print("эксцентриситеты вершин:")
        for v in sorted(eccentricities.keys()):
            print(f"{v}: {self._format_distance(eccentricities[v])}")

    def _prim(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        if not args:
            print("укажите имя для каркаса. пример: prim mst")
            return

        result_name = args[0]
        tree, total_weight = self.current.get_minimum_spanning_tree_prim()
        self.graphs[result_name] = tree
        self.current_key = result_name
        print(f"каркас минимального веса сохранён в {result_name}.")
        print(f"вес каркаса: {total_weight}")

    def _vertices_with_distance_to_target_at_most(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        if len(args) < 2:
            print("укажите вершину и ограничение. пример: within_n V1 10")
            return

        target = args[0]
        try:
            max_distance = float(args[1])
        except ValueError:
            print("N должно быть числом.")
            return
        vertices = self.current.get_vertices_with_distance_to_target_at_most_dijkstra(target, max_distance)

        if vertices:
            vertices_str = ", ".join(vertices)
            print(f"вершины, от которых расстояние до {target} не более {max_distance}: {vertices_str}")
        else:
            print(f"таких вершин для {target} нет.")

    def _bellman_ford_paths(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        if len(args) < 3:
            print("укажите две начальные вершины и конечную. пример: bf_paths A B Z")
            return

        u1, u2, target = args[0], args[1], args[2]
        results = self.current.get_shortest_paths_from_two_vertices_to_target_bellman_ford(u1, u2, target)
        self._print_path_result(u1, target, results[u1])
        self._print_path_result(u2, target, results[u2])

    def _floyd_paths(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        if len(args) < 3:
            print("укажите начальную вершину и две конечные. пример: floyd_paths A X Y")
            return

        source, v1, v2 = args[0], args[1], args[2]
        results = self.current.get_shortest_paths_with_possible_negative_cycles_floyd(source, v1, v2)
        self._print_path_result(source, v1, results[v1])
        self._print_path_result(source, v2, results[v2])

    def _max_flow(self, args):
        if not self.current:
            print("сначала выберите или создайте граф.")
            return

        if len(args) < 2:
            print("укажите источник и сток. пример: max_flow S T")
            return

        source, sink = args[0], args[1]
        result = self.current.get_maximum_flow_edmonds_karp(source, sink)
        value = result["value"]
        print(f"максимальный поток из {source} в {sink}: {value}")

        if not result["flows"]:
            print("положительного потока по рёбрам нет.")
            return

        print("поток по рёбрам:")
        for u, v, flow, capacity in result["flows"]:
            print(f"{u} -> {v}: {flow} из {capacity}")

    @staticmethod
    def _format_distance(value):
        if value == float("-inf"):
            return "минус бесконечность"
        if value == float("inf"):
            return "бесконечность"
        return str(value)

    def _print_path_result(self, source, target, result):
        if result["negative_cycle"]:
            print(f"кратчайший путь из {source} до {target} не определён: на маршруте есть цикл отрицательного веса.")
            return

        if result["path"] is None:
            print(f"пути из {source} до {target} нет.")
            return

        path_str = " -> ".join(result["path"])
        distance = self._format_distance(result["distance"])
        print(f"кратчайший путь из {source} до {target}: {path_str}, длина: {distance}")

    def _symmetric_difference(self, args):
        if len(args) < 3:
            print("нужно 3 аргумента: имя1 имя2 имя_результата")
            return

        name1, name2, res_name = args[0], args[1], args[2]

        if name1 not in self.graphs or name2 not in self.graphs:
            print("один из графов не найден.")
            return

        try:
            g_res = Graph.symmetric_difference(self.graphs[name1], self.graphs[name2])
            self.graphs[res_name] = g_res
            self.current_key = res_name
            print(f"симметрическая разность \"{name1}\" и \"{name2}\" сохранена в \"{res_name}\".")
        except Exception as e:
            print(f"ошибка: {e}")


if __name__ == "__main__":
    GraphManager().run()
