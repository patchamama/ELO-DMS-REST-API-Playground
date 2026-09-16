# import the shared client:  from elo_playground import connect
# topic:    Copy between GRP (index) fields and MAP fields
# category: Testing lab
# id:       lab.grp-to-map

import os
from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"
PARENT = 1

obj_id = None
try:
    # provision a scratch object
    tpl = elo.call("createSord", {"parentId": str(PARENT), "maskId": 0,
                                  "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
    tpl["name"] = "pg-grp2map"
    obj_id = str(elo.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL},
                                          "unlockZ": {"bset": "1"}}))
    print("scratch object:", obj_id)

    # read the GRP (index) fields; a generic folder has none, so fall back
    sord = elo.call("checkoutSord", {"objId": obj_id,
                                     "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
    grp = {k["name"]: (k.get("data") or [None])[0] for k in sord.get("objKeys", []) if k.get("name")}
    source_value = grp.get("INVOICE_NO") or grp.get("ELO_FN") or "INV-2026-0042"
    print("GRP source value:", source_value)

    # copy it into the object's MAP under key "grp_copy"
    elo.call("checkinMap", {
        "objId": int(obj_id), "domainName": "objekte",
        "data": [{"key": "grp_copy", "value": source_value}],
        "unlockZ": {"bset": "1"},          # bset "1" commits; "0" does not
    })
    print(f"wrote MAP grp_copy = {source_value}")

    got = elo.call("checkoutMap", {
        "objId": int(obj_id), "id": obj_id, "domainName": "objekte",
        "keyNames": ["*"], "lockZ": {"bset": "0"},
    })
    print("MAP read-back:", got.get("items"))

    # --- the other way round: MAP -> GRP -------------------------------
    # A GRP field is a line of the object's mask, so it must already exist
    # (the interactive panel can add one). Write a MAP value, then set the
    # matching objKeys entry and check the Sord in.
    elo.call("checkinMap", {
        "objId": int(obj_id), "domainName": "objekte",
        "data": [{"key": "map_src", "value": "MAP-2026-0099"}],
        "unlockZ": {"bset": "1"},
    })
    sord = elo.call("checkoutSord", {"objId": obj_id,
                                     "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
    target = next((k for k in sord.get("objKeys", []) if k.get("name") == "INVOICE_NO"), None)
    if target is None:
        print("MAP -> GRP: this mask has no INVOICE_NO line - add it to the mask first")
    else:
        target["data"] = ["MAP-2026-0099"]
        elo.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})
        print("MAP -> GRP: wrote INVOICE_NO = MAP-2026-0099")
        back = elo.call("checkoutSord", {"objId": obj_id,
                                         "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
        print("GRP read-back:", [k["data"] for k in back.get("objKeys", []) if k.get("name") == "INVOICE_NO"][0])
except EloError as exc:
    print("map operation failed:", exc)
finally:
    if obj_id:
        try:
            elo.call("deleteSord", {"parentId": str(PARENT), "objId": obj_id,
                                    "deleteOptions": {"deleteFinally": False}})
            elo.call("deleteSord", {"parentId": str(PARENT), "objId": obj_id,
                                    "deleteOptions": {"deleteFinally": True}})
        except EloError as exc:
            print("cleanup failed:", exc)
    print("cleaned up")
    elo.close()
