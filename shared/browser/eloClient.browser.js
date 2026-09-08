/**
 * elo-api-playground - browser client for the ELO IX REST API.
 *
 * A browser page cannot call ELO directly:
 *   - the IX endpoint is on another origin  -> blocked by CORS
 *   - you must never ship the ELO password to the browser
 *
 * So this client sends each call to the playground's OWN backend, which holds
 * the connection and forwards the RPC to ELO (or returns mock data):
 *
 *   browser --POST /api/elo/proxy {method, body}--> playground backend --RPC--> ELO
 *
 * The method surface (call / login / findAll) matches the Python and Node
 * clients so the three snippets read almost identically.
 */

export class EloError extends Error {}

export class EloClient {
  constructor({ proxyUrl = "/api/elo/proxy", credentials = null, mock = false, topicId = null, mockData = null } = {}) {
    this._proxyUrl = proxyUrl;
    this._credentials = credentials; // {base_url, user, password, tls_verify} or null
    this._mock = mock;
    this._topicId = topicId; // lets the backend load this topic's mock: block
    this._mockData = mockData; // { "<method>": <entry>, ... } - resolve locally, no backend
    this._calls = {};
    this.user = null;
  }

  /** Make one IX RPC call (via the backend proxy) and return its `result`. */
  async call(method, body = {}) {
    if (this._mockData) return this._mockCall(method);

    let resp;
    try {
      resp = await fetch(this._proxyUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          method,
          body: body ?? {},
          mock: this._mock,
          topic_id: this._topicId,
          credentials: this._credentials,
        }),
      });
    } catch (err) {
      throw new EloError(`${method}: request to playground backend failed: ${err.message}`);
    }
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || data.error) {
      throw new EloError(`${method}: ${data.error || "HTTP " + resp.status}`);
    }
    return data.result;
  }

  /** Local mock resolution (static demo) - mirrors the Python MockEloClient. */
  _mockCall(method) {
    if (!(method in this._mockData)) {
      throw new EloError(`${method}: no mock response configured for the static demo`);
    }
    let entry = this._mockData[method];
    if (Array.isArray(entry)) {
      const i = Math.min(this._calls[method] ?? 0, entry.length - 1);
      this._calls[method] = i + 1;
      entry = entry[i];
    }
    if (entry && typeof entry === "object" && "exception" in entry) {
      throw new EloError(`${method}: ${entry.exception}`);
    }
    if (entry && typeof entry === "object" && "result" in entry) return entry.result;
    return entry;
  }

  async login() {
    const raw = await this.call("login", {});
    this.user = raw && typeof raw === "object" && "user" in raw ? raw.user : raw;
    return this.user;
  }

  async findAll(first, next, resultKey, firstBody, { page = 100 } = {}) {
    // IX rejects a paged search that drops its "...Z" selector on findNext.
    const carry = {};
    for (const k of Object.keys(firstBody || {})) if (k.endsWith("Z")) carry[k] = firstBody[k];
    let res = await this.call(first, firstBody);
    let rows = asList(res?.[resultKey]);
    const searchId = res?.searchId ?? null;
    try {
      while (res && res.moreResults) {
        res = await this.call(next, { searchId, idx: rows.length, max: page, ...carry });
        const chunk = asList(res?.[resultKey]);
        if (!chunk.length) break;
        rows = rows.concat(chunk);
      }
    } finally {
      if (searchId) {
        try {
          await this.call("findClose", { searchId });
        } catch {
          /* best effort */
        }
      }
    }
    return rows;
  }

  async download() {
    // The readdoc download URL is on ELO's document connector (often a
    // different host/port) and cannot be reached from the browser (CORS).
    // Do this step from the Python or Node example instead.
    throw new EloError("download() is not available in the browser - use the Python or Node snippet");
  }

  async upload() {
    throw new EloError("upload() is not available in the browser - use the Python or Node snippet");
  }

  close() {}
}

/**
 * Build a client using the config the playground page injected as
 * `window.__ELOPG__ = { credentials, mock, topicId }`, and log in.
 */
export async function connect({ login = true } = {}) {
  const cfg = (typeof window !== "undefined" && window.__ELOPG__) || {};
  const client = new EloClient({
    proxyUrl: cfg.proxyUrl || "/api/elo/proxy", // absolute when run inside the sandboxed iframe
    credentials: cfg.credentials ?? null,
    mock: !!cfg.mock,
    topicId: cfg.topicId ?? null,
    mockData: cfg.mockData ?? null, // static demo: resolve calls locally, no backend
  });
  if (login) await client.login();
  return client;
}

function asList(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === "object") return Object.values(value);
  return [];
}

// Also expose as globals so the playground's sandboxed run-iframe (which has no
// module loader) can use `connect()` / `new EloClient()` directly.
if (typeof window !== "undefined") {
  window.EloClient = EloClient;
  window.EloError = EloError;
  window.connect = connect;
}
