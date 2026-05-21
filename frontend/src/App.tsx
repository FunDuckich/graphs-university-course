import cytoscape, { Core, ElementDefinition } from "cytoscape";
import { Activity, ArrowDownToLine, CirclePlus, Download, FastForward, Network, Pause, Play, RotateCcw, Save, SkipBack, SkipForward, Sparkles, Trash2, Upload } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

type EdgeData = {
  source: string;
  target: string;
  weight: number | null;
};

type GraphData = {
  directed: boolean;
  weighted: boolean;
  vertices: string[];
  edges: EdgeData[];
};

type StepData = {
  type: string;
  title?: string;
  message?: string;
  activeVertices?: string[];
  activeEdges?: string[][];
  distances?: Record<string, number | string>;
  flows?: Array<{ from: string; to: string; flow: number; capacity: number }>;
  matrix?: Record<string, Record<string, number | string>>;
};

type AlgorithmResponse = {
  summary: string;
  result: unknown;
  steps: StepData[];
};

const emptyGraph: GraphData = {
  directed: true,
  weighted: true,
  vertices: ["S", "A", "B", "T"],
  edges: [
    { source: "S", target: "A", weight: 7 },
    { source: "S", target: "B", weight: 5 },
    { source: "A", target: "T", weight: 4 },
    { source: "B", target: "T", weight: 6 }
  ]
};

const algorithms = [
  { id: "scc", label: "сильно связные компоненты", fields: [] },
  { id: "radius", label: "радиус", fields: [] },
  { id: "prim", label: "прим", fields: [] },
  { id: "within_n", label: "дейкстра до вершины", fields: ["target", "limit"] },
  { id: "bf_paths", label: "беллман-форд", fields: ["u1", "u2", "target"] },
  { id: "floyd_paths", label: "флойд-уоршелл", fields: ["source", "v1", "v2"] },
  { id: "max_flow", label: "максимальный поток", fields: ["source", "sink"] },
  { id: "out_greater_in", label: "исходов больше заходов", fields: [] },
  { id: "non_adjacent", label: "несмежные вершины", fields: ["vertex"] }
];

const fieldLabels: Record<string, string> = {
  target: "цель",
  limit: "N",
  u1: "u1",
  u2: "u2",
  source: "источник",
  sink: "сток",
  v1: "v1",
  v2: "v2",
  vertex: "вершина"
};

function edgeId(edge: EdgeData) {
  return `${edge.source}__${edge.target}`;
}

function edgePairId(source: string, target: string) {
  return `${source}__${target}`;
}

function normalizeWeight(value: string) {
  if (value.trim() === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function algorithmValidationMessage(algorithm: string, params: Record<string, string>) {
  const requiredFields = algorithms.find((item) => item.id === algorithm)?.fields ?? [];
  for (const field of requiredFields) {
    if (!(params[field] ?? "").trim()) {
      return `укажите ${fieldLabels[field].toLowerCase()}.`;
    }
  }
  if (algorithm === "within_n") {
    const limit = Number(params.limit);
    if (!Number.isFinite(limit)) {
      return "N должно быть числом.";
    }
    if (limit < 0) {
      return "N не может быть отрицательным.";
    }
  }
  if (algorithm === "bf_paths" && params.u1.trim() === params.u2.trim()) {
    return "u1 и u2 должны быть разными вершинами.";
  }
  if (algorithm === "floyd_paths" && params.v1.trim() === params.v2.trim()) {
    return "v1 и v2 должны быть разными вершинами.";
  }
  if (algorithm === "max_flow" && params.source.trim() === params.sink.trim()) {
    return "источник и сток должны быть разными вершинами.";
  }
  return "";
}

function resultText(value: unknown): string {
  return JSON.stringify(value, null, 2)
    .split("\"").join("")
    .split("Infinity").join("бесконечность")
    .split("-бесконечность").join("минус бесконечность");
}

export function App() {
  const graphRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const timerRef = useRef<number | null>(null);
  const [graph, setGraph] = useState<GraphData>(emptyGraph);
  const [examples, setExamples] = useState<string[]>([]);
  const [selectedExample, setSelectedExample] = useState("max_flow_classic.txt");
  const [vertexName, setVertexName] = useState("");
  const [edgeSource, setEdgeSource] = useState("S");
  const [edgeTarget, setEdgeTarget] = useState("T");
  const [edgeWeight, setEdgeWeight] = useState("1");
  const [algorithm, setAlgorithm] = useState("max_flow");
  const [params, setParams] = useState<Record<string, string>>({ source: "S", sink: "T", target: "T", limit: "5", u1: "A", u2: "B", v1: "A", v2: "T", vertex: "A" });
  const [response, setResponse] = useState<AlgorithmResponse | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [editorError, setEditorError] = useState("");
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);

  const currentStep = response?.steps[stepIndex] ?? null;

  const elements = useMemo<ElementDefinition[]>(() => {
    const nodes = graph.vertices.map((vertex) => ({
      data: { id: vertex, label: vertex }
    }));
    const edges = graph.edges.map((edge) => ({
      data: {
        id: edgeId(edge),
        source: edge.source,
        target: edge.target,
        label: graph.weighted ? String(edge.weight ?? "") : ""
      }
    }));
    return [...nodes, ...edges];
  }, [graph]);

  useEffect(() => {
    fetch("/api/examples")
      .then((responseData) => responseData.json())
      .then((data) => setExamples(data.examples ?? []))
      .catch(() => setError("не удалось загрузить список примеров"));
  }, []);

  useEffect(() => {
    if (!graphRef.current) {
      return;
    }
    if (!cyRef.current) {
      cyRef.current = cytoscape({
        container: graphRef.current,
        elements,
        wheelSensitivity: 0.18,
        style: [
          {
            selector: "node",
            style: {
              "background-color": "#2dd4bf",
              "border-width": 2,
              "border-color": "#e2e8f0",
              "color": "#e5e7eb",
              "label": "data(label)",
              "font-size": 13,
              "text-valign": "center",
              "text-halign": "center",
              "width": 46,
              "height": 46,
              "text-outline-width": 2,
              "text-outline-color": "#0f172a"
            }
          },
          {
            selector: "edge",
            style: {
              "width": 3,
              "line-color": "#64748b",
              "target-arrow-color": "#64748b",
              "target-arrow-shape": graph.directed ? "triangle" : "none",
              "curve-style": "bezier",
              "label": "data(label)",
              "font-size": 12,
              "color": "#f8fafc",
              "text-background-color": "#111827",
              "text-background-opacity": 0.75,
              "text-background-padding": "3px"
            }
          },
          {
            selector: ".active",
            style: {
              "background-color": "#facc15",
              "line-color": "#facc15",
              "target-arrow-color": "#facc15",
              "border-color": "#fff7ed",
              "width": 6
            }
          },
          {
            selector: ".flow",
            style: {
              "line-color": "#38bdf8",
              "target-arrow-color": "#38bdf8",
              "width": 7
            }
          }
        ],
        layout: { name: "cose", animate: false }
      });
    } else {
      const cy = cyRef.current;
      cy.elements().remove();
      cy.add(elements);
      cy.style().selector("edge").style({ "target-arrow-shape": graph.directed ? "triangle" : "none" }).update();
      cy.layout({ name: "cose", animate: true, animationDuration: 450 }).run();
    }
  }, [elements, graph.directed]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }
    cy.elements().removeClass("active flow");
    if (!currentStep) {
      return;
    }
    for (const vertex of currentStep.activeVertices ?? []) {
      cy.getElementById(vertex).addClass("active");
    }
    for (const pair of currentStep.activeEdges ?? []) {
      cy.getElementById(edgePairId(pair[0], pair[1])).addClass("active");
      if (!graph.directed) {
        cy.getElementById(edgePairId(pair[1], pair[0])).addClass("active");
      }
    }
    for (const flow of currentStep.flows ?? []) {
      if (flow.flow > 0) {
        cy.getElementById(edgePairId(flow.from, flow.to)).addClass("flow");
      }
    }
  }, [currentStep, graph.directed]);

  useEffect(() => {
    if (!playing || !response) {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }
      return;
    }
    timerRef.current = window.setInterval(() => {
      setStepIndex((value) => {
        if (value >= response.steps.length - 1) {
          setPlaying(false);
          return value;
        }
        return value + 1;
      });
    }, 900);
    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }
    };
  }, [playing, response]);

  function applyLayout(name: string) {
    cyRef.current?.layout({ name, animate: true, animationDuration: 500 } as cytoscape.LayoutOptions).run();
  }

  function addVertex() {
    const name = vertexName.trim();
    if (!name) {
      setEditorError("укажите имя вершины.");
      return;
    }
    if (graph.vertices.includes(name)) {
      setEditorError(`вершина "${name}" уже существует.`);
      return;
    }
    setGraph({ ...graph, vertices: [...graph.vertices, name] });
    setVertexName("");
    setEditorError("");
  }

  function addEdge() {
    const source = edgeSource.trim();
    const target = edgeTarget.trim();
    if (!source || !target) {
      setEditorError("укажите обе вершины ребра.");
      return;
    }
    const edgeExists = graph.edges.some((edge) =>
      edge.source === source && edge.target === target
      || !graph.directed && edge.source === target && edge.target === source
    );
    if (edgeExists) {
      setEditorError(`ребро ${source} ${graph.directed ? "->" : "--"} ${target} уже существует.`);
      return;
    }
    const nextVertices = Array.from(new Set([...graph.vertices, source, target]));
    const weight = graph.weighted ? normalizeWeight(edgeWeight) : null;
    if (graph.weighted && weight === null) {
      setEditorError("укажите числовой вес ребра.");
      return;
    }
    setGraph({ ...graph, vertices: nextVertices, edges: [...graph.edges, { source, target, weight }] });
    setEditorError("");
  }

  function deleteVertex(vertex: string) {
    setGraph({
      ...graph,
      vertices: graph.vertices.filter((item) => item !== vertex),
      edges: graph.edges.filter((edge) => edge.source !== vertex && edge.target !== vertex)
    });
    setEditorError("");
  }

  function deleteEdge(edgeToDelete: EdgeData) {
    setGraph({
      ...graph,
      edges: graph.edges.filter((edge) => edge !== edgeToDelete)
    });
    setEditorError("");
  }

  async function loadExample() {
    setError("");
    setEditorError("");
    const responseData = await fetch(`/api/examples/${selectedExample}`);
    if (!responseData.ok) {
      setError("пример не загрузился");
      return;
    }
    const data = await responseData.json();
    setGraph(data);
    setResponse(null);
    setStepIndex(0);
  }

  async function runAlgorithm() {
    setError("");
    setPlaying(false);
    const validationMessage = algorithmValidationMessage(algorithm, params);
    if (validationMessage) {
      setError(validationMessage);
      return;
    }
    const selected = algorithms.find((item) => item.id === algorithm);
    const preparedParams: Record<string, string | number> = {};
    for (const field of selected?.fields ?? []) {
      preparedParams[field] = field === "limit" ? Number(params[field] ?? 0) : params[field] ?? "";
    }
    const responseData = await fetch("/api/algorithm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ graph, algorithm, params: preparedParams })
    });
    const data = await responseData.json();
    if (!responseData.ok) {
      setError(data.detail ?? "алгоритм завершился ошибкой");
      return;
    }
    setResponse(data);
    setStepIndex(0);
  }

  async function exportGraph() {
    const responseData = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    });
    const data = await responseData.json();
    const blob = new Blob([data.text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "graph.txt";
    link.click();
    URL.revokeObjectURL(url);
  }

  function resetDemoGraph() {
    setGraph(emptyGraph);
    setResponse(null);
    setStepIndex(0);
    setEditorError("");
    setError("");
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="top-actions">
          <button onClick={resetDemoGraph} title="сбросить"><RotateCcw size={18} />сброс</button>
          <button onClick={exportGraph} title="экспорт"><Download size={18} />экспорт</button>
        </div>
      </header>

      <main className="workspace">
        <aside className="panel left-panel">
          <section>
            <h2>граф</h2>
            <div className="switch-row">
              <label><input type="checkbox" checked={graph.directed} onChange={(event) => setGraph({ ...graph, directed: event.target.checked })} />ориентированный</label>
              <label><input type="checkbox" checked={graph.weighted} onChange={(event) => setGraph({ ...graph, weighted: event.target.checked })} />взвешенный</label>
            </div>
            <div className="load-row">
              <select value={selectedExample} onChange={(event) => setSelectedExample(event.target.value)}>
                {examples.map((example) => <option key={example} value={example}>{example}</option>)}
              </select>
              <button onClick={loadExample} title="загрузить"><Upload size={18} /></button>
            </div>
          </section>

          <section>
            <h2>вершины</h2>
            <div className="form-row">
              <input value={vertexName} onChange={(event) => {
                setVertexName(event.target.value);
                setEditorError("");
              }} placeholder="имя" />
              <button onClick={addVertex} title="добавить вершину"><CirclePlus size={18} /></button>
            </div>
            <div className="chips">
              {graph.vertices.map((vertex) => (
                <button className="chip" key={vertex} onClick={() => deleteVertex(vertex)} title="удалить вершину">
                  {vertex}<Trash2 size={14} />
                </button>
              ))}
            </div>
            {editorError && <div className="error">{editorError}</div>}
          </section>

          <section>
            <h2>рёбра</h2>
            <div className="grid-form">
              <input value={edgeSource} onChange={(event) => {
                setEdgeSource(event.target.value);
                setEditorError("");
              }} placeholder="из" />
              <input value={edgeTarget} onChange={(event) => {
                setEdgeTarget(event.target.value);
                setEditorError("");
              }} placeholder="в" />
              <input value={edgeWeight} onChange={(event) => {
                setEdgeWeight(event.target.value);
                setEditorError("");
              }} placeholder="вес" disabled={!graph.weighted} />
              <button onClick={addEdge} title="добавить ребро"><Save size={18} /></button>
            </div>
            <div className="edge-list">
              {graph.edges.map((edge, index) => (
                <button key={`${edge.source}-${edge.target}-${index}`} onClick={() => deleteEdge(edge)}>
                  {edge.source} {graph.directed ? "->" : "--"} {edge.target}{graph.weighted ? ` : ${edge.weight}` : ""}<Trash2 size={14} />
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="graph-zone">
          <div className="graph-toolbar">
            <button onClick={() => applyLayout("cose")}><Network size={17} />силы</button>
            <button onClick={() => applyLayout("circle")}><Activity size={17} />круг</button>
            <button onClick={() => applyLayout("breadthfirst")}><ArrowDownToLine size={17} />слои</button>
          </div>
          <div className="graph-canvas" ref={graphRef}></div>
        </section>

        <aside className="panel right-panel">
          <section>
            <h2>алгоритм</h2>
            <select value={algorithm} onChange={(event) => {
              setAlgorithm(event.target.value);
              setError("");
            }}>
              {algorithms.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
            </select>
            <div className="params">
              {algorithms.find((item) => item.id === algorithm)?.fields.map((field) => (
                <label key={field}>
                  {fieldLabels[field]}
                  <input value={params[field] ?? ""} onChange={(event) => {
                    setParams({ ...params, [field]: event.target.value });
                    setError("");
                  }} />
                </label>
              ))}
            </div>
            <button className="primary" onClick={runAlgorithm}><Sparkles size={18} />запустить</button>
            {error && <div className="error">{error}</div>}
          </section>

          <section>
            <h2>шаги</h2>
            <div className="timeline-controls">
              <button onClick={() => setStepIndex(0)} disabled={!response}><SkipBack size={18} /></button>
              <button onClick={() => setPlaying(!playing)} disabled={!response}>{playing ? <Pause size={18} /> : <Play size={18} />}</button>
              <button onClick={() => setStepIndex((value) => Math.min((response?.steps.length ?? 1) - 1, value + 1))} disabled={!response}><SkipForward size={18} /></button>
              <button onClick={() => setStepIndex((response?.steps.length ?? 1) - 1)} disabled={!response}><FastForward size={18} /></button>
            </div>
            <input className="range" type="range" min="0" max={Math.max(0, (response?.steps.length ?? 1) - 1)} value={stepIndex} onChange={(event) => setStepIndex(Number(event.target.value))} disabled={!response} />
            <div className="step-card">
              <h3>{currentStep?.title ?? "запусти алгоритм"}</h3>
              <p>{currentStep?.message ?? "здесь появится пошаговая визуализация"}</p>
              {currentStep?.distances && <pre>{resultText(currentStep.distances)}</pre>}
              {currentStep?.matrix && <pre>{resultText(currentStep.matrix)}</pre>}
            </div>
          </section>

          <section>
            <h2>результат</h2>
            <div className="summary">{response?.summary ?? "результата пока нет"}</div>
            <pre className="result">{response ? resultText(response.result) : ""}</pre>
          </section>
        </aside>
      </main>
    </div>
  );
}
