# import the shared client:  from elo_playground import connect
# topic:    Read a keyword list
# category: Keyword lists
# id:       keywords.list

import os
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

res = elo.call("checkoutKeywordList", {
    "kwid": "ELOSTDSWL",
    "max": 500,
    "keywordZ": {"bset": "7"},
})

def walk(nodes, depth=0):
    for n in nodes or []:
        print("  " * (depth + 1) + "- " + (n.get("text") or "(no text)"))
        walk(n.get("children"), depth + 1)

top = res.get("children") or []
print(f"{res.get('id')}: {len(top)} top-level entries")
walk(top[:8])                       # first few, with any nesting
