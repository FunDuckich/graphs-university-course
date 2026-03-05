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
        print("--- Graph CLI Manager ---")
        self._show_help()
        while True:
            cmd = input(f"\n[{self.current_key or 'Нет графа'}] > ").strip().lower().split()
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
                else:
                    print("Неизвестная команда. Введите 'help'.")
            except Exception as e:
                print(f"Ошибка: {e}")

    def _show_help(self):
        print("""
                Команды:
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
                  exit                                - выход
        """)

    def _copy_graph(self, args):
        if not self.current:
            print("Нет активного графа для копирования.")
            return
        new_name = args[0]
        self.graphs[new_name] = Graph.from_copy(self.current)
        print(f"Граф '{self.current_key}' скопирован в '{new_name}'.")

    def _show_edges(self):
        if not self.current:
            print("Сначала выберите или создайте граф.")
            return

        edges = self.current.get_edge_list()
        connector = "-->" if self.current.directed else "---"
        if not edges:
            print("Граф не содержит рёбер.")
            return

        print(f"--- Список рёбер ({self.current_key}) ---")
        for edge in edges:
            if len(edge) == 3:
                print(f"{edge[0]} ---({edge[2]}){connector} {edge[1]}")
            else:
                print(f"{edge[0]} {connector} {edge[1]}")

    def _create_graph(self, args):
        name, d, w = args[0], int(args[1]), int(args[2])
        self.graphs[name] = Graph(directed=bool(d), weighted=bool(w))
        self.current_key = name
        print(f"Граф '{name}' создан.")

    def _load_graph(self, args):
        name, path = args[0], args[1]
        self.graphs[name] = Graph.from_file(path)
        self.current_key = name
        print(f"Граф '{name}' загружен из {path}.")

    def _save_graph(self, args):
        if not self.current:
            print("Сначала выберите или создайте граф.")
            return
        if not args:
            print("Укажите имя файла. Пример: save my_graph.txt")
            return

        path = args[0]
        try:
            self.current.save_to_file(path)
            print(f"Граф '{self.current_key}' успешно сохранен в файл {path}.")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def _switch_graph(self, args):
        if args[0] in self.graphs:
            self.current_key = args[0]
            print(f"Переключено на '{args[0]}'.")
        else:
            print("Граф не найден.")

    def _list_graphs(self):
        print("Графы в памяти:", ", ".join(self.graphs.keys()) or "пусто")

    def _add_vertex(self, args):
        if self.current: self.current.add_vertex(args[0])

    def _add_edge(self, args):
        if not self.current:
            return
        u, v = args[0], args[1]
        w = float(args[2]) if len(args) > 2 and self.current.weighted else None
        self.current.add_edge(u, v, weight=w)

    def _del_vertex(self, args):
        if self.current:
            self.current.remove_vertex(args[0])

    def _del_edge(self, args):
        if self.current:
            self.current.remove_edge(args[0], args[1])

    def _show_current(self):
        if self.current:
            print(self.current)
        else:
            print("Сначала выберите или создайте граф.")

    def _task1_out_greater_in(self):
        if not self.current:
            print("Сначала выберите или создайте граф.")
            return

        vertices = self.current.get_out_greater_in_vertices()

        if vertices:
            print(f"Вершины, у которых полустепень исхода > полустепени захода: {', '.join(vertices)}")
        else:
            print("Таких вершин нет (у всех полустепень исхода <= полустепени захода).")

    def _task2_non_adjacent(self, args):
        if not self.current:
            print("Сначала выберите или создайте граф.")
            return

        if not args:
            print("Укажите вершину. Пример: task2 A")
            return

        v = args[0]
        try:
            result = self.current.get_non_adjacent_vertices(v)

            if result:
                print(f"Вершины, не смежные с '{v}': {', '.join(result)}")
            else:
                print(f"Все остальные вершины графа смежны с '{v}'.")

        except ValueError as ve:
            print(f"Ошибка логики: {ve}")
        except KeyError as ke:
            print(f"Ошибка ввода: {ke}")
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    GraphManager().run()
