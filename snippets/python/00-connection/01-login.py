# import the shared client:  from elo_playground import connect
# topic:    Log in and open a session
# category: Connection & session
# id:       connection.login

from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

# login=False builds the client but does NOT log in yet, so we can call
# login() ourselves below, read what it returns and handle a failure.
elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS, login=False)

try:
    user = elo.login()             # -> POST /rest/IXServicePortIF/login
    print("logged in as:", user["name"], "(id " + str(user["id"]) + ")")
    print("member of groups:", user.get("groupList"))
except EloError as exc:
    msg = str(exc)
    if "ELOIX:3008" in msg or "authentication failed" in msg or "HTTP 401" in msg or "HTTP 403" in msg:
        print("login failed: wrong user or password -", msg)
    elif "request failed" in msg:
        print("login failed: cannot reach the server, check the host/port in ELO_BASE_URL -", msg)
    elif "HTTP 404" in msg:
        print("login failed: the repository path in ELO_BASE_URL looks wrong -", msg.split(" - ")[0])
    else:
        print("login failed:", msg)
finally:
    elo.close()                    # release the connection pool
