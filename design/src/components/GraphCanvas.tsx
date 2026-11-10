import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';

import type { Phase } from '../types';
import { content } from '../data';
import {
  type Band,
  type GraphModel,
  type SimEdge,
  type SimNode,
  edgeGeometry,
  layoutDomain,
  layoutMainline,
  layoutRadial,
  mainlineEdgeGeometry,
  seedPositions,
  stepForce,
} from '../graph/layout';

export type LayoutMode = 'force' | 'domain' | 'radial';

export interface GraphCanvasProps {
  model: GraphModel;
  mode: 'schema' | 'mainline';
  phases: Phase[];
  layout: LayoutMode;
  showLabels: boolean;
  dimMode: boolean;
  query: string;
  selectedId: string | null;
  visibleDomains: Set<string>;
  visibleRelations: Set<string>;
  onSelectNode: (id: string | null) => void;
  onSelectPhase: (id: string) => void;
}

interface Transform {
  x: number;
  y: number;
  k: number;
}

const CONTAINER_ID = 'module';

/** The interactive canvas of the artifact graph. */
export function GraphCanvas(props: GraphCanvasProps) {
  const {
    model,
    mode,
    phases,
    layout,
    showLabels,
    dimMode,
    query,
    selectedId,
    visibleDomains,
    visibleRelations,
    onSelectNode,
    onSelectPhase,
  } = props;

  const svgRef = useRef<SVGSVGElement | null>(null);
  const viewportRef = useRef<SVGGElement | null>(null);
  const nodeRefs = useRef(new Map<string, SVGGElement>());
  const edgeRefs = useRef(new Map<string, SVGPathElement>());
  const labelRefs = useRef(new Map<string, SVGTextElement>());
  const transformRef = useRef<Transform>({ x: 0, y: 0, k: 1 });
  const alphaRef = useRef(1);
  const autoFitRef = useRef(true);
  const dragRef = useRef<{ node: SimNode; moved: boolean } | null>(null);
  const panRef = useRef<{ x: number; y: number; tx: number; ty: number } | null>(null);

  const [size, setSize] = useState({ width: 1200, height: 800 });
  const [bands, setBands] = useState<Band[]>([]);

  // ── Layout ──────────────────────────────────────────────────────────
  const relayout = useCallback(
    (width: number, height: number) => {
      if (mode === 'mainline') {
        const next = layoutMainline(model, phases, Math.max(400, width - 40));
        setBands(next);
        transformRef.current = { x: 20, y: 10, k: 1 };
        autoFitRef.current = false;
        return;
      }
      for (const node of model.nodes) {
        node.fx = null;
        node.fy = null;
      }
      if (layout === 'domain') layoutDomain(model, width, height);
      else if (layout === 'radial') layoutRadial(model, width, height);
      else seedPositions(model, width, height);
      alphaRef.current = 1;
      autoFitRef.current = true;
    },
    [layout, mode, model, phases],
  );

  useLayoutEffect(() => {
    relayout(size.width, size.height);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layout, mode, model]);

  useEffect(() => {
    const element = svgRef.current;
    if (!element) return undefined;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      setSize({ width: Math.max(320, width), height: Math.max(240, height) });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  // ── Painting ────────────────────────────────────────────────────────
  const paint = useCallback(() => {
    const neighbors = new Set<string>();
    if (selectedId) {
      neighbors.add(selectedId);
      for (const edge of model.edges) {
        if (edge.source.id === selectedId) neighbors.add(edge.target.id);
        if (edge.target.id === selectedId) neighbors.add(edge.source.id);
      }
    }
    const needle = query.trim().toLowerCase();
    const hasQuery = needle.length > 0;

    const nodeVisible = (node: SimNode) => visibleDomains.has(node.domain);
    const edgeVisible = (edge: SimEdge) =>
      visibleRelations.has(edge.relation) && nodeVisible(edge.source) && nodeVisible(edge.target);

    for (const node of model.nodes) {
      const element = nodeRefs.current.get(node.id);
      if (!element) continue;
      element.setAttribute('transform', `translate(${node.x},${node.y})`);
      element.style.display = nodeVisible(node) ? '' : 'none';

      let classes = 'node';
      if (node.id === CONTAINER_ID) classes += ' container';
      if (node.prepared) classes += ' prepared';
      if (mode === 'mainline' && node.onSpine) classes += ' on-spine';
      if (selectedId) {
        if (node.id === selectedId) classes += ' selected';
        else if (neighbors.has(node.id)) classes += ' neighbor';
        else if (dimMode) classes += ' dim';
      }
      if (hasQuery && dimMode && !matches(node, needle)) classes += ' dim';
      element.setAttribute('class', classes);
    }

    for (const edge of model.edges) {
      const path = edgeRefs.current.get(edgeKey(edge));
      const label = labelRefs.current.get(edgeKey(edge));
      if (!path) continue;
      const visible = edgeVisible(edge);
      path.style.display = visible ? '' : 'none';
      if (label) label.style.display = visible && showLabels ? '' : 'none';
      if (!visible) continue;

      const touches = selectedId !== null && (edge.source.id === selectedId || edge.target.id === selectedId);
      let classes = 'edge';
      if (edge.bidirectional) classes += ' both';
      if (edge.mainline) classes += ' main';
      if (edge.relation === 'CONTAINS') classes += ' contain';
      if (dimMode && selectedId && !touches) classes += ' dim';
      if (touches) classes += ' hot';
      path.setAttribute('class', classes);
      if (edge.relation !== 'CONTAINS') {
        path.setAttribute('marker-end', touches ? 'url(#arrow-hot)' : edge.mainline ? 'url(#arrow-main)' : 'url(#arrow)');
      }
      if (label) {
        let labelClasses = 'edge-label';
        if (edge.mainline) labelClasses += ' main';
        if (touches) labelClasses += ' hot';
        else if (dimMode && selectedId) labelClasses += ' dim';
        label.setAttribute('class', labelClasses);
      }
    }
  }, [dimMode, mode, model, query, selectedId, showLabels, visibleDomains, visibleRelations]);

  const paintGeometry = useCallback(() => {
    for (const node of model.nodes) {
      const element = nodeRefs.current.get(node.id);
      if (!element) continue;
      element.setAttribute('transform', `translate(${node.x},${node.y})`);
    }
    for (const edge of model.edges) {
      const path = edgeRefs.current.get(edgeKey(edge));
      const label = labelRefs.current.get(edgeKey(edge));
      if (!path) continue;
      const geometry = mode === 'mainline' ? mainlineEdgeGeometry(edge) : edgeGeometry(edge);
      path.setAttribute('d', geometry.d);
      if (label) {
        label.setAttribute('x', String(geometry.mx));
        label.setAttribute('y', String(geometry.my));
      }
    }
  }, [mode, model]);

  const applyTransform = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const { x, y, k } = transformRef.current;
    viewport.setAttribute('transform', `translate(${x},${y}) scale(${k})`);
  }, []);

  const fitToView = useCallback(() => {
    if (mode === 'mainline') {
      transformRef.current = { x: 20, y: 10, k: 1 };
      applyTransform();
      return;
    }
    const visible = model.nodes.filter((node) => visibleDomains.has(node.domain));
    if (visible.length === 0) return;
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    for (const node of visible) {
      minX = Math.min(minX, node.x - node.radius);
      minY = Math.min(minY, node.y - node.radius);
      maxX = Math.max(maxX, node.x + node.radius);
      maxY = Math.max(maxY, node.y + node.radius);
    }
    const padding = 90;
    let k = Math.min(
      (size.width - padding * 2) / Math.max(1, maxX - minX),
      (size.height - padding * 2) / Math.max(1, maxY - minY),
    );
    k = Math.max(0.15, Math.min(2.2, k));
    transformRef.current = {
      k,
      x: size.width / 2 - ((minX + maxX) / 2) * k,
      y: size.height / 2 - ((minY + maxY) / 2) * k,
    };
    applyTransform();
  }, [applyTransform, mode, model.nodes, size, visibleDomains]);

  // ── Simulation loop ─────────────────────────────────────────────────
  useEffect(() => {
    let frame = 0;
    const tick = () => {
      if (mode === 'schema' && layout === 'force') {
        if (alphaRef.current > 0.005) {
          stepForce(model, alphaRef.current, size.width, size.height);
          alphaRef.current *= 0.97;
        }
      } else if (mode === 'schema' && alphaRef.current > 0.02) {
        if (layout === 'domain') layoutDomain(model, size.width, size.height);
        else layoutRadial(model, size.width, size.height);
        alphaRef.current *= 0.9;
      }
      paintGeometry();
      paint();
      if (autoFitRef.current && mode === 'schema') {
        // Keep the graph framed while the layout settles.
        fitToView();
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [fitToView, layout, mode, model, paint, paintGeometry, size]);

  // Repaint whenever the filters or the selection change.
  useEffect(() => {
    paint();
  }, [paint]);

  // ── Interaction ─────────────────────────────────────────────────────
  const toGraph = useCallback((clientX: number, clientY: number) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    const { x, y, k } = transformRef.current;
    return { x: (clientX - rect.left - x) / k, y: (clientY - rect.top - y) / k };
  }, []);

  const onMouseDown = useCallback(
    (event: React.MouseEvent<SVGSVGElement>) => {
      const target = event.target as Element;
      const nodeElement = target.closest?.('.node');
      if (nodeElement) {
        const id = nodeElement.getAttribute('data-id');
        const node = id ? model.byId.get(id) : undefined;
        if (!node) return;
        dragRef.current = { node, moved: false };
        node.fx = node.x;
        node.fy = node.y;
        alphaRef.current = Math.max(alphaRef.current, 0.35);
        event.preventDefault();
        return;
      }
      panRef.current = {
        x: event.clientX,
        y: event.clientY,
        tx: transformRef.current.x,
        ty: transformRef.current.y,
      };
      autoFitRef.current = false;
      svgRef.current?.classList.add('panning');
    },
    [model.byId],
  );

  const onMouseMove = useCallback(
    (event: React.MouseEvent<SVGSVGElement>) => {
      if (dragRef.current) {
        const point = toGraph(event.clientX, event.clientY);
        dragRef.current.node.fx = point.x;
        dragRef.current.node.fy = point.y;
        dragRef.current.moved = true;
        alphaRef.current = Math.max(alphaRef.current, 0.3);
        return;
      }
      if (panRef.current) {
        transformRef.current.x = panRef.current.tx + (event.clientX - panRef.current.x);
        transformRef.current.y = panRef.current.ty + (event.clientY - panRef.current.y);
        applyTransform();
      }
    },
    [applyTransform, toGraph],
  );

  const onMouseUp = useCallback(() => {
    if (dragRef.current) {
      const { node, moved } = dragRef.current;
      if (!moved) onSelectNode(node.id);
      dragRef.current = null;
      return;
    }
    panRef.current = null;
    svgRef.current?.classList.remove('panning');
  }, [onSelectNode]);

  const onClick = useCallback(
    (event: React.MouseEvent<SVGSVGElement>) => {
      const target = event.target as Element;
      const hit = target.closest?.('.node, .band');
      if (hit && hit.classList.contains('band')) return;
      if (!hit) onSelectNode(null);
    },
    [onSelectNode],
  );

  const onDoubleClick = useCallback(
    (event: React.MouseEvent<SVGSVGElement>) => {
      const target = event.target as Element;
      const nodeElement = target.closest?.('.node');
      if (!nodeElement) return;
      const id = nodeElement.getAttribute('data-id');
      const node = id ? model.byId.get(id) : undefined;
      if (!node) return;
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) return;
      const k = Math.max(transformRef.current.k, 1.4);
      transformRef.current = {
        k,
        x: rect.width / 2 - node.x * k,
        y: rect.height / 2 - node.y * k,
      };
      applyTransform();
      onSelectNode(node.id);
    },
    [applyTransform, model.byId, onSelectNode],
  );

  const onWheel = useCallback(
    (event: React.WheelEvent<SVGSVGElement>) => {
      event.preventDefault();
      const current = transformRef.current;
      if (mode === 'mainline') {
        // The mainline is taller than the viewport — the wheel scrolls it.
        transformRef.current = {
          ...current,
          x: current.x - event.deltaX,
          y: current.y - event.deltaY,
        };
        applyTransform();
        return;
      }
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) return;
      const mx = event.clientX - rect.left;
      const my = event.clientY - rect.top;
      const factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
      const k = Math.max(0.15, Math.min(4, current.k * factor));
      const ratio = k / current.k;
      autoFitRef.current = false;
      transformRef.current = {
        k,
        x: mx - (mx - current.x) * ratio,
        y: my - (my - current.y) * ratio,
      };
      applyTransform();
    },
    [applyTransform, mode],
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'f' || event.key === 'F') {
        const active = document.activeElement;
        if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) return;
        fitToView();
      }
      if (event.key === 'Escape') onSelectNode(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [fitToView, onSelectNode]);

  useEffect(() => {
    applyTransform();
  }, [applyTransform, bands]);

  const domainColor = useMemo(() => new Map(content.domains.map((domain) => [domain.key, domain.color])), []);

  return (
    <svg
      id="graph"
      ref={svgRef}
      xmlns="http://www.w3.org/2000/svg"
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      onWheel={onWheel}
    >
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7fa8" />
        </marker>
        <marker id="arrow-hot" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#4f9dff" />
        </marker>
        <marker id="arrow-main" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#4f9dff" />
        </marker>
      </defs>
      <g ref={viewportRef} className={mode === 'mainline' ? 'mainline' : undefined}>
        {mode === 'mainline' && <BandLayer bands={bands} model={model} onSelectPhase={onSelectPhase} />}
        <g className="edge-layer">
          {model.edges.map((edge) => (
            <path
              key={edgeKey(edge)}
              ref={(element) => {
                if (element) edgeRefs.current.set(edgeKey(edge), element);
                else edgeRefs.current.delete(edgeKey(edge));
              }}
              className="edge"
            />
          ))}
        </g>
        <g className="label-layer">
          {model.edges.map((edge) => (
            <text
              key={edgeKey(edge)}
              ref={(element) => {
                if (element) labelRefs.current.set(edgeKey(edge), element);
                else labelRefs.current.delete(edgeKey(edge));
              }}
              className="edge-label"
            >
              {edge.relation}
            </text>
          ))}
        </g>
        <g className="node-layer">
          {model.nodes.map((node) => (
            <g
              key={node.id}
              data-id={node.id}
              ref={(element) => {
                if (element) nodeRefs.current.set(node.id, element);
                else nodeRefs.current.delete(node.id);
              }}
              className="node"
              style={{ ['--domain' as string]: domainColor.get(node.domain) }}
            >
              {node.id === CONTAINER_ID ? (
                <>
                  <rect className="halo" x={-69} y={-27} width={138} height={54} rx={13} />
                  <rect className="body" x={-69} y={-27} width={138} height={54} rx={13} />
                  <text className="prefix" y={-34}>
                    {node.prefix}
                  </text>
                  <text className="title" y={2}>
                    {node.label}
                  </text>
                  <text className="kind" y={40}>
                    组织容器
                  </text>
                </>
              ) : (
                <>
                  <circle className="halo" r={node.radius + 4} />
                  <circle className="body" r={node.radius} fill={domainColor.get(node.domain)} />
                  <text className="prefix" y={4}>
                    {node.prefix}
                  </text>
                  <text className="title" y={node.radius + 14}>
                    {node.label}
                  </text>
                </>
              )}
            </g>
          ))}
        </g>
      </g>
    </svg>
  );
}

/** The phase bands of the mainline view. */
function BandLayer({
  bands,
  model,
  onSelectPhase,
}: {
  bands: Band[];
  model: GraphModel;
  onSelectPhase: (id: string) => void;
}) {
  const width = model.size.width;
  return (
    <g className="band-layer">
      {bands.length > 1 && (
        <path
          className="spine"
          d={`M 34 ${bands[0].top + 30} L 34 ${bands[bands.length - 1].top + 30}`}
        />
      )}
      {bands.map((band) => (
        <g
          key={band.phase.id}
          className={`band${band.phase.lateral ? ' lateral' : ''}`}
          data-phase={band.phase.id}
          onClick={() => onSelectPhase(band.phase.id)}
        >
          <rect className="band-bg" x={0} y={band.top} width={width} height={band.height} rx={14} />
          {band.splitY !== null && (
            <>
              <line className="band-split" x1={198} x2={width - 24} y1={band.splitY} y2={band.splitY} />
              <text className="band-split-label" x={width - 28} y={band.splitY - 6}>
                可提前准备
              </text>
            </>
          )}
          <circle className="band-step-bg" cx={34} cy={band.top + 30} r={12} />
          <text className="band-step" x={34} y={band.top + 31}>
            {band.phase.lateral ? '横切' : band.index + 1}
          </text>
          <text className="band-title" x={58} y={band.top + 27}>
            {band.phase.label}
          </text>
          <text className="band-question" x={58} y={band.top + 47}>
            {band.phase.question}
          </text>
          <text className="band-count" x={58} y={band.top + 65}>
            {band.produced > 0
              ? `产出 ${band.produced}${band.prepared > 0 ? ` · 预备 ${band.prepared}` : ''}`
              : `预备 ${band.prepared}`}
          </text>
        </g>
      ))}
    </g>
  );
}

/** A stable key for an edge. */
function edgeKey(edge: SimEdge): string {
  return `${edge.source.id}->${edge.target.id}:${edge.relation}`;
}

/** Does the node match the search query? */
function matches(node: SimNode, needle: string): boolean {
  return (
    node.label.toLowerCase().includes(needle) ||
    node.id.toLowerCase().includes(needle) ||
    node.prefix.toLowerCase().includes(needle) ||
    node.artifact.purpose.toLowerCase().includes(needle) ||
    node.artifact.definitionFile.toLowerCase().includes(needle)
  );
}
