import { useEffect, useState } from 'react';

/**
 * The routes of the application.
 *
 * A hash router keeps the app a pure static bundle — it can be opened
 * from the file system or served from any path.
 */
export type Route =
  | { name: 'overview' }
  | { name: 'graph' }
  | { name: 'mainline' }
  | { name: 'artifacts' }
  | { name: 'artifact'; type: string }
  | { name: 'docs' }
  | { name: 'doc'; id: string; anchor?: string };

export const ROUTES = [
  { path: '', label: '概览' },
  { path: 'graph', label: '体系图' },
  { path: 'mainline', label: '开发主线' },
  { path: 'artifacts', label: '制品' },
  { path: 'docs', label: '文档' },
] as const;

/** Parse a location hash into a route. */
export function parseRoute(hash: string): Route {
  const path = hash.replace(/^#\/?/, '').split('#')[0];
  const [head, ...rest] = path.split('/').filter(Boolean);
  switch (head) {
    case 'graph':
      return { name: 'graph' };
    case 'mainline':
      return { name: 'mainline' };
    case 'artifacts':
      return { name: 'artifacts' };
    case 'artifact':
      return rest.length > 0 ? { name: 'artifact', type: rest.join('/') } : { name: 'artifacts' };
    case 'docs':
      return { name: 'docs' };
    case 'doc':
      return rest.length > 0
        ? { name: 'doc', id: rest.join('/'), anchor: hash.split('#')[1] }
        : { name: 'docs' };
    default:
      return { name: 'overview' };
  }
}

/** Build the hash of a route. */
export function routeToHash(route: Route): string {
  switch (route.name) {
    case 'overview':
      return '#/';
    case 'artifact':
      return `#/artifact/${route.type}`;
    case 'doc':
      return `#/doc/${route.id}`;
    default:
      return `#/${route.name}`;
  }
}

/** Subscribe to hash changes. */
export function useRoute(): Route {
  const [route, setRoute] = useState<Route>(() => parseRoute(window.location.hash));
  useEffect(() => {
    const onChange = () => setRoute(parseRoute(window.location.hash));
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return route;
}

/** Navigate to a route. */
export function navigate(route: Route): void {
  window.location.hash = routeToHash(route);
}

/** Scroll to an anchor inside the current page, if there is one. */
export function useAnchor(anchor?: string): void {
  useEffect(() => {
    if (!anchor) return;
    const element = document.getElementById(anchor);
    if (element) element.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [anchor]);
}
