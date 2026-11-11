const fetch = require('node-fetch');

class AiServiceError extends Error {
  constructor(message, code, status = 503) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

function configuredProviders(env) {
  // An explicit local/custom endpoint is authoritative. Never send its
  // requests or a cloud key to a different provider automatically.
  if (env.AI_CHAT_COMPLETIONS_URL) {
    return [{
      name: '自定义模型', url: env.AI_CHAT_COMPLETIONS_URL,
      key: env.AI_API_KEY || '', model: env.AI_MODEL_ID || 'Qwen/Qwen3-1.7B',
      timeout: 60000,
    }];
  }
  const providers = [];
  const doubaoKey = (env.DOUBAO_API_KEY || env.AI_API_KEY || '').trim();
  const doubaoModel = (env.DOUBAO_MODEL_ID || env.AI_MODEL_ID || '').trim();
  if (doubaoKey) providers.push({
    name: '豆包',
    url: env.DOUBAO_API_URL || `https://ark.cn-beijing.volces.com/api/v3/${doubaoModel.startsWith('bot-') ? 'bots/' : ''}chat/completions`,
    key: doubaoKey, model: doubaoModel,
    timeout: 25000,
  });
  let officialDeepSeek = false;
  try { officialDeepSeek = new URL(env.DEEPSEEK_API_BASE || 'https://api.deepseek.com').hostname === 'api.deepseek.com'; } catch {}
  const requestedModel = (env.DEEPSEEK_MODEL || '').trim();
  const deepseekModel = !requestedModel || (officialDeepSeek && ['deepseek-chat','deepseek-reasoner','deepseek-coder'].includes(requestedModel)) ? 'deepseek-flash' : requestedModel;
  if (env.DEEPSEEK_API_KEY) providers.push({
    name: 'DeepSeek',
    url: `${(env.DEEPSEEK_API_BASE || 'https://api.deepseek.com').replace(/\/+$/, '')}/chat/completions`,
    key: env.DEEPSEEK_API_KEY, model: deepseekModel, timeout: 30000, thinkingDisabled: officialDeepSeek,
  });
  return providers;
}

function upstreamError(provider, response, body) {
  const code = String(body?.error?.code || '');
  if (code.includes('ClosedEndpoint') || code.includes('InvalidEndpoint')) {
    return new AiServiceError(`${provider.name}模型端点已关闭或不可用，请启用有效的模型端点后重试。`, 'MODEL_UNAVAILABLE');
  }
  if (response.status === 401 || response.status === 403) {
    return new AiServiceError(`${provider.name}鉴权失败，请检查 API 密钥是否有效。`, 'AUTH_FAILED');
  }
  if (response.status === 402) {
    return new AiServiceError(`${provider.name}服务余额不足，请检查账户余额。`, 'INSUFFICIENT_BALANCE');
  }
  if (response.status === 429) {
    return new AiServiceError(`${provider.name}请求过于频繁，请稍后重试。`, 'RATE_LIMITED');
  }
  return new AiServiceError(`${provider.name}模型服务返回错误（${response.status}），请稍后重试。`, 'UPSTREAM_ERROR', 502);
}

function createAiClient({ env = process.env, fetchImpl = fetch, logger = console } = {}) {
  const providers = configuredProviders(env);
  // Remember an unavailable primary briefly so every subsequent question does
  // not have to wait for the same failing endpoint again.
  const retryAfter = new Map();

  async function request(provider, body, signal) {
    if (!provider.model) throw new AiServiceError(`${provider.name}模型尚未配置，请配置有效的模型或接入点。`, 'MODEL_NOT_CONFIGURED');
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (signal?.aborted) abort();
    signal?.addEventListener('abort', abort, { once: true });
    const timer = setTimeout(() => controller.abort(), provider.timeout);
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (provider.key) headers.Authorization = `Bearer ${provider.key}`;
      const response = await fetchImpl(provider.url, {
        method: 'POST', headers, signal: controller.signal,
        body: JSON.stringify({ ...body, model: provider.model, ...(provider.thinkingDisabled ? {thinking:{type:'disabled'}} : {}) }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw upstreamError(provider, response, data);
      const reply = data.choices?.[0]?.message?.content;
      if (typeof reply !== 'string' || !reply.trim()) {
        throw new AiServiceError(`${provider.name}未返回有效回复，请稍后重试。`, 'EMPTY_RESPONSE', 502);
      }
      return { reply: reply.trim(), provider: provider.name, model: provider.model, truncated: data.choices?.[0]?.finish_reason === 'length' };
    } catch (error) {
      if (error instanceof AiServiceError) throw error;
      if (signal?.aborted) throw new AiServiceError('请求已取消。', 'ABORTED', 499);
      if (error.name === 'AbortError') {
        throw new AiServiceError(`${provider.name}响应超时，请稍后重试。`, 'TIMEOUT', 504);
      }
      throw new AiServiceError(`无法连接${provider.name}模型服务，请检查网络后重试。`, 'NETWORK_ERROR');
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener('abort', abort);
    }
  }

  return async (body, { signal, metadata = false } = {}) => {
    if (!providers.length) {
      throw new AiServiceError('AI 服务尚未配置，请配置有效的 API 密钥并重启 AI 后端。', 'NOT_CONFIGURED');
    }
    const now = Date.now();
    const available = providers.filter(provider => (retryAfter.get(provider.name) || 0) <= now);
    // If all providers are cooling down, still try the last configured one.
    const candidates = available.length ? available : [providers[providers.length - 1]];
    let lastError;
    for (const provider of candidates) {
      if (signal?.aborted) throw new AiServiceError('请求已取消。', 'ABORTED', 499);
      try {
        const result = await request(provider, body, signal);
        retryAfter.delete(provider.name);
        return metadata ? { ...result, fallback: provider !== providers[0] } : result.reply;
      } catch (error) {
        if (error.code === 'ABORTED') throw error;
        lastError = error;
        retryAfter.set(provider.name, Date.now() + 60000);
        // Keep provider response bodies and credentials out of client messages
        // and logs. The stable error code is sufficient for diagnosis.
        logger.warn(`AI 服务 ${provider.name} 暂不可用：${error.code}`);
      }
    }
    throw lastError;
  };
}

module.exports = { createAiClient, AiServiceError };
