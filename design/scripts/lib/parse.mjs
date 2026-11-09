/**
 * Parsers for the design documents.
 *
 * Every artifact definition document is written in the same shape:
 *
 *     ## 目标          一段话：这个制品解决什么问题
 *     ## 字段定义      字段表 + 枚举表
 *     ## 子结构定义    子结构表（可选）
 *     ## 关联          关系表
 *
 * These helpers turn that shape into plain data.  They are deliberately
 * forgiving: a document that does not follow the shape exactly still
 * yields whatever it does contain.
 */

/** Heading that introduces the goal paragraph. */
export const GOAL_HEADING = '目标';
/** Heading that introduces the field table. */
export const FIELD_HEADING = '字段定义';
/** Heading that introduces the sub-structure tables. */
export const STRUCT_HEADING = '子结构定义';
/** Heading that introduces the relation table. */
export const RELATION_HEADING = '关联';
/** Heading that documents the `as` mapping of the business concept. */
export const MAPPING_HEADING = '映射关系';

/** Direction markers used in the relation table. */
const ARROW_OUT = '→';
const ARROW_IN = '←';
const ARROW_BOTH = '↔';

/** Relation names are SCREAMING_SNAKE identifiers. */
const RELATION_TOKEN = /[A-Z][A-Z0-9_]*/g;
/** A markdown link inside a table cell. */
const LINK = /\[([^\]]*)\]\(([^)]*)\)/g;
/** A field name is an identifier. */
const FIELD_NAME = /^[A-Za-z_][A-Za-z0-9_]*$/;

/**
 * Return the body of the `## <heading>` section of `text`.
 *
 * Headings are matched by containment so that numbered variants
 * (`## 一、七个核心映射位置`) are found as well.
 */
export function section(text, heading) {
  const lines = text.split('\n');
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.startsWith('## ') || !line.includes(heading)) continue;
    const body = [];
    for (let follow = index + 1; follow < lines.length; follow += 1) {
      if (lines[follow].startsWith('## ')) break;
      body.push(lines[follow]);
    }
    return body.join('\n');
  }
  return '';
}

/** Tell whether a table row is a separator such as `|---|---|`. */
function isSeparator(row) {
  return row.length > 0 && row.every((cell) => cell !== '' && /^[-\s:]+$/.test(cell));
}

/**
 * Return the tables of `sectionText` together with the heading that
 * precedes them.
 *
 * The heading of the first table is empty — it belongs to the section
 * itself rather than to a subsection.
 */
export function tables(sectionText) {
  const result = [];
  let heading = '';
  let rows = [];

  const flush = () => {
    if (rows.length > 0) result.push({ heading, rows });
  };

  for (const line of sectionText.split('\n')) {
    const stripped = line.trim();
    if (stripped.startsWith('### ')) {
      flush();
      rows = [];
      heading = stripped.slice(4).trim();
      continue;
    }
    if (!stripped.startsWith('|')) continue;
    const cells = stripped.replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
    if (isSeparator(cells)) continue;
    rows.push(cells);
  }
  flush();
  return result;
}

/**
 * Strip the markdown decoration of a table cell.
 *
 * The `../../` repair is kept for historical documents: an old export
 * process replaced stray slashes with `../../`.
 */
export function clean(cell) {
  let text = cell.replace(LINK, '$1');
  text = text.replace(/`/g, '').replace(/\*\*/g, '');
  text = text.replace(/\\</g, '<').replace(/\\>/g, '>');
  text = text.replace(/\.\.\/\.\.\//g, '/');
  return text.trim();
}

/** Parse the field table of an artifact type. */
export function parseFields(rows) {
  const fields = [];
  for (const row of rows.slice(1)) {
    if (row.length < 4 || isSeparator(row)) continue;
    const name = clean(row[0]);
    if (!FIELD_NAME.test(name)) continue;
    fields.push({
      name,
      type: clean(row[1]),
      constraint: clean(row[2]),
      description: clean(row[3]),
    });
  }
  return fields;
}

/** Parse an enum table such as `### type 枚举`. */
export function parseEnum(heading, rows) {
  const values = [];
  for (const row of rows.slice(1)) {
    if (row.length < 2 || isSeparator(row)) continue;
    const value = clean(row[0]);
    if (!value) continue;
    values.push({ value, meaning: clean(row[1]) });
  }
  if (values.length === 0) return null;
  return { name: heading || '枚举', values };
}

/** Parse the `## 子结构定义` tables of an artifact type. */
export function parseStructs(sectionText) {
  const structs = [];
  for (const { heading, rows } of tables(sectionText)) {
    if (rows.length < 2) continue;
    structs.push({
      name: heading || '子结构',
      columns: rows[0].map((cell) => clean(cell)),
      rows: rows.slice(1).filter((row) => !isSeparator(row)).map((row) => row.map((cell) => clean(cell))),
    });
  }
  return structs;
}

/** Extract the relation names of a table cell (a cell may hold several). */
export function relationNames(cell) {
  const names = [];
  for (const token of cell.replace(/`/g, ' ').match(RELATION_TOKEN) ?? []) {
    if (!names.includes(token)) names.push(token);
  }
  return names;
}

/** Classify a direction cell as `out`, `in` or `both`. */
export function direction(cell) {
  if (cell.includes(ARROW_BOTH)) return 'both';
  if (cell.includes(ARROW_OUT)) return 'out';
  if (cell.includes(ARROW_IN)) return 'in';
  return 'out';
}

/** Return the rows of the relation table of a document. */
export function relationRows(sectionText) {
  const rows = [];
  for (const line of sectionText.split('\n')) {
    const stripped = line.trim();
    if (!stripped.startsWith('|') || !stripped.endsWith('|')) continue;
    const cells = stripped.replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
    if (cells.length !== 3) continue;
    if (cells.every((cell) => cell !== '' && /^[-\s:]+$/.test(cell))) continue;
    if (cells[0] === '方向' || cells[0] === 'Direction') continue;
    rows.push({ direction: cells[0], relation: cells[1], target: cells[2] });
  }
  return rows;
}

/** Parse the `as` mapping of the business concept. */
export function parseMappings(text) {
  const mappings = [];
  const entry = /\{\s*artifact_type:\s*([A-Z_]+)\s*,\s*artifact_id:\s*"([^"]+)"\s*\}/g;
  const body = section(text, MAPPING_HEADING);
  for (const match of body.matchAll(entry)) {
    mappings.push({ artifactType: match[1], artifactId: match[2] });
  }
  return mappings;
}

/** Return the goal paragraph of a document. */
export function parseGoal(text) {
  const body = section(text, GOAL_HEADING);
  const paragraphs = body
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0 && !line.startsWith('#') && !line.startsWith('|') && !line.startsWith('---'));
  return clean(paragraphs.join(' '));
}
