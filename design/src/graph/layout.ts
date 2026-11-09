/**
 * The graph model and its layouts.
 *
 * The model is a plain simulation: nodes have a position and a velocity,
 * edges reference their endpoints.  The React layer renders the model
 * and pushes the positions into the DOM, so the simulation never goes
 * through React's render cycle.
 */

import type { Artifact, Edge, Phase } from '../types';

export interface SimNode {
  id: string;
  label: string;
  prefix: string;
  domain: string;
  radius: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  fx: number | null;
  fy: number | null;
  phase: string | null;
  prepared: boolean;
  lateral: boolean;
  onSpine: boolean;
  artifact: Artifact;
}

export interface SimEdge {
  source: SimNode;
  target: SimNode;
  relation: string;
  bidirectional: boolean;
  mainline: boolean;
  origin: string;
  slot: number;
  siblings: number;
  lane: number;
}

export interface Band {
  phase: Phase;
  index: number;
  top: number;
  height: number;
  count: number;
  produced: number;
  prepared: number;
  splitY: number | null;
}

export interface GraphModel {
  nodes: SimNode[];
  edges: SimEdge[];
  byId: Map<string, SimNode>;
  bands: Band[];
  size: { width: number; height: number };
}

/** Force layout constants. */
const REPULSION = 52000;
const SPRING = 0.03;
const REST = 210;
const DAMP = 0.85;
const MAXV = 24;

/** Mainline layout constants. */
const RAIL = 208;
const CARD = 148;
const ROW = 104;
const BAND_TOP = 72;
const BAND_PAD = 30;
const BAND_GAP = 22;

/** Build the simulation model of the artifact graph. */
export function buildGraph(
  artifacts: Artifact[],
  edges: Edge[],
  phases: Phase[],
  mode: 'schema' | 'mainline',
): GraphModel {
  const phaseOf = new Map<string, Phase>();
  const preparedOf = new Set<string>();
  for (const phase of phases) {
    for (const id of phase.artifacts) phaseOf.set(id, phase);
    for (const id of phase.prepares) preparedOf.add(id);
  }

  const nodes: SimNode[] = artifacts.map((artifact) => {
    const phase = phaseOf.get(artifact.id) ?? null;
    return {
      id: artifact.id,
      label: artifact.name,
      prefix: artifact.prefix,
      domain: artifact.domain,
      radius: 15 + Math.min(9, artifact.fields.length * 1.1),
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null,
      phase: phase ? phase.id : null,
      prepared: preparedOf.has(artifact.id),
      lateral: phase ? phase.lateral : false,
      onSpine: false,
      artifact,
    };
  });

  const byId = new Map(nodes.map((node) => [node.id, node]));
  const simEdges: SimEdge[] = [];
  for (const edge of edges) {
    const source = byId.get(edge.source);
    const target = byId.get(edge.target);
    if (!source || !target) continue;
    simEdges.push({
      source,
      target,
      relation: edge.relation,
      bidirectional: edge.bidirectional,
      mainline: edge.mainline,
      origin: edge.origin,
      slot: 0,
      siblings: 1,
      lane: 0,
    });
  }

  if (mode === 'mainline') {
    for (const edge of simEdges) {
      if (!edge.mainline) continue;
      edge.source.onSpine = true;
      edge.target.onSpine = true;
    }
  }

  // Parallel edges between the same pair of nodes would overlap, so
  // they are spread apart.
  const pairs = new Map<string, number>();
  for (const edge of simEdges) {
    const key = pairKey(edge);
    pairs.set(key, (pairs.get(key) ?? 0) + 1);
  }
  const taken = new Map<string, number>();
  for (const edge of simEdges) {
    const key = pairKey(edge);
    const slot = taken.get(key) ?? 0;
    edge.slot = slot;
    edge.siblings = pairs.get(key) ?? 1;
    taken.set(key, slot + 1);
  }

  return { nodes, edges: simEdges, byId, bands: [], size: { width: 0, height: 0 } };
}

function pairKey(edge: SimEdge): string {
  return edge.source.id < edge.target.id
    ? `${edge.source.id}|${edge.target.id}`
    : `${edge.target.id}|${edge.source.id}`;
}

/** Place the nodes on a circle — the starting point of the simulation. */
export function seedPositions(model: GraphModel, width: number, height: number): void {
  model.nodes.forEach((node, index) => {
    const angle = (index / Math.max(1, model.nodes.length)) * Math.PI * 2;
    const radius = Math.min(width, height) * 0.4;
    node.x = width / 2 + Math.cos(angle) * radius;
    node.y = height / 2 + Math.sin(angle) * radius;
    node.vx = 0;
    node.vy = 0;
    node.fx = null;
    node.fy = null;
  });
}

/** One step of the force simulation. */
export function stepForce(model: GraphModel, alpha: number, width: number, height: number): void {
  const { nodes, edges } = model;
  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const first = nodes[i];
      const second = nodes[j];
      let dx = second.x - first.x;
      let dy = second.y - first.y;
      let squared = dx * dx + dy * dy;
      if (squared < 1) {
        dx = Math.random() - 0.5;
        dy = Math.random() - 0.5;
        squared = 1;
      }
      const distance = Math.sqrt(squared);
      const force = (REPULSION / squared) * alpha;
      const ux = dx / distance;
      const uy = dy / distance;
      first.vx -= ux * force;
      first.vy -= uy * force;
      second.vx += ux * force;
      second.vy += uy * force;
    }
  }

  for (const edge of edges) {
    const dx = edge.target.x - edge.source.x;
    const dy = edge.target.y - edge.source.y;
    const distance = Math.max(0.01, Math.sqrt(dx * dx + dy * dy));
    const force = (distance - REST) * SPRING * alpha;
    const ux = dx / distance;
    const uy = dy / distance;
    edge.source.vx += ux * force;
    edge.source.vy += uy * force;
    edge.target.vx -= ux * force;
    edge.target.vy -= uy * force;
  }

  for (const node of nodes) {
    node.vx += (width / 2 - node.x) * 0.006 * alpha;
    node.vy += (height / 2 - node.y) * 0.006 * alpha;
  }

  for (const node of nodes) {
    if (node.fx !== null && node.fy !== null) {
      node.x = node.fx;
      node.y = node.fy;
      node.vx = 0;
      node.vy = 0;
      continue;
    }
    node.vx *= DAMP;
    node.vy *= DAMP;
    node.vx = Math.max(-MAXV, Math.min(MAXV, node.vx));
    node.vy = Math.max(-MAXV, Math.min(MAXV, node.vy));
    node.x += node.vx;
    node.y += node.vy;
  }
}

/** Cluster the nodes by domain. */
export function layoutDomain(model: GraphModel, width: number, height: number): void {
  const groups = new Map<string, SimNode[]>();
  for (const node of model.nodes) {
    const list = groups.get(node.domain) ?? [];
    list.push(node);
    groups.set(node.domain, list);
  }
  const keys = [...groups.keys()];
  const centerX = width / 2;
  const centerY = height / 2;
  const ring = Math.min(width, height) * 0.33;
  keys.forEach((key, groupIndex) => {
    const angle = (groupIndex / keys.length) * Math.PI * 2 - Math.PI / 2;
    const groupX = centerX + Math.cos(angle) * ring;
    const groupY = centerY + Math.sin(angle) * ring;
    const list = groups.get(key) ?? [];
    const inner = Math.min(width, height) * 0.13;
    list.forEach((node, index) => {
      if (node.fx !== null) return;
      const nodeAngle = (index / Math.max(1, list.length)) * Math.PI * 2;
      node.x = groupX + Math.cos(nodeAngle) * inner;
      node.y = groupY + Math.sin(nodeAngle) * inner;
      node.vx = 0;
      node.vy = 0;
    });
  });
}

/** Place the nodes on a circle. */
export function layoutRadial(model: GraphModel, width: number, height: number): void {
  const centerX = width / 2;
  const centerY = height / 2;
  const ring = Math.min(width, height) * 0.38;
  const count = model.nodes.length;
  model.nodes.forEach((node, index) => {
    if (node.fx !== null) return;
    const angle = (index / Math.max(1, count)) * Math.PI * 2;
    node.x = centerX + Math.cos(angle) * ring;
    node.y = centerY + Math.sin(angle) * ring;
    node.vx = 0;
    node.vy = 0;
  });
}

/** Lay the mainline out as a column of phase bands. */
export function layoutMainline(model: GraphModel, phases: Phase[], width: number): Band[] {
  const usable = Math.max(CARD, width - RAIL - 40);
  const perRow = Math.max(1, Math.floor(usable / CARD));
  let y = 24;

  const bands: Band[] = [];
  phases.forEach((phase, index) => {
    const produced = model.nodes.filter((node) => node.phase === phase.id && !node.prepared);
    const prepared = model.nodes.filter((node) => node.phase === phase.id && node.prepared);
    const producedRows = produced.length > 0 ? Math.ceil(produced.length / perRow) : 0;
    const preparedRows = prepared.length > 0 ? Math.ceil(prepared.length / perRow) : 0;
    const rows = Math.max(1, producedRows + preparedRows);
    const top = y;
    const height = BAND_TOP + rows * ROW + BAND_PAD;

    const place = (list: SimNode[], offset: number) => {
      list.forEach((node, index) => {
        if (node.fx !== null) return;
        const column = index % perRow;
        const row = offset + Math.floor(index / perRow);
        node.x = RAIL + column * CARD + CARD / 2;
        node.y = top + BAND_TOP + row * ROW + ROW / 2;
        node.vx = 0;
        node.vy = 0;
      });
    };
    place(produced, 0);
    place(prepared, producedRows);

    bands.push({
      phase,
      index,
      top,
      height,
      count: produced.length + prepared.length,
      produced: produced.length,
      prepared: prepared.length,
      splitY: producedRows > 0 ? top + BAND_TOP + producedRows * ROW - 12 : null,
    });
    y = top + height + BAND_GAP;
  });

  model.bands = bands;
  model.size = { width, height: y };

  // Backward edges (feedback loops) get a lane each, so they do not
  // overlap.
  let lane = 0;
  for (const edge of model.edges) {
    if (edge.target.y > edge.source.y + 1) {
      edge.lane = 0;
      continue;
    }
    edge.lane = lane;
    lane += 1;
  }
  return bands;
}

/** The path of an edge in the schema view. */
export function edgeGeometry(edge: SimEdge): { d: string; mx: number; my: number } {
  const source = edge.source;
  const target = edge.target;
  if (source === target) {
    const radius = source.radius + 14;
    return {
      d:
        `M ${source.x - radius * 0.4} ${source.y - radius} ` +
        `C ${source.x - radius * 2.4} ${source.y - radius * 3.2}, ` +
        `${source.x + radius * 2.4} ${source.y - radius * 3.2}, ` +
        `${source.x + radius * 0.4} ${source.y - radius}`,
      mx: source.x,
      my: source.y - radius * 2.1,
    };
  }
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const distance = Math.max(0.01, Math.sqrt(dx * dx + dy * dy));
  const ux = dx / distance;
  const uy = dy / distance;
  const sx = source.x + ux * (source.radius + 1);
  const sy = source.y + uy * (source.radius + 1);
  const tx = target.x - ux * (target.radius + 7);
  const ty = target.y - uy * (target.radius + 7);
  const spread = edge.siblings > 1 ? edge.slot - (edge.siblings - 1) / 2 : 0;
  const curve = Math.min(52, distance * 0.11) * (1 + spread * 0.55);
  const cx = (sx + tx) / 2 - uy * curve;
  const cy = (sy + ty) / 2 + ux * curve;
  return { d: `M ${sx} ${sy} Q ${cx} ${cy} ${tx} ${ty}`, mx: cx, my: cy };
}

/** The path of an edge in the mainline view. */
export function mainlineEdgeGeometry(edge: SimEdge): { d: string; mx: number; my: number } {
  const source = edge.source;
  const target = edge.target;
  if (target.y > source.y + 1) {
    // Forward: from top to bottom, through the phase bands.
    const sx = source.x;
    const sy = source.y + source.radius + 2;
    const tx = target.x;
    const ty = target.y - target.radius - 9;
    const midY = (sy + ty) / 2;
    return {
      d: `M ${sx} ${sy} C ${sx} ${midY}, ${tx} ${midY}, ${tx} ${ty}`,
      mx: (sx + tx) / 2,
      my: midY,
    };
  }
  // Backward (feedback): around the right hand side.
  const lane = Math.max(source.x, target.x) + 70 + edge.lane * 26;
  const bsx = source.x + source.radius;
  const bsy = source.y;
  const btx = target.x + target.radius;
  const bty = target.y;
  return {
    d: `M ${bsx} ${bsy} C ${lane} ${bsy}, ${lane} ${bty}, ${btx} ${bty}`,
    mx: lane,
    my: (bsy + bty) / 2,
  };
}
