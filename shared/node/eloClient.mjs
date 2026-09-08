/**
 * elo-api-playground - a tiny teaching client for the ELO IX REST API (Node).
 *
 * The ELO 25 "REST" API is really an RPC mapping of the SOAP IXServicePortIF:
 *
 *     POST {baseUrl}/rest/IXServicePortIF/<method>
 *     Content-Type: application/json
 *     Authorization: Basic <base64(user:password)>     // on EVERY request
 *
 *     request body : a JSON object with the method's parameters ({} if none)
 *     response     : { "result": <value> }    on success
 *                    { "exception": <info> }  on a handled error (HTTP still 200)
 *
 * Your server publishes the authoritative schema at {baseUrl}/rest/openapi.json.
 *
 * This mirrors shared/python/elo_playground method-for-method, so the Python and
 * Node snippets read almost identically. Requires Node 18+ (global `fetch`).
 */

export class EloError extends Error {}

// Any short string; ELO records it in the session log as the "client computer".
const CLIENT_NAME = "elo-api-playground";
// Locale / timezone ELO assumes for this session (server-side formatting only).
const CI = { language: "de", country: "DE", timeZone: "Europe/Berlin" };

export class EloClient {
  /**
   * @param {string} baseUrl  IX repository root, e.g. http://localhost:9090/ix-Repository1
   * @param {string} user
   * @param {string} password
   * @param {{verify?: boolean, timeoutMs?: number}} [opts]
   */
  constructor(baseUrl, user, password, { verify = true, timeoutMs = 30000 } = {}) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this._rest = `${this.baseUrl}/rest`;
    this.userName = user;
    this._password = password;
    this._timeoutMs = timeoutMs;
    // Basic-auth header, re-sent on every request (that is what IX expects).
    this._authHeader = "Basic " + Buffer.from(`${user}:${password}`).toString("base64");
    // A minimal cookie jar - just enough to carry JSESSIONID from login() on.
    this._cookie = null;
    // Node's global fetch verifies TLS by default; there is no per-request
    // switch, so self-signed ELO certs are handled in connect() below.
    this._verify = verify;
    this.user = null;
  }

  /**
   * Make one IX RPC call and return its `result`.
   * Throws EloError on transport failure, HTTP error status, non-JSON body,
   * or an { "exception": ... } envelope.
   */
  async call(method, body = {}, { service = "IXServicePortIF" } = {}) {
    const url = `${this._rest}/${service}/${method}`;
    const headers = { "Content-Type": "application/json", Authorization: this._authHeader };
    if (this._cookie) headers.Cookie = this._cookie;

    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), this._timeoutMs);
    let resp;
    try {
      resp = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(body ?? {}),
        signal: ac.signal,
      });
    } catch (err) {
      throw new EloError(`${method}: request failed: ${err.message}`);
    } finally {
      clearTimeout(timer);
    }

    // Remember the session cookie the first time IX sets it.
    const setCookie = resp.headers.get("set-cookie");
    if (setCookie) this._cookie = setCookie.split(";")[0];

    if (resp.status === 401 || resp.status === 403) {
      throw new EloError(
        `${method}: authentication failed (HTTP ${resp.status}) - check user / password`
      );
    }
    if (resp.status >= 400) {
      throw new EloError(`${method}: HTTP ${resp.status} - ${(await resp.text()).slice(0, 200)}`);
    }

    let data;
    try {
      data = await resp.json();
    } catch {
      throw new EloError(`${method}: response body was not JSON`);
    }
    if (data && typeof data === "object" && data.exception) {
      throw new EloError(`${method}: ${exceptionText(data.exception)}`);
    }
    if (data && typeof data === "object" && "result" in data) return data.result;
    return data;
  }

  /** Open an IX session; returns the logged-in UserInfo (also on `this.user`). */
  async login() {
    const result = await this.call("login", {
      userName: this.userName,
      userPwd: this._password,
      clientComputer: CLIENT_NAME,
      runAsUser: "",
      ci: CI,
    });
    this.user =
      result && typeof result === "object" && "user" in result ? result.user : result;
    return this.user;
  }

  /**
   * Drive a findFirst<X> / findNext<X> / findClose loop to the end.
   * `resultKey` is the field holding the rows, e.g. "sords" or "sortedResult".
   */
  async findAll(first, next, resultKey, firstBody, { page = 100 } = {}) {
    // IX rejects a paged search that drops its "...Z" selector on findNext
    // ("Incorrect parameter: sordZ==null"), so carry those forward.
    const carry = {};
    for (const k of Object.keys(firstBody || {})) if (k.endsWith("Z")) carry[k] = firstBody[k];
    let res = await this.call(first, firstBody);
    let rows = asList(res?.[resultKey]);
    const searchId = res?.searchId ?? null;
    try {
      while (res && res.moreResults) {
        res = await this.call(next, { searchId, idx: rows.length, max: page, ...carry });
        const chunk = asList(res?.[resultKey]);
        if (chunk.length === 0) break;
        rows = rows.concat(chunk);
      }
    } finally {
      if (searchId) {
        try {
          await this.call("findClose", { searchId });
        } catch {
          /* best effort - the search times out server-side anyway */
        }
      }
    }
    return rows;
  }

  /**
   * GET a document's bytes from a checkoutDoc download URL, reusing this
   * authenticated session. Returns UTF-8 text, capped at maxBytes.
   */
  async download(url, { maxBytes = 200000 } = {}) {
    const headers = { Authorization: this._authHeader };
    if (this._cookie) headers.Cookie = this._cookie;
    let resp;
    try {
      resp = await fetch(url, { headers });
    } catch (err) {
      throw new EloError(`download: request failed: ${err.message}`);
    }
    if (resp.status >= 400) throw new EloError(`download: HTTP ${resp.status}`);
    const buf = Buffer.from(await resp.arrayBuffer());
    return buf.subarray(0, maxBytes).toString("utf-8");
  }

  /**
   * POST document bytes to a checkinDocBegin upload URL, reusing this session.
   * Returns the server's upload-result token for document.docs[0].uploadResult.
   */
  async upload(url, data) {
    const headers = { Authorization: this._authHeader };
    if (this._cookie) headers.Cookie = this._cookie;
    let resp;
    try {
      resp = await fetch(url, { method: "POST", headers, body: data });
    } catch (err) {
      throw new EloError(`upload: request failed: ${err.message}`);
    }
    if (resp.status >= 400) throw new EloError(`upload: HTTP ${resp.status}`);
    return await resp.text();
  }

  close() {
    /* global fetch keeps no pool we need to close */
  }
}

/** Offline stand-in - same surface, canned responses. See mock map format in
 * shared/python/elo_playground/mock.py. */
export class MockEloClient {
  constructor(data = {}) {
    this._data = data;
    this._calls = {};
    this.baseUrl = "mock://elo";
    this.userName = "Administrator";
    this.user = null;
  }

  close() {}

  async call(method) {
    if (!(method in this._data)) {
      throw new EloError(
        `${method}: no mock response configured - add it to the topic's 'mock:' block`
      );
    }
    let entry = this._data[method];
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
    const raw = "login" in this._data ? await this.call("login") : { id: 0, name: "Administrator" };
    this.user = raw && typeof raw === "object" && "user" in raw ? raw.user : raw;
    return this.user;
  }

  async download() {
    const entry = this._data._download ?? '{"version": 3, "ocr": true}';
    return typeof entry === "string" ? entry : JSON.stringify(entry);
  }

  async upload() {
    return this._data._upload ?? "MOCK-UPLOAD-TOKEN";
  }

  async findAll(first, next, resultKey, firstBody, { page = 100 } = {}) {
    const carry = {};
    for (const k of Object.keys(firstBody || {})) if (k.endsWith("Z")) carry[k] = firstBody[k];
    let res = await this.call(first, firstBody);
    let rows = asList(res?.[resultKey]);
    const searchId = res?.searchId ?? null;
    while (res && res.moreResults) {
      res = await this.call(next, { searchId, idx: rows.length, max: page, ...carry });
      const chunk = asList(res?.[resultKey]);
      if (!chunk.length) break;
      rows = rows.concat(chunk);
    }
    return rows;
  }
}

/**
 * Build a client from environment variables and (by default) log in.
 * Same variables as the Python `connect()`:
 *   ELOPG_MOCK, ELOPG_MOCK_DATA, ELOPG_ELO_BASE_URL, ELOPG_ELO_USER,
 *   ELOPG_ELO_PASSWORD, ELOPG_TLS_VERIFY
 */
export async function connect({ login = true } = {}) {
  const env = process.env;

  if (truthy(env.ELOPG_MOCK)) {
    let data = {};
    if (env.ELOPG_MOCK_DATA) {
      const { readFileSync } = await import("node:fs");
      try {
        data = JSON.parse(readFileSync(env.ELOPG_MOCK_DATA, "utf-8"));
      } catch {
        /* leave the map empty; call() will explain which method is missing */
      }
    }
    const client = new MockEloClient(data);
    if (login) await client.login();
    return client;
  }

  const verify = !falsy(env.ELOPG_TLS_VERIFY);
  if (!verify) {
    // Node's fetch has no per-request "insecure" switch. This is the documented
    // escape hatch; acceptable for a local learning tool against a self-signed
    // ELO, never for production.
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
  }
  const client = new EloClient(
    env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1",
    env.ELOPG_ELO_USER || "Administrator",
    env.ELOPG_ELO_PASSWORD || "",
    { verify }
  );
  if (login) await client.login();
  return client;
}

// ---- small helpers ---------------------------------------------------- //
function asList(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === "object") return Object.values(value);
  return [];
}

function exceptionText(exc) {
  let text =
    exc && typeof exc === "object"
      ? exc.message || exc.Exception || JSON.stringify(exc)
      : String(exc);
  return text.replace(/\[TICKET:[^\]]*\]|\[(?:NO-)?DETAILS[^\]]*\]/g, "").trim();
}

function truthy(v) {
  return ["1", "true", "yes", "on"].includes(String(v ?? "").trim().toLowerCase());
}

function falsy(v) {
  return ["0", "false", "no", "off"].includes(String(v ?? "").trim().toLowerCase());
}
