# FAQ

## What is `elo_playground` / `from elo_playground import connect`?

A deliberately small, heavily-commented client that wraps the raw ELO IX REST
calls. It is **not** part of ELO - it lives in this project under `shared/` and
you can copy it into your own code. Every snippet uses it so the interesting
part stays the ELO call, not the plumbing. The **"The elo_playground client"**
entry at the top of the Catalog shows its full source.

Surface (the same in all three runtimes):

| | what it does |
|---|---|
| `connect()` | build a client from env vars / the form and log in (returns a mock client in Mock mode) |
| `elo.call(method, body)` | one RPC: `POST {base}/rest/IXServicePortIF/<method>`, returns `result`, raises `EloError` on the `{exception}` envelope |
| `elo.login()` | open the IX session (`connect()` already does this) |
| `elo.find_all(...)` / `elo.findAll(...)` | drive a `findFirst` / `findNext` / `findClose` loop to the end |
| `elo.download(url)` / `elo.upload(url, bytes)` | GET / POST a document's bytes on the same session |

## Why do the Python, Node and browser clients differ?

The **snippet-facing surface is the same** - that is why the three code blocks
read almost identically. The differences are:

1. **`find_all` (Python) vs `findAll` (Node / browser)** - naming idiom.
   `snake_case` is idiomatic Python, `camelCase` is idiomatic JS.
2. **`download()` / `upload()` throw in the browser.** A page cannot reach ELO's
   document connector (usually `:9093`, a different origin - CORS - and the URL
   carries a session ticket). The method exists for a uniform surface but fails
   fast, telling you to do that step from Python or Node.
3. **The transport is fundamentally different.** Python and Node run
   server-side: they hold the credentials and call
   `{base}/rest/IXServicePortIF/<method>` **directly** (`httpx` / `fetch`),
   HTTP Basic on every request. The **browser cannot**: it must not hold the
   password and its origin differs from ELO's, so by default each `elo.call()`
   goes through this app's own backend (`POST /api/elo/proxy`), which holds the
   connection. The static demo adds a local mock path and an optional
   "call the URL directly" path (needs CORS on that server). None of this leaks
   into snippet code.

## Mock mode vs live mode

- **Mock** (default): calls are answered from `fixtures/ix/default.json` plus the
  topic's own `mock:` block. No ELO needed. Great for reading the shapes.
- **Live**: untick *Mock*, fill in Base URL + Port + user + password, press
  *Check connection*, then *Run*. Python and Node then call your ELO directly;
  browser snippets go through the backend proxy.

## Where does `connect()` get the credentials? Why isn't the password in the code?

`connect()` reads the connection from **environment variables** -
`ELOPG_ELO_BASE_URL`, `ELOPG_ELO_USER`, `ELOPG_ELO_PASSWORD`,
`ELOPG_TLS_VERIFY`. If a variable is unset (or empty), it falls back to the
values for a stock local ELO test box: `Administrator` / `elo` on
`http://localhost:9090/ix-Repository1`. So a snippet copied into your own
project runs as-is against a local ELO, and you override any of it by setting
the `ELOPG_*` variables.

When you press **Run** in the playground, the connection form's values are
passed through as `ELOPG_*` for that one run - so whatever you type in the form
wins over the defaults. The form itself pre-fills from your local `.env`
(`ELOPG_ELO_PASSWORD=...`), and *Remember password* keeps it in this browser.

## The static demo (GitHub Pages) - what runs?

The published demo has no backend. It behaves like the app, defaulting to Mock:

- **Browser** snippets run for real in the sandboxed iframe against a JS mock.
- **Python / Node** snippets show their pre-computed Mock output (the build ran
  each one).
- Untick Mock + enter a reachable ELO Base URL + credentials, and **Browser**
  snippets call that server directly - it must send CORS headers for the demo's
  origin, which most ELO installs do not by default.

## Base URL and Port

The connection form has a **Port** field (default **9090**, the ELO Indexserver
HTTP port). It is spliced into the Base URL for every call and doc link, so you
can point at a different port without rewriting the URL.

## Versioning

The backend and the frontend are versioned independently and both are shown in
the top-right corner as `UI x · API y`. Backend version:
`backend-python/app/__init__.py`. Frontend version: `frontend/VERSION`. Endpoint:
`GET /api/version`.

A pre-commit hook bumps the patch number automatically: touching `frontend/`
bumps the frontend version, touching `backend-python/` / `backend-node/` /
`shared/` bumps the backend version, once per commit. Enable it per clone with
`git config core.hooksPath .githooks` (the start scripts do this).

## "API reference" tab

Browses `openapi.json`:

- **Live** (Mock off, a reachable Base URL): all operations the server exposes
  (~358 across ~12 services on ELO 25).
- **Offline / Mock**: a trimmed `fixtures/openapi.sample.json` (~24 operations,
  tagged "sample").

Each operation links to the schema and to ELO's own reference for it.

## Where does my code run? Is it safe?

- **Python / Node**: in a child process on the backend, on the machine running
  the app, with a timeout and an output cap - **no real sandbox**.
- **Browser**: in a `sandbox="allow-scripts"` iframe on your page.
- CORS is wide open (`*`) and there is no auth. This is fine for a **local
  development tool**; do not expose it on a shared server without adding a
  sandbox, auth, tighter CORS and rate limiting.

## Is this an ELO product?

No. Independent learning project, MIT-licensed, not affiliated with or endorsed
by ELO Digital Office GmbH. Request/response shapes were verified against an
ELO 25 (25.0.1.3) test instance; other versions may differ - always check your
own server's `{base_url}/rest/openapi.json`.
