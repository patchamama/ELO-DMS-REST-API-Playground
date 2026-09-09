# import the shared client:  from elo_playground import connect
# topic:    Read server info and licence
# category: Connection & session
# id:       connection.server-info

from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)  # env vars + login() already done

info = elo.call("getServerInfo", {})         # -> POST .../getServerInfo
server = (info.get("indexServers") or [{}])[0]
lic = (info.get("license") or {}).get("licenseOptions", {})

print("repository :", server.get("arcName"))
print("IX version :", info.get("version"))
print("database   :", info.get("databaseEngine"))
print("product    :", lic.get("product"), "/ users:", lic.get("usercount1"))
