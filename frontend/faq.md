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
- **Live**: untick *Mock*, fill in Base URL (the port is part of it, e.g.
  `http://localhost:9090/ix-Repository1`) + user + password, press *Test*, then
  *Run*. Python and Node then call your ELO directly; browser snippets go through
  the backend proxy.

## Where does `connect()` get the credentials?

Every snippet starts by defining the whole connection, for a stock local ELO
test box:

```python
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"   # the port lives in the URL
ELO_USER = "Administrator"
ELO_PASS = "elo"
elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
```

`connect()` also accepts `verify` (`baseUrl` is the option name in Node). For
each of `base_url` / `user` / `password` / `verify` the order is: **the explicit
argument -> the matching `ELOPG_*` environment variable -> the built-in
default**. So `connect()` with no arguments still works, and setting
`ELOPG_ELO_BASE_URL` / `ELOPG_ELO_USER` / `ELOPG_ELO_PASSWORD` overrides whatever
the snippet hard-codes.

When you press **Run** in the playground, the connection form's values are
passed through as `ELOPG_*` for that one run, so the form wins over the
snippet's constants. The form pre-fills from your local `.env`
(`ELOPG_ELO_PASSWORD=...`); *Remember password* keeps it in this browser.

## "Choose file" on the OCR topics

The two **OCR & text extraction** topics show a *Choose file* button. Pick a
real scan (there are samples in `examples/invoices/`) and it is sent to
`processOcr` / uploaded to the archive; with nothing picked, the snippet sends a
tiny built-in invoice so it still runs. In code the picked file is
`attachment()` from `elo-playground` - `(name, bytes)` in Python,
`{ name, bytes }` in Node/browser, or `None`/`null`. The upload is capped at
8 MB and is written to the run's temp dir (`ELOPG_ATTACH`), never kept.

## "Generate an ELO structure on the local filesystem" (Testing lab)

That topic is an interactive panel, live mode only. Two directions:

- **ELO -> local.** Expand the folder tree, pick a folder, press *Mirror*. Its
  whole subtree - folders **and** document bytes - is written into
  `sandbox/elo-archiv-structure/`, which is **emptied first**, and then opened in
  your OS file manager (so it only makes sense when the app runs on your own
  machine).
- **local -> ELO.** Give a folder as a path on the backend host, or pick one with
  the browser directory button, and it is recreated as folders + documents under
  a chosen ELO folder.

Both directions are capped (object count and per-file size; the browser picker
also has a ~16 MB total limit) and every ELO error is caught, so one unreadable
document does not abort the run. In Mock / static mode the panel is inert - only
its collapsed *"Show the code"* section works.

Every exported folder also carries a **`metadata.opf`** (XML): the mask name,
GRP + MAP field values, dates, owner and ACL - a small backup / import template.
On import that file is applied to the freshly created ELO folder (mask, `desc`,
dates, colour, GRP + MAP values) and is **not** uploaded as a document; owner
and ACL are kept for reference only.

## The static demo (GitHub Pages) - what runs?

The published demo has no backend. It behaves like the app, defaulting to Mock:

- **Browser** snippets run for real in the sandboxed iframe against a JS mock.
- **Python / Node** snippets show their pre-computed Mock output (the build ran
  each one).
- Untick Mock + enter a reachable ELO Base URL + credentials, and **Browser**
  snippets call that server directly - it must send CORS headers for the demo's
  origin, which most ELO installs do not by default.

## Base URL (and the http/https toggle)

There is no separate Port field - the port is part of the **Base URL**
(`http://localhost:9090/ix-Repository1`, or `https://elo.example/ix-Repository1`
behind a reverse proxy on 443). The **`→ https` / `→ http`** button next to
*Test* flips the scheme of the Base URL and re-tests in one click. Going to
https also:

- swaps an explicit **`:9090` ↔ `:9093`** (ELO's paired default IX ports; a
  non-default port is left as you set it);
- replaces `localhost` / `127.0.0.1` with the server's real hostname when the
  app knows it, because a TLS certificate never matches `localhost`;
- unticks *Verify TLS certificate*, since a local ELO's IX/HTTPS (`:9093`) uses
  a self-signed certificate.

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
