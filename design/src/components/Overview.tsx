import { artifacts, content, domains, phaseById, phases } from '../data';

/** The landing page: what this is, and where everything lives. */
export function Overview() {
  const stats = content.stats;
  const summary =
    (content.meta.summary as string | undefined) ??
    '软件生命周期内的一切，都由严谨的结构化制品来定义和驱动。';

  return (
    <div className="page">
      <section className="hero">
        <h1>结构化制品体系</h1>
        <p className="lead">{summary}</p>
        <div className="stat-row">
          <Stat value={stats.artifacts} label="种制品" />
          <Stat value={stats.edges} label="条关系" />
          <Stat value={stats.relations} label="种关系类型" />
          <Stat value={stats.phases} label="个主线阶段" />
          <Stat value={stats.handoffs} label="次交接" />
          <Stat value={stats.fields} label="个字段" />
        </div>
        <div className="hero-actions">
          <a className="button primary" href="#/graph">
            打开体系图
          </a>
          <a className="button" href="#/mainline">
            查看开发主线
          </a>
          <a className="button" href="#/artifacts">
            浏览全部制品
          </a>
        </div>
      </section>

      <section className="section">
        <h2>域模型</h2>
        <p className="muted">
          制品按关注点划分为 11 个域。域是横向的切分，主线是纵向的推进——两者正交。
        </p>
        <div className="domain-grid">
          {domains.map((domain) => {
            const count = artifacts.filter((artifact) => artifact.domain === domain.key).length;
            return (
              <article key={domain.key} className="domain-card" style={{ ['--domain' as string]: domain.color }}>
                <h3>
                  <span className="swatch" style={{ background: domain.color }} />
                  {domain.label}
                  <span className="count">{count}</span>
                </h3>
                <p>{domain.question}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="section">
        <h2>制品总览</h2>
        <p className="muted">
          35 种制品，每一种都有一份定义文档——字段、枚举、关系都在文档里，图和清单都是从它们生成的。
        </p>
        <table className="grid">
          <thead>
            <tr>
              <th>制品</th>
              <th>ID 前缀</th>
              <th>域</th>
              <th>用途</th>
            </tr>
          </thead>
          <tbody>
            {artifacts.map((artifact) => (
              <tr key={artifact.id}>
                <td>
                  <a href={`#/artifact/${artifact.id}`}>{artifact.name}</a>
                </td>
                <td className="mono">{artifact.prefix}</td>
                <td>
                  <span className="dot-label">
                    <span
                      className="swatch"
                      style={{ background: domains.find((d) => d.key === artifact.domain)?.color }}
                    />
                    {artifact.domainLabel}
                  </span>
                </td>
                <td>{artifact.purpose}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="section">
        <h2>开发主线</h2>
        <p className="muted">
          域是"关注点"的横向切分，主线是"工作顺序"的纵向推进。
          每个阶段分「产出」与「可提前准备」——后者可以早就准备好，主线只说它在这一步已经就位。
        </p>
        <table className="grid">
          <thead>
            <tr>
              <th>#</th>
              <th>阶段</th>
              <th>回答什么</th>
              <th>产出</th>
              <th>可提前准备</th>
            </tr>
          </thead>
          <tbody>
            {phases.map((phase, index) => (
              <tr key={phase.id} className={phase.lateral ? 'lateral' : undefined}>
                <td>{phase.lateral ? '横切' : index + 1}</td>
                <td>{phase.label}</td>
                <td className="muted">{phase.question}</td>
                <td>
                  {phase.produces.map((id) => (
                    <ArtifactChip key={id} id={id} />
                  ))}
                </td>
                <td>
                  {phase.prepares.length === 0 ? (
                    <span className="muted">—</span>
                  ) : (
                    phase.prepares.map((id) => <ArtifactChip key={id} id={id} />)
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted small">
          横切阶段不推进主线，只准备贯穿全程的制品。阶段归属见
          <code>design/data/artifacts.yaml</code> 的 <code>mainline:</code> 段。
        </p>
      </section>

      <section className="section">
        <h2>设计原则</h2>
        <ol className="principles">
          <li>
            <strong>两个描述性字段</strong>——每个制品最多包含 <code>name</code>（短标题）和
            <code>description</code>（一句话说明）两个自由文本字段。
          </li>
          <li>
            <strong>其余字段皆结构化</strong>——所有非描述性字段必须可枚举、可验证或可计算。
          </li>
          <li>
            <strong>ID 即引用</strong>——制品之间通过 typed ID 互相引用，形成可追溯的知识图谱。
          </li>
          <li>
            <strong>单向熵减</strong>——信息从非结构化的 Draft 逐层转化为严格结构化的制品，不允许反向退化。
          </li>
        </ol>
        <p className="muted small">
          更完整的说明见 <a href="#/doc/concepts">制品体系概览</a> 与{' '}
          <a href="#/doc/vision">为什么是结构化制品</a>。
        </p>
      </section>
    </div>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="stat">
      <b>{value}</b>
      <span>{label}</span>
    </div>
  );
}

function ArtifactChip({ id }: { id: string }) {
  const artifact = artifacts.find((item) => item.id === id);
  if (!artifact) return null;
  const phase = artifact.phase ? phaseById.get(artifact.phase) : undefined;
  return (
    <a className="chip" href={`#/artifact/${artifact.id}`} title={phase ? `${phase.label}` : undefined}>
      {artifact.name}
    </a>
  );
}
