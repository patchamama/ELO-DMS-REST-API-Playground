# sandbox

Scratch space for running one snippet from the terminal. After the one-time
**Setup** in the repo README, from the repo root:

```
python sandbox/example.py     # Python
node   sandbox/example.mjs    # Node
```

Both files are the `connection.login` snippet. Paste any other snippet from the
**Catalog** or from `snippets/<language>/<category>/<slug>.<ext>` over them and
re-run.

## Credentials

Each snippet defines the whole connection at the top (`ELO_BASE_URL` - the port
is part of the URL - `ELO_USER`, `ELO_PASS`) and passes it to
`connect(base_url=..., user=..., password=...)`. `connect()` also accepts
`verify`. For each field the order is: **explicit argument -> `ELOPG_*`
environment variable -> built-in default** for a stock local ELO test box:

| variable | default |
|---|---|
| `ELOPG_ELO_BASE_URL` | `http://localhost:9090/ix-Repository1` |
| `ELOPG_ELO_USER` | `Administrator` |
| `ELOPG_ELO_PASSWORD` | `elo` |

So editing the constants, exporting `ELOPG_*`, or a repo `.env` (copied from
`env.sample`) all point it elsewhere - the env var wins over the constant.

## What the errors mean

- `httpx.ConnectError` / `EloError: login: request failed: ...` (Python),
  `EloError: login: request failed: fetch failed` (Node) — nothing is listening
  on that Base URL. Start ELO, or fix `ELOPG_ELO_BASE_URL`.
- `EloError: login: authentication failed (HTTP 401)` — wrong user / password.
- A `ModuleNotFoundError: elo_playground` (Python) means the editable install
  from Setup did not run - re-run `pip install -r backend-python/requirements-dev.txt`
  from the repo root.

Files you add here other than `example.py`, `example.mjs` and this README are
git-ignored.
