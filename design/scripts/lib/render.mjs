/**
 * Markdown rendering for the design documents.
 *
 * The documents are the source of truth, so they are rendered to HTML at
 * build time.  Two things need special treatment:
 *
 * - **Links.**  A link to another document becomes an in-app route; a link
 *   to a file that does not exist becomes plain text instead of a broken
 *   link.
 * - **Mermaid.**  Diagram blocks are extracted and rendered by the client,
 *   so they are replaced by a placeholder element.
 */

import { Marked } from 'marked';
import { dirname, join, relative, resolve, sep } from 'node:path';

/** Convert a Windows path to POSIX form. */
export function toPosix(path) {
  return path.split(sep).join('/');
}

/** Strip HTML tags from a string. */
function stripTags(text) {
  return text.replace(/<[^>]*>/g, '');
}

/** Build an anchor id from a heading text (GitHub-ish). */
export function slugify(text) {
  return stripTags(text)
    .trim()
    .toLowerCase()
    .replace(/[`*_~]/g, '')
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .replace(/\s+/g, '-');
}

/**
 * Replace every mermaid block with a placeholder element.
 *
 * Returns the rewritten markdown and the extracted diagrams.
 */
export function extractMermaid(markdown) {
  const diagrams = [];
  const rewritten = markdown.replace(
    /```mermaid\r?\n([\s\S]*?)```/g,
    (_match, code) => {
      const id = `mermaid-${diagrams.length + 1}`;
      diagrams.push({ id, code: code.replace(/\s+$/, '') });
      return `<div class="mermaid" data-mermaid="${id}"></div>`;
    },
  );
  return { markdown: rewritten, diagrams };
}

/**
 * Build a link resolver for one document.
 *
 * @param {object} options
 * @param {string} options.docId       Id of the document being rendered.
 * @param {Map<string,string>} options.docs  Known document ids.
 * @param {string} options.contentRoot Absolute path of the content directory.
 * @param {string} options.designRoot  Absolute path of the design project.
 */
export function createLinkResolver({ docId, docs, contentRoot, designRoot }) {
  const docFile = join(contentRoot, `${docId}.md`);
  const baseDir = dirname(docFile);

  return function resolveLink(href) {
    if (!href) return { kind: 'dead', title: '空链接' };
    if (/^(https?:|mailto:|tel:|data:)/i.test(href)) return { kind: 'external' };

    const hashIndex = href.indexOf('#');
    const rawPath = hashIndex >= 0 ? href.slice(0, hashIndex) : href;
    const anchor = hashIndex >= 0 ? href.slice(hashIndex) : '';

    if (!rawPath) {
      return { kind: 'internal', href: `#/doc/${docId}${anchor}` };
    }
    if (rawPath.startsWith('/')) {
      return { kind: 'dead', title: `仓库内绝对路径：${href}` };
    }

    const absolute = resolve(baseDir, decodeURIComponent(rawPath));

    if (absolute === designRoot) {
      return { kind: 'internal', href: '#/graph' };
    }
    if (absolute.startsWith(contentRoot + sep)) {
      const relativePath = toPosix(relative(contentRoot, absolute));
      if (relativePath.endsWith('.md')) {
        const targetId = relativePath.slice(0, -3);
        if (docs.has(targetId)) {
          return { kind: 'internal', href: `#/doc/${targetId}${anchor}` };
        }
        return { kind: 'dead', title: `文档不存在：${relativePath}` };
      }
      return { kind: 'dead', title: `链接指向目录：${relativePath}` };
    }
    if (absolute.startsWith(designRoot + sep)) {
      const relativePath = toPosix(relative(designRoot, absolute));
      if (relativePath === 'data/artifacts.yaml') {
        return { kind: 'internal', href: '#/artifacts' };
      }
      return { kind: 'dead', title: `链接指向工程文件：${relativePath}` };
    }
    return { kind: 'dead', title: `链接指向仓库其他位置：${rawPath}` };
  };
}

/**
 * Render markdown to HTML.
 *
 * @param {string} markdown Raw markdown.
 * @param {Function} resolveLink Link resolver, see `createLinkResolver`.
 */
export function renderMarkdown(markdown, resolveLink) {
  const marked = new Marked({ gfm: true, breaks: false });

  const renderer = {
    heading({ tokens, depth }) {
      const text = this.parser.parseInline(tokens);
      const slug = slugify(text);
      return `<h${depth} id="${slug}">${text}</h${depth}>\n`;
    },
    link({ href, title, tokens }) {
      const text = this.parser.parseInline(tokens);
      const target = resolveLink(href);
      const titleAttr = title ? ` title="${title}"` : '';
      if (target.kind === 'external') {
        return `<a href="${href}"${titleAttr} target="_blank" rel="noreferrer">${text}</a>`;
      }
      if (target.kind === 'internal') {
        return `<a href="${target.href}"${titleAttr}>${text}</a>`;
      }
      return `<span class="link-dead" title="${target.title ?? ''}">${text}</span>`;
    },
  };

  marked.use({ renderer });
  return marked.parse(markdown);
}

/** Return the title of a document — its first level-1 heading. */
export function documentTitle(markdown) {
  const match = markdown.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : '';
}

/** Return the headings of a document, for the outline. */
export function documentHeadings(markdown) {
  const headings = [];
  let inFence = false;
  for (const line of markdown.split('\n')) {
    if (line.trim().startsWith('```')) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;
    const match = line.match(/^(#{1,4})\s+(.+)$/);
    if (!match) continue;
    const text = match[2].trim();
    headings.push({ level: match[1].length, text, slug: slugify(text) });
  }
  return headings;
}
