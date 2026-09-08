# import the shared client:  from elo_playground import connect
# topic:    File an object into a second folder (reference, write)
# category: Repository & objects
# id:       repository.add-reference

from elo_playground import connect

elo = connect()
ALL = "449304431574384639"

obj_id = 4711            # the object to reference
old_parent = 1           # a folder it is already in
new_parent = 4712        # the folder to also file it under

elo.call("refSord", {
    "objId": str(obj_id),
    "oldParentId": str(old_parent),
    "newParentId": str(new_parent),
})
print("reference added")

kids = elo.call("findFirstSords", {
    "findInfo": {"findChildren": {"parentId": new_parent, "mainParent": False, "endLevel": 1}},
    "max": 20,
    "sordZ": {"bset": ALL},
}).get("sords", [])
print("new parent now contains:", [k["name"] for k in kids])
