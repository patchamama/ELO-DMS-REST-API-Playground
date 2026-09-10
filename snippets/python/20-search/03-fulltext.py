# import the shared client:  from elo_playground import connect
# topic:    Full-text search
# category: Search
# id:       search.fulltext

import os
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

rows = elo.find_all(
    "findFirstSords", "findNextSords", "sords",
    {
        "findInfo": {"findByFulltext": {"fulltext": "agreement", "isTree": False}},
        "max": 50,
        "sordZ": {"bset": "449304431574384639"},
    },
)

print(f"{len(rows)} documents match 'agreement'")
for s in rows:
    print(f"  {s['name']}")
if not rows:
    print("  (0 hits usually means the ELO full-text service is not running "
          "or has not finished indexing on this instance)")
