# import the shared client:  from elo_playground import connect
# topic:    Decode a user's rights bitset
# category: Users & groups
# id:       users.permissions

import os
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1")
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator")
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "")

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

# AccessC right bits (ELO 25) -> readable label
ACCESS = [
    (1, "main administrator (all rights)"), (2, "edit configuration"),
    (4, "edit structure"), (8, "edit documents"), (16, "change password"),
    (128, "edit workflows"), (256, "start workflows"), (512, "delete documents"),
    (8192, "import"), (16384, "export"), (32768, "edit masks"),
    (65536, "edit scripts"), (2097152, "edit ACL"), (536870912, "author"),
]

def rights(flags):
    flags = flags or 0
    if flags & 1:
        return ["main administrator (all rights)"]
    return [label for bit, label in ACCESS if flags & bit]

users = elo.call("checkoutUsers", {"ids": [0, 1], "checkoutUsersZ": {"bset": "513"}})
for u in users:
    print(f"{u['name']}: {', '.join(rights(u.get('flags'))) or '(none)'}")
