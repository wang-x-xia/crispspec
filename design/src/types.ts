/**
 * The shape of the compiled content.
 *
 * `scripts/build-content.mjs` writes this JSON from `data/artifacts.yaml`
 * and the documents below `content/`.  Nothing here is written by hand.
 */

export interface Domain {
  key: string;
  label: string;
  question: string;
  color: string;
}

export interface Field {
  name: string;
  type: string;
  constraint: string;
  description: string;
}

export interface EnumValue {
  value: string;
  meaning: string;
}

export interface EnumTable {
  name: string;
  values: EnumValue[];
}

export interface StructTable {
  name: string;
  columns: string[];
  rows: string[][];
}

export interface Mapping {
  artifactType: string;
  artifactId: string;
}

export interface OutgoingRelation {
  relation: string;
  target: string;
  origin: string;
}

export interface IncomingRelation {
  relation: string;
  source: string;
  origin: string;
}

export interface Artifact {
  id: string;
  name: string;
  prefix: string;
  idPattern: string;
  domain: string;
  domainLabel: string;
  definition: string;
  definitionFile: string;
  purpose: string;
  notes: string;
  goal: string;
  fields: Field[];
  enums: EnumTable[];
  structs: StructTable[];
  mappings: Mapping[];
  mappingTargets: string[];
  outgoing: OutgoingRelation[];
  incoming: IncomingRelation[];
  phase: string | null;
  prepared: boolean;
  lateral: boolean;
}

export interface Edge {
  source: string;
  target: string;
  relation: string;
  bidirectional: boolean;
  mainline: boolean;
  origin: string;
}

export interface Handoff {
  relation: string;
  source: string;
  target: string;
}

export interface Phase {
  id: string;
  label: string;
  question: string;
  produces: string[];
  prepares: string[];
  artifacts: string[];
  lateral: boolean;
  handoff: Handoff[];
}

export interface RelationType {
  name: string;
  count: number;
}

export interface DocHeading {
  level: number;
  text: string;
  slug: string;
}

export interface MermaidDiagram {
  id: string;
  code: string;
}

export interface Doc {
  id: string;
  title: string;
  group: string;
  file: string;
  html: string;
  headings: DocHeading[];
  mermaid: MermaidDiagram[];
}

export interface ContentStats {
  artifacts: number;
  edges: number;
  relations: number;
  domains: number;
  phases: number;
  lateralPhases: number;
  handoffs: number;
  docs: number;
  fields: number;
}

export interface ContentData {
  meta: Record<string, unknown> & { updated?: string; phase?: string };
  domains: Domain[];
  phases: Phase[];
  artifacts: Artifact[];
  edges: Edge[];
  relationTypes: RelationType[];
  docs: Doc[];
  stats: ContentStats;
}
