import { useEffect, useRef } from 'react';

import { useTheme } from '../theme';
import type { MermaidDiagram } from '../types';

interface MarkdownProps {
  html: string;
  diagrams?: MermaidDiagram[];
}

/**
 * Renders a compiled document.
 *
 * Mermaid blocks are rendered by the client — the compiler replaces them
 * with a placeholder element that carries the diagram id.
 */
export function Markdown({ html, diagrams = [] }: MarkdownProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const renderId = useRef(0);
  const { theme } = useTheme();

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    const placeholders = Array.from(container.querySelectorAll<HTMLElement>('div[data-mermaid]'));
    if (placeholders.length === 0) return undefined;

    let cancelled = false;
    renderId.current += 1;
    const run = renderId.current;

    const render = async () => {
      const mermaid = (await import('mermaid')).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: theme === 'light' ? 'default' : 'dark',
        securityLevel: 'strict',
        fontFamily: 'Inter, "PingFang SC", "Microsoft YaHei", sans-serif',
      });
      for (const placeholder of placeholders) {
        if (cancelled) return;
        const id = placeholder.dataset.mermaid;
        const diagram = diagrams.find((item) => item.id === id);
        if (!diagram) continue;
        try {
          const { svg } = await mermaid.render(`crisp-mermaid-${run}-${id}`, diagram.code);
          if (cancelled) return;
          placeholder.innerHTML = svg;
        } catch {
          placeholder.textContent = diagram.code;
          placeholder.classList.add('mermaid-failed');
        }
      }
    };

    void render();
    return () => {
      cancelled = true;
    };
  }, [diagrams, html, theme]);

  return <div ref={containerRef} className="markdown" dangerouslySetInnerHTML={{ __html: html }} />;
}
