# import the shared client:  from elo_playground import connect
# topic:    List users (and groups)
# category: Users & groups
# id:       users.find-users

import os
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

users = elo.find_all(
    "findFirstUsers", "findNextUsers", "sortedResult",
    {"findUserInfo": {"onlyUsers": True}, "max": 200},
)

print(f"{len(users)} users")
for u in users:
    print(f"  [{u['id']:>5}] {u['name']:<16} {u.get('displayName', '')}")
