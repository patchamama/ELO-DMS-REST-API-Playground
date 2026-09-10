# import the shared client:  from elo_playground import connect
# topic:    List session options
# category: Connection & session
# id:       connection.session-options

import os
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

res = elo.call("getSessionOptions", {})
options = res.get("options", res if isinstance(res, list) else [])

print(f"{len(options)} session options")
for opt in options[:10]:                       # just the first few
    print(f"  {opt['key']} = {opt['value']}")
