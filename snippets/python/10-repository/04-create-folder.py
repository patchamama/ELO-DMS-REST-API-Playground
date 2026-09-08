# import the shared client:  from elo_playground import connect
# topic:    Create a folder (write)
# category: Repository & objects
# id:       repository.create-folder

from elo_playground import connect

elo = connect()
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
new_id = elo.call("checkinSord", {
    "sord": sord,
    "sordZ": {"bset": ALL},
    "unlockZ": {"bset": "1"},
})
print("created folder id:", new_id)
