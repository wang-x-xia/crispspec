#!/usr/bin/env node
/**
 * Compile the design content into the JSON the frontend consumes.
 *
 * Usage: node scripts/build-content.mjs
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, relative } from 'node:path';

import { buildContent, OUTPUT_FILE, PROJECT_ROOT } from './lib/build.mjs';
import { toPosix } from './lib/render.mjs';

const { payload, problems, warnings } = buildContent();

if (problems.length > 0) {
  console.error(`\n✗ 构建失败，发现 ${problems.length} 个问题：`);
  for (const problem of problems) console.error(`  · ${problem}`);
  process.exit(1);
}

mkdirSync(dirname(OUTPUT_FILE), { recursive: true });
writeFileSync(OUTPUT_FILE, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');

const stats = payload.stats;
console.log('✓ 内容已编译');
console.log(
  `  ${stats.artifacts} 种制品 · ${stats.edges} 条关系 · ${stats.relations} 种关系类型 · ` +
    `${stats.phases} 个主线阶段 · ${stats.docs} 篇文档 · ${stats.fields} 个字段`,
);
for (const warning of warnings) console.warn(`  ! ${warning}`);
console.log(`  → ${toPosix(relative(PROJECT_ROOT, OUTPUT_FILE))}`);
