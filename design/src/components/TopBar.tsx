import { content } from '../data';
import { ROUTES, type Route } from '../router';
import { useTheme } from '../theme';

interface TopBarProps {
  route: Route;
  query: string;
  onQuery: (value: string) => void;
}

/** The header of the application. */
export function TopBar({ route, query, onQuery }: TopBarProps) {
  const { theme, toggle } = useTheme();
  const stats = content.stats;

  const active = (name: string) => {
    if (name === 'artifacts') return route.name === 'artifacts' || route.name === 'artifact';
    if (name === 'docs') return route.name === 'docs' || route.name === 'doc';
    return route.name === name;
  };

  return (
    <header className="topbar">
      <a className="brand" href="#/">
        <span className="logo">◆</span>
        <span className="brand-text">
          <strong>CrispSpec</strong>
          <span className="subtitle">
            {stats.artifacts} 种制品 · {stats.edges} 条关系 · {stats.phases} 个主线阶段 · {stats.docs} 篇文档
          </span>
        </span>
      </a>

      <nav className="views" aria-label="视图">
        {ROUTES.map((item) => (
          <a key={item.path} className={`view-tab${active(item.path) ? ' active' : ''}`} href={`#/${item.path}`}>
            {item.label}
          </a>
        ))}
      </nav>

      <div className="tools">
        <div className="search-wrap">
          <span className="search-icon">⌕</span>
          <input
            id="search"
            type="search"
            placeholder="搜索制品 / 文档 / 关系…"
            value={query}
            onChange={(event) => onQuery(event.target.value)}
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <button type="button" className="icon-btn" onClick={toggle} title="切换明暗主题">
          {theme === 'dark' ? '◐' : '◑'}
        </button>
      </div>
    </header>
  );
}
