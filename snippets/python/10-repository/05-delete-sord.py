# import the shared client:  from elo_playground import connect
# topic:    Delete an object (write, two steps)
# category: Repository & objects
# id:       repository.delete-sord

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
tpl["name"] = "pg-delete-me"
obj_id = str(elo.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL},
                                      "unlockZ": {"bset": "1"}}))
print("scratch folder:", obj_id)

try:
    # step 1 - move it to the recycle bin
    elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                            "deleteOptions": {"deleteFinally": False}})
    print("step 1 (to recycle bin): ok")

    # step 2 - purge it for good
    elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                            "deleteOptions": {"deleteFinally": True}})
    print("step 2 (purge):          ok")

    # confirm it is gone
    try:
        elo.call("checkoutSord", {"objId": obj_id,
                                  "editInfoZ": {"bset": "1", "sordZ": {"bset": "0"}}})
        print("gone: False")
    except EloError:
        print("gone: True")
finally:
    elo.close()
