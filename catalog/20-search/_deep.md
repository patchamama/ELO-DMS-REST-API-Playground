# Search - deep dive

More ways to shape a `findFirstSords` query. Press **Run** on any block.

## 1. Combine selectors in one query

`findInfo` can hold several selectors at once - they are AND-ed. Here: a name
pattern plus "documents only".

```python
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

rows = elo.find_all(
    "findFirstSords", "findNextSords", "sords",
    {
        "findInfo": {
            "findByIndex": {"name": "Invoice*"},        # name pattern
            "findByType": {"typeMin": 254, "typeMax": 998},  # ...and only documents
        },
        "max": 100,
        "sordZ": {"bset": "449304431574384639"},
    },
)
print(f"{len(rows)} invoice documents")
```

## 2. Restrict by object kind (folders vs documents)

`findByType` uses ELO's numeric type ranges: `< 254` is a folder / structure,
`254..998` is a document.

```js
import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: {
    findByIndex: { name: "*" },
    findByType: { typeMin: 254, typeMax: 998 }, // documents only
  },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});
console.log(`${rows.length} documents (no folders)`);
```

## 3. How many match, cheaply

Fetch one small page and read `moreResults` instead of streaming everything.

```python
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

head = elo.call("findFirstSords", {
    "findInfo": {"findByIndex": {"name": "Invoice*"}},
    "max": 10,                       # a small first page
    "sordZ": {"bset": "449304431574384639"},
})
n = len(head.get("sords", []))
print(f"at least {n} match" + (", more available" if head.get("moreResults") else ""))
elo.call("findClose", {"searchId": head["searchId"]})
```
