"use strict";
/* ELO API Playground - single-page frontend (no build step, plain ES).
 *
 * Layout:
 *   - a connection form + Mock toggle in the top bar (kept in localStorage)
 *   - a language switch (EN / DE / ES)
 *   - two tabs: Catalog (nav tree + topic panels) and Scratchpad (free editor)
 *   - every code block gets Copy + Run:
 *       python / node / Go / PHP / Java -> POST /api/run  (executed on the backend)
 *       browser        -> executed here, inside a sandboxed <iframe>
 */
(function () {
  const CFG = window.__PLAYGROUND__ || {};
  const LS = {
    conn: "elopg.conn.v1",
    lang: "elopg.lang",
    topic: "elopg.topic", // "t:<id>" or "d:<categoryId>"
    sub: "elopg.sublang", // last used snippet tab
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
  const RUNTIMES = ["python", "node", "browser", "go", "php", "java", "rhino"];
  const CODEMIRROR_MODES = Object.freeze({
    python: "python",
    node: "javascript",
    browser: "javascript",
    rhino: "javascript",
    go: "go",
    php: "php",
    java: "java",
  });
  const HIGHLIGHT_LANGUAGES = Object.freeze({
    node: "javascript",
    browser: "javascript",
    rhino: "javascript",
    go: "go",
    php: "php",
    java: "java",
  });
  const codeMirrorMode = (runtime) => CODEMIRROR_MODES[runtime] || "javascript";
  const highlightLanguage = (runtime) => HIGHLIGHT_LANGUAGES[runtime] || runtime || "plaintext";
  let BROWSER_CLIENT_SRC = null; // cached source of eloClient.browser.js

  // "static demo" mode: no backend - baked JSON under ./api/ and a run cache
  const STATIC = !!CFG.staticMode;
  let RUN_CACHE = {}; // key "t:<id>|<lang>" / "d:<cat>#<i>|<lang>" -> RunResult
  let CURRENT_MOCK = null; // merged mock:{} of the open topic/deep, for the browser JS mock
  let RUNTIME_STATE = Object.fromEntries(RUNTIMES.map((id) => [id, { id, enabled: true, installed: true, core: true }]));

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
    if (path === "/api/lab/fs-source") return "api/lab/fs-source.json";
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
  // Unlike postJSON above, this rejects on a non-2xx response instead of
  // resolving with the error body - callers that need to distinguish a
  // failed request from a successful one (e.g. an installer that may
  // legitimately fail) should use this instead.
  async function postJSONStrict(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => null);
    if (!r.ok) throw new Error((data && data.detail) || `${url} -> HTTP ${r.status}`);
    return data;
  }

  // ---- optional runtime activation ---------------------------------- //
  function runtimeEnabled(id) {
    return !!(RUNTIME_STATE[id] || {}).enabled;
  }
  function runtimeLabel(item) {
    if (item.core) return tr("runtime.ready");
    if (item.id === "rhino") return tr("runtime.serverSide");
    return item.installed ? tr("runtime.installed") : tr("runtime.optional");
  }
  function applyRuntimeAvailability() {
    const select = $("#scratch-lang");
    if (select) {
      Array.from(select.options).forEach((option) => {
        option.hidden = !runtimeEnabled(option.value);
        option.disabled = !runtimeEnabled(option.value);
      });
      if (select.selectedOptions[0]?.disabled) select.value = "python";
    }
  }
  async function loadRuntimes() {
    if (STATIC) return;
    const data = await getJSON("/api/runtimes");
    RUNTIME_STATE = Object.fromEntries((data.runtimes || []).map((item) => [item.id, item]));
    applyRuntimeAvailability();
  }
  function renderRuntimeList() {
    const list = $("#runtime-list");
    if (!list) return;
    const items = RUNTIMES.map((id) => RUNTIME_STATE[id] || { id, enabled: false, installed: false, core: false });
    list.innerHTML = items.map((item) => {
      const disabled = item.core || STATIC ? "disabled" : "";
      return `<label class="runtime-row"><input type="checkbox" value="${esc(item.id)}" ${item.enabled ? "checked" : ""} ${disabled}>` +
        `<span><strong>${esc(tr("tab." + item.id))}</strong><small>${esc(item.description || "")}</small></span>` +
        `<span class="runtime-kind">${esc(runtimeLabel(item))}</span></label>`;
    }).join("");
  }
  function setRuntimeStatus(message, isError) {
    const status = $("#runtime-status");
    if (!status) return;
    status.textContent = message || "";
    status.className = "runtime-status" + (message ? (isError ? " err" : " ok") : "");
  }
  async function openRuntimeSettings(firstRun) {
    const modal = $("#runtime-modal");
    if (!modal) return;
    const progressWrap = $("#runtime-progress");
    if (progressWrap) progressWrap.hidden = true;
    try {
      await loadRuntimes();
      renderRuntimeList();
      setRuntimeStatus(STATIC ? tr("runtime.static") : "", false);
    } catch (error) {
      setRuntimeStatus(String(error), true);
    }
    modal.hidden = false;
    if (firstRun) store.set("elopg.runtime-onboarded.v1", "1");
  }
  // "HH:mm:ss|runtime-id|message" - see Write-InstallProgress in
  // scripts/bootstrap-toolchains.ps1.
  function parseProgressLine(line) {
    const i = line.indexOf("|");
    const j = line.indexOf("|", i + 1);
    if (i < 0 || j < 0) return null;
    return { time: line.slice(0, i), name: line.slice(i + 1, j), message: line.slice(j + 1) };
  }
  // Polls /api/runtimes/progress while the (single, blocking) POST /api/runtimes
  // install request is in flight, so the modal can show live download/verify/
  // extract status instead of a single static "installing..." message.
  // Returns a stop function; onLines(lines) is called after every successful poll.
  function pollInstallProgress(onLines) {
    let stopped = false;
    async function tick() {
      if (stopped) return;
      try {
        const data = await getJSON("/api/runtimes/progress");
        onLines(data.lines || []);
      } catch (error) {
        // transient - the server may be busy installing; keep polling
      }
      if (!stopped) setTimeout(tick, 700);
    }
    tick();
    return () => { stopped = true; };
  }
  async function saveRuntimeSettings() {
    if (STATIC) return setRuntimeStatus(tr("runtime.static"), true);
    const list = $("#runtime-list");
    const selected = $$('input[type="checkbox"]:checked', list).map((input) => input.value);
    const optional = RUNTIMES.filter((id) => !["python", "node", "browser"].includes(id));
    const enabled = selected.filter((id) => optional.includes(id));
    const disabled = optional.filter((id) => !enabled.includes(id));
    const button = $("#runtime-save");
    button.disabled = true;
    setRuntimeStatus(tr("runtime.installing"), false);

    const installable = ["go", "php", "java"];
    const willInstall = enabled.filter((id) => installable.includes(id) && !RUNTIME_STATE[id]?.installed);
    const progressWrap = $("#runtime-progress");
    const progressFill = $("#runtime-progress-fill");
    const progressLog = $("#runtime-progress-log");
    let stopPoll = null;
    if (willInstall.length) {
      progressWrap.hidden = false;
      progressFill.classList.add("indeterminate");
      progressLog.textContent = "";
      const readyIds = new Set();
      stopPoll = pollInstallProgress((lines) => {
        progressLog.textContent = lines
          .map((line) => {
            const parsed = parseProgressLine(line);
            return parsed ? `[${parsed.time}] ${parsed.name}: ${parsed.message}` : line;
          })
          .join("\n");
        progressLog.scrollTop = progressLog.scrollHeight;
        lines.forEach((line) => {
          const parsed = parseProgressLine(line);
          if (parsed && /^ready under/.test(parsed.message)) readyIds.add(parsed.name);
        });
        progressFill.classList.remove("indeterminate");
        progressFill.style.width = Math.min(100, Math.round((readyIds.size / willInstall.length) * 100)) + "%";
      });
    }

    try {
      // One activation request can download Go/PHP/JDK. A second, non-mutating
      // request stores disabled optional languages without removing files.
      if (enabled.length) await postJSONStrict("/api/runtimes", { runtimes: enabled, enabled: true });
      if (disabled.length) await postJSONStrict("/api/runtimes", { runtimes: disabled, enabled: false });
      await loadRuntimes();
      renderRuntimeList();
      setRuntimeStatus(tr("runtime.saved"), false);
      reopenLast();
    } catch (error) {
      setRuntimeStatus(String(error), true);
    } finally {
      if (stopPoll) stopPoll();
      if (willInstall.length) progressFill.style.width = "100%";
      button.disabled = false;
    }
  }
  function wireRuntimeSettings() {
    const modal = $("#runtime-modal");
    const settings = $("#runtime-settings");
    if (!modal || !settings) return;
    settings.addEventListener("click", () => openRuntimeSettings(false));
    $$(".runtime-close", modal).forEach((button) => button.addEventListener("click", () => (modal.hidden = true)));
    modal.addEventListener("click", (event) => { if (event.target === modal) modal.hidden = true; });
    $("#runtime-save").addEventListener("click", saveRuntimeSettings);
  }

  // ---- connection state -------------------------------------------- //
  // the ELO port lives in the Base URL itself (e.g. .../ix-Repository1 on :9090,
  // or an https reverse proxy on :443) - there is no separate Port field.
  function effectiveBaseUrl() {
    let raw = ($("#conn").base_url.value || "").trim();
    if (!raw) return "";
    if (!/^https?:\/\//i.test(raw)) raw = "http://" + raw;
    return raw.replace(/\/+$/, "");
  }

  // Every generated connection default carries one of these stable markers.
  // Do not broaden this into a heuristic replacement: user code without a marker
  // must never be rewritten when a form value changes.
  const CONNECTION_DEFAULTS = Object.freeze({
    base_url: "ELOPG_DEFAULT:base_url",
    user: "ELOPG_DEFAULT:user",
    password: "ELOPG_DEFAULT:password",
  });

  function escapeCodeString(value, quote) {
    return String(value)
      .replace(/\\/g, "\\\\")
      .replace(/\r/g, "\\r")
      .replace(/\n/g, "\\n")
      .replace(new RegExp(quote, "g"), "\\" + quote);
  }

  function connectionDefaultLine(language, key, value) {
    const env = { base_url: "ELOPG_ELO_BASE_URL", user: "ELOPG_ELO_USER", password: "ELOPG_ELO_PASSWORD" }[key];
    const names = { base_url: "ELO_BASE_URL", user: "ELO_USER", password: "ELO_PASS" };
    const marker = CONNECTION_DEFAULTS[key];
    if (language === "python") return `${names[key]} = os.getenv("${env}", "${escapeCodeString(value, '"')}") # ${marker}`;
    if (language === "node") return `const ${names[key]} = process.env.${env} || "${escapeCodeString(value, '"')}"; // ${marker}`;
    if (language === "browser") return `const ${names[key]} = globalThis.${env} || "${escapeCodeString(value, '"')}"; // ${marker}`;
    if (language === "go") {
      const goName = names[key];
      return `${goName} := elo.Env("${env}", "${escapeCodeString(value, '"')}") // ${marker}`;
    }
    if (language === "php") return `$${names[key]} = getenv('${env}') ?: '${escapeCodeString(value, "'")}'; // ${marker}`;
    if (language === "java") {
      const javaName = names[key];
      return `String ${javaName} = EloClient.env("${env}", "${escapeCodeString(value, '"')}"); // ${marker}`;
    }
    if (language === "rhino") return `var ${names[key]} = java.lang.System.getenv("${env}") || "${escapeCodeString(value, '"')}"; // ${marker}`;
    return null;
  }

  // Rewrite only the marked ELO_* defaults from the connection form. A blank
  // field keeps the generated teaching default. Form values remain in memory
  // (and optional browser storage), never in catalog or static deployment files.
  function applyCreds(code, language) {
    const f = $("#conn");
    if (!f || !code) return code;
    const values = {
      base_url: effectiveBaseUrl(),
      user: (f.user.value || "").trim(),
      password: f.password.value || "",
    };
    let out = code;
    Object.entries(values).forEach(([key, value]) => {
      if (!value) return;
      const marker = CONNECTION_DEFAULTS[key].replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const line = connectionDefaultLine(language, key, value);
      if (!line) return;
      const re = new RegExp("^([ \\t]*).*?(?:#|//)\\s*" + marker + "\\s*$", "m");
      out = out.replace(re, (_, indent) => indent + line);
    });
    return out;
  }

  function readConn() {
    const f = $("#conn");
    return {
      base_url: effectiveBaseUrl(),
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
    updateSchemeBtn();
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
  // Detect a complete structured response.  Do not try to pull JSON/XML out of
  // log output: that would hide useful text.  A response is reformatted only
  // when its complete body is one valid JSON or XML document.
  function structuredOutput(text) {
    const source = String(text || "");
    const t = source.trim();
    if (!t) return null;
    try {
      return { text: JSON.stringify(JSON.parse(t), null, 2), language: "json" };
    } catch (e) {
      // It may be XML; retain the original response if it is neither format.
    }
    const xml = prettyXml(t);
    return xml == null ? null : { text: xml, language: "xml" };
  }

  // put `code` into `outputEl` as a highlighted <code> block. Version-agnostic:
  // highlight.js 10.7+ has highlightElement, older builds have highlightBlock.
  function renderHighlighted(outputEl, code, lang) {
    outputEl.textContent = "";
    const c = document.createElement("code");
    c.className = "language-" + lang;
    c.textContent = code; // textContent, so hljs escapes and tokenises it
    outputEl.appendChild(c);
    outputEl.classList.add("hljs");
    outputEl.classList.remove("err");
    const hl = window.hljs && (window.hljs.highlightElement || window.hljs.highlightBlock);
    if (hl) {
      try {
        hl.call(window.hljs, c);
      } catch (e) {
        /* leave it as plain text */
      }
    }
  }

  // ---- output reformatters: the JSON / XML buttons on a run's output ---- //
  // pretty-print `text` as JSON (2-space). Tolerates a leading line before the
  // JSON body (e.g. "result:\n{...}"). Returns a string or null.
  function jsonPretty(text) {
    const t = (text || "").trim();
    if (!t) return null;
    const tryParse = (s) => {
      try {
        return JSON.stringify(JSON.parse(s), null, 2);
      } catch (e) {
        return null;
      }
    };
    let out = tryParse(t);
    if (out == null) {
      const i = t.search(/[{[]/);
      if (i > 0) out = tryParse(t.slice(i));
    }
    return out;
  }

  // pretty-print `text` as XML (2-space, via DOMParser). Returns a string or null.
  function prettyXml(text) {
    const t = (text || "").trim();
    if (!t || t[0] !== "<") return null;
    let doc;
    try {
      doc = new DOMParser().parseFromString(t, "application/xml");
    } catch (e) {
      return null;
    }
    if (doc.getElementsByTagName("parsererror").length) return null;
    const PAD = "  ";
    const attrs = (el) =>
      Array.from(el.attributes || [])
        .map(
          (a) =>
            ` ${a.name}="${String(a.value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;")}"`
        )
        .join("");
    const ser = (node, depth) => {
      const pad = PAD.repeat(depth);
      if (node.nodeType === 8) return `${pad}<!--${node.nodeValue}-->\n`;
      if (node.nodeType !== 1) return "";
      const kids = Array.from(node.childNodes).filter(
        (c) => c.nodeType === 1 || c.nodeType === 8 || (c.nodeType === 3 && c.nodeValue.trim())
      );
      if (!kids.length) return `${pad}<${node.nodeName}${attrs(node)}/>\n`;
      if (kids.length === 1 && kids[0].nodeType === 3) {
        return `${pad}<${node.nodeName}${attrs(node)}>${kids[0].nodeValue.trim()}</${node.nodeName}>\n`;
      }
      let s = `${pad}<${node.nodeName}${attrs(node)}>\n`;
      for (const c of kids) {
        s += c.nodeType === 3 ? `${PAD.repeat(depth + 1)}${c.nodeValue.trim()}\n` : ser(c, depth + 1);
      }
      return s + `${pad}</${node.nodeName}>\n`;
    };
    const root = doc.documentElement;
    if (!root || root.nodeName === "parsererror") return null;
    const decl = /^<\?xml/i.test(t) ? '<?xml version="1.0" encoding="utf-8"?>\n' : "";
    return (decl + ser(root, 0)).replace(/\s+$/, "");
  }

  // add "JSON" / "XML" buttons to an .output-head; they reformat outputEl in place
  function wireOutputFormatters(headEl, outputEl) {
    if (!headEl || headEl.querySelector(".fmt")) return;
    const host = headEl.querySelector(".oh-left") || headEl;
    const mk = (label, fn, lang) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "fmt";
      b.textContent = label;
      b.addEventListener("click", () => {
        const raw = outputEl.dataset.raw != null ? outputEl.dataset.raw : outputEl.textContent;
        if (!raw || !raw.trim()) {
          b.textContent = "–";
          setTimeout(() => (b.textContent = label), 800);
          return;
        }
        // pretty-print when it parses; otherwise just highlight what is there
        const pretty = fn(raw);
        renderHighlighted(outputEl, pretty != null ? pretty : raw, lang);
      });
      return b;
    };
    host.appendChild(mk("JSON", jsonPretty, "json"));
    host.appendChild(mk("XML", prettyXml, "xml"));
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

  // ---- Run: backend (Python / Node / Go / PHP / Java) ------------- //
  async function runBackend(language, code, topicId, outputEl, metaEl, btn, cacheKey, attach) {
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
        attachment: attach || null,
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
      outputEl.dataset.raw = outputEl.textContent;
      outputEl.classList.add("err");
    } else {
      const parts = [];
      if (res.stdout) parts.push(res.stdout.replace(/\n$/, ""));
      if (res.stderr) parts.push((parts.length ? "\n--- stderr ---\n" : "") + res.stderr.replace(/\n$/, ""));
      const text = parts.join("\n") || "(no output)";
      outputEl.dataset.raw = text; // kept so the JSON / XML buttons can reformat it
      const structured = !res.stderr ? structuredOutput(res.stdout) : null;
      if (structured != null) {
        renderHighlighted(outputEl, structured.text, structured.language);
      } else {
        outputEl.textContent = text;
        outputEl.classList.remove("hljs");
      }
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

  async function runBrowser(code, topicId, outputEl, metaEl, btn, attach) {
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
      attachment: attach || null, // "Choose file" -> window.__ELOPG__.attachment
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
        outputEl.dataset.raw = outputEl.textContent; // for the JSON / XML buttons
        if (d.ok && !outputEl.classList.contains("err")) {
          const structured = structuredOutput(outputEl.textContent);
          if (structured != null) renderHighlighted(outputEl, structured.text, structured.language);
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
// show the message, not just the stack (Firefox's err.stack has no message line)
const errText = (err) => {
  if (!err) return String(err);
  if (err.message) return (err.name || "Error") + ": " + err.message;
  return String(err.stack || err);
};
window.addEventListener("error", (e) => post("error", [e.message]));
window.addEventListener("unhandledrejection", (e) => post("error", [errText(e.reason)]));
${clientSrc}
(async () => {
  try {
${snippet}
    parent.postMessage({ __elopg: true, done: true, ok: true }, "*");
  } catch (err) {
    post("error", [errText(err)]);
    parent.postMessage({ __elopg: true, done: true, ok: false }, "*");
  }
})();
<\/script>`;
  }

  function runAny(language, code, topicId, outputEl, metaEl, btn, cacheKey, attach) {
    if (language === "browser") return runBrowser(code, topicId, outputEl, metaEl, btn, attach);
    return runBackend(language, code, topicId, outputEl, metaEl, btn, cacheKey, attach);
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
      box.innerHTML = `<div class="catname">${esc(cat.title)}<span class="catcount">${cat.topics.length}</span></div>`;
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

  // >>> lab-fs slice  (Testing lab: ELO <-> local filesystem panel)
  //
  // Rendered for a topic with `lab_fs: true`. Talks to three live-only endpoints:
  //   POST /api/lab/elo-children  - one level of the ELO folder tree (lazy)
  //   POST /api/lab/mirror        - ELO subtree -> sandbox/elo-archiv-structure/
  //                                 (wiped first) + open it in the file manager
  //   POST /api/lab/upload-tree   - a local folder (server path or the browser
  //                                 directory picker) -> folders + documents in ELO
  // In Mock / static mode the panel is inert; only the collapsed "show the code"
  // section (GET /api/lab/fs-source) still works.
  function labFsPanelHtml() {
    return `
      <div class="labfs-panel">
        <p class="labfs-note" hidden></p>
      <div class="labfs-cols">
          <section class="labfs-side" data-role="source">
            <h3>${esc(tr("labfs.eloTree"))}</h3>
            <div class="labfs-tree"><button class="labfs-load">${esc(tr("labfs.loadTree"))}</button><ul class="labfs-root" hidden></ul></div>
            <p class="labfs-selected">${esc(tr("labfs.selectFolder"))}</p>
            <div class="labfs-actions"><button class="labfs-mirror" disabled>${esc(tr("labfs.mirror"))}</button></div>
            <p class="hint">${esc(tr("labfs.mirrorHint"))}</p>
          </section>
          <section class="labfs-side" data-role="target">
            <h3>${esc(tr("labfs.localToElo"))}</h3>
            <label class="labfs-field">${esc(tr("labfs.serverPath"))}
              <input type="text" class="labfs-server-path" placeholder="C:\\path\\to\\folder" />
            </label>
            <label class="labfs-btn"><span>${esc(tr("labfs.pickDir"))}</span>
              <input type="file" class="labfs-dir" hidden webkitdirectory directory multiple />
            </label>
            <span class="labfs-dir-name"></span>
            <h3>${esc(tr("labfs.targetFolder"))}</h3>
            <div class="labfs-tree"><button class="labfs-load">${esc(tr("labfs.loadTree"))}</button><ul class="labfs-root" hidden></ul></div>
            <p class="labfs-selected">${esc(tr("labfs.selectFolder"))}</p>
            <div class="labfs-actions"><button class="labfs-upload" disabled>${esc(tr("labfs.upload"))}</button></div>
          </section>
        </div>
        <section class="labrepo-panel" aria-label="Local repository browser">
          <div class="labrepo-head">
            <div><h3>Repository files</h3><p class="hint">The 50 most recently modified files in the selected local ELO repository folder.</p></div>
            <label>Folder <select class="labrepo-folder" aria-label="Repository folder"><option value="Administration">Administration</option></select></label>
          </div>
          <p class="labrepo-status hint">Loading Administration…</p>
          <div class="labrepo-table-wrap">
            <table class="labrepo-table"><thead><tr><th>Name</th><th>Repository path</th><th>Modified</th></tr></thead><tbody></tbody></table>
          </div>
        </section>
        <pre class="labfs-log" hidden></pre>
        <details class="labfs-src">
          <summary>${esc(tr("labfs.showCode"))}</summary>
          <div class="labfs-src-host"></div>
        </details>
      </div>`;
  }

  function wireLabFs(host) {
    const panel = host.querySelector(".labfs-panel");
    if (!panel) return;
    const log = panel.querySelector(".labfs-log");
    const say = (line, isErr) => {
      log.hidden = false;
      log.textContent += (log.textContent ? "\n" : "") + line;
      if (isErr) log.classList.add("err");
    };
    const labPost = (url, body) =>
      postJSON(url, Object.assign({ credentials: isMock() ? null : creds() }, body));

    // --- configured local repository browser (not dependent on a live ELO) --
    const repoPanel = panel.querySelector(".labrepo-panel");
    const repoFolder = repoPanel.querySelector(".labrepo-folder");
    const repoStatus = repoPanel.querySelector(".labrepo-status");
    const repoRows = repoPanel.querySelector("tbody");
    const fmtDate = (value) => {
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
    };
    const previewLanguage = (extension) => ({
      ".js": "javascript", ".json": "json", ".xml": "xml", ".css": "css",
      ".csv": "plaintext", ".txt": "plaintext", ".md": "markdown",
    })[extension] || "plaintext";
    const closeRepoPreview = (modal) => {
      const url = modal.dataset.objectUrl;
      if (url) URL.revokeObjectURL(url);
      modal.remove();
    };
    const openRepoPreview = async (path) => {
      try {
        const data = await postJSON("/api/lab/repository-file", { path });
        if (data.error) throw new Error(data.error);
        const modal = document.createElement("div");
        modal.className = "labrepo-modal";
        modal.setAttribute("role", "dialog");
        modal.setAttribute("aria-modal", "true");
        let content = "";
        if (data.kind === "text") {
          content = `<pre class="labrepo-code"><code class="language-${previewLanguage(data.extension)}">${esc(data.content)}</code></pre>`;
        } else if (data.kind === "pdf" || data.kind === "word") {
          const bytes = Uint8Array.from(atob(data.b64), (c) => c.charCodeAt(0));
          const objectUrl = URL.createObjectURL(new Blob([bytes], { type: data.mime }));
          modal.dataset.objectUrl = objectUrl;
          const link = `<a href="${esc(objectUrl)}" download="${esc(data.name)}">Download ${esc(data.name)}</a>`;
          content = data.kind === "pdf"
            ? `<iframe class="labrepo-pdf" title="${esc(data.name)}" src="${esc(objectUrl)}"></iframe><p>${link} if the PDF preview is unavailable.</p>`
            : `<iframe class="labrepo-word" title="${esc(data.name)}" src="${esc(objectUrl)}"></iframe>` +
              `<p>Try the browser's native handler: <a href="${esc(objectUrl)}" target="_blank" rel="noopener">open ${esc(data.name)}</a>. ${link} if it cannot preview this Word file.</p>`;
        } else {
          content = `<p>No inline preview is available for this file type.</p>`;
        }
        modal.innerHTML = `<div class="labrepo-dialog"><div class="labrepo-dialog-head"><div><h2>${esc(data.name)}</h2><p>${esc(data.path)} · ${esc(String(data.size))} bytes</p></div><button type="button" aria-label="Close preview">×</button></div>${content}</div>`;
        modal.addEventListener("click", (event) => { if (event.target === modal) closeRepoPreview(modal); });
        modal.querySelector("button").addEventListener("click", () => closeRepoPreview(modal));
        document.body.append(modal);
        if (window.hljs && data.kind === "text") window.hljs.highlightElement(modal.querySelector("code"));
      } catch (error) {
        repoStatus.textContent = `Preview failed: ${error}`;
        repoStatus.className = "labrepo-status err";
      }
    };
    const loadRepositoryFiles = async () => {
      repoStatus.textContent = "Loading files…";
      repoStatus.className = "labrepo-status hint";
      repoRows.innerHTML = "";
      try {
        const data = await postJSON("/api/lab/repository-files", { folder: repoFolder.value });
        if (data.error) throw new Error(data.error);
        const files = data.files || [];
        repoStatus.textContent = files.length ? `${files.length} file${files.length === 1 ? "" : "s"} in ${data.folder || "repository root"}` : "No files in this folder.";
        repoRows.innerHTML = files.map((file) => `<tr><td><button class="labrepo-file" data-path="${esc(file.path)}">${esc(file.name)}</button></td><td><code>${esc(file.path)}</code></td><td>${esc(fmtDate(file.modified))}</td></tr>`).join("");
      } catch (error) {
        repoStatus.textContent = `Repository browser unavailable: ${error}`;
        repoStatus.className = "labrepo-status err";
      }
    };
    repoRows.addEventListener("click", (event) => {
      const button = event.target.closest(".labrepo-file");
      if (button) openRepoPreview(button.dataset.path);
    });
    repoFolder.addEventListener("change", loadRepositoryFiles);
    (async () => {
      try {
        const data = await postJSON("/api/lab/repository-folders", {});
        if (data.error) throw new Error(data.error);
        const folders = data.folders || [];
        repoFolder.innerHTML = folders.map((folder) => `<option value="${esc(folder)}">${esc(folder || "/")}</option>`).join("");
        if (folders.includes("Administration")) repoFolder.value = "Administration";
        await loadRepositoryFiles();
      } catch (error) {
        repoStatus.textContent = `Repository browser unavailable: ${error}`;
        repoStatus.className = "labrepo-status err";
      }
    })();

    // --- collapsed "show the code": real source, works offline too ----------
    let srcLoaded = false;
    const details = panel.querySelector(".labfs-src");
    details.addEventListener("toggle", async () => {
      if (!details.open || srcLoaded) return;
      srcLoaded = true;
      const holder = panel.querySelector(".labfs-src-host");
      holder.innerHTML = `<p class="hint">${esc(tr("run.running"))}</p>`;
      try {
        const data = await getJSON("/api/lab/fs-source");
        const files = [].concat(data.backend || [], data.frontend || []);
        holder.innerHTML = files
          .map(
            (f) =>
              `<div class="lib-file"><div class="lib-file-name">${esc(f.title)}</div>` +
              `<pre class="code"><code class="language-${/\.py\b/.test(f.title) ? "python" : "javascript"}">${esc(f.code)}</code></pre></div>`
          )
          .join("");
        if (window.hljs) holder.querySelectorAll("pre code").forEach((el) => window.hljs.highlightElement(el));
      } catch (e) {
        holder.innerHTML = `<p class="err">${esc(String(e))}</p>`;
      }
    });

    // --- live-only guard: the tree + actions need a real ELO + local disk ---
    if (STATIC || isMock()) {
      const note = panel.querySelector(".labfs-note");
      note.hidden = false;
      note.textContent = tr("labfs.needsBackend");
      panel
        .querySelectorAll(".labfs-load, .labfs-mirror, .labfs-upload, .labfs-server-path, .labfs-btn")
        .forEach((el) => {
          if ("disabled" in el) el.disabled = true;
          el.classList.add("is-off");
        });
      return;
    }

    // --- one lazy folder tree, reused for the "source" and "target" sides ---
    function wireTree(section, onSelect) {
      const treeEl = section.querySelector(".labfs-tree");
      const rootUl = treeEl.querySelector(".labfs-root");
      const loadBtn = treeEl.querySelector(".labfs-load");
      const selEl = section.querySelector(".labfs-selected");

      const rowHtml = (r) =>
        `<li>` +
        `<span class="labfs-toggle${r.is_folder ? "" : " leaf"}">${r.is_folder ? "\u25B8" : "\u00B7"}</span>` +
        `<button class="labfs-pick" data-id="${esc(r.id)}" data-name="${esc(r.name)}">${esc(r.name)}</button>` +
        `<ul hidden></ul></li>`;

      async function fill(ul, parentId) {
        ul.innerHTML = `<li class="hint">\u2026</li>`;
        const res = await labPost("/api/lab/elo-children", { parent_id: String(parentId) });
        if (res.error) {
          ul.innerHTML = `<li class="err">${esc(res.error)}</li>`;
          return;
        }
        ul.innerHTML = (res.rows || []).map(rowHtml).join("") || `<li class="hint">(empty)</li>`;
        ul.dataset.loaded = "1";
      }

      loadBtn.addEventListener("click", async () => {
        loadBtn.disabled = true;
        await fill(rootUl, "1");
        rootUl.hidden = false;
        loadBtn.hidden = true;
      });

      treeEl.addEventListener("click", async (ev) => {
        const tog = ev.target.closest(".labfs-toggle");
        if (tog && !tog.classList.contains("leaf")) {
          const li = tog.closest("li");
          const ul = li.querySelector("ul");
          const pick = li.querySelector(".labfs-pick");
          if (!ul.dataset.loaded) await fill(ul, pick.dataset.id);
          ul.hidden = !ul.hidden;
          tog.classList.toggle("open", !ul.hidden);
          return;
        }
        const pick = ev.target.closest(".labfs-pick");
        if (pick) {
          treeEl.querySelectorAll(".labfs-pick.active").forEach((b) => b.classList.remove("active"));
          pick.classList.add("active");
          selEl.textContent = `${tr("labfs.selected")}: ${pick.dataset.name} (id ${pick.dataset.id})`;
          onSelect({ id: pick.dataset.id, name: pick.dataset.name });
        }
      });
    }

    // --- ELO subtree -> sandbox/elo-archiv-structure -----------------------
    const sourceSection = panel.querySelector('[data-role="source"]');
    const mirrorBtn = sourceSection.querySelector(".labfs-mirror");
    let SELECTED = null;
    wireTree(sourceSection, (f) => {
      SELECTED = f;
      mirrorBtn.disabled = false;
    });
    mirrorBtn.addEventListener("click", async () => {
      if (!SELECTED) return;
      const label = mirrorBtn.textContent;
      mirrorBtn.disabled = true;
      mirrorBtn.textContent = tr("labfs.running");
      say(`> mirror ${SELECTED.name} (id ${SELECTED.id})`);
      try {
        const res = await labPost("/api/lab/mirror", {
          folder_id: String(SELECTED.id),
          folder_name: SELECTED.name,
        });
        if (res.error) say("! " + res.error, true);
        else {
          say(
            `  ${res.folders} folders, ${res.documents} documents, ${res.metadata} metadata.opf, ${res.bytes} bytes -> ${res.root}`
          );
          if (res.truncated) say("  (stopped at the object cap)");
          (res.skipped || []).forEach((s) => say("  skipped " + s));
          say(res.opened ? `  ${tr("labfs.done")} - opened in the file manager` : `  ${tr("labfs.done")}`);
        }
      } catch (e) {
        say("! " + String(e), true);
      } finally {
        mirrorBtn.textContent = label;
        mirrorBtn.disabled = false;
      }
    });

    // --- a local folder -> folders + documents in ELO --------------------
    const targetSection = panel.querySelector('[data-role="target"]');
    const uploadBtn = targetSection.querySelector(".labfs-upload");
    const serverPathEl = targetSection.querySelector(".labfs-server-path");
    const dirInput = targetSection.querySelector(".labfs-dir");
    const dirNameEl = targetSection.querySelector(".labfs-dir-name");
    const CAP = 16 * 1024 * 1024;
    let TARGET = null;
    let PICKED = []; // [{ rel_path, b64 }]
    let PICKED_ROOT = "uploaded";

    function refreshUpload() {
      uploadBtn.disabled = !TARGET || (!serverPathEl.value.trim() && !PICKED.length);
    }
    wireTree(targetSection, (f) => {
      TARGET = f;
      refreshUpload();
    });
    serverPathEl.addEventListener("input", refreshUpload);

    dirInput.addEventListener("change", async () => {
      const files = Array.from(dirInput.files || []);
      PICKED = [];
      dirNameEl.classList.remove("err");
      if (!files.length) {
        dirNameEl.textContent = "";
        refreshUpload();
        return;
      }
      const total = files.reduce((n, f) => n + f.size, 0);
      if (total > CAP) {
        dirNameEl.textContent = tr("labfs.tooBig");
        dirNameEl.classList.add("err");
        refreshUpload();
        return;
      }
      PICKED_ROOT = (files[0].webkitRelativePath || "uploaded/x").split("/")[0] || "uploaded";
      PICKED = await Promise.all(
        files.map(
          (f) =>
            new Promise((resolve) => {
              const fr = new FileReader();
              fr.onload = () =>
                resolve({
                  rel_path: (f.webkitRelativePath || f.name).split("/").slice(1).join("/") || f.name,
                  b64: String(fr.result).split(",")[1] || "",
                });
              fr.readAsDataURL(f);
            })
        )
      );
      dirNameEl.textContent = `${PICKED_ROOT}/ - ${files.length} files (${Math.round(total / 1024)} KB)`;
      refreshUpload();
    });

    uploadBtn.addEventListener("click", async () => {
      if (!TARGET) return;
      const usingPath = !!serverPathEl.value.trim();
      const label = uploadBtn.textContent;
      uploadBtn.disabled = true;
      uploadBtn.textContent = tr("labfs.running");
      const what = usingPath ? serverPathEl.value.trim() : `${PICKED_ROOT}/ (${PICKED.length} files)`;
      say(`> upload ${what} -> ${TARGET.name} (id ${TARGET.id})`);
      try {
        const body = usingPath
          ? { target_id: String(TARGET.id), server_path: serverPathEl.value.trim() }
          : { target_id: String(TARGET.id), root_name: PICKED_ROOT, items: PICKED };
        const res = await labPost("/api/lab/upload-tree", body);
        if (res.error) say("! " + res.error, true);
        else {
          say(`  ${res.folders} folders, ${res.documents} documents, ${res.bytes} bytes under id ${res.target_id}`);
          if (res.metadata_applied) say(`  metadata.opf applied to ${res.metadata_applied} folder(s)`);
          if (res.skipped) say(`  skipped ${res.skipped} oversized file(s)`);
          (res.warnings || []).forEach((w) => say("  ! " + w, true));
          if (res.truncated) say("  (stopped at the object cap)");
          say("  " + tr("labfs.done"));
        }
      } catch (e) {
        say("! " + String(e), true);
      } finally {
        uploadBtn.textContent = label;
        uploadBtn.disabled = false;
      }
    });
  }
  // <<< lab-fs slice

  // >>> lab-perms slice  (Testing lab: user/folder permissions panel)
  //
  // Rendered for a topic with `lab_perms: true`. Talks to seven live-only
  // endpoints (POST unless noted):
  //   /api/lab/perm-principals        - groups + users for the left panel
  //   /api/lab/perm-members           - first N members of a group
  //   /api/lab/perm-subtree           - a folder's children, annotated with the
  //                                      selected principal's resolved access
  //   /api/lab/perm-folder-principals - every group/user's access to one folder
  //   /api/lab/perm-folder-acl        - one folder's decoded ACL (+ diff vs parent)
  //   /api/lab/perm-special           - folders whose ACL departs from the parent's
  //   GET /api/lab/perm-source        - real source, for "show the code"
  // ELO has no "effective permission" RPC: access is resolved from each
  // folder's aclItems (group/user entries, andGroups, owner, inherit marker,
  // nested groups, main-admin bypass) - see resolve_access() in
  // backend-python/app/lab_perms.py.
  // In Mock / static mode the panel is inert; only "show the code" still works.
  function labPermsPanelHtml() {
    return `
      <div class="labfs-panel labperm-panel">
        <p class="labfs-note" hidden></p>
        <div class="labperm-topbar">
          <div class="labperm-modes">
            <button type="button" class="active" data-mode="byPrincipal">${esc(tr("labperm.modeByPrincipal"))}</button>
            <button type="button" data-mode="byFolder">${esc(tr("labperm.modeByFolder"))}</button>
            <button type="button" data-mode="bySpecial" title="${esc(tr("labperm.modeSpecialTitle"))}">${esc(tr("labperm.modeSpecial"))}</button>
            <button type="button" data-mode="byDiag" title="${esc(tr("labperm.modeDiagTitle"))}">${esc(tr("labperm.modeDiag"))}</button>
            <button type="button" data-mode="byOrg" title="${esc(tr("labperm.modeOrgTitle"))}">${esc(tr("labperm.modeOrg"))}</button>
          </div>
          <label class="labperm-only-access"><input type="checkbox" class="labperm-only-access-cb" /> ${esc(tr("labperm.onlyWithAccess"))}</label>
          <label class="labperm-only-access" title="${esc(tr("labperm.exclusiveTitle"))}"><input type="checkbox" class="labperm-exclusive-cb" /> ${esc(tr("labperm.exclusive"))}</label>
          <button type="button" class="labperm-maximize" title="${esc(tr("labperm.maximize"))}" aria-label="${esc(tr("labperm.maximize"))}">⤢</button>
        </div>

        <div class="labperm-mode-host" data-mode-host="byPrincipal">
          <div class="labfs-cols">
            <section class="labfs-side" data-role="principals">
              <div class="labperm-modes">
                <button type="button" class="active" data-kind="groups">${esc(tr("labperm.groupsTab"))}</button>
                <button type="button" data-kind="users">${esc(tr("labperm.usersTab"))}</button>
              </div>
              <div class="labfs-tree"><button class="labfs-load labperm-load-principals">${esc(tr("labperm.loadPrincipals"))}</button><ul class="labperm-list" hidden></ul></div>
              <p class="labfs-selected labperm-principal-selected">${esc(tr("labperm.noPrincipalSelected"))}</p>
            </section>
            <section class="labfs-side" data-role="perm-folders">
              <div class="labperm-controls">
                <label>${esc(tr("labperm.depthLabel"))} <input type="number" class="labperm-depth" min="0" max="6" value="3" /></label>
                <label><input type="checkbox" class="labperm-only-visible" /> ${esc(tr("labperm.onlyVisible"))}</label>
                <details class="labperm-legend"><summary>${esc(tr("labperm.legend"))}</summary><p class="hint">${esc(tr("labperm.legendText"))}</p></details>
              </div>
              <div class="labfs-tree labperm-tree"><ul class="labperm-folder-root"></ul></div>
              <p class="labperm-empty-msg hint" hidden>${esc(tr("labperm.noVisibleFolders"))}</p>
            </section>
          </div>
        </div>

        <div class="labperm-mode-host" data-mode-host="byFolder" hidden>
          <div class="labfs-cols">
            <section class="labfs-side" data-role="perm-folder-pick">
              <div class="labfs-tree"><button class="labfs-load">${esc(tr("labperm.loadFolders"))}</button><ul class="labfs-root" hidden></ul></div>
              <p class="labfs-selected">${esc(tr("labperm.selectFolderHint"))}</p>
            </section>
            <section class="labfs-side" data-role="perm-folder-result">
              <div class="labperm-filter">
                <span>${esc(tr("labperm.filterTitle"))}:</span>
                <label><input type="checkbox" data-bit="1" /> R</label>
                <label><input type="checkbox" data-bit="2" /> W</label>
                <label><input type="checkbox" data-bit="4" /> D</label>
                <label><input type="checkbox" data-bit="8" /> ER</label>
                <label><input type="checkbox" data-bit="16" /> L</label>
                <label><input type="checkbox" data-bit="32" /> P</label>
                <button type="button" class="labperm-preset-read">${esc(tr("labperm.filterAtLeastRead"))}</button>
              </div>
              <ul class="labperm-result-list"></ul>
            </section>
          </div>
        </div>

        <div class="labperm-mode-host" data-mode-host="bySpecial" hidden>
          <section class="labfs-side" data-role="perm-special">
            <div class="labperm-controls">
              <label>${esc(tr("labperm.depthLabel"))} <input type="number" class="labperm-depth" min="1" max="6" value="3" /></label>
              <label><input type="checkbox" class="labperm-only-special" /> ${esc(tr("labperm.onlySpecial"))}</label>
              <details class="labperm-legend"><summary>${esc(tr("labperm.legend"))}</summary><p class="hint">${esc(tr("labperm.specialLegend"))}</p></details>
            </div>
            <div class="labfs-tree labperm-tree"><button class="labfs-load labperm-load-special">${esc(tr("labperm.loadSpecial"))}</button><ul class="labperm-special-root" hidden></ul></div>
            <p class="labperm-empty-msg hint" hidden>${esc(tr("labperm.noSpecialFolders"))}</p>
          </section>
        </div>

        <div class="labperm-mode-host" data-mode-host="byDiag" hidden>
          <section class="labfs-side" data-role="perm-diag">
            <div class="labperm-controls">
              <label>${esc(tr("labperm.depthLabel"))} <input type="number" class="labperm-depth" min="1" max="6" value="3" /></label>
              <button class="labfs-load labperm-run-diag">${esc(tr("labperm.runDiag"))}</button>
              <span class="labperm-diag-status hint"></span>
            </div>
            <div class="labperm-diag-results"></div>
          </section>
        </div>

        <div class="labperm-mode-host" data-mode-host="byOrg" hidden>
          <section class="labfs-side" data-role="perm-org">
            <div class="labperm-controls">
              <div class="labperm-modes">
                <button type="button" class="active" data-chart="groups">${esc(tr("labperm.orgGroups"))}</button>
                <button type="button" data-chart="superiors">${esc(tr("labperm.orgSuperiors"))}</button>
              </div>
              <button class="labfs-load labperm-load-org">${esc(tr("labperm.loadOrg"))}</button>
              <label><input type="checkbox" class="labperm-org-hide-empty" checked /> ${esc(tr("labperm.orgHideEmpty"))}</label>
              <span class="labperm-org-status hint"></span>
              <details class="labperm-legend"><summary>${esc(tr("labperm.legend"))}</summary><p class="hint">${esc(tr("labperm.orgLegend"))}</p></details>
            </div>
            <div class="labperm-org-host"></div>
          </section>
        </div>

        <div class="labperm-log-bar" hidden><button type="button" class="labperm-clear-log">${esc(tr("labperm.clearLog"))}</button></div>
        <pre class="labfs-log" hidden></pre>
        <details class="labfs-src">
          <summary>${esc(tr("labfs.showCode"))}</summary>
          <div class="labfs-src-host"></div>
        </details>
      </div>`;
  }

  function wireLabPerms(host) {
    const panel = host.querySelector(".labperm-panel");
    if (!panel) return;
    const log = panel.querySelector(".labfs-log");
    const logBar = panel.querySelector(".labperm-log-bar");
    const say = (line, isErr) => {
      log.hidden = false;
      logBar.hidden = false;
      log.textContent += (log.textContent ? "\n" : "") + line;
      if (isErr) log.classList.add("err");
    };
    panel.querySelector(".labperm-clear-log").addEventListener("click", () => {
      log.textContent = "";
      log.classList.remove("err");
      log.hidden = true;
      logBar.hidden = true;
    });
    const labPost = (url, body) =>
      postJSON(url, Object.assign({ credentials: isMock() ? null : creds() }, body));

    // Same message classification as the "Log in" topic's own snippet
    // (catalog/00-connection/01-login.yaml) - a raw EloError like
    // "login: HTTP 404 - <!DOCTYPE html>..." is a connection problem, not a
    // permissions result, so it gets a clear headline instead of raw HTML.
    function explainError(msg) {
      const m = String(msg || "");
      if (/ELOIX:3008|authentication failed|HTTP 401|HTTP 403/.test(m)) return `${tr("labperm.errAuth")}: ${m}`;
      if (/request failed/.test(m)) return `${tr("labperm.errUnreachable")}: ${m}`;
      if (/HTTP 404/.test(m)) return `${tr("labperm.errNotFound")}: ${m.split(" - ")[0]}`;
      return `${tr("labperm.errGeneric")}: ${m}`;
    }
    const SPINNER_ROW = `<li class="labperm-loading"><span class="labperm-spinner"></span> ${esc(tr("labperm.loading"))}</li>`;

    // AccessC.LUR_* bits and AclItemC.TYPE_* - mirrors backend-python/app/lab_perms.py
    const ACCESS_BITS = [[1, "R"], [2, "W"], [4, "D"], [8, "E"], [16, "L"], [32, "P"]];
    const ACL_KIND = { 0: "group", 1: "user", 10: "key", 100: "inherit", 200: "owner", 300: "participants" };
    const ACL_ICON = { group: "👥", user: "👤", owner: "🔑", inherit: "↑", key: "🗝", participants: "⚙" };
    const accessLabel = (bits) => (bits === 63 ? "full" : !bits ? "no access" : ACCESS_BITS.filter(([b]) => bits & b).map(([, n]) => n).join(", "));
    const bitFlags = (bits) => ACCESS_BITS.map(([b, n]) => (bits & b ? n : "·")).join(" ");

    // The log is a <pre>, so a padded, column-aligned dump reads like a table.
    function formatAclEntries(entries) {
      const width = Math.max(12, ...entries.map((e) => (e.name || "").length));
      return entries.map((e) => {
        const kind = e.kind || ACL_KIND[e.type] || String(e.type);
        const bits = Number(e.access || 0);
        const ands = e.and_groups && e.and_groups.length ? `   AND ${e.and_groups.join(", ")}` : "";
        return `    ${ACL_ICON[kind] || "•"} ${String(e.name || e.id).padEnd(width)}  ${bitFlags(bits)}   ${e.label || accessLabel(bits)}${ands}`;
      });
    }
    function sayAcl(folder, entries, owner, principal, diff) {
      // every block opens with an unmissable "which folder" banner: the full
      // path when the backend had it (checkoutSord's refPaths), else the name
      const where = `📁 ${folder.path || folder.name}  (id ${folder.id})`;
      const banner = `━━━ ${where} ${"━".repeat(Math.max(3, 70 - where.length))}`;
      const head = `> ACL` + (owner && owner.name ? `   owner: ${owner.name}` : "");
      const lines = entries.length ? formatAclEntries(entries) : [`    (${tr("labperm.aclEmpty")})`];
      lines.unshift(banner, head);
      lines.push(`    ${tr("labperm.legendBits")}`);
      // how this ACL departs from the parent's - ELO copies the parent's ACL
      // onto a new child, so any difference was set on purpose.
      if (diff && folder.parent_name) {
        if (!diff.differs) {
          lines.push(`  = ${tr("labperm.sameAsParent")} (${folder.parent_name})`);
        } else {
          lines.push(`  ≠ ${tr("labperm.differsFromParent")} (${folder.parent_name}):`);
          diff.added.forEach((e) => lines.push(`    + ${ACL_ICON[e.kind] || "•"} ${e.name}  ${e.label}   (${tr("labperm.aclDiffAdded")})`));
          diff.removed.forEach((e) => lines.push(`    - ${ACL_ICON[e.kind] || "•"} ${e.name}  ${e.label}   (${tr("labperm.aclDiffRemoved")})`));
          diff.changed.forEach((e) => lines.push(`    ~ ${ACL_ICON[e.kind] || "•"} ${e.name}  ${e.parent_label} → ${e.label}   (${tr("labperm.aclDiffChanged")})`));
        }
      }
      if (principal) {
        const via = principal.group_names && principal.group_names.length ? `   ${tr("labperm.viaGroups")}: ${principal.group_names.join(", ")}` : "";
        const admin = principal.is_main_admin ? `   (${tr("labperm.mainAdmin")})` : "";
        lines.push(`  → ${principal.kind === "group" ? "👥" : "👤"} ${principal.name || principal.id}: ${principal.label}${principal.conditional ? " ∧" : ""}${admin}${via}`);
      }
      say(lines.join("\n"));
    }

    // --- collapsed "show the code": real source, works offline too ----------
    let srcLoaded = false;
    const details = panel.querySelector(".labfs-src");
    details.addEventListener("toggle", async () => {
      if (!details.open || srcLoaded) return;
      srcLoaded = true;
      const holder = panel.querySelector(".labfs-src-host");
      holder.innerHTML = `<p class="hint">${esc(tr("run.running"))}</p>`;
      try {
        const data = await getJSON("/api/lab/perm-source");
        const files = [].concat(data.backend || [], data.frontend || []);
        holder.innerHTML = files
          .map(
            (f) =>
              `<div class="lib-file"><div class="lib-file-name">${esc(f.title)}</div>` +
              `<pre class="code"><code class="language-${/\.py\b/.test(f.title) ? "python" : "javascript"}">${esc(f.code)}</code></pre></div>`
          )
          .join("");
        if (window.hljs) holder.querySelectorAll("pre code").forEach((el) => window.hljs.highlightElement(el));
      } catch (e) {
        holder.innerHTML = `<p class="err">${esc(String(e))}</p>`;
      }
    });

    // --- live-only guard: everything here needs a real ELO -----------------
    if (STATIC || isMock()) {
      const note = panel.querySelector(".labfs-note");
      note.hidden = false;
      note.textContent = tr("labfs.needsBackend");
      panel.querySelectorAll("button, input").forEach((el) => {
        if (el.closest(".labfs-src")) return;
        if ("disabled" in el) el.disabled = true;
        el.classList.add("is-off");
      });
      return;
    }

    // --- a lazy folder tree, optionally annotated with resolved access -----
    // (forked from labfs's wireTree: this one also renders a greyed/struck
    // "no access" row and an italic permission suffix when rows carry them,
    // and accepts already-resolved nested `children` for auto-expand.)
    function wirePermTree(section, { fetchRows, onSelect }) {
      const treeEl = section.querySelector(".labfs-tree");

      // Three row flavours share this markup: plain folders (mode B's picker),
      // access-annotated rows (mode A: label, ∧, ◆ exclusive, ≠ special) and
      // "special ACL" rows (mode C: ≠ badge with +added −removed ~changed).
      const diffBadge = (r) =>
        ` <span class="labperm-diff" title="${esc(r.added_names && r.added_names.length ? `+ ${r.added_names.join(", ")}` : tr("labperm.specialBadgeTitle"))}">≠` +
        (typeof r.added === "number" ? ` +${r.added} −${r.removed} ~${r.changed}` : "") +
        `</span>`;
      const rowHtml = (r) => {
        const hasInfo = typeof r.access === "boolean";
        const isSpecial = typeof r.differs === "boolean";
        const noAccess = hasInfo && !r.access;
        // hideable = no access AND nothing accessible (fetched) below it; a
        // folder that only leads to accessible ones stays visible, greyed.
        // The same idea drives "exclusive only" and "special only".
        const hideable = noAccess && !r.descendant_access;
        const nonExclusive = hasInfo && !r.exclusive && !r.descendant_exclusive;
        const plain = isSpecial && !r.differs && !r.descendant_differs;
        const cond = r.conditional ? ` <span class="labperm-cond" title="${esc(tr("labperm.conditional"))}">∧</span>` : "";
        const excl = r.exclusive ? ` <span class="labperm-excl" title="${esc(tr("labperm.exclusiveBadge"))}">◆</span>` : "";
        let suffix = "";
        if (hasInfo) suffix = ` <em class="labperm-access">(${esc(r.label)})</em>${cond}${excl}${r.acl_differs ? diffBadge(r) : ""}`;
        else if (isSpecial) suffix = r.differs ? diffBadge(r) : r.inherits_marker ? ` <span class="labperm-inherit" title="${esc(tr("labperm.inheritsMarker"))}">↑</span>` : "";
        const cls = [
          noAccess ? "labperm-noaccess" : "",
          hideable ? "labperm-hideable" : "",
          nonExclusive ? "labperm-nonexclusive" : "",
          plain ? "labperm-plain" : "",
          isSpecial && r.differs ? "labperm-special" : "",
        ].filter(Boolean).join(" ");
        return (
          `<li class="${cls}">` +
          `<span class="labfs-toggle${r.child_count ? "" : " leaf"}">${r.child_count ? "▸" : "·"}</span>` +
          `<button class="labfs-pick" data-id="${esc(r.id)}" data-name="${esc(r.name)}">${esc(r.name)}</button>${suffix}` +
          `<ul${r.children && r.children.length ? "" : " hidden"}></ul></li>`
        );
      };

      function renderInto(ul, rows) {
        ul.innerHTML = rows.map(rowHtml).join("") || `<li class="hint">(empty)</li>`;
        ul.dataset.loaded = "1";
        rows.forEach((r, i) => {
          if (r.children) {
            const li = ul.children[i];
            if (!li) return;
            renderInto(li.querySelector("ul"), r.children);
            if (r.children.length) li.querySelector(".labfs-toggle").classList.add("open");
          }
        });
      }

      treeEl.addEventListener("click", async (ev) => {
        const tog = ev.target.closest(".labfs-toggle");
        if (tog && !tog.classList.contains("leaf")) {
          const li = tog.closest("li");
          const ul = li.querySelector("ul");
          const pick = li.querySelector(".labfs-pick");
          if (!ul.dataset.loaded) {
            ul.innerHTML = SPINNER_ROW;
            ul.hidden = false;
            renderInto(ul, await fetchRows(pick.dataset.id));
          }
          ul.hidden = !ul.hidden;
          tog.classList.toggle("open", !ul.hidden);
          return;
        }
        if (!onSelect) return;
        const pick = ev.target.closest(".labfs-pick");
        if (pick) {
          treeEl.querySelectorAll(".labfs-pick.active").forEach((b) => b.classList.remove("active"));
          pick.classList.add("active");
          onSelect({ id: pick.dataset.id, name: pick.dataset.name });
        }
      });

      return { renderInto };
    }

    // --- maximize: fill the viewport for easier tree/list reading -----------
    const maximizeBtn = panel.querySelector(".labperm-maximize");
    maximizeBtn.addEventListener("click", () => {
      const on = panel.classList.toggle("maximized");
      const label = tr(on ? "labperm.restore" : "labperm.maximize");
      maximizeBtn.textContent = on ? "⤡" : "⤢";
      maximizeBtn.title = label;
      maximizeBtn.setAttribute("aria-label", label);
    });

    // --- mode toggle: "by group/user" vs "by folder" ------------------------
    const modeButtons = panel.querySelectorAll(".labperm-topbar > .labperm-modes > button");
    const modeHosts = panel.querySelectorAll(".labperm-mode-host");
    const onlyAccessCb = panel.querySelector(".labperm-only-access-cb");
    const exclusiveCb = panel.querySelector(".labperm-exclusive-cb");
    const wired = { byPrincipal: false, byFolder: false, bySpecial: false, byDiag: false, byOrg: false };
    const wireFor = { byPrincipal: wireByPrincipal, byFolder: wireByFolder, bySpecial: wireBySpecial, byDiag: wireDiagnostics, byOrg: wireOrgChart };
    modeButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const mode = btn.dataset.mode;
        modeButtons.forEach((b) => b.classList.toggle("active", b === btn));
        modeHosts.forEach((h) => (h.hidden = h.dataset.modeHost !== mode));
        // the two topbar filters only mean something in modes A and B
        panel.querySelectorAll(".labperm-only-access").forEach((l) => (l.hidden = mode !== "byPrincipal" && mode !== "byFolder"));
        if (!wired[mode]) {
          wired[mode] = true;
          wireFor[mode]();
        }
      });
    });

    // --- Mode A: pick a group/user, see its accessible folders --------------
    function wireByPrincipal() {
      const section = panel.querySelector('[data-role="principals"]');
      const kindButtons = section.querySelectorAll(".labperm-modes button");
      const loadBtn = section.querySelector(".labperm-load-principals");
      const list = section.querySelector(".labperm-list");
      const selEl = section.querySelector(".labperm-principal-selected");
      const folderSection = panel.querySelector('[data-role="perm-folders"]');
      const depthInput = folderSection.querySelector(".labperm-depth");
      const onlyVisible = folderSection.querySelector(".labperm-only-visible");
      const folderRoot = folderSection.querySelector(".labperm-folder-root");
      const emptyMsg = folderSection.querySelector(".labperm-empty-msg");

      // "show only visible" and "exclusive" hide rows in pure CSS; this just
      // decides whether the "nothing visible" hint should show on top of
      // that, checked whenever a filter or the tree content changes.
      function refreshEmptyState() {
        if (!onlyVisible.checked && !exclusiveCb.checked) {
          emptyMsg.hidden = true;
          return;
        }
        const rows = Array.from(folderRoot.children).filter((li) => li.tagName === "LI" && !li.classList.contains("hint"));
        const anyShown = rows.some((li) => li.getClientRects().length > 0);
        emptyMsg.hidden = rows.length === 0 || anyShown;
      }

      let DATA = { groups: [], users: [] };
      let KIND = "groups";
      let CURRENT_PRINCIPAL = null;
      let CURRENT_NAME = "";

      const permTree = wirePermTree(folderSection, {
        fetchRows: async (parentId) => {
          if (!CURRENT_PRINCIPAL) return [];
          const r = await labPost("/api/lab/perm-subtree", { parent_id: parentId, principal: CURRENT_PRINCIPAL, depth: 1 });
          if (r.error) {
            say("! " + explainError(r.error), true);
            return [];
          }
          return r.rows;
        },
        // clicking a folder name dumps its decoded ACL - and how the selected
        // principal resolves against it - into the log (the debugging aid).
        onSelect: async (f) => {
          const res = await labPost("/api/lab/perm-folder-acl", { folder_id: String(f.id), principal: CURRENT_PRINCIPAL });
          if (res.error) return say("! " + explainError(res.error), true);
          sayAcl(res.folder, res.entries, res.owner, res.principal ? { ...res.principal, name: CURRENT_NAME } : null, res.diff);
        },
      });

      kindButtons.forEach((b) =>
        b.addEventListener("click", () => {
          kindButtons.forEach((x) => x.classList.toggle("active", x === b));
          KIND = b.dataset.kind;
          renderList();
        })
      );

      function renderList() {
        const rows = KIND === "groups" ? DATA.groups : DATA.users;
        list.innerHTML =
          rows
            .map((p) => {
              const icon = KIND === "groups" ? "👥" : "👤";
              const groupsHint =
                KIND === "users" && p.groups && p.groups.length
                  ? ` <span class="labperm-usergroups-toggle">(${p.groups.length})</span>` +
                    `<div class="labperm-usergroups-list" hidden>` +
                    p.groups
                      .map(
                        (g) =>
                          `<button class="labfs-pick labperm-inline-group" data-kind="group" data-id="${esc(g.id)}" data-name="${esc(g.name)}">${esc(g.name)}</button>`
                      )
                      .join(", ") +
                    `</div>`
                  : "";
              const admin = p.is_main_admin ? ` <span class="labperm-admin-badge" title="${esc(tr("labperm.mainAdmin"))}">★</span>` : "";
              const members =
                KIND === "groups"
                  ? `<span class="labperm-members-toggle" data-id="${esc(p.id)}">▸ ${esc(tr("labperm.showMembers"))}</span><ul class="labperm-members" hidden></ul>`
                  : "";
              return (
                `<li><button class="labfs-pick" data-kind="${KIND === "groups" ? "group" : "user"}" data-id="${esc(p.id)}" data-name="${esc(p.name)}">${icon} ${esc(p.name)}</button>${admin}${groupsHint}` +
                members +
                `</li>`
              );
            })
            .join("") || `<li class="hint">(empty)</li>`;
      }

      loadBtn.addEventListener("click", async () => {
        loadBtn.disabled = true;
        const label = loadBtn.textContent;
        loadBtn.textContent = tr("labfs.running");
        try {
          const res = await labPost("/api/lab/perm-principals", {});
          if (res.error) {
            say("! " + explainError(res.error), true);
            return;
          }
          DATA = res;
          list.hidden = false;
          renderList();
          loadBtn.hidden = true;
        } finally {
          loadBtn.disabled = false;
          loadBtn.textContent = label;
        }
      });

      // members become their own clickable principal (a plain .labfs-pick
      // button), so picking one re-uses the exact same selection handler below.
      const memberCache = new Map();
      list.addEventListener("click", async (ev) => {
        const toggle = ev.target.closest(".labperm-members-toggle");
        if (toggle) {
          const ul = toggle.nextElementSibling;
          if (!memberCache.has(toggle.dataset.id)) {
            ul.innerHTML = `<li class="hint">…</li>`;
            ul.hidden = false;
            const res = await labPost("/api/lab/perm-members", { group_id: toggle.dataset.id, preview: 10 });
            if (res.error) {
              ul.innerHTML = `<li class="err">${esc(explainError(res.error))}</li>`;
              return;
            }
            memberCache.set(toggle.dataset.id, res);
            const names = res.members.map((m) => m.name);
            const rest = res.total - names.length;
            ul.innerHTML =
              res.members
                .map(
                  (m) =>
                    `<li><button class="labfs-pick" data-kind="user" data-id="${esc(m.id)}" data-name="${esc(m.name)}">👤 ${esc(m.name)}</button></li>`
                )
                .join("") + (rest > 0 ? `<li class="hint">+${rest} ${esc(tr("labperm.more"))}</li>` : "");
            // the toggle label itself: the single member's name when there is
            // only one, otherwise the total count.
            toggle.innerHTML = `▾ ${esc(tr("labperm.showMembers"))} (${res.total === 1 ? esc(names[0]) : res.total})`;
            toggle.title = names.join(", ") + (rest > 0 ? `, +${rest} ${tr("labperm.more")}` : "");
          } else {
            ul.hidden = !ul.hidden;
            toggle.textContent = toggle.textContent.replace(/^./, ul.hidden ? "▸" : "▾");
          }
          return;
        }
        // a user's "(N)" group count - reveals the comma-separated,
        // individually clickable group list right below it.
        const gtoggle = ev.target.closest(".labperm-usergroups-toggle");
        if (gtoggle) {
          gtoggle.nextElementSibling.hidden = !gtoggle.nextElementSibling.hidden;
          return;
        }
        const pick = ev.target.closest(".labfs-pick");
        if (pick) {
          list.querySelectorAll(".labfs-pick.active").forEach((b) => b.classList.remove("active"));
          pick.classList.add("active");
          selEl.textContent = `${tr("labfs.selected")}: ${pick.dataset.name}`;
          CURRENT_PRINCIPAL = { kind: pick.dataset.kind, id: pick.dataset.id };
          CURRENT_NAME = pick.dataset.name;
          const depth = Math.max(0, Math.min(6, Number(depthInput.value) || 0));
          folderRoot.innerHTML = SPINNER_ROW;
          emptyMsg.hidden = true;
          const res = await labPost("/api/lab/perm-subtree", { parent_id: "1", principal: CURRENT_PRINCIPAL, depth });
          if (res.error) {
            folderRoot.innerHTML = `<li class="err">${esc(explainError(res.error))}</li>`;
            return;
          }
          permTree.renderInto(folderRoot, res.rows);
          if (res.truncated) folderRoot.insertAdjacentHTML("beforeend", `<li class="hint">${esc(tr("labperm.truncated"))}</li>`);
          refreshEmptyState();
          if (res.is_main_admin) say(`  ${pick.dataset.name}: ${tr("labperm.mainAdminNote")}`);
          if (res.truncated) say(`  ${tr("labperm.truncated")}`);
        }
      });

      onlyVisible.addEventListener("change", () => {
        folderSection.querySelector(".labperm-tree").classList.toggle("hide-noaccess", onlyVisible.checked);
        refreshEmptyState();
      });
      // "exclusive": only folders where the selected principal is the sole
      // non-administrator with access (plus the path down to them)
      exclusiveCb.addEventListener("change", () => {
        folderSection.querySelector(".labperm-tree").classList.toggle("hide-nonexclusive", exclusiveCb.checked);
        refreshEmptyState();
      });
    }

    // --- Mode B: pick one folder, see who has access ------------------------
    function wireByFolder() {
      const pickSection = panel.querySelector('[data-role="perm-folder-pick"]');
      const resultSection = panel.querySelector('[data-role="perm-folder-result"]');
      const loadBtn = pickSection.querySelector(".labfs-load");
      const rootUl = pickSection.querySelector(".labfs-root");
      const selEl = pickSection.querySelector(".labfs-selected");
      const resultList = resultSection.querySelector(".labperm-result-list");
      const checkboxes = resultSection.querySelectorAll('.labperm-filter input[type="checkbox"]');
      const presetBtn = resultSection.querySelector(".labperm-preset-read");

      let PRINCIPALS = null;

      // groups-with-access, then users-with-access, then groups/users
      // without access - group before user within each access tier.
      function sortPrincipals(rows) {
        const rank = (p) => (p.access ? 0 : 2) + (p.kind === "group" ? 0 : 1);
        return rows.slice().sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name));
      }

      function adminBadge(p) {
        return p.is_main_admin ? ` <span class="labperm-admin-badge" title="${esc(tr("labperm.mainAdmin"))}">★</span>` : "";
      }

      const condMark = (p) => (p.conditional ? ` <span class="labperm-cond" title="${esc(tr("labperm.conditional"))}">∧</span>` : "");
      // a user's direct groups: "[👥 N]" (names on hover), click reveals them
      // indented below, comma-separated - mirrors mode A's "(N)" toggle.
      let GROUP_NAMES = new Map();
      function userGroupsHtml(p) {
        const ids = p.group_ids || [];
        if (!ids.length) return "";
        const names = ids.map((id) => GROUP_NAMES.get(String(id)) || String(id)).sort((a, b) => a.localeCompare(b));
        return (
          ` <span class="labperm-usergroups-toggle labperm-count" title="${esc(names.join(", "))}">[👥 ${ids.length}]</span>` +
          `<div class="labperm-usergroups-list" hidden>👥 ${names.map(esc).join(", ")}</div>`
        );
      }
      function userRowHtml(m) {
        return (
          `<li class="${m.access ? "" : "labperm-noaccess"}"><span class="labperm-name">👤 ${esc(m.name)}</span>${adminBadge(m)} ` +
          `<em class="labperm-access">(${esc(m.label)})</em>${condMark(m)}${userGroupsHtml(m)}</li>`
        );
      }
      function rowHtml(p) {
        if (p.kind !== "group") return userRowHtml(p);
        const cls = p.access ? "" : " labperm-noaccess";
        return (
          `<li class="labperm-group-row${cls}">` +
          `<span class="labperm-toggle-members" data-id="${esc(p.id)}">▸</span> <span class="labperm-name">👥 ${esc(p.name)}</span>${adminBadge(p)} ` +
          `<em class="labperm-access">(${esc(p.label)})</em>${condMark(p)} <span class="labperm-count">[👤 ${p.member_count}]</span>` +
          `<ul class="labperm-group-users" hidden></ul></li>`
        );
      }

      function renderResults() {
        if (!PRINCIPALS) return;
        const mask = Array.from(checkboxes)
          .filter((c) => c.checked)
          .reduce((m, c) => m | Number(c.dataset.bit), 0);
        let rows = PRINCIPALS.filter((p) => (mask ? (p.bits & mask) === mask : true));
        if (onlyAccessCb.checked) rows = rows.filter((p) => p.access);
        // "exclusive": who has access on their own merits - main
        // administrators bypass every ACL, so they are left out.
        if (exclusiveCb.checked) rows = rows.filter((p) => p.access && !p.is_main_admin);
        resultList.innerHTML = sortPrincipals(rows).map(rowHtml).join("") || `<li class="hint">(none)</li>`;
      }
      checkboxes.forEach((c) => c.addEventListener("change", renderResults));
      onlyAccessCb.addEventListener("change", renderResults);
      exclusiveCb.addEventListener("change", renderResults);
      presetBtn.addEventListener("click", () => {
        checkboxes.forEach((c) => (c.checked = c.dataset.bit === "1"));
        renderResults();
      });

      // a group row expands (indented) to its member users, each showing
      // their own resolved access to the same folder.
      resultList.addEventListener("click", (ev) => {
        const gtoggle = ev.target.closest(".labperm-usergroups-toggle");
        if (gtoggle) {
          gtoggle.nextElementSibling.hidden = !gtoggle.nextElementSibling.hidden;
          return;
        }
        const toggle = ev.target.closest(".labperm-toggle-members");
        if (!toggle) return;
        const li = toggle.closest("li");
        const ul = li.querySelector(".labperm-group-users");
        if (ul.hidden) {
          // rebuilt on every open (cheap - PRINCIPALS is already in memory)
          // so the "exclusive" filter applies to members too
          const gid = Number(toggle.dataset.id);
          let members = PRINCIPALS.filter((p) => p.kind === "user" && (p.group_ids || []).includes(gid));
          if (exclusiveCb.checked) members = members.filter((m) => m.access && !m.is_main_admin);
          ul.innerHTML = sortPrincipals(members).map(userRowHtml).join("") || `<li class="hint">(${esc(tr("labperm.emptyGroup"))})</li>`;
        }
        ul.hidden = !ul.hidden;
        toggle.classList.toggle("open", !ul.hidden);
      });

      const tree = wirePermTree(pickSection, {
        fetchRows: async (parentId) => {
          const res = await labPost("/api/lab/elo-children", { parent_id: String(parentId) });
          if (res.error) {
            say("! " + explainError(res.error), true);
            return [];
          }
          return (res.rows || []).filter((r) => r.is_folder);
        },
        onSelect: async (f) => {
          selEl.textContent = `${tr("labfs.selected")}: ${f.name} (id ${f.id})`;
          resultList.innerHTML = `<li class="hint">…</li>`;
          PRINCIPALS = null;
          const res = await labPost("/api/lab/perm-folder-principals", { folder_id: String(f.id) });
          if (res.error) {
            resultList.innerHTML = `<li class="err">${esc(explainError(res.error))}</li>`;
            return;
          }
          PRINCIPALS = res.principals;
          GROUP_NAMES = new Map(PRINCIPALS.filter((p) => p.kind === "group").map((g) => [String(g.id), g.name]));
          renderResults();
          sayAcl(res.folder || f, res.acl_items || [], null, null);
        },
      });

      loadBtn.addEventListener("click", async () => {
        loadBtn.disabled = true;
        const res = await labPost("/api/lab/elo-children", { parent_id: "1" });
        if (res.error) say("! " + explainError(res.error), true);
        tree.renderInto(rootUl, res.error ? [] : (res.rows || []).filter((r) => r.is_folder));
        rootUl.hidden = false;
        loadBtn.hidden = true;
      });
    }

    // --- Mode C: folders whose ACL departs from their parent's -------------
    // ELO copies the parent's ACL onto every new child, so a child that
    // differs (entries added / removed / access changed) had special
    // permissions set on purpose. The tree keeps the path down to such
    // folders; "only special" hides everything else.
    function wireBySpecial() {
      const section = panel.querySelector('[data-role="perm-special"]');
      const depthInput = section.querySelector(".labperm-depth");
      const onlySpecial = section.querySelector(".labperm-only-special");
      const loadBtn = section.querySelector(".labperm-load-special");
      const rootUl = section.querySelector(".labperm-special-root");
      const emptyMsg = section.querySelector(".labperm-empty-msg");
      const treeEl = section.querySelector(".labperm-tree");

      function refreshEmptyState() {
        const rows = Array.from(rootUl.children).filter((li) => li.tagName === "LI" && !li.classList.contains("hint"));
        emptyMsg.hidden = !onlySpecial.checked || rows.length === 0 || rows.some((li) => li.getClientRects().length > 0);
      }

      const tree = wirePermTree(section, {
        fetchRows: async (parentId) => {
          const res = await labPost("/api/lab/perm-special", { parent_id: String(parentId), depth: 1 });
          if (res.error) {
            say("! " + explainError(res.error), true);
            return [];
          }
          return res.rows;
        },
        onSelect: async (f) => {
          const res = await labPost("/api/lab/perm-folder-acl", { folder_id: String(f.id) });
          if (res.error) return say("! " + explainError(res.error), true);
          sayAcl(res.folder, res.entries, res.owner, null, res.diff);
        },
      });

      loadBtn.addEventListener("click", async () => {
        loadBtn.disabled = true;
        const depth = Math.max(1, Math.min(6, Number(depthInput.value) || 1));
        rootUl.hidden = false;
        rootUl.innerHTML = SPINNER_ROW;
        const res = await labPost("/api/lab/perm-special", { parent_id: "1", depth });
        loadBtn.disabled = false;
        if (res.error) {
          rootUl.innerHTML = `<li class="err">${esc(explainError(res.error))}</li>`;
          return;
        }
        tree.renderInto(rootUl, res.rows);
        if (res.truncated) {
          rootUl.insertAdjacentHTML("beforeend", `<li class="hint">${esc(tr("labperm.truncated"))}</li>`);
          say(`  ${tr("labperm.truncated")}`);
        }
        const count = section.querySelectorAll("li.labperm-special").length;
        say(`  ${res.parent.name}: ${count} ${tr("labperm.specialFound")}`);
        // the button stays: change the depth and load again
        refreshEmptyState();
      });

      onlySpecial.addEventListener("change", () => {
        treeEl.classList.toggle("hide-plain", onlySpecial.checked);
        refreshEmptyState();
      });
    }

    // --- Mode D: diagnostics - ACL smells, each explained (why / how to fix) --
    // The backend only emits a `code` per finding; the wording lives in i18n
    // as labperm.diag.<code>.{title,why,fix}, so the explanations translate.
    const DIAG_SEVERITY = {
      write_without_read: "err", everyone_full: "err",
      orphan_entry: "warn", admin_only: "warn", and_unsatisfiable: "warn",
      empty_group: "info", users_without_groups: "info", groups_without_members: "info",
    };
    const DIAG_ORDER = Object.keys(DIAG_SEVERITY);
    const SEV_ICON = { err: "⛔", warn: "⚠", info: "ℹ" };
    function wireDiagnostics() {
      const section = panel.querySelector('[data-role="perm-diag"]');
      const depthInput = section.querySelector(".labperm-depth");
      const runBtn = section.querySelector(".labperm-run-diag");
      const status = section.querySelector(".labperm-diag-status");
      const results = section.querySelector(".labperm-diag-results");

      const entryHtml = (e) =>
        e ? `<span class="labperm-name">${ACL_ICON[e.kind] || "•"} ${esc(e.name)}</span>` + (e.label ? ` <em class="labperm-access">(${esc(e.label)})</em>` : "") : "";
      const findingHtml = (f) => {
        const folder = f.folder
          ? `<button class="labfs-pick labperm-diag-folder" data-id="${esc(f.folder.id)}" title="id ${esc(f.folder.id)}">📁 ${esc(f.folder.path || f.folder.name)}</button>`
          : "";
        const ands = f.and_groups ? ` <span class="hint">AND ${esc(f.and_groups.join(", "))}</span>` : "";
        const n = typeof f.entries === "number" ? ` <span class="hint">(${f.entries} ${tr("labperm.diagEntries")})</span>` : "";
        return `<li>${folder}${folder && f.entry ? " — " : ""}${entryHtml(f.entry)}${ands}${n}</li>`;
      };

      function render(res) {
        const groups = new Map();
        res.findings.forEach((f) => {
          if (!groups.has(f.code)) groups.set(f.code, []);
          groups.get(f.code).push(f);
        });
        const codes = DIAG_ORDER.filter((c) => groups.has(c)).concat(Array.from(groups.keys()).filter((c) => !DIAG_ORDER.includes(c)));
        if (!codes.length) {
          results.innerHTML = `<p class="hint">✓ ${esc(tr("labperm.diagNone"))}</p>`;
          return;
        }
        results.innerHTML = codes
          .map((code) => {
            const sev = DIAG_SEVERITY[code] || "info";
            const items = groups.get(code);
            const t = (k) => tr(`labperm.diag.${code}.${k}`);
            return (
              `<details class="labperm-diag-group sev-${sev}"${sev === "err" ? " open" : ""}>` +
              `<summary><span class="labperm-diag-sev">${SEV_ICON[sev]}</span> ${esc(t("title"))} <span class="labperm-count">[${items.length}]</span></summary>` +
              `<div class="labperm-diag-body">` +
              `<p><b>${esc(tr("labperm.diagWhy"))}</b> ${esc(t("why"))}</p>` +
              `<p><b>${esc(tr("labperm.diagFix"))}</b> ${esc(t("fix"))}</p>` +
              `<ul class="labperm-diag-list">${items.map(findingHtml).join("")}</ul>` +
              `</div></details>`
            );
          })
          .join("");
      }

      runBtn.addEventListener("click", async () => {
        runBtn.disabled = true;
        status.textContent = tr("labperm.loading");
        results.innerHTML = "";
        const depth = Math.max(1, Math.min(6, Number(depthInput.value) || 1));
        const res = await labPost("/api/lab/perm-diagnose", { parent_id: "1", depth });
        runBtn.disabled = false;
        if (res.error) {
          status.textContent = "";
          results.innerHTML = `<p class="err">${esc(explainError(res.error))}</p>`;
          return;
        }
        status.textContent = `${res.scanned} ${tr("labperm.diagScanned")}, ${res.findings.length} ${tr("labperm.diagFindings")}` + (res.truncated ? ` — ${tr("labperm.truncated")}` : "");
        render(res);
        say(`  ${tr("labperm.modeDiag")} (${res.parent.name}): ` + Object.entries(res.summary).map(([c, n]) => `${tr(`labperm.diag.${c}.title`)}: ${n}`).join(" · "));
      });

      // a finding's folder dumps its ACL into the log, like everywhere else
      results.addEventListener("click", async (ev) => {
        const pick = ev.target.closest(".labperm-diag-folder");
        if (!pick) return;
        const res = await labPost("/api/lab/perm-folder-acl", { folder_id: String(pick.dataset.id) });
        if (res.error) return say("! " + explainError(res.error), true);
        sayAcl(res.folder, res.entries, res.owner, null, res.diff);
      });
    }

    // --- Mode E: org chart - group nesting, or the supervisor tree -----------
    // ELO has no org-chart RPC; a group's UserInfo.groupList names its parent
    // groups and a user's superiorId its supervisor. Drawn as a CSS tree:
    // roots side by side, children below. A group under several parents is
    // drawn under each (marked ↗). Clicking a node reveals its members
    // (groups) or its groups (users).
    function wireOrgChart() {
      const section = panel.querySelector('[data-role="perm-org"]');
      const chartButtons = section.querySelectorAll(".labperm-modes button");
      const loadBtn = section.querySelector(".labperm-load-org");
      const status = section.querySelector(".labperm-org-status");
      const host = section.querySelector(".labperm-org-host");
      const hideEmpty = section.querySelector(".labperm-org-hide-empty");
      let DATA = null;
      let CHART = "groups";
      hideEmpty.addEventListener("change", () => render());

      const admin = (p) => (p.is_main_admin ? ` <span class="labperm-admin-badge" title="${esc(tr("labperm.mainAdmin"))}">★</span>` : "");

      function groupsForest() {
        const byId = new Map(DATA.groups.map((g) => [g.id, g]));
        // an everyone-group ("Jeder") is the parent of half the directory and
        // says nothing about structure - it is drawn as a lone dashed node
        // and never as a parent.
        const realParents = (g) => g.parent_ids.filter((p) => byId.has(p) && !byId.get(p).everyone);
        const children = new Map();
        DATA.groups.forEach((g) => realParents(g).forEach((p) => {
          if (!children.has(p)) children.set(p, []);
          children.get(p).push(g);
        }));
        const membersOf = (gid) => DATA.users.filter((u) => u.group_ids.includes(gid));
        const shown = (g) => !hideEmpty.checked || g.total_members > 0 || (children.get(g.id) || []).length > 0;
        const node = (g, path) => {
          const kids = (children.get(g.id) || []).filter((k) => !path.has(k.id) && shown(k));
          const parents = realParents(g);
          const again = parents.length > 1 ? ` <span class="labperm-org-multi" title="${esc(tr("labperm.orgMultiParent"))}: ${esc(parents.map((p) => byId.get(p).name).join(", "))}">↗</span>` : "";
          const members = membersOf(g.id);
          return (
            `<li><div class="labperm-org-node${g.everyone ? " everyone" : ""}" data-kind="group" data-id="${esc(g.id)}" title="id ${esc(g.id)} · ${members.length} ${esc(tr("labperm.showMembers"))}, ${g.total_members} ${esc(tr("labperm.orgTotal"))}">` +
            `👥 ${esc(g.name)}${admin(g)}${again} <span class="labperm-count">[👤 ${members.length}]</span>` +
            `<div class="labperm-org-members" hidden>${members.length ? members.map((u) => `👤 ${esc(u.name)}${admin(u)}`).join(", ") : `<span class="hint">${esc(tr("labperm.emptyGroup"))}</span>`}</div>` +
            `</div>` +
            (kids.length ? `<ul>${kids.map((k) => node(k, new Set([...path, g.id]))).join("")}</ul>` : "") +
            `</li>`
          );
        };
        const roots = DATA.groups.filter((g) => realParents(g).length === 0 && shown(g));
        // nested groups first (they make a tree), then the flat ones, then everyone-groups
        roots.sort((a, b) => ((children.get(b.id) || []).length - (children.get(a.id) || []).length) || (a.everyone - b.everyone) || a.name.localeCompare(b.name));
        return `<ul>${roots.map((g) => node(g, new Set())).join("")}</ul>`;
      }

      function superiorsForest() {
        const byId = new Map(DATA.users.map((u) => [u.id, u]));
        const groupName = new Map(DATA.groups.map((g) => [g.id, g.name]));
        const reports = new Map();
        DATA.users.forEach((u) => {
          if (u.superior_id && byId.has(u.superior_id) && u.superior_id !== u.id) {
            if (!reports.has(u.superior_id)) reports.set(u.superior_id, []);
            reports.get(u.superior_id).push(u);
          }
        });
        const node = (u, path) => {
          const kids = (reports.get(u.id) || []).filter((k) => !path.has(k.id));
          const groups = u.group_ids.map((g) => groupName.get(g) || g).sort((a, b) => a.localeCompare(b));
          return (
            `<li><div class="labperm-org-node" data-kind="user" data-id="${esc(u.id)}" title="id ${esc(u.id)}">` +
            `👤 ${esc(u.display_name || u.name)}${admin(u)}` + (kids.length ? ` <span class="labperm-count">[👤 ${kids.length}]</span>` : "") +
            `<div class="labperm-org-members" hidden>${groups.length ? `👥 ${groups.map(esc).join(", ")}` : `<span class="hint">${esc(tr("labperm.orgNoGroups"))}</span>`}</div>` +
            `</div>` +
            (kids.length ? `<ul>${kids.map((k) => node(k, new Set([...path, u.id]))).join("")}</ul>` : "") +
            `</li>`
          );
        };
        const roots = DATA.users.filter((u) => !u.superior_id || !byId.has(u.superior_id));
        roots.sort((a, b) => ((reports.get(b.id) || []).length - (reports.get(a.id) || []).length) || a.name.localeCompare(b.name));
        return `<ul>${roots.map((u) => node(u, new Set())).join("")}</ul>`;
      }

      function render() {
        if (!DATA) return;
        host.innerHTML = `<div class="labperm-orgtree">${CHART === "groups" ? groupsForest() : superiorsForest()}</div>`;
        const withBoss = DATA.users.filter((u) => u.superior_id).length;
        status.textContent = `${DATA.groups.length} ${tr("labperm.groupsTab")}, ${DATA.users.length} ${tr("labperm.usersTab")}, ${withBoss} ${tr("labperm.orgWithSuperior")}`;
      }

      chartButtons.forEach((b) =>
        b.addEventListener("click", () => {
          chartButtons.forEach((x) => x.classList.toggle("active", x === b));
          CHART = b.dataset.chart;
          render();
        })
      );
      loadBtn.addEventListener("click", async () => {
        loadBtn.disabled = true;
        status.textContent = tr("labperm.loading");
        const res = await labPost("/api/lab/perm-org-chart", {});
        loadBtn.disabled = false;
        if (res.error) {
          status.textContent = "";
          host.innerHTML = `<p class="err">${esc(explainError(res.error))}</p>`;
          return;
        }
        DATA = res;
        render();
      });
      // a node toggles its members / groups box
      host.addEventListener("click", (ev) => {
        const node = ev.target.closest(".labperm-org-node");
        if (!node) return;
        const box = node.querySelector(".labperm-org-members");
        box.hidden = !box.hidden;
        node.classList.toggle("open", !box.hidden);
      });
    }

    wireByPrincipal();
    wired.byPrincipal = true;
  }
  // <<< lab-perms slice

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

    const langs = RUNTIMES.filter((k) => runtimeEnabled(k) && (topic.snippets || {})[k]);
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

        ${
          topic.attach_file
            ? `<div class="attach">
                 <label class="attach-btn"><span>${esc(tr("attach.choose"))}</span>
                   <input type="file" hidden /></label>
                 <span class="attach-name">${esc(tr("attach.none"))}</span>
                 <button class="attach-clear" title="clear" hidden>&times;</button>
               </div>`
            : ""
        }

        ${topic.lab_fs ? labFsPanelHtml() : ""}
        ${topic.lab_perms ? labPermsPanelHtml() : ""}

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

    // ---- optional "Choose file" picker (topic.attach_file) ----------
    let ATTACH = null; // { name, b64 } or null -> the snippet sends a sample
    const attachBox = host.querySelector(".attach");
    if (attachBox) {
      const input = attachBox.querySelector('input[type="file"]');
      const nameEl = attachBox.querySelector(".attach-name");
      const clearBtn = attachBox.querySelector(".attach-clear");
      const CAP = 8 * 1024 * 1024;
      const setNone = () => {
        ATTACH = null;
        nameEl.textContent = tr("attach.none");
        nameEl.classList.remove("err");
        clearBtn.hidden = true;
        input.value = "";
      };
      input.addEventListener("change", () => {
        const f = input.files && input.files[0];
        if (!f) return setNone();
        if (f.size > CAP) {
          ATTACH = null;
          nameEl.textContent = tr("attach.tooBig");
          nameEl.classList.add("err");
          clearBtn.hidden = false;
          return;
        }
        const fr = new FileReader();
        fr.onload = () => {
          ATTACH = { name: f.name, b64: String(fr.result).split(",")[1] || "" };
          nameEl.textContent = `${f.name} (${Math.max(1, Math.round(f.size / 1024))} KB)`;
          nameEl.classList.remove("err");
          clearBtn.hidden = false;
        };
        fr.readAsDataURL(f);
      });
      clearBtn.addEventListener("click", setNone);
    }

    // ---- interactive ELO <-> local filesystem panel (topic.lab_fs) --
    if (topic.lab_fs) wireLabFs(host);
    // ---- interactive user/folder permissions panel (topic.lab_perms) --
    if (topic.lab_perms) wireLabPerms(host);

    const sub = host.querySelector(".subtabs");
    const snipHost = host.querySelector(".snippet-host");
    // Keep one detached runner per language. Switching a tab is therefore a
    // purely client-side DOM swap: the topic, edited code and output survive.
    const runners = new Map();
    function showLang(lang) {
      store.set(LS.sub, lang);
      $$(".sub", sub).forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
      let runner = runners.get(lang);
      if (!runner) {
        runner = makeRunner(lang, topic.snippets[lang], topic.id, "t:" + topic.id, () => ATTACH);
        runners.set(lang, runner);
      }
      snipHost.replaceChildren(runner);
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
  function makeRunner(language, code, topicId, cacheKey, getAttach) {
    code = applyCreds(code, language); // seed the ELO_* constants from the form
    let original = code;
    const cmMode = codeMirrorMode(language);
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
        <div class="output-head"><span class="oh-left"><span>${esc(tr("topic.output"))}</span></span><span class="meta"></span></div>
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
    wireOutputFormatters(wrap.querySelector(".output-head"), out);

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

    // re-sync the ELO_* constants when the connection form changes. Only those
    // three lines move; the user's other edits (and the "edited" flag) survive.
    wrap._syncCreds = () => {
      const before = getCode();
      const after = applyCreds(before, language);
      original = applyCreds(original, language);
      if (after !== before) {
        setCode(after);
        if (cm) cm.refresh();
      }
      refreshMeta();
    };

    // --- buttons -------------------------------------------------------
    btn.addEventListener("click", () => {
      const attach = getAttach ? getAttach() : null;
      // a pre-computed static result only matches the ORIGINAL snippet + no file
      const key = isEdited() || attach ? null : cacheKey;
      runAny(language, getCode(), topicId, out, meta, btn, key, attach);
    });
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
    const langs = RUNTIMES.filter((k) => runtimeEnabled(k) && (data[k] || []).length);
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
            `<pre class="code"><code class="language-${highlightLanguage(lang)}">${esc(f.code)}</code></pre></div>`
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
    const langs = RUNTIMES.filter(runtimeEnabled);
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
    const runners = new Map();
    function showLang(lang) {
      $$(".sub", sub).forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
      let runner = runners.get(lang);
      if (!runner) {
        runner = makeRunner(lang, d.snippets[lang], null);
        runners.set(lang, runner);
      }
      snipHost.replaceChildren(runner);
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
  let SCRATCH_SYNC = null;
  function wireScratchpad() {
    const langSel = $("#scratch-lang");
    const runBtn = $("#scratch-run");
    const codeEl = $("#scratch-code");
    const out = $("#scratch-output");
    const meta = $("#scratch-meta");
    wireOutputFormatters(out.closest(".output-wrap").querySelector(".output-head"), out);
    const samples = {
      python:
        'import os\nfrom elo_playground import connect\n\n' +
        '# local ELO test box (or set ELOPG_* / .env)\n' +
        'ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url\n' +
        'ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user\n' +
        'ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password\n\n' +
        'elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)\n' +
        'print(elo.call("getServerInfo", {}).get("version"))\n',
      node:
        'import { connect } from "elo-playground";\n\n' +
        '// local ELO test box (or set ELOPG_* / .env)\n' +
        'const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url\n' +
        'const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user\n' +
        'const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password\n\n' +
        'const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });\n' +
        'console.log((await elo.call("getServerInfo", {})).version);\n',
      browser:
        '// local ELO test box (or set ELOPG_* / .env)\n' +
        'const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url\n' +
        'const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user\n' +
        'const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password\n\n' +
        'const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });\n' +
        'console.log((await elo.call("getServerInfo", {})).version);\n',
      go:
        'package main\n\nimport (\n  "encoding/json"\n  "fmt"\n  "example.com/elopg/elo"\n)\n\nfunc main() {\n' +
        '  ELO_BASE_URL := elo.Env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") // ELOPG_DEFAULT:base_url\n' +
        '  ELO_USER := elo.Env("ELOPG_ELO_USER", "Administrator") // ELOPG_DEFAULT:user\n' +
        '  ELO_PASS := elo.Env("ELOPG_ELO_PASSWORD", "elo") // ELOPG_DEFAULT:password\n\n' +
        '  client := elo.New(ELO_BASE_URL, ELO_USER, ELO_PASS)\n  result, err := client.Call("getServerInfo", json.RawMessage(`{}`))\n  if err != nil { panic(err) }\n  fmt.Println(string(result))\n}\n',
      php:
        '<?php\nrequire_once __DIR__ . "/EloClient.php";\n\n' +
        '$ELO_BASE_URL = getenv("ELOPG_ELO_BASE_URL") ?: "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url\n' +
        '$ELO_USER = getenv("ELOPG_ELO_USER") ?: "Administrator"; // ELOPG_DEFAULT:user\n' +
        '$ELO_PASS = getenv("ELOPG_ELO_PASSWORD") ?: "elo"; // ELOPG_DEFAULT:password\n\n' +
        '$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);\necho json_encode($elo->call("getServerInfo", [])), PHP_EOL;\n',
      java:
        'public final class Main {\n  public static void main(String[] args) throws Exception {\n' +
        '    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url\n' +
        '    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user\n' +
        '    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password\n\n' +
        '    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);\n    System.out.println(elo.call("getServerInfo", "{}"));\n  }\n}\n',
      rhino:
        '// Reviewed IndexServer script; deploy server-side, never into Web Client.\n' +
        'var ELO_BASE_URL = java.lang.System.getenv("ELOPG_ELO_BASE_URL") || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url\n' +
        'var ELO_USER = java.lang.System.getenv("ELOPG_ELO_USER") || "Administrator"; // ELOPG_DEFAULT:user\n' +
        'var ELO_PASS = java.lang.System.getenv("ELOPG_ELO_PASSWORD") || "elo"; // ELOPG_DEFAULT:password\n\n' +
        'function playgroundIx(baseUrl, user, password) {\n  if (!baseUrl || !user || !password) throw "ELO connection settings are required";\n  return ixConnect.ix();\n}\n\n' +
        'function RF_playground_server_info(ec, args) {\n  return playgroundIx(ELO_BASE_URL, ELO_USER, ELO_PASS).getServerInfo();\n}\n',
    };
      const cmMode = codeMirrorMode;

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

    SCRATCH_SYNC = () => {
      const before = getCode();
      const after = applyCreds(before, langSel.value);
      if (after !== before) setCode(after);
    };

    langSel.addEventListener("change", () => {
      if (SCRATCH_CM) SCRATCH_CM.setOption("mode", cmMode(langSel.value));
      if (!touched) setCode(samples[langSel.value]);
    });
    runBtn.addEventListener("click", () => runAny(langSel.value, getCode(), null, out, meta, runBtn));
  }

  async function runConnCheck() {
    const status = $("#conn-status");
    if (isMock()) {
      status.textContent = tr("conn.mockOn");
      status.className = "conn-status ok";
      return;
    }
    if (STATIC) {
      status.textContent = tr("static.backendOnly");
      status.className = "conn-status err";
      return;
    }
    status.textContent = tr("conn.checking");
    status.className = "conn-status";
    const res = await postJSON("/api/elo/login-check", creds());
    status.textContent = res.detail || (res.ok ? "ok" : "failed");
    status.className = "conn-status " + (res.ok ? "ok" : "err");
  }

  // label the http/https toggle with the scheme it will switch TO
  function updateSchemeBtn() {
    const btn = $("#conn-scheme");
    if (!btn) return;
    const isHttps = /^https:\/\//i.test(($("#conn").base_url.value || "").trim());
    btn.textContent = isHttps ? "→ http" : "→ https";
  }

  // push the current form user / password / Base URL into every open runner's
  // ELO_* constants (debounced)
  let credSyncTimer = 0;
  function syncOpenRunnersCreds() {
    clearTimeout(credSyncTimer);
    credSyncTimer = setTimeout(() => {
      $$("#topic-host .runner, #spec-host .runner").forEach((r) => {
        if (typeof r._syncCreds === "function") r._syncCreds();
      });
      if (typeof SCRATCH_SYNC === "function") SCRATCH_SYNC();
    }, 200);
  }

  function wireConn() {
    const f = $("#conn");
    f.addEventListener("change", saveConn); // covers the checkboxes
    f.base_url.addEventListener("input", updateSchemeBtn);
    // persist + propagate on every keystroke, not just on blur ("change"), so a
    // reload right after typing does not lose the URL / user / password
    ["base_url", "user", "password"].forEach((n) =>
      f[n].addEventListener("input", () => {
        saveConn();
        syncOpenRunnersCreds();
      })
    );
    $("#conn-check").addEventListener("click", runConnCheck);

    // flip the Base URL between http:// and https:// and re-test. ELO's default
    // IX ports are paired (9090 http / 9093 https), so swap an explicit default
    // port too. Switching to https also drops TLS verify (local ELO is
    // self-signed); a non-default port is left as the user set it.
    const HTTP_PORT = "9090";
    const HTTPS_PORT = "9093";
    $("#conn-scheme").addEventListener("click", () => {
      let raw = (f.base_url.value || "").trim();
      if (!raw) raw = "http://localhost:9090/ix-Repository1";
      if (!/^https?:\/\//i.test(raw)) raw = "http://" + raw;
      let u;
      try {
        u = new URL(raw);
      } catch (e) {
        return;
      }
      if (u.protocol === "http:") {
        u.protocol = "https:";
        if (u.port === HTTP_PORT) u.port = HTTPS_PORT;
        // a TLS cert never matches "localhost" - use the server's real hostname
        if (CFG.serverHost && /^(localhost|127\.0\.0\.1)$/i.test(u.hostname)) {
          u.hostname = CFG.serverHost;
        }
        f.tls_verify.checked = false;
      } else {
        u.protocol = "http:";
        if (u.port === HTTPS_PORT) u.port = HTTP_PORT;
      }
      f.base_url.value = u.toString().replace(/\/$/, "");
      updateSchemeBtn();
      saveConn();
      syncOpenRunnersCreds();
      runConnCheck();
    });
    updateSchemeBtn();
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
      ["#conn-check", "#conn-scheme"].forEach((s) => {
        const b = $(s);
        if (b) b.hidden = true; // both need the backend to test
      });
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
    wireRuntimeSettings();
    try {
      await loadRuntimes();
    } catch (e) {
      // The static mock build has no runtime endpoint; it intentionally keeps
      // all examples visible and does not require optional local toolchains.
    }
    if (STATIC) await enterStaticMode();
    renderVersion();
    await loadCatalog();
    reopenLast();
    if (store.get("elopg.runtime-onboarded.v1", "") !== "1") openRuntimeSettings(true);
  })();
})();
