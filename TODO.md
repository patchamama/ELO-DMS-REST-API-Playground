# ELO API Playground - TODO / roadmap

Continuation notes. Checkbox items ordered roughly by value. Paths relative to
`elo-api-playground/`.

---

## Status (2026-09-08)

- [x] M1 vertical slice: 2 backends, shared 3-language client, mock mode,
      Scratchpad, live runner, `start.bat` / `run.ps1` / `run.sh`.
- [x] **18 topics / 9 categories**, deep dives for `00-connection` and `20-search`.
- [x] **i18n**: UI fully EN/DE/ES with a language switch; catalogue category +
      topic titles translated. Summaries / `elo_api` notes are English-only
      (fallback) - see M3 below.
- [x] **M2 "API reference" tab**: browses `openapi.json` (live from the server,
      or the trimmed `fixtures/openapi.sample.json` offline) - services ->
      operations -> request params + response ref + a generated `elo.call(...)`
      skeleton in all three runtimes. Live-tested against ELO 25 (358 operations,
      12 services).
- [x] **Full live pass 2026-09-08** through the runner: all 19 topics + every
      deep-dive block, Python AND Node, 0 failures, archive left clean. Fixes:
      `find_all` carries `...Z` on findNext; `checkoutSord`/`createSord` need
      `sordZ` inside `editInfoZ`; `checkinSord` `sordZ` is the write mask;
      `startWorkflow`->`startWorkFlow` (`templFlowId`/`flowName`); read a running
      instance with `checkoutWorkFlow` `typeZ {bset:"0"}` (2 reads it as a
      template); `deleteSord` is two-step (bin -> `deleteFinally`);
      `checkoutKeywordList` entry label is `text`; capped the flooding loops in
      `search.pagination` / `workflows.templates`; full-text returns 0 here (ELO
      FT service not indexed) - snippet now says so.
- [x] i18n fully done: UI + category + title + summary + `elo_api[].notes` in
      EN / DE / ES; language switch; `test_catalog` / `test_i18n` enforce parity.
- [x] Scratchpad editor is CodeMirror 5 (vendored, hash-pinned).
- [x] Playground moved to **port 8010** (8000 is the sibling ELOphant app);
      `start.bat` hardened (absolute python path, `cd` into `backend-python`,
      warns if the port is busy).
- [x] Green: `python -m pytest backend-python` (60), `node --test backend-node/test/*.test.mjs` (4),
      `python scripts/smoke.py`. Read-only topics also verified live against ELO 25.
- [x] Local ELO 25 reachable (`/rest/openapi.json` 200; `getServerInfo` 401
      without auth - the shape the client expects).

---

## M1 polish

- [x] Inline SVG favicon (`frontend/templates/base.html`).
- [x] Copy button on every code block (`makeRunner()` in `frontend/static/app.js`).
- [x] Persist last-opened topic + active snippet tab in `localStorage`.
- [x] `scripts/run.sh` (bash mirror of `run.ps1`).
- [x] Vendor-hash pin test (`backend-python/tests/test_vendor.py`).
- [x] **Live verification pass** against a real ELO 25 25.0.1.3 instance
      (`Administrator`). All 16 read-only topics pass on the Python AND Node
      tabs. Fixes that came out of it:
      - `find_all` / `findAll` now carry the `...Z` selector onto every
        `findNext` page (IX: `Incorrect parameter: sordZ==null`).
      - `checkoutSord` needs `sordZ` **inside** `editInfoZ` with
        `editInfoZ.bset "1"` (mbSord) - a bare top-level `sordZ` returns `{}`.
      - added `EloClient.download(url)` (py + node) so `business-solutions.find-config`
        actually downloads + parses the config JSON.
- [x] **Write topics verified live 2026-09-08** through the actual runner
      (Python + Node), every test folder / workflow deleted afterwards. Fixes:
      - `createSord`: same nested-`sordZ`-in-`editInfoZ` rule as `checkoutSord`;
        `maskId 1` is "Ordner".
      - `checkinSord`: `sordZ` is the WRITE mask - `"0"` persists nothing, use a
        full bitset.
      - `startWorkflow` -> **`startWorkFlow`** (capital F); params are
        `templFlowId` / `flowName` / `objId`.
      - `getWorkFlowStatus` does not exist - read a running instance with
        `checkoutWorkFlow` (`typeZ {bset:"2"}`, `lockZ {bset:"0"}`).
- [ ] `checkoutSord` on the repository *root* (id 1) classifies as "document"
      (cosmetic - the type test in the snippet); real folders/docs classify right.
- [x] Scratchpad now uses CodeMirror 5 (vendored + hash-pinned; graceful
      `<textarea>` fallback if the lib fails to load).
- [x] JSON output is syntax-highlighted: the "Result shape" block, and a runner
      output that is a single JSON value (pretty-printed via highlight.js).
- [x] Catalog nav has a pinned **"The elo_playground client"** entry (top): the
      intro, a method table (connect / call / login / find_all / download / upload),
      and the real source of all three shared clients with comments
      (`/api/client-lib`, `app/client_lib.py`).
- [x] "API reference" header now shows the operation count and, offline, a note
      that it is a trimmed sample - live mode browses the full ~358-op API.

## More topics (fill out the catalogue)

Each is one `catalog/<NN-cat>/<NN-slug>.yaml` + `python scripts/build_snippets.py`.

- [x] `10-repository/04-create-folder` (createSord + checkinSord, write).
- [x] `20-search/03-fulltext` (findByFulltext).
- [x] `40-users-groups/03-permissions` (decode `UserInfo.flags`).
- [x] `60-masks/01-list-masks` (findFirstDocMasks + line types).
- [x] `70-keywords/01-keyword-list` (checkoutKeywordList).
- [x] `80-workflows-advanced/01-start-workflow` (startWorkflow + getWorkFlowStatus).
- [x] Downloading a document's bytes is now a client method (`EloClient.download`),
      used by `business-solutions.find-config`. A dedicated `10-repository` topic
      for it would still be nice.
- [x] `10-repository/05-delete-sord` - the two-step `deleteSord` (recycle bin ->
      purge), verified live.
- [x] **treskon `elo-indexserver-client` use cases** (user request 2026-09-08 -
      https://treskon.github.io/elo-indexserver-client/), all verified live:
      - `search.by-field-value` (`findByIndex.objKeys`)
      - `masks.read-write-fields` (checkout -> edit `sord.objKeys` -> checkin)
      - `repository.rename` (read/modify/write cycle; `move` = same with `parentId`)
      - `repository.upload-download` (`createDoc` -> `checkinDocBegin` -> POST bytes
        to the writedoc URL -> `checkinDocEnd`; `EloClient.upload()` / `download()`)
      - `repository.add-reference` (`refSord` {objId, oldParentId, newParentId})
      - `users.create` (`checkinUsers` id:-1, type 1/0; group membership via the
        user's `groupList`; `deleteUsers`; note: pwd policy here is >= 15 chars)
- [ ] `write_map_fields` / `read_map_fields`: `checkinMap` takes `data: [KeyValue]`
      + int `objId` (NOT `items`), no error - but `checkoutMap` (`id` = str objId)
      still reads back empty. Needs more digging (maybe a registered map domain,
      or maps only attach to documents). Deferred.
- [ ] `20-search`: search by date range; sort options.
- [ ] `50-business-solutions`: register an extra BS package; read DATEV config.
- [ ] `80-workflows-advanced`: forward a workflow node; read active workflows for
      a Sord; node conditions / escalations (already in the `wfDiagramZ` payload
      - see the parent repo's `_wf_node`).
- [ ] `90-admin`: document stores (`getServerInfoDM`); colours; report options.
- [ ] Add a `_deep.md` (+ `_deep.mock.json`) to the categories that lack one.

## M3 - finish i18n

- [x] `frontend/i18n/{de,es}.json` complete; parity test
      (`backend-python/tests/test_i18n.py`).
- [x] Language switch wired in `frontend/static/app.js` (re-fetches
      `/api/i18n/<lang>` + `/api/catalog?lang=<lang>`, re-opens the last panel).
- [x] `de` / `es` for every `category` + `title` in `catalog/**/*.yaml`.
- [x] `de` / `es` for every `summary` and `elo_api[].notes` (all 18 topics;
      `test_catalog` enforces both).
- [ ] Translate the `_deep.md` files (or accept English there).
- [ ] Snippet code + comments stay English regardless of UI language.

## M2 - "docs walkthrough" mode - DONE (core), with follow-ups

- [x] `backend-python/app/openapi_ref.py`: fetch + TTL-cache `{base}/rest/openapi.json`
      (mock / offline -> `fixtures/openapi.sample.json`, built by
      `scripts/trim_openapi_sample.py`).
- [x] `GET /api/spec/services`, `/api/spec/operations`, `/api/spec/op/{id}`.
- [x] Codegen: top-level request properties (with types) -> `elo.call(...)`
      skeleton for py / node / browser; `service` arg added for non-IX services.
- [x] Frontend "API reference" tab - services -> operations -> params table +
      response ref + 3 generated runners (Run reuses `makeRunner()`).
- [x] Resolve nested `$ref` one level deeper in the params panel (`FindInfo` ->
      its `findByIndex` / `findByFulltext` / ... with schema descriptions,
      copyright boilerplate stripped).
- [x] Cross-link both ways: a topic's `spec` jumps to the reference operation;
      an operation lists the curated topics that use it.
- [x] Show the response schema fields (resolves `BResult_* -> result` one level).
- [ ] Deeper `$ref` resolution (2+ levels) behind an expander.
- [ ] Shrink `fixtures/openapi.sample.json` (320 KiB) - lower `MAX_DEPTH` in
      `scripts/trim_openapi_sample.py` or keep fewer operations.

## Hardening (only if this leaves the local-dev box) - NOT STARTED

- [ ] Real sandbox for the runner (container / nsjail) - today it is a bare child
      process with a timeout + output cap.
- [ ] Auth on the app; drop `allow_origins=["*"]` (needed now only for the
      `null`-origin run iframe - `app/main.py`).
- [ ] Single-flight / rate-limit `/api/run` per client.
- [ ] Session-token creds instead of sending `credentials` in every request body.

## Notes for whoever picks this up

- Stay independent of the parent `app.*` package (this becomes its own repo).
  Study `../app/collectors/elo_ix.py` for request bodies / Z-bitsets; don't import.
- Node bare import `elo-playground` resolves via the root `package.json`
  `"file:shared/node"` link -> run `npm install` at the project root once.
- Node snippet temp files must live UNDER the project tree (`runtime/node-run/`)
  or the bare import will not resolve (`backend-node/src/runner.mjs`).
- Deep-dive blocks pass the *category id* as `topic_id`; their mock data comes
  from `catalog/<category>/_deep.mock.json` (`app/runner.py:mock_data`).
- This Starlette needs `TemplateResponse(request, name, ctx)` (new signature).
- `python` is not on PATH in Git Bash here; the parent repo's
  `.venv\Scripts\python.exe` already has fastapi / httpx / pydantic-settings / pyyaml.
