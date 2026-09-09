# import the shared client:  from elo_playground import connect
# topic:    Change owner, colour and permissions
# category: Testing lab
# id:       lab.owner-color-acl

from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"

# Provision a throwaway folder so this snippet is self-contained.
tpl = elo.call("createSord", {"parentId": "1", "maskId": 0,
                              "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
tpl["name"] = "pg-owner-color-acl"
obj_id = str(elo.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL},
                                      "unlockZ": {"bset": "1"}}))

try:
    # the colour palette (id -> name); colours are administered under Administration
    palette = elo.call("checkoutColors", {"checkoutInfo": {}})
    print("palette:", [(c["id"], c["name"]) for c in palette[:4]])

    # read / modify / write
    sord = elo.call("checkoutSord", {
        "objId": obj_id, "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
    })["sord"]

    sord["kind"] = 2                       # 'kind' == colour id from the palette

    # owner: an int user id. Reassigning needs a main-admin; ownerName is read-only.
    # sord["ownerId"] = 123

    # permissions: append an ACL entry {id, type, access}
    #   type 0 = user/group id ;  access bits: 1 R  2 W  4 D  8 rights  16 L  32 P
    sord.setdefault("aclItems", []).append({"id": 9998, "type": 0, "access": 1 + 16})

    elo.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})

    after = elo.call("checkoutSord", {
        "objId": obj_id, "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
    })["sord"]
    print("colour id:", after["kind"], "  owner:", after.get("ownerName"))
    print("acl:", [(a["name"], a["access"]) for a in after.get("aclItems", [])])
except EloError as exc:
    print("operation failed:", exc)
finally:
    try:
        elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                                "deleteOptions": {"deleteFinally": False}})
        elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                                "deleteOptions": {"deleteFinally": True}})
    except EloError:
        pass
    elo.close()
