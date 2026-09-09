# import the shared client:  from elo_playground import connect
# topic:    Find an object by GUID, id or name
# category: Testing lab
# id:       lab.find

from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"          # "give me every Sord field" bitset

# --- by integer id --------------------------------------------------
by_id = elo.call("checkoutSord", {
    "objId": 2,                                  # "Administration" on any repo
    "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
})["sord"]
print(f"by id 2   -> {by_id['name']}  guid {by_id['guid']}")

# --- by GUID (same call - objId also accepts a "(GUID)") ----------
by_guid = elo.call("checkoutSord", {
    "objId": by_id["guid"],
    "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
})["sord"]
print(f"by guid   -> {by_guid['name']}  (id {by_guid['id']})")

# --- by name (findByIndex.name, '*' wildcards allowed) -----------
res = elo.call("findFirstSords", {
    "findInfo": {"findByIndex": {"name": "Administration*"}},
    "max": 10,
    "sordZ": {"bset": ALL},
})
print("by name   ->", [(s["id"], s["name"]) for s in res.get("sords", [])])
elo.call("findClose", {"searchId": res.get("searchId")})

# For CONTENT (words inside documents) use findByFulltext - the
# iSearch / Elasticsearch index. See the "Search" category.
