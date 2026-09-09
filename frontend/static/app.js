"use strict";
/* ELO API Playground - single-page frontend (no build step, plain ES).
 *
 * Layout:
 *   - a connection form + Mock toggle in the top bar (kept in localStorage)
 *   - a language switch (EN / DE / ES)
 *   - two tabs: Catalog (nav tree + topic panels) and Scratchpad (free editor)
 *   - every code block gets Copy + Run:
 *       python / node  -> POST /api/run  (executed on the backend)
 *       browser        -> executed here, inside a sandboxed <iframe>
 */
(function () {
  const CFG = window.__PLAYGROUND__ || {};
  const LS = {
    conn: "elopg.conn.v1",
    lang: "elopg.lang",
    topic: "elopg.topic", // "t:<id>" or "d:<categoryId>"
    sub: "elopg.sublang", // last used snippet tab (python|node|browser)
  };
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const store = {
    get(k, dflt) {
      try {
        return localStorage.getItem(k) ?? dflt;
      } catch (e) {
        return dflt;
      }
    },
    set(k, v) {
      try {
        localStorage.setItem(k, v);
      } catch (e) {
        /* private mode - ignore */
      }
    },
  };

  let T = {}; // i18n dictionary
  let LANG = store.get(LS.lang, "en");
  if (!["en", "de", "es"].includes(LANG)) LANG = "en";
  let BROWSER_CLIENT_SRC = null; // cached source of eloClient.browser.js

  // "static demo" mode: no backend - baked JSON under ./api/ and a run cache
  const STATIC = !!CFG.staticMode;
  let RUN_CACHE = {}; // key "t:<id>|<lang>" / "d:<cat>#<i>|<lang>" -> RunResult
  let CURRENT_MOCK = null; // merged mock:{} of the open topic/deep, for the browser JS mock

  // map a former "/api/..." endpoint to its baked static file
  function toStatic(url) {
    const [path, qs] = url.split("?");
    const p = new URLSearchParams(qs || "");
    const lang = p.get("lang") || LANG;
    let m;
    if (path === "/api/catalog") return `api/catalog/${lang}.json`;
    if ((m = path.match(/^\/api\/i18n\/(.+)$/))) return `api/i18n/${m[1]}.json`;
    if ((m = path.match(/^\/api\/topics\/(.+)$/))) return `api/topics/${lang}/${m[1]}.json`;
    if ((m = path.match(/^\/api\/deep\/(.+)$/))) return `api/deep/${m[1]}.json`;
    if (path === "/api/version") return "api/version.json";
    if (path === "/api/faq") return "api/faq.json";
    if (path === "/api/client-lib") return "api/client-lib.json";
    if (path === "/api/spec/services") return "api/spec/services.json";
    if (path === "/api/spec/operations") return `api/spec/operations/${p.get("service")}.json`;
    if ((m = path.match(/^\/api\/spec\/op\/(.+)$/))) return `api/spec/op/${m[1]}.json`;
    return url;
  }

  // ---- small fetch helpers ------------------------------------------- //
  async function getJSON(url) {
    const target = STATIC && url.startsWith("/api/") ? toStatic(url) : url;
    const r = await fetch(target);
    if (!r.ok) throw new Error(`${target} -> HTTP ${r.status}`);
    return r.json();
  }
  async function postJSON(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return r.json();
  }

  // ---- connection state -------------------------------------------- //
  const DEFAULT_PORT = "9090"; // ELO Indexserver default (HTTP)

  // combine the "Base URL" field with the separate "Port" field
  function effectiveBaseUrl() {
    const f = $("#conn");
    let raw = (f.base_url.value || "").trim();
    if (!raw) return "";
    if (!/^https?:\/\//i.test(raw)) raw = "http://" + raw;
    let u;
    try {
      u = new URL(raw);
    } catch (e) {
      return raw;
    }
    const port = (f.port.value || "").trim();
    if (port) u.port = port;
    return `${u.protocol}//${u.hostname}${u.port ? ":" + u.port : ""}${u.pathname}`.replace(/\/$/, "");
  }

  function readConn() {
    const f = $("#conn");
    return {
      base_url: effectiveBaseUrl(),
      port: (f.port.value || "").trim(),
      user: f.user.value.trim(),
      password: f.password.value,
      tls_verify: f.tls_verify.checked,
      mock: f.mock.checked,
      remember: f.remember.checked,
    };
  }
  function creds() {
    const c = readConn();
    return { base_url: c.base_url, user: c.user, password: c.password, tls_verify: c.tls_verify };
  }
  function isMock() {
    return $("#conn").mock.checked;
  }
  function saveConn() {
    const f = $("#conn");
    const c = readConn();
    const blob = {
      base_url: f.base_url.value.trim(), // store what the user typed, not the assembled URL
      port: c.port,
      user: c.user,
      tls_verify: c.tls_verify,
      mock: c.mock,
      remember: c.remember,
    };
    if (c.remember) blob.password = c.password;
    store.set(LS.conn, JSON.stringify(blob));
  }
  function loadConn() {
    let blob = {};
    try {
      blob = JSON.parse(store.get(LS.conn, "{}"));
    } catch (e) {
      blob = {};
    }
    const f = $("#conn");
    f.base_url.value = blob.base_url || CFG.defaultBaseUrl || "";
    f.port.value = blob.port || CFG.defaultPort || DEFAULT_PORT;
    f.user.value = blob.user || CFG.defaultUser || "Administrator";
    // password: a remembered one wins; then a local .env (ELOPG_ELO_PASSWORD);
    // then the stock local test password. Overridden by whatever you type.
    f.password.value = blob.password || CFG.defaultPassword || "elo";
    f.tls_verify.checked = blob.tls_verify !== false;
    f.mock.checked = blob.mock != null ? !!blob.mock : !!CFG.mockDefault;
    f.remember.checked = !!blob.remember;
  }

  // ---- i18n ------------------------------------------------------- //
  async function loadI18n(lang) {
    try {
      T = await getJSON("/api/i18n/" + lang);
    } catch (e) {
      T = {};
    }
  }
  function applyI18n() {
    document.documentElement.lang = LANG;
    $$("[data-t]").forEach((el) => {
      const v = T[el.dataset.t];
      if (v) el.textContent = v;
    });
    $$("[data-t-title]").forEach((el) => {
      const v = T[el.dataset.tTitle];
      if (v) el.title = v;
    });
  }
  const tr = (k) => T[k] || k;

  async function renderVersion() {
    const el = $("#app-version");
    if (!el) return;
    try {
      const v = await getJSON("/api/version");
      el.textContent = `UI ${v.frontend} · API ${v.backend}`;
      el.title = `frontend ${v.frontend} / backend ${v.backend}`;
    } catch (e) {
      /* leave it blank */
    }
  }

  // ---- highlight helpers ------------------------------------------ //
  function looksJson(text) {
    const t = (text || "").trim();
    return (t.startsWith("{") && t.endsWith("}")) || (t.startsWith("[") && t.endsWith("]"));
  }
  // set a language class on a <code> element and run highlight.js over it
  function highlightBlock(codeEl, text, preferJson) {
    if (!codeEl) return;
    codeEl.className = preferJson || looksJson(text) ? "language-json" : "language-plaintext";
    if (window.hljs) window.hljs.highlightElement(codeEl);
  }
  // if `text` is a single JSON value, return it pretty-printed + hl'd HTML, else null
  function jsonHighlightHtml(text) {
    const t = (text || "").trim();
    if (!looksJson(t) || !window.hljs) return null;
    try {
      const pretty = JSON.stringify(JSON.parse(t), null, 2);
      return window.hljs.highlight(pretty, { language: "json" }).value;
    } catch (e) {
      return null;
    }
  }

  async function setLang(lang) {
    LANG = lang;
    store.set(LS.lang, lang);
    $$(".lang").forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
    await loadI18n(lang);
    applyI18n();
    await loadCatalog();
    reopenLast();
    SPEC_LOADED = false; // re-render the API-reference tab (labels) on next visit
    if (!$("#view-spec").hidden) loadSpec(true);
  }

  // ---- Run: backend (python / node) ------------------------------ //
  async function runBackend(language, code, topicId, outputEl, metaEl, btn, cacheKey) {
    const label = btn ? btn.textContent : "";
    if (btn) {
      btn.disabled = true;
      btn.textContent = tr("run.running");
    }
    outputEl.textContent = "";
    outputEl.className = "output";
    if (metaEl) metaEl.textContent = "";

    if (STATIC) {
      const cached = isMock() && cacheKey && RUN_CACHE[cacheKey + "|" + language];
      if (cached) {
        renderRunResult(cached, outputEl, metaEl);
        if (metaEl) metaEl.textContent += " · " + tr("static.precomputed");
      } else {
        outputEl.textContent = isMock() ? tr("static.noRun") : tr("static.backendOnly");
        outputEl.classList.add("err");
      }
      if (btn) {
        btn.disabled = false;
        btn.textContent = label;
      }
      return;
    }

    try {
      const res = await postJSON("/api/run", {
        language,
        code,
        mock: isMock(),
        topic_id: topicId || null,
        credentials: isMock() ? null : creds(),
      });
      renderRunResult(res, outputEl, metaEl);
    } catch (e) {
      outputEl.textContent = String(e);
      outputEl.classList.add("err");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = label;
      }
    }
  }

  function renderRunResult(res, outputEl, metaEl) {
    if (res.detail) {
      outputEl.textContent = "! " + res.detail + (res.stderr ? "\n\n" + res.stderr : "");
      outputEl.classList.add("err");
    } else {
      const parts = [];
      if (res.stdout) parts.push(res.stdout.replace(/\n$/, ""));
      if (res.stderr) parts.push((parts.length ? "\n--- stderr ---\n" : "") + res.stderr.replace(/\n$/, ""));
      const text = parts.join("\n") || "(no output)";
      const jsonHtml = res.ok && !res.stderr ? jsonHighlightHtml(res.stdout) : null;
      if (jsonHtml) {
        outputEl.innerHTML = jsonHtml;
      } else {
        outputEl.textContent = text;
      }
      outputEl.classList.toggle("hljs", !!jsonHtml);
      outputEl.classList.toggle("err", !res.ok);
    }
    if (metaEl) {
      const bits = [];
      if (res.exit_code != null) bits.push("exit " + res.exit_code);
      if (res.duration_ms != null) bits.push(res.duration_ms + " ms");
      metaEl.textContent = bits.join(" · ");
    }
  }

  // ---- Run: browser (sandboxed iframe) -------------------------- //
  async function loadBrowserClientSrc() {
    if (BROWSER_CLIENT_SRC == null) {
      const u = STATIC ? "client/eloClient.browser.js" : "/client/eloClient.browser.js";
      BROWSER_CLIENT_SRC = await (await fetch(u)).text();
    }
    return BROWSER_CLIENT_SRC;
  }

  async function runBrowser(code, topicId, outputEl, metaEl, btn) {
    const label = btn ? btn.textContent : "";
    if (btn) {
      btn.disabled = true;
      btn.textContent = tr("run.running");
    }
    outputEl.textContent = "";
    outputEl.className = "output";
    if (metaEl) metaEl.textContent = "";

    const clientSrc = await loadBrowserClientSrc();
    const mock = isMock();
    const config = {
      proxyUrl: CFG.proxyUrl,
      credentials: mock ? null : creds(),
      mock,
      topicId: topicId || null,
      // static demo: mock -> resolve locally; not mock -> call the given ELO directly
      mockData: STATIC && mock ? CURRENT_MOCK : null,
      directUrl: STATIC && !mock ? (creds().base_url || null) : null,
    };
    const srcdoc = buildIframeDoc(clientSrc, config, code);

    const frame = document.createElement("iframe");
    frame.setAttribute("sandbox", "allow-scripts");
    frame.style.display = "none";
    const started = performance.now();
    let settled = false;

    const onMsg = (ev) => {
      const d = ev.data;
      if (!d || !d.__elopg) return;
      if (d.done) {
        settled = true;
        if (metaEl) metaEl.textContent = Math.round(performance.now() - started) + " ms";
        outputEl.classList.toggle("err", !d.ok);
        if (!outputEl.textContent) outputEl.textContent = d.ok ? "(no output)" : "(failed)";
        if (d.ok && !outputEl.classList.contains("err")) {
          const jsonHtml = jsonHighlightHtml(outputEl.textContent);
          if (jsonHtml) outputEl.innerHTML = jsonHtml;
        }
        cleanup();
        return;
      }
      const line = (d.level === "error" ? "! " : "") + d.text + "\n";
      outputEl.textContent += line;
      if (d.level === "error") outputEl.classList.add("err");
    };
    function cleanup() {
      window.removeEventListener("message", onMsg);
      setTimeout(() => frame.remove(), 50);
      if (btn) {
        btn.disabled = false;
        btn.textContent = label;
      }
    }
    window.addEventListener("message", onMsg);
    setTimeout(() => {
      if (!settled) {
        outputEl.textContent += "! timed out (15s)\n";
        outputEl.classList.add("err");
        cleanup();
      }
    }, 15000);

    frame.srcdoc = srcdoc;
    document.body.appendChild(frame);
  }

  function buildIframeDoc(clientSrc, config, snippet) {
    return `<!doctype html><meta charset="utf-8"><script type="module">
window.__ELOPG__ = ${JSON.stringify(config)};
const fmt = (v) => { try { return typeof v === "string" ? v : JSON.stringify(v); } catch (e) { return String(v); } };
const post = (level, args) => parent.postMessage({ __elopg: true, level, text: args.map(fmt).join(" ") }, "*");
["log", "info", "warn", "error"].forEach((k) => {
  const orig = console[k] ? console[k].bind(console) : function(){};
  console[k] = (...a) => { orig(...a); post(k === "info" ? "log" : k, a); };
});
window.addEventListener("error", (e) => post("error", [e.message]));
window.addEventListener("unhandledrejection", (e) => post("error", [String(e.reason && e.reason.stack || e.reason)]));
${clientSrc}
(async () => {
  try {
${snippet}
    parent.postMessage({ __elopg: true, done: true, ok: true }, "*");
  } catch (err) {
    post("error", [String(err && err.stack || err)]);
    parent.postMessage({ __elopg: true, done: true, ok: false }, "*");
  }
})();
<\/script>`;
  }

  function runAny(language, code, topicId, outputEl, metaEl, btn, cacheKey) {
    if (language === "browser") return runBrowser(code, topicId, outputEl, metaEl, btn);
    return runBackend(language, code, topicId, outputEl, metaEl, btn, cacheKey);
  }

  // ---- catalogue nav ------------------------------------------- //
  async function loadCatalog() {
    const data = await getJSON("/api/catalog?lang=" + LANG);
    const nav = $("#catnav");
    nav.innerHTML = "";

    // pinned first: the shared client every snippet imports
    const libBox = document.createElement("div");
    libBox.className = "catgroup";
    libBox.innerHTML = `<button class="topiclink lib" data-lib="1">▸ ${esc(tr("nav.clientLib"))}</button>`;
    nav.appendChild(libBox);

    for (const cat of data.categories) {
      const box = document.createElement("div");
      box.className = "catgroup";
      box.innerHTML = `<div class="catname">${esc(cat.title)}</div>`;
      const ul = document.createElement("ul");
      for (const topic of cat.topics) {
        const li = document.createElement("li");
        li.innerHTML = `<button class="topiclink" data-topic="${esc(topic.id)}">${esc(topic.title)}</button>`;
        ul.appendChild(li);
      }
      if (cat.has_deep) {
        const li = document.createElement("li");
        li.innerHTML = `<button class="topiclink deep" data-deep="${esc(cat.id)}">▸ ${esc(tr("deep.open"))}</button>`;
        ul.appendChild(li);
      }
      box.appendChild(ul);
      nav.appendChild(box);
    }
  }

  function markActiveNav(selector) {
    $$(".topiclink").forEach((b) => b.classList.remove("active"));
    const el = $(selector);
    if (el) el.classList.add("active");
  }

  function docLink(ref) {
    const base = (effectiveBaseUrl() || CFG.defaultBaseUrl || "").replace(/\/+$/, "");
    return (ref.doc_url || "").replace("{base}", base);
  }

  // {base}-templated link to ELO's own API docs; empty when no server is known
  function eloDocHref(tmpl) {
    const base = (effectiveBaseUrl() || CFG.defaultBaseUrl || "").replace(/\/+$/, "");
    if (!base || !tmpl) return "";
    return tmpl.replace("{base}", base);
  }

  async function openTopic(id) {
    store.set(LS.topic, "t:" + id);
    markActiveNav(`.topiclink[data-topic="${cssEsc(id)}"]`);
    const host = $("#topic-host");
    host.innerHTML = `<p class="hint">${esc(tr("run.running"))}</p>`;
    let topic;
    try {
      topic = await getJSON("/api/topics/" + encodeURIComponent(id) + "?lang=" + LANG);
    } catch (e) {
      host.innerHTML = `<p class="err">${esc(String(e))}</p>`;
      return;
    }
    CURRENT_MOCK = topic.mock || null; // for browser snippets in static mode

    const apiRows = (topic.elo_api || [])
      .map(
        (r) => `<tr>
          <td><code>${esc(r.method)}</code></td>
          <td><code>${esc(r.rpc)}</code></td>
          <td><a href="${esc(docLink(r))}" target="_blank" rel="noopener">${esc(tr("topic.docs"))}</a>${
            r.spec
              ? ` <button class="link xref-op" data-op="${esc(r.spec.replace("/", "_"))}">${esc(r.spec)}</button>`
              : ""
          }</td>
          <td>${esc(r.notes || "")}</td>
        </tr>`
      )
      .join("");

    const langs = ["python", "node", "browser"].filter((k) => (topic.snippets || {})[k]);
    const tabs = langs
      .map((k) => `<button class="sub" data-lang="${k}">${esc(tr("tab." + k))}</button>`)
      .join("");

    host.innerHTML = `
      <article class="topic">
        <h1>${esc(topic.title)}</h1>
        <p class="summary">${esc(topic.summary)}</p>

        <h2>${esc(tr("topic.apiUsed"))}</h2>
        <table class="apitable">
          <thead><tr>
            <th>${esc(tr("topic.method"))}</th><th>${esc(tr("topic.rpc"))}</th>
            <th>${esc(tr("topic.docs"))}</th><th>${esc(tr("topic.notes"))}</th>
          </tr></thead>
          <tbody>${apiRows}</tbody>
        </table>

        ${
          topic.result_shape
            ? `<h2>${esc(tr("topic.resultShape"))}</h2><pre class="shape"><code>${esc(topic.result_shape)}</code></pre>`
            : ""
        }

        <div class="subtabs">${tabs}</div>
        <div class="snippet-host"></div>
      </article>`;

    host.querySelectorAll(".xref-op").forEach((b) =>
      b.addEventListener("click", () => {
        $('.tab[data-view="spec"]').click();
        openOperation(b.dataset.op);
      })
    );

    // syntax-highlight the "Result shape" block (JSON when it looks like it)
    highlightBlock(host.querySelector("pre.shape code"), topic.result_shape);

    const sub = host.querySelector(".subtabs");
    const snipHost = host.querySelector(".snippet-host");
    function showLang(lang) {
      store.set(LS.sub, lang);
      $$(".sub", sub).forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
      snipHost.innerHTML = "";
      snipHost.appendChild(makeRunner(lang, topic.snippets[lang], topic.id, "t:" + topic.id));
    }
    sub.addEventListener("click", (ev) => {
      const b = ev.target.closest(".sub");
      if (b) showLang(b.dataset.lang);
    });
    if (langs.length) {
      const preferred = store.get(LS.sub, "python");
      showLang(langs.includes(preferred) ? preferred : langs[0]);
    } else {
      snipHost.innerHTML = `<p class="hint">No snippet for this topic yet.</p>`;
    }
  }

  // ---- "functions used in this snippet" list ------------------- //
  const ELO_CLIENT_METHODS = new Set(["call", "login", "find_all", "findAll", "download", "upload", "close"]);
  const PY_JSON = new Set(["loads", "dumps", "load", "dump"]);
  const PY_BUILTINS = new Set(
    ("print len range enumerate sorted reversed list dict set tuple str int float bool min max sum abs zip map " +
      "filter open repr type isinstance getattr hasattr format any all round input").split(" ")
  );
  const JS_OBJECTS = new Set(["console", "JSON", "Object", "Array", "Math", "Number", "String", "Promise", "Date"]);
  const JS_PROTO_METHODS = new Set(
    ("forEach map filter slice splice join split push pop shift unshift find findIndex sort reverse concat includes " +
      "indexOf lastIndexOf reduce some every keys values entries replace replaceAll trim trimStart trimEnd toUpperCase " +
      "toLowerCase padStart padEnd repeat flat flatMap at fill match matchAll startsWith endsWith toString toFixed").split(" ")
  );
  const MDN_GLOBAL = "https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/";
  const JS_GLOBAL_FN = {
    btoa: "https://developer.mozilla.org/docs/Web/API/btoa",
    atob: "https://developer.mozilla.org/docs/Web/API/atob",
    fetch: "https://developer.mozilla.org/docs/Web/API/fetch",
    setTimeout: "https://developer.mozilla.org/docs/Web/API/setTimeout",
    structuredClone: "https://developer.mozilla.org/docs/Web/API/structuredClone",
    parseInt: MDN_GLOBAL + "parseInt",
    parseFloat: MDN_GLOBAL + "parseFloat",
    isNaN: MDN_GLOBAL + "isNaN",
    encodeURIComponent: MDN_GLOBAL + "encodeURIComponent",
    decodeURIComponent: MDN_GLOBAL + "decodeURIComponent",
  };
  function jsObjUrl(obj, meth) {
    if (obj === "console") return "https://developer.mozilla.org/docs/Web/API/console/" + meth + "_static";
    return MDN_GLOBAL + obj + "/" + meth;
  }

  // scan `code` for  function(...)  and  object.method(...)  calls and classify
  // each: ELO client methods and ELO IX operation names link into this site,
  // generic JS / Python builtins link to MDN / docs.python.org (new tab).
  function refsFromCode(code, language) {
    const seen = new Set();
    const out = [];
    const add = (label, kind, target) => {
      if (seen.has(label)) return;
      seen.add(label);
      out.push({ label, kind, target });
    };
    let m;

    // 1. ELO IX operations, named as string literals to elo.call / find_all
    const callRe = /\.call\(\s*(["'])([A-Za-z][\w]*)\1/g;
    while ((m = callRe.exec(code))) add(m[2] + "()", "elo-op", m[2]);
    const faRe = /\.(?:find_all|findAll)\(\s*(["'])([A-Za-z][\w]*)\1\s*,\s*(["'])([A-Za-z][\w]*)\3/g;
    while ((m = faRe.exec(code))) {
      add(m[2] + "()", "elo-op", m[2]);
      add(m[4] + "()", "elo-op", m[4]);
    }

    // 2. member calls  obj.method(
    const memRe = /\b([A-Za-z_$][\w$]*)\.([A-Za-z_$][\w$]*)\s*\(/g;
    while ((m = memRe.exec(code))) {
      const obj = m[1];
      const meth = m[2];
      if (obj === "elo" && ELO_CLIENT_METHODS.has(meth)) add("elo." + meth + "()", "elo-lib", null);
      else if (language === "python" && obj === "json" && PY_JSON.has(meth))
        add("json." + meth + "()", "py", "json.html#json." + meth);
      else if (obj === "Buffer")
        add("Buffer." + meth + "()", "mdn", "https://nodejs.org/api/buffer.html");
      else if (JS_OBJECTS.has(obj)) add(obj + "." + meth + "()", "mdn", jsObjUrl(obj, meth));
      else if (language !== "python" && JS_PROTO_METHODS.has(meth))
        add(obj + "." + meth + "()", "mdn", MDN_GLOBAL + "Array/" + meth);
    }

    // 3. bare calls  name(
    const bareRe = /(?:^|[^.\w$])([A-Za-z_$][\w$]*)\s*\(/g;
    while ((m = bareRe.exec(code))) {
      const name = m[1];
      if (name === "connect") add("connect()", "elo-lib", null);
      else if (language === "python" && PY_BUILTINS.has(name)) add(name + "()", "py", "functions.html#" + name);
      else if (language !== "python" && JS_GLOBAL_FN[name]) add(name + "()", "mdn", JS_GLOBAL_FN[name]);
    }
    return out;
  }

  // (re)fill a .fn-refs host with the "functions used in this snippet" list
  function renderFnRefs(hostEl, code, language) {
    const refs = refsFromCode(code, language);
    hostEl.hidden = !refs.length;
    if (!refs.length) {
      hostEl.innerHTML = "";
      return;
    }
    const item = (r) => {
      if (r.kind === "elo-op")
        return `<button class="fn-ref link" data-op="IXServicePortIF_${esc(r.target)}">${esc(r.label)}</button>`;
      if (r.kind === "elo-lib") return `<button class="fn-ref link" data-lib="1">${esc(r.label)}</button>`;
      const href = r.kind === "py" ? "https://docs.python.org/3/library/" + r.target : r.target;
      return `<a class="fn-ref" href="${esc(href)}" target="_blank" rel="noopener">${esc(r.label)}</a>`;
    };
    hostEl.innerHTML =
      `<span class="fn-refs-label">${esc(tr("topic.fnRefs"))}</span> ` +
      refs.map(item).join(' <span class="fn-sep">·</span> ');
    hostEl.querySelectorAll("[data-op]").forEach((b) =>
      b.addEventListener("click", () => {
        $('.tab[data-view="spec"]').click();
        openOperation(b.dataset.op);
      })
    );
    hostEl.querySelectorAll("[data-lib]").forEach((b) =>
      b.addEventListener("click", () => {
        $('.tab[data-view="catalog"]').click();
        openClientLib();
      })
    );
  }

  // one EDITABLE code block + Copy + Reset + Run + output panel
  function makeRunner(language, code, topicId, cacheKey) {
    const original = code;
    const cmMode = language === "python" ? "python" : "javascript";
    const wrap = document.createElement("div");
    wrap.className = "runner";
    wrap.innerHTML = `
      <div class="code-head">
        <span class="lang-badge">${esc(language)}</span>
        <button class="run">${esc(tr("run.button"))}</button>
        <button class="copy" data-t-title="action.copy" title="Copy">${esc(tr("action.copy"))}</button>
        <button class="reset" title="${esc(tr("action.reset"))}" hidden>${esc(tr("action.reset"))}</button>
        <span class="edited-flag" hidden>${esc(tr("code.edited"))}</span>
        <span class="warn-inline">${language !== "browser" ? esc(tr("warn.localOnly")) : ""}</span>
      </div>
      <div class="code-edit"></div>
      <div class="output-wrap">
        <div class="output-head"><span>${esc(tr("topic.output"))}</span><span class="meta"></span></div>
        <pre class="output"></pre>
      </div>
      <div class="fn-refs" hidden></div>`;

    const editHost = wrap.querySelector(".code-edit");
    const btn = wrap.querySelector(".run");
    const copyBtn = wrap.querySelector(".copy");
    const resetBtn = wrap.querySelector(".reset");
    const editedFlag = wrap.querySelector(".edited-flag");
    const out = wrap.querySelector(".output");
    const meta = wrap.querySelector(".meta");
    const fnHost = wrap.querySelector(".fn-refs");

    // --- the editor: CodeMirror when available, <textarea> otherwise -----
    let getCode;
    let setCode;
    let cm = null;
    if (window.CodeMirror) {
      cm = window.CodeMirror(editHost, {
        value: code,
        mode: cmMode,
        lineNumbers: true,
        indentUnit: 2,
        tabSize: 2,
        viewportMargin: Infinity, // grow to fit the snippet
      });
      getCode = () => cm.getValue();
      setCode = (v) => cm.setValue(v);
    } else {
      const ta = document.createElement("textarea");
      ta.className = "code code-textarea";
      ta.spellcheck = false;
      ta.value = code;
      ta.rows = Math.min(30, code.split("\n").length + 1);
      editHost.appendChild(ta);
      getCode = () => ta.value;
      setCode = (v) => {
        ta.value = v;
        ta.rows = Math.min(30, v.split("\n").length + 1);
      };
    }
    const isEdited = () => getCode() !== original;

    let refsTimer = 0;
    function refreshMeta() {
      const edited = isEdited();
      resetBtn.hidden = !edited;
      editedFlag.hidden = !edited;
      clearTimeout(refsTimer);
      refsTimer = setTimeout(() => renderFnRefs(fnHost, getCode(), language), 300);
    }
    if (cm) cm.on("change", refreshMeta);
    else editHost.querySelector("textarea").addEventListener("input", refreshMeta);

    // --- buttons -------------------------------------------------------
    btn.addEventListener("click", () =>
      // a pre-computed static result only matches the ORIGINAL snippet
      runAny(language, getCode(), topicId, out, meta, btn, isEdited() ? null : cacheKey)
    );
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(getCode());
        const prev = copyBtn.textContent;
        copyBtn.textContent = tr("action.copied");
        setTimeout(() => (copyBtn.textContent = prev), 1200);
      } catch (e) {
        /* clipboard blocked - ignore */
      }
    });
    resetBtn.addEventListener("click", () => {
      setCode(original);
      if (cm) cm.refresh();
      refreshMeta();
    });

    renderFnRefs(fnHost, code, language);
    if (cm) setTimeout(() => cm.refresh(), 0); // settle layout when first shown
    return wrap;
  }

  async function openDeep(catId) {
    store.set(LS.topic, "d:" + catId);
    markActiveNav(`.topiclink[data-deep="${cssEsc(catId)}"]`);
    const host = $("#topic-host");
    host.innerHTML = `<p class="hint">${esc(tr("run.running"))}</p>`;
    let data;
    try {
      data = await getJSON("/api/deep/" + encodeURIComponent(catId));
    } catch (e) {
      host.innerHTML = `<p class="err">${esc(String(e))}</p>`;
      return;
    }
    CURRENT_MOCK = data.mock || null; // for browser snippets in static mode
    const html = window.DOMPurify.sanitize(window.marked.parse(data.markdown, { breaks: false }));
    host.innerHTML = `<article class="topic deepdoc">${html}</article>`;

    // Turn each fenced code block into a runnable snippet.
    let bi = -1; // index among python/node/browser blocks (matches build_static)
    $$("pre code", host).forEach((codeEl) => {
      const cls = codeEl.className || "";
      let language = null;
      if (/language-python/.test(cls)) language = "python";
      else if (/language-js|language-javascript/.test(cls)) language = "node";
      else if (/language-browser/.test(cls)) language = "browser";
      if (!language) {
        if (window.hljs) window.hljs.highlightElement(codeEl);
        return;
      }
      bi += 1;
      const pre = codeEl.closest("pre");
      pre.replaceWith(makeRunner(language, codeEl.textContent.replace(/\n$/, ""), catId, `d:${catId}#${bi}`));
    });
  }

  // the shared client every snippet imports
  async function openClientLib() {
    store.set(LS.topic, "lib");
    markActiveNav(".topiclink.lib");
    const host = $("#topic-host");
    host.innerHTML = `<p class="hint">${esc(tr("run.running"))}</p>`;
    let data;
    try {
      data = await getJSON("/api/client-lib");
    } catch (e) {
      host.innerHTML = `<p class="err">${esc(String(e))}</p>`;
      return;
    }
    const langs = ["python", "node", "browser"].filter((k) => (data[k] || []).length);
    const tabs = langs.map((k) => `<button class="sub" data-lang="${k}">${esc(tr("tab." + k))}</button>`).join("");
    const row = (m, d) => `<tr><td><code>${esc(m)}</code></td><td>${esc(tr(d))}</td></tr>`;
    host.innerHTML = `
      <article class="topic">
        <h1>${esc(tr("nav.clientLib"))}</h1>
        <p class="summary">${esc(tr("lib.intro"))}</p>
        <h2>${esc(tr("lib.methods"))}</h2>
        <table class="apitable"><tbody>
          ${row("connect()", "lib.m.connect")}
          ${row("elo.call(method, body)", "lib.m.call")}
          ${row("elo.login()", "lib.m.login")}
          ${row("elo.find_all(first, next, key, body)", "lib.m.findall")}
          ${row("elo.download(url) / elo.upload(url, bytes)", "lib.m.blob")}
        </tbody></table>
        <h2>${esc(tr("lib.source"))}</h2>
        <div class="subtabs">${tabs}</div>
        <div class="lib-host"></div>
      </article>`;
    const sub = host.querySelector(".subtabs");
    const libHost = host.querySelector(".lib-host");
    function show(lang) {
      $$(".sub", sub).forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
      libHost.innerHTML = (data[lang] || [])
        .map(
          (f) =>
            `<div class="lib-file"><div class="lib-file-name">${esc(f.title)}</div>` +
            `<pre class="code"><code class="language-${lang === "python" ? "python" : "javascript"}">${esc(f.code)}</code></pre></div>`
        )
        .join("");
      if (window.hljs) libHost.querySelectorAll("pre code").forEach((el) => window.hljs.highlightElement(el));
    }
    sub.addEventListener("click", (ev) => {
      const b = ev.target.closest(".sub");
      if (b) show(b.dataset.lang);
    });
    if (langs.length) show(langs[0]);
  }

  function cssEsc(s) {
    return window.CSS && CSS.escape ? CSS.escape(s) : String(s).replace(/["\\]/g, "\\$&");
  }

  function reopenLast() {
    const saved = store.get(LS.topic, "");
    if (saved === "lib" && $(".topiclink.lib")) {
      openClientLib();
    } else if (saved.startsWith("t:") && $(`.topiclink[data-topic="${cssEsc(saved.slice(2))}"]`)) {
      openTopic(saved.slice(2));
    } else if (saved.startsWith("d:") && $(`.topiclink[data-deep="${cssEsc(saved.slice(2))}"]`)) {
      openDeep(saved.slice(2));
    }
  }

  // ---- wiring ------------------------------------------------ //
  function wireNav() {
    $("#catnav").addEventListener("click", (ev) => {
      const t = ev.target.closest("button.topiclink");
      if (!t) return;
      if (t.dataset.lib) openClientLib();
      else if (t.dataset.topic) openTopic(t.dataset.topic);
      else if (t.dataset.deep) openDeep(t.dataset.deep);
    });
  }

  const VIEWS = ["catalog", "spec", "scratchpad", "faq"];
  function wireTabs() {
    $$(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        $$(".tab").forEach((t) => t.classList.toggle("active", t === tab));
        VIEWS.forEach((v) => ($("#view-" + v).hidden = tab.dataset.view !== v));
        if (tab.dataset.view === "spec") loadSpec();
        if (tab.dataset.view === "faq") loadFaq();
        if (tab.dataset.view === "scratchpad" && SCRATCH_CM) setTimeout(() => SCRATCH_CM.refresh(), 0);
      });
    });
    $$(".lang").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.lang)));
  }

  // ---- FAQ tab (Markdown, loaded once) ------------------------- //
  let FAQ_LOADED = false;
  async function loadFaq() {
    if (FAQ_LOADED) return;
    const host = $("#faq-host");
    try {
      const d = await getJSON("/api/faq");
      const html = window.DOMPurify.sanitize(window.marked.parse(d.markdown || "", { breaks: false }));
      host.innerHTML = `<article class="topic deepdoc">${html}</article>`;
      if (window.hljs) host.querySelectorAll("pre code").forEach((el) => window.hljs.highlightElement(el));
      FAQ_LOADED = true;
    } catch (e) {
      host.innerHTML = `<p class="err">${esc(String(e))}</p>`;
    }
  }

  // ---- "API reference" tab (openapi.json walkthrough) --------- //
  let SPEC_LOADED = false;
  function specQuery() {
    const base = encodeURIComponent(effectiveBaseUrl() || CFG.defaultBaseUrl || "");
    return `mock=${isMock() ? 1 : 0}&base_url=${base}`;
  }
  async function loadSpec(force) {
    if (SPEC_LOADED && !force) return;
    SPEC_LOADED = true;
    const nav = $("#specnav");
    nav.innerHTML = `<p class="hint">${esc(tr("run.running"))}</p>`;
    let data;
    try {
      data = await getJSON("/api/spec/services?" + specQuery());
    } catch (e) {
      nav.innerHTML = `<p class="err">${esc(String(e))}</p>`;
      SPEC_LOADED = false;
      return;
    }
    const info = data.info || {};
    nav.innerHTML =
      `<div class="specmeta">${esc(info.title || "Indexserver")} ${esc(info.version || "")} · ` +
      `${esc(String(info.operations || 0))} ${esc(tr("spec.ops"))}` +
      `${info.sample ? ' · <span class="tag">sample</span>' : ""}` +
      `${info.fetch_error ? ' · <span class="tag err">offline</span>' : ""}` +
      `${info.sample ? `<div class="hint">${esc(tr("spec.sampleNote"))}</div>` : ""}</div>`;
    for (const svc of data.services) {
      const box = document.createElement("div");
      box.className = "catgroup";
      box.innerHTML =
        `<button class="catname specsvc" data-svc="${esc(svc.service)}">${esc(svc.service)}` +
        ` <span class="count">${svc.count}</span></button><ul hidden></ul>`;
      nav.appendChild(box);
    }
    nav.onclick = onSpecNavClick;
  }
  async function onSpecNavClick(ev) {
    const svcBtn = ev.target.closest(".specsvc");
    if (svcBtn) {
      const ul = svcBtn.nextElementSibling;
      if (!ul.dataset.loaded) {
        ul.innerHTML = `<li class="hint">…</li>`;
        try {
          const d = await getJSON(
            `/api/spec/operations?service=${encodeURIComponent(svcBtn.dataset.svc)}&` + specQuery()
          );
          ul.innerHTML = d.operations
            .map((o) => `<li><button class="topiclink" data-op="${esc(o.operation_id)}">${esc(o.method)}</button></li>`)
            .join("");
          ul.dataset.loaded = "1";
        } catch (e) {
          ul.innerHTML = `<li class="err">${esc(String(e))}</li>`;
        }
      }
      ul.hidden = !ul.hidden;
      return;
    }
    const opBtn = ev.target.closest("[data-op]");
    if (opBtn) {
      $$("#specnav .topiclink").forEach((b) => b.classList.remove("active"));
      opBtn.classList.add("active");
      openOperation(opBtn.dataset.op);
    }
  }
  async function openOperation(opId) {
    const host = $("#spec-host");
    host.innerHTML = `<p class="hint">${esc(tr("run.running"))}</p>`;
    let d;
    try {
      d = await getJSON("/api/spec/op/" + encodeURIComponent(opId) + "?" + specQuery());
    } catch (e) {
      host.innerHTML = `<p class="err">${esc(String(e))}</p>`;
      return;
    }
    const langs = ["python", "node", "browser"];
    const tabs = langs.map((k) => `<button class="sub" data-lang="${k}">${esc(tr("tab." + k))}</button>`).join("");
    const usedBy = (d.used_by || [])
      .map((u) => `<button class="link xref" data-topic="${esc(u.id)}">${esc(u.title)}</button>`)
      .join(" ");
    const eloDoc = eloDocHref(d.elo_doc_url);
    host.innerHTML = `
      <article class="topic">
        <h1><code>${esc(d.method)}</code></h1>
        <p class="summary"><code>${esc(d.http_method)} ${esc(d.path)}</code>${
          d.service !== "IXServicePortIF" ? ` · service <code>${esc(d.service)}</code>` : ""
        }</p>
        ${
          eloDoc
            ? `<p class="elo-doc"><a href="${esc(eloDoc)}" target="_blank" rel="noopener">${esc(tr("spec.eloDocs"))} ↗</a></p>`
            : ""
        }
        ${usedBy ? `<p class="xref-line">${esc(tr("spec.usedBy"))}: ${usedBy}</p>` : ""}
        <p class="warn">${esc(tr("spec.liveHint"))}</p>

        <h2>${esc(tr("spec.request"))}</h2>
        ${propList(d.request_props)}

        ${
          d.response_props && d.response_props.length
            ? `<h2>${esc(tr("spec.response"))} <span class="spec">${esc(d.result_ref || d.response_ref)}</span></h2>${propList(
                d.response_props
              )}`
            : d.response_ref
            ? `<h2>${esc(tr("spec.response"))}</h2><pre class="shape"><code>${esc(d.response_ref)}</code></pre>`
            : ""
        }

        <h2>${esc(tr("spec.generated"))}</h2>
        <div class="subtabs">${tabs}</div>
        <div class="snippet-host"></div>
      </article>`;

    host.querySelectorAll(".xref").forEach((b) =>
      b.addEventListener("click", () => {
        $('.tab[data-view="catalog"]').click();
        openTopic(b.dataset.topic);
      })
    );
    const sub = host.querySelector(".subtabs");
    const snipHost = host.querySelector(".snippet-host");
    function showLang(lang) {
      $$(".sub", sub).forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
      snipHost.innerHTML = "";
      snipHost.appendChild(makeRunner(lang, d.snippets[lang], null));
    }
    sub.addEventListener("click", (ev) => {
      const b = ev.target.closest(".sub");
      if (b) showLang(b.dataset.lang);
    });
    showLang("python");
  }

  // render a list of {name,type,ref,description,fields}
  function propList(props) {
    if (!props || !props.length) return `<p class="hint">-</p>`;
    const row = (p) => {
      const head =
        `<code>${esc(p.name)}</code> <span class="ptype">${esc(p.type)}</span>` +
        (p.description ? `<span class="pdesc">${esc(p.description)}</span>` : "");
      if (p.fields && p.fields.length) {
        return (
          `<details class="prop"><summary>${head}</summary>` +
          `<div class="prop-nested">${p.fields.map((f) => `<div class="prop-leaf">${row2(f)}</div>`).join("")}</div>` +
          `</details>`
        );
      }
      return `<div class="prop prop-leaf">${head}</div>`;
    };
    const row2 = (f) =>
      `<code>${esc(f.name)}</code> <span class="ptype">${esc(f.type)}</span>` +
      (f.description ? `<span class="pdesc">${esc(f.description)}</span>` : "");
    return `<div class="proplist">${props.map(row).join("")}</div>`;
  }

  let SCRATCH_CM = null;
  function wireScratchpad() {
    const langSel = $("#scratch-lang");
    const runBtn = $("#scratch-run");
    const codeEl = $("#scratch-code");
    const out = $("#scratch-output");
    const meta = $("#scratch-meta");
    const samples = {
      python:
        'from elo_playground import connect\n\n' +
        'ELO_USER = "Administrator"   # local ELO test box (or set ELOPG_* / .env)\n' +
        'ELO_PASS = "elo"\n\n' +
        'elo = connect(user=ELO_USER, password=ELO_PASS)\n' +
        'print(elo.call("getServerInfo", {}).get("version"))\n',
      node:
        'import { connect } from "elo-playground";\n\n' +
        'const ELO_USER = "Administrator";   // local ELO test box (or set ELOPG_* / .env)\n' +
        'const ELO_PASS = "elo";\n\n' +
        'const elo = await connect({ user: ELO_USER, password: ELO_PASS });\n' +
        'console.log((await elo.call("getServerInfo", {})).version);\n',
      browser:
        'const ELO_USER = "Administrator";   // local ELO test box (or set ELOPG_* / .env)\n' +
        'const ELO_PASS = "elo";\n\n' +
        'const elo = await connect({ user: ELO_USER, password: ELO_PASS });\n' +
        'console.log((await elo.call("getServerInfo", {})).version);\n',
    };
    const cmMode = (lang) => (lang === "python" ? "python" : "javascript");

    let touched = false;
    let getCode = () => codeEl.value;
    let setCode = (v) => (codeEl.value = v);

    if (window.CodeMirror) {
      SCRATCH_CM = window.CodeMirror.fromTextArea(codeEl, {
        mode: cmMode(langSel.value),
        lineNumbers: true,
        indentUnit: 2,
        tabSize: 2,
        viewportMargin: Infinity,
      });
      SCRATCH_CM.setSize("100%", 340);
      getCode = () => SCRATCH_CM.getValue();
      setCode = (v) => SCRATCH_CM.setValue(v);
      SCRATCH_CM.on("change", () => (touched = true));
    } else {
      codeEl.addEventListener("input", () => (touched = true));
    }

    langSel.addEventListener("change", () => {
      if (SCRATCH_CM) SCRATCH_CM.setOption("mode", cmMode(langSel.value));
      if (!touched) setCode(samples[langSel.value]);
    });
    runBtn.addEventListener("click", () => runAny(langSel.value, getCode(), null, out, meta, runBtn));
  }

  function wireConn() {
    const f = $("#conn");
    f.addEventListener("change", saveConn);
    $("#conn-check").addEventListener("click", async () => {
      const status = $("#conn-status");
      if (isMock()) {
        status.textContent = tr("conn.mockOn");
        status.className = "conn-status ok";
        return;
      }
      status.textContent = tr("conn.checking");
      status.className = "conn-status";
      const res = await postJSON("/api/elo/login-check", creds());
      status.textContent = res.detail || (res.ok ? "ok" : "failed");
      status.className = "conn-status " + (res.ok ? "ok" : "err");
    });
  }

  async function enterStaticMode() {
    // no backend: load the pre-computed run cache, keep the connection form
    // visible (default = Mock), drop the controls that need the backend.
    try {
      RUN_CACHE = await getJSON("api/run-cache.json");
    } catch (e) {
      RUN_CACHE = {};
    }
    const conn = $("#conn");
    if (conn) {
      const check = $("#conn-check");
      if (check) check.hidden = true; // login-check needs the backend
      conn.querySelectorAll("label.chk").forEach((l) => {
        if (/remember|tls_verify/.test(l.querySelector("input")?.name || "")) l.hidden = true;
      });
      const base = conn.base_url;
      if (base && !base.value) base.placeholder = "https://your-elo-host/ix-Repository1  (needs CORS)";
    }
    const bar = document.querySelector(".topbar-right") || document.querySelector(".topbar");
    if (bar && !bar.querySelector(".static-badge")) {
      const b = document.createElement("span");
      b.className = "static-badge";
      b.title = tr("static.help");
      b.textContent = tr("static.badge");
      bar.appendChild(b);
    }
  }

  // ---- boot ------------------------------------------------ //
  (async function init() {
    await loadI18n(LANG);
    $$(".lang").forEach((b) => b.classList.toggle("active", b.dataset.lang === LANG));
    applyI18n();
    loadConn();
    wireConn();
    wireNav();
    wireTabs();
    wireScratchpad();
    if (STATIC) await enterStaticMode();
    renderVersion();
    await loadCatalog();
    reopenLast();
  })();
})();
