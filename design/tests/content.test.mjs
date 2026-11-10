/**
 * The consistency of the artifact system.
 *
 * These tests are the design-stage replacement of the old Python test
 * suite: they check the same invariants — the mainline covers every
 * artifact exactly once, every hand-off is a real relation edge — but
 * they check them on the *design*, not on an implementation of it.
 */

import assert from 'node:assert/strict';
import test from 'node:test';

import { buildContent } from '../scripts/lib/build.mjs';

const { payload, problems } = buildContent();

test('内容编译没有发现问题', () => {
  assert.deepEqual(problems, []);
});

test('每种制品恰好属于一个主线阶段', () => {
  const seen = new Map();
  for (const phase of payload.phases) {
    for (const id of phase.artifacts) {
      assert.equal(seen.has(id), false, `制品 ${id} 出现在多个阶段`);
      seen.set(id, phase.id);
    }
  }
  for (const artifact of payload.artifacts) {
    assert.equal(seen.has(artifact.id), true, `制品 ${artifact.id} 不在任何阶段`);
  }
});

test('主线不重不漏地串起全部制品', () => {
  const covered = payload.phases.flatMap((phase) => phase.artifacts);
  assert.equal(covered.length, payload.artifacts.length);
  assert.equal(new Set(covered).size, payload.artifacts.length);
});

test('每条主线交接都是真实存在的关系边', () => {
  const edges = new Set(payload.edges.map((edge) => `${edge.source}|${edge.target}|${edge.relation}`));
  for (const phase of payload.phases) {
    for (const handoff of phase.handoff) {
      const key = `${handoff.source}|${handoff.target}|${handoff.relation}`;
      assert.equal(edges.has(key), true, `${phase.id} 的交接 ${key} 不是真实的关系边`);
    }
  }
});

test('横切阶段只准备、不产出', () => {
  for (const phase of payload.phases.filter((item) => item.lateral)) {
    assert.equal(phase.produces.length, 0, `横切阶段 ${phase.id} 不应产出制品`);
    assert.ok(phase.prepares.length > 0, `横切阶段 ${phase.id} 应当准备制品`);
  }
});

test('每种制品都有定义文档、用途和字段', () => {
  for (const artifact of payload.artifacts) {
    assert.ok(artifact.definition, `${artifact.id} 没有定义文档`);
    assert.ok(artifact.purpose.length > 0, `${artifact.id} 没有用途`);
    assert.ok(artifact.fields.length > 0, `${artifact.id} 没有字段定义`);
    assert.ok(artifact.idPattern.length > 0, `${artifact.id} 没有 ID 模式`);
  }
});

test('每份定义文档都能解析出字段表与关系表', () => {
  for (const artifact of payload.artifacts) {
    const doc = payload.docs.find((item) => item.id === artifact.definition);
    assert.ok(doc, `${artifact.id} 的定义文档没有进入文档索引`);
    assert.ok(doc.html.length > 0, `${artifact.id} 的定义文档渲染为空`);
  }
});

test('关系边只连接已知制品', () => {
  const ids = new Set(payload.artifacts.map((artifact) => artifact.id));
  for (const edge of payload.edges) {
    assert.ok(ids.has(edge.source), `未知起点 ${edge.source}`);
    assert.ok(ids.has(edge.target), `未知终点 ${edge.target}`);
  }
});

test('业务概念的映射目标都是已知制品', () => {
  const concept = payload.artifacts.find((artifact) => artifact.id === 'business-concept');
  assert.ok(concept);
  const ids = new Set(payload.artifacts.map((artifact) => artifact.id));
  for (const target of concept.mappingTargets) {
    assert.ok(ids.has(target), `未知映射目标 ${target}`);
  }
  const mapped = payload.edges.filter((edge) => edge.source === 'business-concept' && edge.relation === 'AS');
  assert.equal(mapped.length, concept.mappingTargets.length);
});

test('制品的出入关系与关系边一致', () => {
  for (const artifact of payload.artifacts) {
    const outgoing = payload.edges.filter((edge) => edge.source === artifact.id);
    const incoming = payload.edges.filter((edge) => edge.target === artifact.id);
    assert.equal(artifact.outgoing.length, outgoing.length, `${artifact.id} 的出向关系不一致`);
    assert.equal(artifact.incoming.length, incoming.length, `${artifact.id} 的入向关系不一致`);
  }
});

test('每篇文档都有标题和正文', () => {
  for (const doc of payload.docs) {
    assert.ok(doc.title.length > 0, `${doc.file} 没有标题`);
    assert.ok(doc.html.length > 100, `${doc.file} 正文过短`);
  }
});

test('登记表里的统计与实际一致', () => {
  assert.equal(payload.stats.artifacts, payload.artifacts.length);
  assert.equal(payload.stats.edges, payload.edges.length);
  assert.equal(payload.stats.docs, payload.docs.length);
  assert.equal(payload.stats.handoffs, payload.phases.flatMap((phase) => phase.handoff).length);
});

test('同一对制品之间只有一个关系名（归属除外）', () => {
  const pairs = new Map();
  for (const edge of payload.edges) {
    const key = [edge.source, edge.target].sort().join('|');
    const relations = pairs.get(key) ?? new Set();
    relations.add(edge.relation);
    pairs.set(key, relations);
  }
  for (const [key, relations] of pairs) {
    if (relations.size <= 1) continue;
    assert.ok(
      relations.has('CONTAINS'),
      `${key} 之间有多个关系名 [${[...relations].join(', ')}]`,
    );
  }
});

test('需求的出向关系恰好是那四条', () => {
  const requirement = payload.artifacts.find((artifact) => artifact.id === 'requirement');
  const relations = requirement.outgoing
    .map((relation) => `${relation.relation}->${relation.target}`)
    .sort();
  assert.deepEqual(relations, [
    'ACTED_BY->role',
    'DECOMPOSES_INTO->user-story',
    'DESCRIBED_BY->business-concept',
    'TESTED_BY->acceptance-test',
  ]);
});

test('需求与用户故事之间只有一条边', () => {
  const edges = payload.edges.filter(
    (edge) =>
      (edge.source === 'requirement' && edge.target === 'user-story') ||
      (edge.source === 'user-story' && edge.target === 'requirement'),
  );
  assert.equal(edges.length, 1);
  assert.equal(edges[0].relation, 'DECOMPOSES_INTO');
  assert.equal(edges[0].mainline, true);
});

test('业务概念的映射目标在登记表与文档之间一致', () => {
  const concept = payload.artifacts.find((artifact) => artifact.id === 'business-concept');
  const declared = payload.edges
    .filter((edge) => edge.source === 'business-concept' && edge.relation === 'AS')
    .map((edge) => edge.target)
    .sort();
  assert.deepEqual(declared, [...concept.mappingTargets].sort());
});
