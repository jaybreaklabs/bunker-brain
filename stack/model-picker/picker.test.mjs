import assert from 'node:assert/strict';
import test from 'node:test';
import { facets, options, pickerItems } from './picker.mjs';

const label = model => model.name || model.id;

test('separates the model family from its connection protocol', () => {
  for (const [id, family] of [
    ['pc.qwen3', 'Qwen'], ['medgemma', 'Gemma'], ['claude-code', 'Anthropic'],
    ['gpt-oss', 'OpenAI'], ['deepseek-r1-distill-qwen', 'DeepSeek'], ['moonshotai/kimi', 'Kimi'],
  ]) assert.equal(facets({ id, owned_by: 'openai' }).family, family);
  assert.equal(facets({ id: 'custom', owned_by: 'openai' }).family, undefined);
});

test('uses a connection tag before a prefix or the project Ollama default', () => {
  const model = { id: 'qwen3', owned_by: 'ollama' };
  assert.equal(facets(model).host, 'Mac');
  assert.equal(facets({ ...model, id: 'pc.qwen3' }).host, 'PC');
  assert.equal(facets({ ...model, tags: [{ name: 'host:Lab' }] }).host, 'Lab');
});

test('keeps a disconnected pin visible and restores it once on reconnect', () => {
  const cache = new Map();
  const model = { id: 'qwen3', name: 'Local Qwen', owned_by: 'ollama', loaded: false };
  const list = models => pickerItems(models, [model.id], null, label, cache);
  assert.equal(list([model])[0].unavailable, false);
  const [missing] = list([]);
  assert.equal(missing.host, 'Mac');
  assert.equal(missing.label, model.name);
  assert.equal(missing.unavailable, true);
  assert.deepEqual(list([model]).map(item => item.unavailable), [false]);
  assert.deepEqual(pickerItems([], [], null, label, cache), []);
});

test('terminal pins belong to the selected terminal', () => {
  const id = 'agent:demo:claude-code:opus';
  assert.deepEqual(pickerItems([], [id], 'other', label), []);
  const [missing] = pickerItems([], [id], 'demo', label);
  assert.equal(missing.family, 'Anthropic');
  assert.equal(missing.unavailable, true);
});

test('handles unavailable workspace presets and excludes hidden models from filters', () => {
  const models = [
    { id: 'assistant', info: { base_model_id: 'pc.gemma' }, picker_base_missing: true },
    { id: 'kimi', info: { meta: { hidden: true } } },
  ];
  const items = pickerItems(models, ['kimi'], null, label);
  assert.equal(items[0].unavailable, true);
  assert.deepEqual(options(items, 'family'), ['Gemma']);
  assert.deepEqual(options(items, 'host'), ['PC']);
});

test('lists missing configured models on cold start and prefers a live copy', () => {
  const model = { id: 'pc.qwen3', name: 'Workspace Qwen', tags: [{ name: 'PC' }] };
  const cold = pickerItems([], [model.id], null, label, new Map(), [model]);
  assert.equal(cold.length, 1);
  assert.equal(cold[0].label, model.name);
  assert.equal(cold[0].unavailable, true);
  assert.deepEqual(pickerItems([model], [], null, label, new Map(), [model])
    .map(item => item.unavailable), [false]);
});
