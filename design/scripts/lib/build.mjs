/**
 * Compile the design content into the JSON the frontend consumes.
 *
 * Sources of truth:
 *   data/artifacts.yaml   the artifact registry (types, domains, mainline)
 *   content/<domain>/<artifact>.md   the artifact definition documents
 *
 * Everything the frontend shows — the graph, the mainline, the field
 * tables, the documents — is derived from those two sources.  There is
 * no second, hand-maintained copy of anything.
 */

import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import YAML from 'yaml';

import {
  FIELD_HEADING,
  RELATION_HEADING,
  STRUCT_HEADING,
  direction,
  parseEnum,
  parseFields,
  parseGoal,
  parseMappings,
  parseStructs,
  relationNames,
  relationRows,
  section,
  tables,
} from './parse.mjs';
import {
  createLinkResolver,
  documentHeadings,
  documentTitle,
  extractMermaid,
  renderMarkdown,
  toPosix,
} from './render.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));

/** The root of the design project. */
export const PROJECT_ROOT = resolve(HERE, '..', '..');
/** The directory holding the design documents. */
export const CONTENT_ROOT = join(PROJECT_ROOT, 'content');
/** The artifact registry. */
export const REGISTRY_FILE = join(PROJECT_ROOT, 'data', 'artifacts.yaml');
/** The JSON the frontend consumes. */
export const OUTPUT_FILE = join(PROJECT_ROOT, 'src', 'generated', 'content.json');

/** Colours of the domains, in the order the domains are declared. */
const DOMAIN_COLORS = [
  '#4f9dff', // requirement
  '#22c55e', // contract
  '#f59e0b', // behavior
  '#a855f7', // code
  '#ef4444', // incident
  '#06b6d4', // governance
  '#f97316', // access
  '#ec4899', // delivery
  '#84cc16', // verification
  '#eab308', // organization
  '#64748b', // meta
];


/** Collect every markdown file below `directory`. */
function collectDocs(directory, base = CONTENT_ROOT) {
  const docs = [];
  const entries = readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name));
  for (const entry of entries) {
    const full = join(directory, entry.name);
    if (entry.isDirectory()) {
      docs.push(...collectDocs(full, base));
    } else if (entry.name.endsWith('.md')) {
      const file = toPosix(relative(base, full));
      docs.push({ id: file.replace(/\.md$/, ''), file, path: full });
    }
  }
  return docs;
}

/** Resolve the targets of a relation row to artifact type keys. */
function resolveTargets(cell, doc, definitionMap, domains, typesInDomain) {
  const targets = [];

  for (const match of cell.matchAll(/\[([^\]]*)\]\(([^)]+)\)/g)) {
    const link = match[2];
    if (/^(https?:|#)/.test(link)) continue;
    const absolute = resolve(dirname(doc.path), link.split('#')[0]);
    if (!absolute.startsWith(CONTENT_ROOT + sep)) continue;
    const relativePath = toPosix(relative(CONTENT_ROOT, absolute));
    const type = definitionMap.get(relativePath);
    if (type && !targets.includes(type)) targets.push(type);
  }

  if (targets.length > 0) return targets;

  const plain = cell.replace(/\[([^\]]*)\]\(([^)]+)\)/g, '$1');
  if (['任意', '全部'].some((marker) => plain.includes(marker))) return [];

  for (const domain of domains) {
    const mentioned =
      plain.includes(domain.label) || new RegExp(`\\b${domain.key}\\b`).test(plain);
    if (!mentioned) continue;
    for (const type of typesInDomain(domain.key)) {
      if (!targets.includes(type)) targets.push(type);
    }
  }
  return targets;
}

/** Build the payload and report every inconsistency found on the way. */
export function buildContent() {
  const problems = [];
  const warnings = [];
  const fail = (message) => problems.push(message);
  const warn = (message) => warnings.push(message);

  const registry = YAML.parse(readFileSync(REGISTRY_FILE, 'utf8'));
  const domains = Object.entries(registry.domains ?? {}).map(([key, value], index) => ({
    key,
    label: value.label ?? key,
    question: value.question ?? '',
    color: DOMAIN_COLORS[index % DOMAIN_COLORS.length],
  }));

  const docs = collectDocs(CONTENT_ROOT);
  const docsById = new Map(docs.map((doc) => [doc.id, doc]));
  for (const doc of docs) {
    doc.text = readFileSync(doc.path, 'utf8');
    doc.title = documentTitle(doc.text);
    doc.headings = documentHeadings(doc.text);
    doc.group = doc.id.includes('/') ? doc.id.split('/')[0] : 'overview';
  }

  const registryArtifacts = registry.artifacts ?? [];
  const definitionMap = new Map();
  for (const entry of registryArtifacts) {
    definitionMap.set(toPosix(entry.definition), entry.type);
  }

  const typesInDomain = (key) =>
    registryArtifacts.filter((entry) => entry.domain === key).map((entry) => entry.type);

  const domainByKey = new Map(domains.map((domain) => [domain.key, domain]));

  // ── Artifacts ────────────────────────────────────────────────────────
  const artifacts = registryArtifacts.map((entry) => {
    const docId = toPosix(entry.definition).replace(/\.md$/, '');
    const doc = docsById.get(docId);
    if (!doc) {
      fail(`制品 ${entry.type} 的定义文档不存在：${entry.definition}`);
      return null;
    }

    const details = tables(section(doc.text, FIELD_HEADING));
    let fields = [];
    const enums = [];
    for (const { heading, rows } of details) {
      if (rows.length === 0) continue;
      if (fields.length === 0 && rows[0].length >= 4) {
        fields = parseFields(rows);
        continue;
      }
      const parsed = parseEnum(heading, rows);
      if (parsed) enums.push(parsed);
    }
    if (fields.length === 0) {
      warn(`制品 ${entry.type} 没有解析出字段表（${entry.definition}）`);
    }

    const structs = parseStructs(section(doc.text, STRUCT_HEADING));
    const mappings = entry.type === 'business-concept' ? parseMappings(doc.text) : [];

    if (!entry.purpose) {
      fail(`制品 ${entry.type} 缺少 purpose（用途）`);
    }

    const artifact = {
      id: entry.type,
      name: entry.name,
      prefix: entry.id_prefix,
      idPattern: entry.id_pattern ?? `${entry.id_prefix}-\\d+`,
      domain: entry.domain,
      domainLabel: domainByKey.get(entry.domain)?.label ?? entry.domain,
      definition: docId,
      definitionFile: toPosix(entry.definition),
      purpose: entry.purpose ?? '',
      notes: (entry.notes ?? '').trim(),
      goal: parseGoal(doc.text),
      fields,
      enums,
      structs,
      mappings,
      mappingTargets: entry.mapping_targets ?? [],
      outgoing: [],
      incoming: [],
      phase: null,
      prepared: false,
      lateral: false,
    };
    return artifact;
  });

  const artifactById = new Map(artifacts.filter(Boolean).map((artifact) => [artifact.id, artifact]));

  // ── Edges ────────────────────────────────────────────────────────────
  const edges = [];
  const edgeIndex = new Map();

  function addEdge(source, target, relation, kind, origin) {
    const key = `${source}|${target}|${relation}`;
    const existing = edgeIndex.get(key);
    if (existing) {
      if (kind === 'both') existing.bidirectional = true;
      return;
    }
    const edge = { source, target, relation, bidirectional: kind === 'both', mainline: false, origin };
    edgeIndex.set(key, edge);
    edges.push(edge);
  }

  for (const artifact of artifacts.filter(Boolean)) {
    const doc = docsById.get(artifact.definition);
    for (const row of relationRows(section(doc.text, RELATION_HEADING))) {
      const names = relationNames(row.relation);
      const kind = direction(row.direction);
      const targets = resolveTargets(row.target, doc, definitionMap, domains, typesInDomain);
      if (names.length === 0 || targets.length === 0) continue;
      for (const name of names) {
        for (const target of targets) {
          if (kind === 'in') addEdge(target, artifact.id, name, kind, doc.id);
          else addEdge(artifact.id, target, name, kind, doc.id);
        }
      }
    }
  }

  // The business concept is mapped onto the artifacts that realise it.
  for (const artifact of artifacts.filter(Boolean)) {
    for (const target of artifact.mappingTargets) {
      if (!artifactById.has(target)) {
        fail(`制品 ${artifact.id} 的映射目标 ${target} 不是已知制品类型`);
        continue;
      }
      addEdge(artifact.id, target, 'AS', 'out', artifact.definition);
    }
  }

  // The registry and the definition document must agree on the mapping.
  for (const artifact of artifacts.filter(Boolean)) {
    if (artifact.mappingTargets.length === 0) continue;
    const declared = edges
      .filter((edge) => edge.source === artifact.id && edge.relation === 'AS')
      .map((edge) => edge.target)
      .sort();
    const registered = [...artifact.mappingTargets].sort();
    if (declared.join(',') !== registered.join(',')) {
      fail(
        `制品 ${artifact.id} 的映射目标在登记表与定义文档之间不一致：` +
          `登记表 [${registered.join(', ')}]，文档 [${declared.join(', ')}]`,
      );
    }
  }

  // One relation name per pair of artifacts.
  //
  // Two edges between the same pair are only allowed when one of them
  // is `CONTAINS` — that is "this artifact belongs to that module" plus
  // a behavioural relation.  Anything else means the same fact was
  // given two names, which makes the graph unreadable.
  const pairs = new Map();
  for (const edge of edges) {
    const key = [edge.source, edge.target].sort().join('|');
    const relations = pairs.get(key) ?? new Set();
    relations.add(edge.relation);
    pairs.set(key, relations);
  }
  for (const [key, relations] of pairs) {
    if (relations.size <= 1) continue;
    if (relations.has('CONTAINS')) continue;
    const [source, target] = key.split('|');
    fail(
      `制品 ${source} 与 ${target} 之间有多个关系名 [${[...relations].join(', ')}]——` +
        '同一事实只能有一个关系名（归属用 CONTAINS 除外）',
    );
  }

  // ── Mainline ─────────────────────────────────────────────────────────
  const phases = (registry.mainline ?? []).map((phase) => ({
    id: phase.id,
    label: phase.label,
    question: phase.question ?? '',
    produces: [...(phase.produces ?? [])],
    prepares: [...(phase.prepares ?? [])],
    artifacts: [...(phase.produces ?? []), ...(phase.prepares ?? [])],
    lateral: Boolean(phase.lateral),
    handoff: (phase.handoff ?? []).map((handoff) => ({
      relation: handoff.relation,
      source: handoff.from,
      target: handoff.to,
    })),
  }));

  const placement = new Map();
  for (const phase of phases) {
    for (const id of phase.artifacts) {
      if (placement.has(id)) {
        fail(`制品 ${id} 同时出现在多个主线阶段：${placement.get(id)} 与 ${phase.id}`);
        continue;
      }
      placement.set(id, phase.id);
      const artifact = artifactById.get(id);
      if (!artifact) {
        fail(`主线阶段 ${phase.id} 引用了未知制品 ${id}`);
        continue;
      }
      artifact.phase = phase.id;
      artifact.prepared = phase.prepares.includes(id);
      artifact.lateral = phase.lateral;
    }
    if (phase.lateral && phase.produces.length > 0) {
      fail(`横切阶段 ${phase.id} 不允许产出制品`);
    }
  }
  for (const artifact of artifacts.filter(Boolean)) {
    if (!placement.has(artifact.id)) {
      fail(`制品 ${artifact.id} 没有出现在任何主线阶段`);
    }
  }

  for (const phase of phases) {
    for (const handoff of phase.handoff) {
      const key = `${handoff.source}|${handoff.target}|${handoff.relation}`;
      if (!edgeIndex.has(key)) {
        fail(`主线交接 ${phase.id}：${handoff.source} -[${handoff.relation}]-> ${handoff.target} 不是真实存在的关系边`);
        continue;
      }
      edgeIndex.get(key).mainline = true;
    }
  }

  // ── Relations of every artifact ──────────────────────────────────────
  for (const edge of edges) {
    const source = artifactById.get(edge.source);
    const target = artifactById.get(edge.target);
    if (!source || !target) continue;
    source.outgoing.push({ relation: edge.relation, target: edge.target, origin: edge.origin });
    target.incoming.push({ relation: edge.relation, source: edge.source, origin: edge.origin });
  }

  // ── Documents ────────────────────────────────────────────────────────
  const rendered = [];
  for (const doc of docs) {
    const { markdown, diagrams } = extractMermaid(doc.text);
    const resolveLink = createLinkResolver({
      docId: doc.id,
      docs: new Set(docsById.keys()),
      contentRoot: CONTENT_ROOT,
      designRoot: PROJECT_ROOT,
    });
    const html = renderMarkdown(markdown, resolveLink);
    checkLinks(doc, html, problems);
    rendered.push({
      id: doc.id,
      title: doc.title,
      group: doc.group,
      file: doc.file,
      html,
      headings: doc.headings,
      mermaid: diagrams,
    });
  }

  const relationTypes = [...new Set(edges.map((edge) => edge.relation))]
    .map((name) => ({ name, count: edges.filter((edge) => edge.relation === name).length }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));

  return {
    payload: {
      meta: {
        ...(registry.meta ?? {}),
        generatedAt: new Date().toISOString(),
      },
      domains,
      phases,
      artifacts: artifacts.filter(Boolean),
      edges,
      relationTypes,
      docs: rendered,
      stats: {
        artifacts: artifacts.filter(Boolean).length,
        edges: edges.length,
        relations: relationTypes.length,
        domains: domains.length,
        phases: phases.length,
        lateralPhases: phases.filter((phase) => phase.lateral).length,
        handoffs: phases.reduce((total, phase) => total + phase.handoff.length, 0),
        docs: rendered.length,
        fields: artifacts.filter(Boolean).reduce((total, artifact) => total + artifact.fields.length, 0),
      },
    },
    problems,
    warnings,
  };
}

/** Report links that point nowhere. */
function checkLinks(doc, html, problems) {
  for (const match of html.matchAll(/<span class="link-dead" title="([^"]*)"/g)) {
    problems.push(`${doc.file}：链接失效——${match[1]}`);
  }
}
