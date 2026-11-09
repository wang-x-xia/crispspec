import { useMemo } from 'react';

import { docById, docGroupLabel } from '../data';
import { useAnchor } from '../router';
import { Markdown } from './Markdown';

/** One document, rendered. */
export function DocPage({ id, anchor }: { id: string; anchor?: string }) {
  const doc = docById.get(id);
  useAnchor(anchor);

  const outline = useMemo(
    () => (doc ? doc.headings.filter((heading) => heading.level >= 2 && heading.level <= 3) : []),
    [doc],
  );

  if (!doc) {
    return (
      <div className="page">
        <section className="section">
          <h1>找不到这篇文档</h1>
          <p className="muted">
            没有 id 为 <code>{id}</code> 的文档。<a href="#/docs">回到文档索引</a>。
          </p>
        </section>
      </div>
    );
  }

  return (
    <div className="page doc-page">
      <nav className="crumbs">
        <a href="#/">概览</a>
        <span>/</span>
        <a href="#/docs">文档</a>
        <span>/</span>
        <span>{docGroupLabel(doc.group)}</span>
      </nav>

      <div className="doc-layout">
        <article className="doc-main">
          <Markdown html={doc.html} diagrams={doc.mermaid} />
        </article>
        {outline.length > 0 && (
          <aside className="outline">
            <h2>目录</h2>
            <ul>
              {outline.map((heading) => (
                <li key={heading.slug} className={`level-${heading.level}`}>
                  <a href={`#/doc/${doc.id}#${heading.slug}`}>{heading.text}</a>
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>
    </div>
  );
}
