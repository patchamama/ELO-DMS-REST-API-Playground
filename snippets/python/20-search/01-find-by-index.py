# import the shared client:  from elo_playground import connect
# topic:    Find objects by index field
# category: Search
# id:       search.find-by-index

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
        "findInfo": {"findByIndex": {
            "name": "Invoice *",        # wildcard match on the object name
            "exactName": False,
        }},
        "max": 50,
        "sordZ": {"bset": "449304431574384639"},
    },
)

print(f"{len(rows)} matches")
for s in rows:
    print(f"  {s['name']}  (mask: {s.get('maskName')})")
