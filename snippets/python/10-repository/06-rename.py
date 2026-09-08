# import the shared client:  from elo_playground import connect
# topic:    Rename an object (write)
# category: Repository & objects
# id:       repository.rename

from elo_playground import connect

elo = connect()
ALL = "449304431574384639"

obj_id = 5390        # a throwaway object's id

# 1) check it out (with a lock)
sord = elo.call("checkoutSord", {
    "objId": obj_id,
    "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}, "lockZ": {"bset": "1"}},
})["sord"]
print("before:", sord["name"])

# 2) change the name
sord["name"] = "playground new name"

# 3) check it back in and release the lock
elo.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})

after = elo.call("checkoutSord", {
    "objId": obj_id, "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
})["sord"]
print("after: ", after["name"])
