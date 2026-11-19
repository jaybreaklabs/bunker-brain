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

export function facets(model, baseHost) {
  const tags = (model.tags ?? []).map(tag => tag.name ?? tag).filter(tag => typeof tag === 'string');
  const base = model.info?.base_model_id || model.id;
  const agent = model.agent?.provider;
  const prefix = base.match(/^(mac|pc)\./i)?.[1];
  const hostTag = tags.find(tag => /^host:\s*\S/i.test(tag))?.slice(5).trim()
    || tags.find(tag => /^(mac|pc)$/i.test(tag));
  let host = agent ? 'Terminal' : hostTag || baseHost || prefix;
  if (!host && !model.info?.base_model_id && model.owned_by === 'ollama') host = 'Mac';
  if (/^pc$/i.test(host)) host = 'PC';
  if (/^mac$/i.test(host)) host = 'Mac';
  const identity = agent ? [agent, model.agent.model, model.name] : [base, model.name];
  const family = families.find(([, pattern]) => pattern.test(identity.join(' ')))?.[0];
  return { host, family };
}

function unavailableItem(model, label, saved) {
  const tags = new Map();
  for (const tag of [...(saved?.tags ?? []), ...(model.tags ?? [])]) {
    tags.set(tag.name, tag);
  }
  const displayModel = {
    ...model,
    tags: [...tags.values()],
    connection_type: model.connection_type ?? saved?.connection_type,
    direct: model.direct ?? saved?.direct,
  };
  const { host, family } = facets(displayModel, saved?.host);
  return { value: model.id, label, model: displayModel, host, family: family ?? saved?.family, unavailable: true };
}

export function pickerItems(models, pins, terminalId, label, remembered = new Map(), configured = []) {
  const known = new Map(models.map(model => [model.id, model]));
  const pinned = new Set(pins ?? []);
  for (const id of remembered.keys()) {
    if (!pinned.has(id)) remembered.delete(id);
  }
  const items = models.map(model => {
    const saved = remembered.get(model.id);
    if (model.info?.meta?.hidden) remembered.delete(model.id);
    if (model.picker_base_missing && !model.direct) return unavailableItem(model, label(model), saved);
    const base = known.get(model.info?.base_model_id);
    const { host, family } = facets(model, base && facets(base).host);
    const item = {
      value: model.id, label: label(model), model,
      host: host ?? saved?.host,
      family, unavailable: false,
    };
    if (pinned.has(model.id) && !model.info?.meta?.hidden) {
      remembered.set(model.id, {
        label: item.label, host: item.host, family,
        connection_type: model.connection_type, direct: model.direct, tags: model.tags,
      });
    }
    return item;
  });

  for (const model of configured) {
    if (known.has(model.id)) continue;
    known.set(model.id, model);
    items.push(unavailableItem(model, label(model), remembered.get(model.id)));
  }

  // Only restore the user's own explicit pins. Keep agent pins inside their terminal.
  for (const id of pinned) {
    if (!id || known.has(id)) continue;
    const parts = id.split(':');
    const isAgent = parts[0] === 'agent';
    if (isAgent && (!terminalId || parts[1] !== encodeURIComponent(terminalId))) continue;
    const name = isAgent ? parts.slice(2).join('/') : id;
    const saved = remembered.get(id);
    const model = { id, name, agent: isAgent ? { provider: parts[2] } : undefined };
    items.push(unavailableItem(model, saved?.label ?? name, saved));
  }
  return items;
}

export function options(items, key) {
  return [...new Set(items.filter(item => !item.model.info?.meta?.hidden)
    .map(item => item[key]).filter(Boolean))].sort();
}
