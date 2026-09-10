# import the shared client:  from elo_playground import connect
# topic:    Read and write a Sord's index fields (write)
# category: Metadata masks
# id:       masks.read-write-fields

import os
from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1")
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator")
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "")

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"

def fields(s):
    return {k["name"]: k["data"] for k in (s.get("objKeys") or []) if k.get("data")}

# a scratch object with a fielded mask (34 = "ELO Business Solution Configuration")
sord = elo.call("createSord", {"parentId": 1, "maskId": 34,
                               "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
sord["name"] = "playground fields demo"

# write two field values into objKeys
wanted = {"BS_CONFIG_NAME": ["playground-value"], "BS_CONFIG_VERSION": ["1.0"]}
for key in sord["objKeys"]:
    if key["name"] in wanted:
        key["data"] = wanted[key["name"]]
print("before:", fields(sord))

new_id = str(elo.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL},
                                      "unlockZ": {"bset": "1"}}))
try:
    # read it back
    check = elo.call("checkoutSord", {"objId": new_id,
                                      "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
    print("after: ", fields(check))
except EloError as exc:
    print("read/write failed:", exc)
finally:
    for step in (False, True):
        try:
            elo.call("deleteSord", {"objId": new_id, "parentId": "1",
                                    "deleteOptions": {"deleteFinally": step}})
        except EloError:
            pass
    elo.close()
