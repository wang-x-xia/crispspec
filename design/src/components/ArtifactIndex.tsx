import { useMemo, useState } from 'react';

import { artifacts, domains, phaseById } from '../data';

/** The index of every artifact type. */
export function ArtifactIndex({ query }: { query: string }) {
  const [domain, setDomain] = useState<string>('all');

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return artifacts.filter((artifact) => {
      if (domain !== 'all' && artifact.domain !== domain) return false;
      if (!needle) return true;
      return (
        artifact.name.toLowerCase().includes(needle) ||
        artifact.id.toLowerCase().includes(needle) ||
        artifact.prefix.toLowerCase().includes(needle) ||
        artifact.purpose.toLowerCase().includes(needle) ||
        artifact.domainLabel.toLowerCase().includes(needle)
      );
    });
  }, [domain, query]);

  const grouped = useMemo(() => {
    const groups = new Map<string, typeof artifacts>();
    for (const artifact of filtered) {
      const list = groups.get(artifact.domain) ?? [];
      list.push(artifact);
      groups.set(artifact.domain, list);
    }
    return [...groups.entries()];
  }, [filtered]);

  return (
    <div className="page">
      <section className="section">
        <div className="page-head">
          <div>
            <h1>制品清单</h1>
            <p className="muted">
              {filtered.length} / {artifacts.length} 种制品。点开任意一种，看它的字段、枚举、关系与完整定义。
            </p>
          </div>
          <div className="filter-chips">
            <button
              type="button"
              className={`chip${domain === 'all' ? ' active' : ''}`}
              onClick={() => setDomain('all')}
            >
              全部
            </button>
            {domains.map((item) => (
              <button
                key={item.key}
                type="button"
                className={`chip${domain === item.key ? ' active' : ''}`}
                onClick={() => setDomain(item.key)}
              >
                <span className="swatch" style={{ background: item.color }} />
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {grouped.map(([key, list]) => {
          const info = domains.find((item) => item.key === key);
          return (
            <section key={key} className="artifact-group">
              <h2>
                <span className="swatch" style={{ background: info?.color }} />
                {info?.label ?? key}
                <span className="count">{list.length}</span>
              </h2>
              <div className="card-grid">
                {list.map((artifact) => {
                  const phase = artifact.phase ? phaseById.get(artifact.phase) : undefined;
                  return (
                    <a key={artifact.id} className="artifact-card" href={`#/artifact/${artifact.id}`}>
                      <div className="card-head">
                        <h3>{artifact.name}</h3>
                        <span className="mono prefix">{artifact.prefix}</span>
                      </div>
                      <p>{artifact.purpose}</p>
                      <div className="card-foot">
                        <span>{artifact.fields.length} 字段</span>
                        <span>{artifact.outgoing.length + artifact.incoming.length} 关系</span>
                        {phase && <span>{phase.label}</span>}
                      </div>
                    </a>
                  );
                })}
              </div>
            </section>
          );
        })}
      </section>
    </div>
  );
}
