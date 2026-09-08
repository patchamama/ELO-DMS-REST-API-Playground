# import the shared client:  from elo_playground import connect
# topic:    Read server info and licence
# category: Connection & session
# id:       connection.server-info

from elo_playground import connect

elo = connect()                              # env vars + login() already done

info = elo.call("getServerInfo", {})         # -> POST .../getServerInfo
server = (info.get("indexServers") or [{}])[0]
lic = (info.get("license") or {}).get("licenseOptions", {})

print("repository :", server.get("arcName"))
print("IX version :", info.get("version"))
print("database   :", info.get("databaseEngine"))
print("product    :", lic.get("product"), "/ users:", lic.get("usercount1"))
