# import the shared client:  from elo_playground import connect
# topic:    Delete an object (write, two steps)
# category: Repository & objects
# id:       repository.delete-sord

from elo_playground import connect, EloError

elo = connect()

obj_id = "5361"   # a throwaway object's id (e.g. one from repository.create-folder)

# step 1 - move it to the recycle bin
elo.call("deleteSord", {
    "objId": obj_id, "parentId": "1",
    "deleteOptions": {"deleteFinally": False},
})
print("step 1 (to recycle bin): ok")

# step 2 - purge it for good
elo.call("deleteSord", {
    "objId": obj_id, "parentId": "1",
    "deleteOptions": {"deleteFinally": True},
})
print("step 2 (purge):          ok")

# confirm it is gone
try:
    elo.call("checkoutSord", {"objId": obj_id, "editInfoZ": {"bset": "1", "sordZ": {"bset": "0"}}})
    print("gone: False")
except EloError:
    print("gone: True")
