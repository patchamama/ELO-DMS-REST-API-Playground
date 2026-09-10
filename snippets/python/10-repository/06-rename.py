# import the shared client:  from elo_playground import connect
# topic:    Rename an object (write)
# category: Repository & objects
# id:       repository.rename

import os
from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1")
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator")
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "")

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"

# Provision a throwaway folder so this snippet is self-contained.
tpl = elo.call("createSord", {"parentId": "1", "maskId": 0,
                              "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
tpl["name"] = "playground old name"
obj_id = str(elo.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL},
                                      "unlockZ": {"bset": "1"}}))

try:
    # 1) check it out (with a lock)
    sord = elo.call("checkoutSord", {
        "objId": obj_id,
        "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}, "lockZ": {"bset": "1"}},
    })["sord"]
    print("before:", sord["name"])

    # 2) change the name, 3) check it back in and release the lock
    sord["name"] = "playground new name"
    elo.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})

    after = elo.call("checkoutSord", {
        "objId": obj_id, "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
    })["sord"]
    print("after: ", after["name"])
except EloError as exc:
    print("rename failed:", exc)
finally:
    # tidy up the scratch folder
    try:
        elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                                "deleteOptions": {"deleteFinally": False}})
        elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                                "deleteOptions": {"deleteFinally": True}})
    except EloError:
        pass
    elo.close()
