import { useMemo, useState } from 'react';

import { artifacts, content, domains, edges, phases, relationTypes } from '../data';
import { buildGraph } from '../graph/layout';
import { ArtifactPanel } from './ArtifactPanel';
import { GraphCanvas, type LayoutMode } from './GraphCanvas';

/** The schema view: every artifact type and every relation between them. */
export function GraphView({ query }: { query: string }) {
  const model = useMemo(() => buildGraph(artifacts, edges, phases, 'schema'), []);

  const [layout, setLayout] = useState<LayoutMode>('force');
  const [showLabels, setShowLabels] = useState(true);
  const [dimMode, setDimMode] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [visibleDomains, setVisibleDomains] = useState(() => new Set(domains.map((domain) => domain.key)));
  const [visibleRelations, setVisibleRelations] = useState(
    () => new Set(relationTypes.map((relation) => relation.name)),
  );

  const relationUsage = useMemo(() => {
    const usage = new Map<string, number>();
    for (const edge of content.edges) {
      usage.set(edge.relation, (usage.get(edge.relation) ?? 0) + 1);
    }
    return usage;
  }, []);

  const selected = selectedId ? (artifacts.find((artifact) => artifact.id === selectedId) ?? null) : null;

  const toggleDomain = (key: string) => {
    setVisibleDomains((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleRelation = (name: string) => {
    setVisibleRelations((current) => {
      const next = new Set(current);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const reset = () => {
    setVisibleDomains(new Set(domains.map((domain) => domain.key)));
    setVisibleRelations(new Set(relationTypes.map((relation) => relation.name)));
    setSelectedId(null);
  };

  const visibleNodes = model.nodes.filter((node) => visibleDomains.has(node.domain)).length;
  const visibleEdges = model.edges.filter(
    (edge) =>
      visibleRelations.has(edge.relation) &&
      visibleDomains.has(edge.source.domain) &&
      visibleDomains.has(edge.target.domain),
  ).length;

  return (
    <div className="workspace">
      <aside className="sidebar">
        <section className="panel">
          <h2>
            域 <span className="count">{visibleDomains.size} / {domains.length}</span>
          </h2>
          <ul className="filter-list">
            {domains.map((domain) => {
              const count = model.nodes.filter((node) => node.domain === domain.key).length;
              if (count === 0) return null;
              const on = visibleDomains.has(domain.key);
              return (
                <li key={domain.key}>
                  <label className={`filter-row${on ? '' : ' off'}`}>
                    <input type="checkbox" checked={on} onChange={() => toggleDomain(domain.key)} />
                    <span className="swatch" style={{ background: domain.color }} />
                    <span className="label">{domain.label}</span>
                    <span className="num">{count}</span>
                  </label>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="panel">
          <h2>
            关系类型 <span className="count">{visibleRelations.size} / {relationTypes.length}</span>
          </h2>
          <ul className="filter-list">
            {relationTypes.map((relation) => {
              const on = visibleRelations.has(relation.name);
              return (
                <li key={relation.name}>
                  <label className={`filter-row${on ? '' : ' off'}`}>
                    <input type="checkbox" checked={on} onChange={() => toggleRelation(relation.name)} />
                    <span className="label">{relation.name}</span>
                    <span className="num">{relationUsage.get(relation.name) ?? relation.count}</span>
                  </label>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="panel">
          <h2>布局</h2>
          <div className="control">
            <label htmlFor="layout-sel">算法</label>
            <select id="layout-sel" value={layout} onChange={(event) => setLayout(event.target.value as LayoutMode)}>
              <option value="force">力导向</option>
              <option value="domain">按域聚类</option>
              <option value="radial">同心圆</option>
            </select>
          </div>
          <div className="control">
            <label htmlFor="labels-chk">显示关系标签</label>
            <input id="labels-chk" type="checkbox" checked={showLabels} onChange={(event) => setShowLabels(event.target.checked)} />
          </div>
          <div className="control">
            <label htmlFor="dim-chk">聚焦模式（弱化无关）</label>
            <input id="dim-chk" type="checkbox" checked={dimMode} onChange={(event) => setDimMode(event.target.checked)} />
          </div>
          <button type="button" className="btn" onClick={reset}>
            重置筛选与视图
          </button>
        </section>
      </aside>

      <section className="canvas">
        <GraphCanvas
          model={model}
          mode="schema"
          phases={phases}
          layout={layout}
          showLabels={showLabels}
          dimMode={dimMode}
          query={query}
          selectedId={selectedId}
          visibleDomains={visibleDomains}
          visibleRelations={visibleRelations}
          onSelectNode={setSelectedId}
          onSelectPhase={() => undefined}
        />
        <div className="overlay stats">
          <span>
            节点 <b>{visibleNodes}</b> / {model.nodes.length}
          </span>
          <span>
            关系 <b>{visibleEdges}</b> / {model.edges.length}
          </span>
          <span>
            关系类型 <b>{visibleRelations.size}</b>
          </span>
        </div>
        <div className="overlay hint">拖拽节点 · 滚轮缩放 · 单击查看详情 · 双击聚焦 · F 适应视图</div>
      </section>

      <aside className="detail">
        <ArtifactPanel artifact={selected} onSelect={setSelectedId} />
      </aside>
    </div>
  );
}
