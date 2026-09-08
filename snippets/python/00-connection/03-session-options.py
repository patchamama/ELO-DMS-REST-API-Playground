# import the shared client:  from elo_playground import connect
# topic:    List session options
# category: Connection & session
# id:       connection.session-options

from elo_playground import connect

elo = connect()

res = elo.call("getSessionOptions", {})
options = res.get("options", res if isinstance(res, list) else [])

print(f"{len(options)} session options")
for opt in options[:10]:                       # just the first few
    print(f"  {opt['key']} = {opt['value']}")
