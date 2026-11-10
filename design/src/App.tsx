import { useState } from 'react';

import { ArtifactIndex } from './components/ArtifactIndex';
import { ArtifactPage } from './components/ArtifactPage';
import { DocPage } from './components/DocPage';
import { DocsIndex } from './components/DocsIndex';
import { GraphView } from './components/GraphView';
import { MainlineView } from './components/MainlineView';
import { Overview } from './components/Overview';
import { TopBar } from './components/TopBar';
import { useRoute } from './router';
import { ThemeProvider } from './theme-provider';

/** The application shell. */
export function App() {
  return (
    <ThemeProvider>
      <Shell />
    </ThemeProvider>
  );
}

function Shell() {
  const route = useRoute();
  const [query, setQuery] = useState('');

  const isCanvas = route.name === 'graph' || route.name === 'mainline';

  return (
    <div className="app">
      <TopBar route={route} query={query} onQuery={setQuery} />
      <main className={isCanvas ? 'main canvas-mode' : 'main page-mode'}>
        {route.name === 'overview' && <Overview />}
        {route.name === 'graph' && <GraphView query={query} />}
        {route.name === 'mainline' && <MainlineView query={query} />}
        {route.name === 'artifacts' && <ArtifactIndex query={query} />}
        {route.name === 'artifact' && <ArtifactPage type={route.type} />}
        {route.name === 'docs' && <DocsIndex query={query} />}
        {route.name === 'doc' && <DocPage id={route.id} anchor={route.anchor} />}
      </main>
    </div>
  );
}
