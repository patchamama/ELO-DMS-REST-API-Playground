# import the shared client:  from elo_playground import connect
# topic:    List Sord types (the entry icons)
# category: Repository & objects
# id:       repository.sord-types

import os
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1")
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator")
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "")

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

res = elo.call("checkoutSordTypes", {"id": -1, "sordTypeZ": {"bset": "31"}})
types = res if isinstance(res, list) else res.get("sordTypes", [])

print(f"{len(types)} Sord types")
for t in types:
    has_icon = "icon" if t.get("icon") else "no icon"
    print(f"  [{t['id']:>4}] {t['name']}  ({has_icon})")
