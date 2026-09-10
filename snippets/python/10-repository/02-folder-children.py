# import the shared client:  from elo_playground import connect
# topic:    List the children of a folder
# category: Repository & objects
# id:       repository.folder-children

import os
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

# find_all() runs findFirstSords -> findNextSords -> findClose for us.
rows = elo.find_all(
    "findFirstSords", "findNextSords", "sords",
    {
        "findInfo": {"findChildren": {
            "parentId": 1,          # 1 = repository root
            "mainParent": True,
            "endLevel": 2,          # root + one level down
        }},
        "max": 100,
        "sordZ": {"bset": "449304431574384639"},   # full objects
    },
)

print(f"{len(rows)} objects under the root")
for s in rows:
    print(f"  [{s['id']:>5}] {s['name']}  ({s.get('childCount', 0)} children)")
