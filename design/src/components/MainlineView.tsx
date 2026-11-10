import { useMemo, useState } from 'react';

import { artifacts, edges, phaseById, phases } from '../data';
import { buildGraph } from '../graph/layout';
import { ArtifactPanel, PhasePanel } from './ArtifactPanel';
import { GraphCanvas } from './GraphCanvas';

/** The mainline view: the ten vertical phases and the three lateral ones. */
export function MainlineView({ query }: { query: string }) {
  const model = useMemo(() => buildGraph(artifacts, edges, phases, 'mainline'), []);
  const [selectedPhase, setSelectedPhase] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const phase = selectedPhase ? (phaseById.get(selectedPhase) ?? null) : null;
  const artifact = selectedNode ? (artifacts.find((item) => item.id === selectedNode) ?? null) : null;

  const visibleDomains = useMemo(() => new Set(artifacts.map((item) => item.domain)), []);
  const visibleRelations = useMemo(() => new Set(edges.map((edge) => edge.relation)), []);

  return (
    <div className="workspace">
      <aside className="sidebar">
        <section className="panel">
          <h2>
            阶段 <span className="count">{phases.length}</span>
          </h2>
          <ul className="phase-list">
            {phases.map((item, index) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={`phase-row${selectedPhase === item.id ? ' active' : ''}${item.lateral ? ' lateral' : ''}`}
                  onClick={() => {
                    setSelectedPhase(item.id);
                    setSelectedNode(null);
                  }}
                >
                  <span className="step">{item.lateral ? '横切' : index + 1}</span>
                  <span className="label">{item.label}</span>
                  <span className="num">{item.artifacts.length}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <h2>图例</h2>
          <ul className="legend-list">
            <li>
              <i className="dot main" /> 主线交接
            </li>
            <li>
              <i className="dot side" /> 上下文关系
            </li>
            <li>
              <i className="dot prepared" /> 可提前准备
            </li>
            <li>
              <i className="dot lateral" /> 横切关注点
            </li>
          </ul>
        </section>

        <section className="panel">
          <h2>说明</h2>
          <p className="note">
            域是"关注点"的横向切分，主线是"工作顺序"的纵向推进——两者正交。
            每个阶段分「产出」与「可提前准备」：后者可以早就准备好，主线只说它在这一步已经就位。
          </p>
        </section>
      </aside>

      <section className="canvas">
        <GraphCanvas
          model={model}
          mode="mainline"
          phases={phases}
          layout="force"
          showLabels
          dimMode={false}
          query={query}
          selectedId={selectedNode}
          visibleDomains={visibleDomains}
          visibleRelations={visibleRelations}
          onSelectNode={(id) => {
            setSelectedNode(id);
            if (id) setSelectedPhase(null);
          }}
          onSelectPhase={(id) => {
            setSelectedPhase(id);
            setSelectedNode(null);
          }}
        />
        <div className="overlay stats">
          <span>
            阶段 <b>{phases.length}</b>
          </span>
          <span>
            交接 <b>{phases.reduce((total, item) => total + item.handoff.length, 0)}</b>
          </span>
          <span>
            制品 <b>{artifacts.length}</b>
          </span>
        </div>
        <div className="overlay hint">点击阶段带查看该阶段 · 点击节点查看制品</div>
      </section>

      <aside className="detail">
        {artifact ? (
          <ArtifactPanel artifact={artifact} onSelect={setSelectedNode} />
        ) : (
          <PhasePanel phase={phase} onSelect={setSelectedNode} />
        )}
      </aside>
    </div>
  );
}
