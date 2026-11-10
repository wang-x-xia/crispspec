import { artifactById, content, docById, phaseById } from '../data';
import { Markdown } from './Markdown';

/** The full page of one artifact type. */
export function ArtifactPage({ type }: { type: string }) {
  const artifact = artifactById.get(type);

  if (!artifact) {
    return (
      <div className="page">
        <section className="section">
          <h1>找不到这种制品</h1>
          <p className="muted">
            没有类型键为 <code>{type}</code> 的制品。<a href="#/artifacts">回到制品清单</a>。
          </p>
        </section>
      </div>
    );
  }

  const doc = docById.get(artifact.definition);
  const phase = artifact.phase ? phaseById.get(artifact.phase) : undefined;
  const domain = content.domains.find((item) => item.key === artifact.domain);

  return (
    <div className="page">
      <nav className="crumbs">
        <a href="#/">概览</a>
        <span>/</span>
        <a href="#/artifacts">制品</a>
        <span>/</span>
        <span>{artifact.name}</span>
      </nav>

      <header className="artifact-head">
        <div>
          <h1>
            {artifact.name}
            <span className="mono prefix">{artifact.prefix}</span>
          </h1>
          <p className="lead">{artifact.purpose}</p>
          <div className="badge-row">
            <span className="badge">
              <span className="swatch" style={{ background: domain?.color }} />
              {artifact.domainLabel}
            </span>
            <span className="badge mono">{artifact.idPattern}</span>
            {phase && (
              <span className="badge">
                {phase.label}
                {artifact.prepared ? ' · 可提前准备' : ''}
              </span>
            )}
            {artifact.lateral && <span className="badge">横切</span>}
            <a className="badge link" href={`#/doc/${artifact.definition}`}>
              定义文档
            </a>
          </div>
        </div>
      </header>

      {artifact.goal && <p className="goal">{artifact.goal}</p>}
      {artifact.notes && <p className="muted">{artifact.notes}</p>}

      {artifact.fields.length > 0 && (
        <section className="section">
          <h2>字段定义</h2>
          <table className="grid">
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
                  <td className="mono name">{field.name}</td>
                  <td className="mono">{field.type}</td>
                  <td className="mono constraint">{field.constraint}</td>
                  <td>{field.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {artifact.enums.length > 0 && (
        <section className="section">
          <h2>枚举</h2>
          <div className="enum-grid">
            {artifact.enums.map((enumTable) => (
              <article key={enumTable.name} className="enum-card">
                <h3>{enumTable.name}</h3>
                <table className="grid compact">
                  <tbody>
                    {enumTable.values.map((entry) => (
                      <tr key={entry.value}>
                        <td className="mono name">{entry.value}</td>
                        <td>{entry.meaning}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </article>
            ))}
          </div>
        </section>
      )}

      {artifact.structs.length > 0 && (
        <section className="section">
          <h2>子结构</h2>
          {artifact.structs.map((struct) => (
            <article key={struct.name} className="enum-card">
              <h3>{struct.name}</h3>
              <table className="grid compact">
                <thead>
                  <tr>
                    {struct.columns.map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {struct.rows.map((row, index) => (
                    <tr key={`${struct.name}-${index}`}>
                      {row.map((cell, cellIndex) => (
                        <td key={`${index}-${cellIndex}`} className={cellIndex === 0 ? 'mono name' : undefined}>
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </article>
          ))}
        </section>
      )}

      {(artifact.outgoing.length > 0 || artifact.incoming.length > 0) && (
        <section className="section">
          <h2>关系</h2>
          <div className="relation-columns">
            <RelationColumn
              title={`出向关系 (${artifact.outgoing.length})`}
              relations={artifact.outgoing.map((relation) => ({ relation: relation.relation, id: relation.target }))}
            />
            <RelationColumn
              title={`入向关系 (${artifact.incoming.length})`}
              relations={artifact.incoming.map((relation) => ({ relation: relation.relation, id: relation.source }))}
            />
          </div>
        </section>
      )}

      {doc && (
        <section className="section">
          <h2>完整定义</h2>
          <Markdown html={doc.html} diagrams={doc.mermaid} />
        </section>
      )}
    </div>
  );
}

function RelationColumn({
  title,
  relations,
}: {
  title: string;
  relations: { relation: string; id: string }[];
}) {
  if (relations.length === 0) return null;
  return (
    <div>
      <h3>{title}</h3>
      <ul className="rel-list">
        {relations.map((relation) => {
          const other = artifactById.get(relation.id);
          if (!other) return null;
          return (
            <li key={`${relation.relation}-${relation.id}`}>
              <a className="rel-link" href={`#/artifact/${other.id}`}>
                <span className="rel">{relation.relation}</span>
                <span className="tgt">{other.name}</span>
              </a>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
