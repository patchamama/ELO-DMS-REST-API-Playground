# import the shared client:  from elo_playground import connect
# topic:    CRUD Operations: create, read, update, delete an object
# category: Testing lab
# id:       lab.crud

from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"

PARENT = 1          # the folder to file the object under (its "path")

# --- CREATE ---------------------------------------------------------
tpl = elo.call("createSord", {
    "parentId": str(PARENT), "maskId": 0,
    "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
})["sord"]
tpl["name"] = "pg-lab-crud"
tpl["desc"] = "created by the playground"     # the memo/description field
obj_id = str(elo.call("checkinSord", {
    "sord": tpl, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"},
}))
print("created:", obj_id)

# --- READ --------------------------------------------------------
got = elo.call("checkoutSord", {
    "objId": obj_id, "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
})["sord"]
print("read   :", got["name"], "|", got.get("desc"))

# --- UPDATE (read / modify / write) --------------------------
got["name"] = "pg-lab-crud (renamed)"
elo.call("checkinSord", {"sord": got, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})
again = elo.call("checkoutSord", {
    "objId": obj_id, "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
})["sord"]
print("updated:", again["name"])

# --- DELETE (recycle bin, then purge) -----------------------
elo.call("deleteSord", {"parentId": str(PARENT), "objId": obj_id,
                        "deleteOptions": {"deleteFinally": False}})
elo.call("deleteSord", {"parentId": str(PARENT), "objId": obj_id,
                        "deleteOptions": {"deleteFinally": True}})
print("deleted:", obj_id)
