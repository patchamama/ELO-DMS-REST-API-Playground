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
all backed by mock data. **Browser** snippets run for real in the sandboxed
iframe against a JS mock; **Python / Node** snippets show their pre-computed
mock-mode output (the build runs each one).

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
