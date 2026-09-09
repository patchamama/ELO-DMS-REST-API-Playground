# import the shared client:  from elo_playground import connect
# topic:    File an object into a second folder (reference, write)
# category: Repository & objects
# id:       repository.add-reference

from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"

def make_folder(name):
    tpl = elo.call("createSord", {"parentId": "1", "maskId": 0,
                                  "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
    tpl["name"] = name
    return str(elo.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL},
                                        "unlockZ": {"bset": "1"}}))

obj_id = old_parent = new_parent = None
try:
    old_parent = make_folder("pg-ref-source")
    new_parent = make_folder("pg-ref-target")
    obj_id = make_folder("pg-ref-object")            # lives under old_parent's sibling; parent is 1

    try:
        elo.call("refSord", {"objId": obj_id, "oldParentId": "1", "newParentId": new_parent})
        print("reference added")
    except EloError as exc:
        # refSord needs the "reference" right; some repositories deny it
        print("refSord not permitted here:", exc)

    kids = elo.call("findFirstSords", {
        "findInfo": {"findChildren": {"parentId": new_parent, "mainParent": False, "endLevel": 1}},
        "max": 20, "sordZ": {"bset": ALL},
    }).get("sords", [])
    print("target folder now contains:", [k["name"] for k in kids])
finally:
    for oid in (obj_id, old_parent, new_parent):
        if oid:
            try:
                elo.call("deleteSord", {"objId": oid, "parentId": "1",
                                        "deleteOptions": {"deleteFinally": False}})
                elo.call("deleteSord", {"objId": oid, "parentId": "1",
                                        "deleteOptions": {"deleteFinally": True}})
            except EloError:
                pass
    elo.close()
