# Paste any snippet from the Catalog (or snippets/) over this file, then re-run:
#   python sandbox/example.py

from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_USER = "Administrator"
ELO_PASS = "elo"

# login=False builds the client but does NOT log in yet, so we can call
# login() ourselves below and read what it returns.
elo = connect(user=ELO_USER, password=ELO_PASS, login=False)

user = elo.login()                 # -> POST /rest/IXServicePortIF/login
print("logged in as:", user["name"], "(id " + str(user["id"]) + ")")
print("member of groups:", user.get("groupList"))

elo.close()                        # release the connection pool
