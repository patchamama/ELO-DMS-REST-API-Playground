# import the shared client:  from elo_playground import connect
# topic:    List Sord types (the entry icons)
# category: Repository & objects
# id:       repository.sord-types

from elo_playground import connect

elo = connect()

res = elo.call("checkoutSordTypes", {"id": -1, "sordTypeZ": {"bset": "31"}})
types = res if isinstance(res, list) else res.get("sordTypes", [])

print(f"{len(types)} Sord types")
for t in types:
    has_icon = "icon" if t.get("icon") else "no icon"
    print(f"  [{t['id']:>4}] {t['name']}  ({has_icon})")
