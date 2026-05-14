from pathlib import Path
from typing import Any
import math

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from graph import Graph
from visual_algorithms import bellman_ford_visual
from visual_algorithms import dijkstra_to_target_visual
from visual_algorithms import floyd_visual
from visual_algorithms import max_flow_visual
from visual_algorithms import non_adjacent_visual
from visual_algorithms import out_greater_in_visual
from visual_algorithms import prim_visual
from visual_algorithms import radius_visual
from visual_algorithms import scc_visual


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
FRONTEND_DIST = ROOT / "frontend" / "dist"


class EdgeData(BaseModel):
    source: str
    target: str
    weight: float | None = None


class GraphData(BaseModel):
    directed: bool = False
    weighted: bool = False
    vertices: list[str] = []
    edges: list[EdgeData] = []


class AlgorithmRequest(BaseModel):
    graph: GraphData
    algorithm: str
    params: dict[str, Any] = {}


app = FastAPI(title="визуальная лаборатория графов")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def payload_to_graph(data):
    graph = Graph(directed=data.directed, weighted=data.weighted)
    for vertex in data.vertices:
        graph.add_vertex(vertex)
    for edge in data.edges:
        graph.add_edge(edge.source, edge.target, edge.weight if data.weighted else None)
    return graph


def graph_to_payload(graph):
    edges = []
    for edge in graph.get_edge_list():
        if len(edge) == 3:
            edges.append({"source": edge[0], "target": edge[1], "weight": edge[2]})
        else:
            edges.append({"source": edge[0], "target": edge[1], "weight": None})
    return {
        "directed": graph.directed,
        "weighted": graph.weighted,
        "vertices": list(graph._adj.keys()),
        "edges": edges
    }


def graph_to_text(data):
    lines = [str(int(data.directed)), str(int(data.weighted))]
    adjacency = {vertex: [] for vertex in data.vertices}
    for edge in data.edges:
        adjacency.setdefault(edge.source, [])
        adjacency.setdefault(edge.target, [])
        if data.weighted:
            adjacency[edge.source].append(f"{edge.target} {edge.weight}")
        else:
            adjacency[edge.source].append(edge.target)
        if not data.directed:
            if data.weighted:
                adjacency[edge.target].append(f"{edge.source} {edge.weight}")
            else:
                adjacency[edge.target].append(edge.source)
    for vertex in sorted(adjacency.keys()):
        if adjacency[vertex]:
            lines.append(f"{vertex} | {", ".join(adjacency[vertex])}")
        else:
            lines.append(vertex)
    return "\n".join(lines)


def run_algorithm(graph, algorithm, params):
    if algorithm == "out_greater_in":
        return out_greater_in_visual(graph)
    if algorithm == "non_adjacent":
        return non_adjacent_visual(graph, params.get("vertex", ""))
    if algorithm == "scc":
        return scc_visual(graph)
    if algorithm == "radius":
        return radius_visual(graph)
    if algorithm == "prim":
        return prim_visual(graph)
    if algorithm == "within_n":
        if not graph.directed:
            raise ValueError("по условию задачи требуется орграф.")
        return dijkstra_to_target_visual(graph, params.get("target", ""), number_param(params, "limit", "N"))
    if algorithm == "bf_paths":
        return bellman_ford_visual(graph, params.get("u1", ""), params.get("u2", ""), params.get("target", ""))
    if algorithm == "floyd_paths":
        return floyd_visual(graph, params.get("source", ""), params.get("v1", ""), params.get("v2", ""))
    if algorithm == "max_flow":
        return max_flow_visual(graph, params.get("source", ""), params.get("sink", ""))
    raise ValueError("неизвестный алгоритм.")


def number_param(params, key, label):
    value = params.get(key)
    if value is None or value == "":
        raise ValueError(f"укажите число {label}.")
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{label} должно быть числом.")


def make_json_safe(value):
    if isinstance(value, float):
        if math.isinf(value):
            return "бесконечность" if value > 0 else "минус бесконечность"
        if math.isnan(value):
            return "не число"
        return value
    if isinstance(value, dict):
        return {key: make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]
    return value


@app.get("/api/examples")
def examples():
    return {
        "examples": sorted(path.name for path in DATA_DIR.glob("*.txt"))
    }


@app.get("/api/examples/{name}")
def example(name: str):
    path = DATA_DIR / name
    if path.parent != DATA_DIR or not path.exists():
        raise HTTPException(status_code=404, detail="пример не найден")
    try:
        graph = Graph.from_file(str(path))
        return graph_to_payload(graph)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/algorithm")
def algorithm(request: AlgorithmRequest):
    try:
        graph = payload_to_graph(request.graph)
        return make_json_safe(run_algorithm(graph, request.algorithm, request.params))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/export")
def export_graph(data: GraphData):
    try:
        return {"text": graph_to_text(data)}
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/")
def index():
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "фронтенд запускается командой npm run dev в папке frontend"}
