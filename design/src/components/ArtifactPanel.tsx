import { artifactById, domainColor, phaseById } from '../data';
import type { Artifact, Phase } from '../types';

/** The detail panel of the graph views. */
export function ArtifactPanel({
  artifact,
  onSelect,
}: {
  artifact: Artifact | null;
  onSelect: (id: string) => void;
}) {
  if (!artifact) {
    return (
      <div className="empty">
        点击图中的节点
        <br />
        查看制品定义与关系
      </div>
    );
  }

  const phase = artifact.phase ? phaseById.get(artifact.phase) : undefined;

  return (
    <div className="panel-body">
      <h3>{artifact.name}</h3>
      <div className="sub">
        {artifact.prefix} · {artifact.idPattern}
      </div>

      <div className="badge-row">
        <span className="badge">
          <span className="swatch" style={{ background: domainColor(artifact.domain) }} />
          {artifact.domainLabel}
        </span>
        {phase && (
          <span className="badge">
            {phase.label}
            {artifact.prepared ? ' · 可提前准备' : ''}
          </span>
        )}
        {artifact.lateral && <span className="badge">横切</span>}
      </div>

      {artifact.purpose && <p className="note">{artifact.purpose}</p>}
      {artifact.notes && <p className="note">{artifact.notes}</p>}

      {artifact.fields.length > 0 && (
        <>
          <h4>字段 ({artifact.fields.length})</h4>
          <table className="fields">
            <thead>
              <tr>
                <th>字段</th>
                <th>类型</th>
                <th>约束</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              {artifact.fields.map((field) => (
                <tr key={field.name}>
                  <td className="name">{field.name}</td>
                  <td className="type">{field.type}</td>
                  <td className="constraint">{field.constraint}</td>
                  <td>{field.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {artifact.enums.map((enumTable) => (
        <div key={enumTable.name}>
          <h4>{enumTable.name}</h4>
          <ul className="rel-list">
            {enumTable.values.map((entry) => (
              <li key={entry.value}>
                <div className="rel-link">
                  <span className="rel">{entry.value}</span>
                  <span className="tgt">{entry.meaning}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}

      {artifact.mappings.length > 0 && (
        <>
          <h4>映射到内部制品（as）</h4>
          <ul className="rel-list">
            {artifact.mappings.map((mapping) => (
              <li key={`${mapping.artifactType}-${mapping.artifactId}`}>
                <div className="rel-link">
                  <span className="rel">{mapping.artifactType}</span>
                  <span className="tgt">{mapping.artifactId}</span>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      {artifact.outgoing.length > 0 && (
        <>
          <h4>出向关系 ({artifact.outgoing.length})</h4>
          <RelationList
            relations={artifact.outgoing.map((relation) => ({
              relation: relation.relation,
              other: relation.target,
              direction: 'out',
            }))}
            onSelect={onSelect}
          />
        </>
      )}

      {artifact.incoming.length > 0 && (
        <>
          <h4>入向关系 ({artifact.incoming.length})</h4>
          <RelationList
            relations={artifact.incoming.map((relation) => ({
              relation: relation.relation,
              other: relation.source,
              direction: 'in',
            }))}
            onSelect={onSelect}
          />
        </>
      )}

      <h4>定义文档</h4>
      <p className="note">
        <a href={`#/artifact/${artifact.id}`}>打开完整定义 →</a>
      </p>
    </div>
  );
}

/** The detail panel of the mainline view. */
export function PhasePanel({
  phase,
  onSelect,
}: {
  phase: Phase | null;
  onSelect: (id: string) => void;
}) {
  if (!phase) {
    return (
      <div className="empty">
        点击阶段带
        <br />
        查看该阶段的制品与交接
      </div>
    );
  }

  return (
    <div className="panel-body">
      <h3>{phase.label}</h3>
      <div className="sub">{phase.question}</div>

      <div className="badge-row">
        {phase.lateral && <span className="badge">横切关注点</span>}
        <span className="badge">{phase.produces.length} 产出</span>
        <span className="badge">{phase.prepares.length} 可提前准备</span>
        <span className="badge">{phase.handoff.length} 次交接</span>
      </div>

      <ArtifactList title="本阶段产出" ids={phase.produces} onSelect={onSelect} />
      <ArtifactList title="可提前准备（不由本阶段产出）" ids={phase.prepares} onSelect={onSelect} />

      {phase.handoff.length > 0 && (
        <>
          <h4>交接</h4>
          <ul className="rel-list">
            {phase.handoff.map((handoff) => {
              const source = artifactById.get(handoff.source);
              const target = artifactById.get(handoff.target);
              if (!source || !target) return null;
              return (
                <li key={`${handoff.source}-${handoff.relation}-${handoff.target}`}>
                  <button type="button" className="rel-link" onClick={() => onSelect(handoff.target)}>
                    <span className="rel">{handoff.relation}</span>
                    <span className="tgt">
                      {source.name} → {target.name}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}

function ArtifactList({
  title,
  ids,
  onSelect,
}: {
  title: string;
  ids: string[];
  onSelect: (id: string) => void;
}) {
  if (ids.length === 0) return null;
  return (
    <>
      <h4>{title}</h4>
      <ul className="rel-list">
        {ids.map((id) => {
          const artifact = artifactById.get(id);
          if (!artifact) return null;
          return (
            <li key={id}>
              <button type="button" className="rel-link" onClick={() => onSelect(id)}>
                <span className="rel">{artifact.prefix}</span>
                <span className="tgt">{artifact.name}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </>
  );
}

function RelationList({
  relations,
  onSelect,
}: {
  relations: { relation: string; other: string; direction: 'out' | 'in' }[];
  onSelect: (id: string) => void;
}) {
  return (
    <ul className="rel-list">
      {relations.map((relation) => {
        const other = artifactById.get(relation.other);
        if (!other) return null;
        return (
          <li key={`${relation.relation}-${relation.other}`}>
            <button type="button" className="rel-link" onClick={() => onSelect(relation.other)}>
              <span className="rel">{relation.relation}</span>
              <span className="tgt">{other.name}</span>
              <span className="dir">{relation.direction === 'out' ? '→' : '←'}</span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

