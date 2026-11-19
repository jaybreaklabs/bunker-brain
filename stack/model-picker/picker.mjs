// Family is independent of the API protocol used to serve a model.
const families = [
  ['DeepSeek', /deepseek/i],
  ['Qwen', /qwen/i],
  ['Gemma', /gemma/i],
  ['Kimi', /kimi|moonshot/i],
  ['Anthropic', /anthropic|claude/i],
  ['OpenAI', /openai|codex|(?:^|[^a-z])(?:gpt|o[134])(?:[^a-z]|$)/i],
  ['Llama', /llama/i],
  ['Nemotron', /nemotron/i],
];

export function facets(model) {
  const tags = (model.tags ?? []).map(tag => tag.name ?? tag).filter(tag => typeof tag === 'string');
  const base = model.info?.base_model_id || model.id;
  const agent = model.agent?.provider;
  const prefix = base.match(/^(mac|pc)\./i)?.[1];
  const hostTag = tags.find(tag => /^host:\s*\S/i.test(tag))?.slice(5).trim()
    || tags.find(tag => /^(mac|pc)$/i.test(tag));
  let host = agent ? 'Terminal' : hostTag || prefix;
  if (!host && !model.info?.base_model_id && model.owned_by === 'ollama') host = 'Mac';
  if (/^pc$/i.test(host)) host = 'PC';
  if (/^mac$/i.test(host)) host = 'Mac';
  const family = families.find(([, pattern]) => pattern.test([agent, base, model.name].join(' ')))?.[0];
  return { host, family };
}

export function pickerItems(models, pins, terminalId, label, remembered = new Map(), configured = []) {
  const known = new Map(models.map(model => [model.id, model]));
  const pinned = new Set(pins ?? []);
  for (const id of remembered.keys()) {
    if (!pinned.has(id)) remembered.delete(id);
  }
  const items = models.map(model => {
    const base = known.get(model.info?.base_model_id);
    const { host, family } = facets(model);
    const baseHost = base && facets(base).host;
    const item = {
      value: model.id, label: label(model), model,
      host: host ?? baseHost ?? remembered.get(model.id)?.host,
      family, unavailable: !!model.picker_base_missing && !model.direct,
    };
    if (pinned.has(model.id)) {
      if (model.info?.meta?.hidden) remembered.delete(model.id);
      else remembered.set(model.id, { label: item.label, host: item.host, family });
    }
    return item;
  });

  for (const model of configured) {
    if (known.has(model.id)) continue;
    known.set(model.id, model);
    const { host, family } = facets(model);
    items.push({
      value: model.id, label: label(model), model, family,
      host: host ?? remembered.get(model.id)?.host,
      unavailable: true,
    });
  }

  // Only restore the user's own explicit pins. Keep agent pins inside their terminal.
  for (const id of pinned) {
    if (!id || known.has(id)) continue;
    const parts = id.split(':');
    const isAgent = parts[0] === 'agent';
    if (isAgent && (!terminalId || parts[1] !== encodeURIComponent(terminalId))) continue;
    const name = isAgent ? parts.slice(2).join('/') : id;
    const model = { id, name, agent: isAgent ? { provider: parts[2] } : undefined };
    items.push({ value: id, label: name, model, ...facets(model), ...remembered.get(id), unavailable: true });
  }
  return items;
}

export function options(items, key) {
  return [...new Set(items.filter(item => !item.model.info?.meta?.hidden)
    .map(item => item[key]).filter(Boolean))].sort();
}
