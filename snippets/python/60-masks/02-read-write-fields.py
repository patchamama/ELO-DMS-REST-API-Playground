# import the shared client:  from elo_playground import connect
# topic:    Read and write a Sord's index fields (write)
# category: Metadata masks
# id:       masks.read-write-fields

from elo_playground import connect

elo = connect()
ALL = "449304431574384639"

# a scratch object with a fielded mask (34 = "ELO Business Solution Configuration")
tmpl = elo.call("createSord", {"parentId": 1, "maskId": 34,
                               "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})
sord = tmpl["sord"]
sord["name"] = "playground fields demo"

def fields(s):
    return {k["name"]: k["data"] for k in (s.get("objKeys") or []) if k.get("data")}

print("before:", fields(sord))

# write two field values into objKeys
wanted = {"BS_CONFIG_NAME": ["playground-value"], "BS_CONFIG_VERSION": ["1.0"]}
for key in sord["objKeys"]:
    if key["name"] in wanted:
        key["data"] = wanted[key["name"]]

new_id = elo.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL},
                                  "unlockZ": {"bset": "1"}})

# read it back
check = elo.call("checkoutSord", {"objId": new_id,
                                  "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
print("after: ", fields(check))
