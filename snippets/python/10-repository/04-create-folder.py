# import the shared client:  from elo_playground import connect
# topic:    Create a folder (write)
# category: Repository & objects
# id:       repository.create-folder

from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"   # SordC.mbAllIndex

# 1) blank Sord template under parent 1, "Ordner" mask (id 1).
#    sordZ goes INSIDE editInfoZ, exactly like checkoutSord.
tmpl = elo.call("createSord", {
    "parentId": 1,
    "maskId": 1,
    "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
})
sord = tmpl["sord"]
sord["name"] = "Playground test folder"

# 2) persist it - sordZ here is the WRITE mask, so use a full bitset
new_id = str(elo.call("checkinSord", {
    "sord": sord,
    "sordZ": {"bset": ALL},
    "unlockZ": {"bset": "1"},
}))
print("created folder id:", new_id)

# 3) clean up so re-running this stays tidy (see repository.delete-sord)
try:
    for step in (False, True):
        elo.call("deleteSord", {"objId": new_id, "parentId": "1",
                                "deleteOptions": {"deleteFinally": step}})
    print("removed the test folder again")
except EloError as exc:
    print("could not remove the test folder:", exc)
finally:
    elo.close()
