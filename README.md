# ELO API Playground

An interactive site for **learning the ELO IX REST API by example**. Every topic
shows the minimum call needed to produce a documented result, in three runtimes -
**Python backend**, **Node.js backend**, **browser JS** - with short, heavily
commented snippets you can run live. It works offline in **mock mode** and against
a real ELO on `localhost`. UI in English / German / Spanish.

25 topics across 9 categories today; adding more is one YAML file each (see below).

Self-contained: one FastAPI backend, one small Express service, a shared client
in three languages, and a no-build-step frontend. Python 3.12 + Node 18+.

> ⚠️ The **Run** button executes code on *this machine* with *your ELO
> credentials*. Use it only on a local development box.

---

## Layout

```
elo-api-playground/
  backend-python/     FastAPI app - the page, the catalogue API, the Python runner,
                      and the browser -> ELO proxy
  backend-node/       Express service - runs Node snippets natively; a couple of
                      endpoints call ELO directly through the shared Node client
  shared/             the "import and simplify" client, one per runtime, same surface:
    python/elo_playground/   connect() / EloClient / MockEloClient
    node/eloClient.mjs
    browser/eloClient.browser.js
  catalog/            the curated content - one YAML per topic, grouped by category,
                      plus optional _deep.md "deep dive" companions
  snippets/           the same snippets materialised as standalone files
                      (snippets/<language>/<category>/<topic>.<ext>) - generated,
                      kept in git, checked in CI
  fixtures/ix/        canned IX responses for mock mode
  frontend/           Jinja shell + one vanilla-JS file + vendored libs (no build step)
  scripts/            build_snippets.py, run.ps1, smoke.py
```

## How ELO's "REST" API actually works

It is an **RPC mapping of the SOAP `IXServicePortIF`**:

```
POST {base_url}/rest/IXServicePortIF/<method>
Content-Type: application/json
Authorization: Basic <base64(user:password)>      <-- on EVERY request

request  : a JSON parameters object ({} if none)
response : {"result": <value>}    on success
           {"exception": <info>}  on a handled error (HTTP is still 200)
```

The authoritative schema for **your** server is served by the server itself at
`{base_url}/rest/openapi.json`. Every topic's "ELO API used" table links there and
names the `operationId` to look up.

## The three runtimes

| Runtime | Talks to ELO | Notes |
|---|---|---|
| **Python** | directly (`httpx`) | runs in a child process on the FastAPI backend |
| **Node** | directly (`fetch`) | runs on the Express service (`backend-node`) |
| **Browser** | via the backend proxy | a page must not hold the ELO password and cannot cross CORS, so `eloClient.browser.js` POSTs each call to `/api/elo/proxy`, which forwards it |

All three expose the same methods - `connect()`, `call()`, `login()`,
`find_all()` / `findAll()` - so the snippets read almost identically.

## Setup

```powershell
cd elo-api-playground   # the repo root

# Python
python -m venv .venv
.\.venv\Scripts\pip install -r backend-python\requirements-dev.txt

# Node (links the shared client into node_modules, installs express)
npm install

# optional: copy env.sample to .env and edit
copy env.sample .env
```

## Run

Double-click **`start.bat`** (or `.\scripts\run.ps1`). It creates `.env` from
`env.sample` if needed, runs `npm install` on first use, starts the Node runner
on `:8787` and the FastAPI app on `:8010`, each in its own window, then opens
<http://127.0.0.1:8010>. Change the ports with `ELOPG_PORT` / `ELOPG_NODE_URL`
in `.env`.

- **Mock mode** (default): every snippet runs against `fixtures/ix/` + the topic's
  own `mock:` block. No ELO needed.
- **Live mode**: untick *Mock mode*, fill in the connection form (a stock local
  ELO is `http://localhost:9090/ix-Repository1`, user `Administrator`), press
  *Check connection*, then *Run*.

Pending work and the roadmap live in [`TODO.md`](TODO.md).

## Tabs

- **Catalog** - curated topics grouped by category, each with a minimal call in
  Python / Node / browser, links into the schema, and a Run button. Some
  categories have a **Deep dive** with longer runnable examples. Pinned at the
  top: **The elo_playground client** - the intro, a method table, and the full
  commented source of the shared client (what `from elo_playground import connect`
  actually is).
- **API reference** - browses the server's own `openapi.json`: **live** = all
  ~358 operations across 12 services; **offline / Mock** = the trimmed
  `fixtures/openapi.sample.json` (~24 ops, tagged "sample"). Per operation:
  request parameters, response schema, links to curated topics, and a generated
  `elo.call(...)` skeleton in all three runtimes.
- **Scratchpad** - CodeMirror editor + language selector + Run.
- **FAQ** - the questions below, rendered in-app (`frontend/faq.md`, served at
  `GET /api/faq`).

Every runnable snippet lists, under its output, the functions it calls: ELO
client methods and IX operation names link into this site, generic
JavaScript / Python builtins link to MDN / docs.python.org.

## FAQ

### What is `elo_playground` / `from elo_playground import connect`?

A deliberately small, heavily-commented client that wraps the raw ELO IX REST
calls. It is **not** part of ELO - it lives under `shared/` and you can copy it
into your own code. Every snippet uses it so the interesting part stays the ELO
call, not the plumbing. Same surface in all three runtimes: `connect()`,
`elo.call(method, body)`, `elo.login()`, `elo.find_all(...)` /
`elo.findAll(...)`, `elo.download(url)` / `elo.upload(url, bytes)`.

### Why do the Python, Node and browser clients differ?

The snippet-facing surface is the same - that is why the three code blocks read
almost identically. The differences:

1. **`find_all` (Python) vs `findAll` (Node / browser)** - naming idiom only.
2. **`download()` / `upload()` throw in the browser.** A page cannot reach ELO's
   document connector (usually `:9093`, a different origin, and the URL carries a
   session ticket). The method exists for a uniform surface but fails fast,
   pointing you at the Python or Node snippet.
3. **The transport differs.** Python and Node run server-side: they hold the
   credentials and call `{base}/rest/IXServicePortIF/<method>` directly, HTTP
   Basic on every request. The browser must not hold the password and its origin
   differs from ELO's, so each `elo.call()` goes through this app's backend
   (`POST /api/elo/proxy`). The static demo adds a local mock path and an
   optional "call the URL directly" path (needs CORS on that server). None of
   this leaks into snippet code.

### Mock mode vs live mode

- **Mock** (default): calls are answered from `fixtures/ix/default.json` plus the
  topic's own `mock:` block. No ELO needed.
- **Live**: untick *Mock*, fill in Base URL + Port + user + password, press
  *Check connection*, then *Run*.

### Base URL and Port

The connection form has a separate **Port** field (default **9090**, the ELO
Indexserver HTTP port). It is spliced into the Base URL for every call and doc
link, so you can retarget the port without rewriting the URL.

### Versioning

The backend and the frontend are versioned independently and both are shown in
the top-right corner as `UI x · API y`. Backend:
`backend-python/app/__init__.py`. Frontend: `frontend/VERSION`. Endpoint:
`GET /api/version`.

A committed pre-commit hook (`.githooks/pre-commit` → `scripts/bump_version.py`)
bumps the **patch** number automatically: staging anything under `frontend/`
bumps the frontend version, staging anything under `backend-python/`,
`backend-node/` or `shared/` bumps the backend version, and the bumped file is
folded into the same commit. At most one bump per layer per commit (a hand bump
is left alone). Enable it once per clone with
`git config core.hooksPath .githooks` - `start.bat`, `scripts/run.ps1` and
`scripts/run.sh` do that for you. Bump the minor / major digits by hand when a
change deserves it.

### Where does my code run? Is it safe?

- **Python / Node**: in a child process on the backend, on the machine running
  the app, with a timeout and an output cap - **no real sandbox**.
- **Browser**: in a `sandbox="allow-scripts"` iframe.
- CORS is wide open (`*`) and there is no auth. Fine for a **local development
  tool**; do not expose it on a shared server without adding a sandbox, auth,
  tighter CORS and rate limiting.

## Test

```powershell
python -m pytest backend-python
node --test backend-node/test/*.test.mjs
python scripts/smoke.py            # offline: catalogue, snippet sync, one run each
```

## Adding a topic

1. Create `catalog/<NN-category>/<NN-slug>.yaml` (copy an existing one). Fill
   `elo_api`, `result_shape`, the three `snippets`, and a `mock:` block with the
   methods the snippet calls. `category`, `title`, `summary` and each
   `elo_api[].notes` carry `en` / `de` / `es` (missing keys fall back to `en`).
   Snippet code + comments stay English.
2. `python scripts/build_snippets.py` to materialise it under `snippets/`.
3. `python -m pytest backend-python` - `test_catalog`, `test_snippets_sync` and
   `test_i18n` keep you honest.

## Static demo (no backend)

`python scripts/build_static.py` writes a fully static copy into `dist/`: the
whole catalogue, every snippet, the shared-client source and the API reference,
all backed by mock data. It behaves like the real app - the connection form is
there, defaulting to **Mock mode**:

- **Mock** (default): **Browser** snippets run for real in the sandboxed iframe
  against a JS mock; **Python / Node** snippets show their pre-computed mock
  output (the build runs each one).
- **Untick Mock + enter a base URL + credentials**: **Browser** snippets then
  call that ELO server *directly* (`fetch` + HTTP Basic). That server has to
  send CORS headers for the demo's origin - most ELO installs do not by default,
  so this is a "point it at your own server" option. Python / Node still need
  the local app.

The local app's connection form defaults to `http://localhost:9090/ix-Repository1`
(from `ELOPG_ELO_BASE_URL`); the static build ships it blank.

`.github/workflows/pages.yml` builds and publishes it to GitHub Pages on every
push to `main` (enable it once at **Settings -> Pages -> Source = GitHub Actions**).

## Regenerate the offline OpenAPI sample (after an ELO upgrade)

```powershell
curl http://localhost:9090/ix-Repository1/rest/openapi.json -o runtime\openapi.real.json
python scripts\trim_openapi_sample.py runtime\openapi.real.json
```

## License & disclaimer

MIT - see [LICENSE](LICENSE).

This is an independent learning project. It is **not** affiliated with, endorsed
by, or supported by ELO Digital Office GmbH. "ELO" and the IX / Indexserver names
are trademarks of their respective owner. The request/response shapes here were
verified against an ELO 25 (25.0.1.3) test instance; other versions may differ -
always check your own server's `{base_url}/rest/openapi.json`.
