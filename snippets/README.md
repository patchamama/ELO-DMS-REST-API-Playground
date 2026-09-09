# snippets/

`snippets/<language>/<category>/<slug>.<ext>` - every Catalog example
materialised as a standalone file, so the whole tree reads as a plain,
structured code library.

**These files are generated.** `python scripts/build_snippets.py` writes them
from `catalog/**/*.yaml`; `--check` (run in CI) fails if they are stale. To
change a snippet, edit its YAML in `catalog/` and re-run the builder - do not
edit the files here.

## Running one

Copy any file into `sandbox/` and run it from the repo root (see
[`../sandbox/README.md`](../sandbox/README.md) and the "Run one snippet from the
terminal" section of the main README):

```
python sandbox/example.py     # after `pip install -r backend-python/requirements-dev.txt`
node   sandbox/example.mjs     # after `npm install`
```

`.py` and `.mjs` files run directly. The `.js` (browser) files rely on
`connect()` / `EloClient` being injected by the site's sandboxed run iframe -
they only run inside the playground page, not from a terminal.
