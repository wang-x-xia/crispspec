import { useMemo } from 'react';

import { docs, docGroupLabel, isArtifactDoc } from '../data';

/** The index of every design document. */
export function DocsIndex({ query }: { query: string }) {
  const groups = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = docs.filter((doc) => {
      if (!needle) return true;
      return (
        doc.title.toLowerCase().includes(needle) ||
        doc.id.toLowerCase().includes(needle) ||
        doc.file.toLowerCase().includes(needle)
      );
    });
    const map = new Map<string, typeof docs>();
    for (const doc of filtered) {
      const list = map.get(doc.group) ?? [];
      list.push(doc);
      map.set(doc.group, list);
    }
    return [...map.entries()];
  }, [query]);

  return (
    <div className="page">
      <section className="section">
        <h1>设计文档</h1>
        <p className="muted">
          全部设计文档都在这里——愿景、体系概览、逐个制品的定义、访问控制子系统、自然语言结构化……
        </p>
        {groups.map(([group, list]) => (
          <div key={group} className="doc-group">
            <h2>
              {docGroupLabel(group)}
              <span className="count">{list.length}</span>
            </h2>
            <ul className="doc-list">
              {list.map((doc) => (
                <li key={doc.id}>
                  <a href={`#/doc/${doc.id}`}>{doc.title || doc.id}</a>
                  <span className="muted small">{doc.file}</span>
                  {isArtifactDoc(doc) && <span className="chip">制品定义</span>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>
    </div>
  );
}
