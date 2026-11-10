import raw from './generated/content.json';
import type { Artifact, ContentData, Doc, Domain, Phase } from './types';

/** The compiled content — the single source the UI renders from. */
export const content = raw as unknown as ContentData;

export const artifacts: Artifact[] = content.artifacts;
export const edges = content.edges;
export const relationTypes = content.relationTypes;
export const domains: Domain[] = content.domains;
export const phases: Phase[] = content.phases;
export const docs: Doc[] = content.docs;

export const artifactById = new Map(artifacts.map((artifact) => [artifact.id, artifact]));
export const domainByKey = new Map(domains.map((domain) => [domain.key, domain]));
export const phaseById = new Map(phases.map((phase) => [phase.id, phase]));
export const docById = new Map(docs.map((doc) => [doc.id, doc]));

/** The colour of a domain. */
export function domainColor(domainKey: string): string {
  return domainByKey.get(domainKey)?.color ?? '#64748b';
}

/** The documents that are not artifact definitions, grouped for the index. */
export function isArtifactDoc(doc: Doc): boolean {
  return artifacts.some((artifact) => artifact.definition === doc.id);
}

/** Domain of a document — the folder it lives in. */
export function docGroupLabel(group: string): string {
  const labels: Record<string, string> = {
    overview: '总览',
    requirement: '需求域',
    contract: '契约域',
    behavior: '行为域',
    code: '代码域',
    module: '组织单元',
    governance: '治理域',
    access: '访问控制域',
    delivery: '交付域',
    incident: '故障域',
    test: '验证域',
    schema: '元制品',
    archive: '归档',
  };
  return labels[group] ?? group;
}
