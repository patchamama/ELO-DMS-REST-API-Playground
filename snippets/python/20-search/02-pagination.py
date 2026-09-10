# import the shared client:  from elo_playground import connect
# topic:    Page through a large result set by hand
# category: Search
# id:       search.pagination

import os
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1")
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator")
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "")

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

body = {
    "findInfo": {"findByIndex": {"name": "Invoice *"}},
    "max": 2,                                   # tiny page size to force paging
    "sordZ": {"bset": "449304431574384639"},
}
res = elo.call("findFirstSords", body)
search_id = res["searchId"]
rows = list(res.get("sords", []))
print(f"page 1: {len(rows)} rows, moreResults={res.get('moreResults')}")

page = 1
while res.get("moreResults") and page < 3:        # stop after a few pages for the demo
    page += 1
    res = elo.call("findNextSords", {
        "searchId": search_id, "idx": len(rows), "max": 2,
        "sordZ": body["sordZ"],          # IX needs the selector on every page
    })
    rows.extend(res.get("sords", []))
    print(f"page {page}: {len(res.get('sords', []))} rows, moreResults={res.get('moreResults')}")

elo.call("findClose", {"searchId": search_id})   # release the search
print(f"-> {len(rows)} rows so far (more available: {bool(res.get('moreResults'))})")
