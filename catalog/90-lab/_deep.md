# Testing lab - CRUD Operations end to end

One scratch object through its whole life: **create -> colour + permissions ->
find it back -> rename -> delete**. Press **Run** on any block. Every block is
self-contained (it creates and deletes its own object), so it is safe to run
against a real repository - nothing is left behind.

`ALL` below is the "every Sord field" bitset `449304431574384639`; a checkin
with anything less silently drops part of your change.

## 1. Create, then colour it and widen its ACL

```python
from elo_playground import connect

elo = connect()
ALL = "449304431574384639"
PARENT = 1                       # the folder to file it under

# CREATE
tpl = elo.call("createSord", {"parentId": str(PARENT), "maskId": 0,
                              "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
tpl["name"] = "pg-lab-e2e"
tpl["kind"] = 2                  # colour id (see checkoutColors)
tpl.setdefault("aclItems", []).append({"id": 9998, "type": 0, "access": 1 + 16})
obj_id = str(elo.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL},
                                      "unlockZ": {"bset": "1"}}))
print("created:", obj_id)

# READ BACK
sord = elo.call("checkoutSord", {"objId": obj_id,
                                 "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
print("colour:", sord["kind"], "| acl:", [(a["name"], a["access"]) for a in sord.get("aclItems", [])])

# CLEAN UP
elo.call("deleteSord", {"parentId": str(PARENT), "objId": obj_id, "deleteOptions": {"deleteFinally": False}})
elo.call("deleteSord", {"parentId": str(PARENT), "objId": obj_id, "deleteOptions": {"deleteFinally": True}})
print("deleted:", obj_id)
```

## 2. Create, find it by name, rename, delete

```js
import { connect } from "elo-playground";

const elo = await connect();
const ALL = "449304431574384639";
const PARENT = 1;

// CREATE
const tpl = (await elo.call("createSord", {
  parentId: String(PARENT), maskId: 0,
  editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
tpl.name = "pg-lab-e2e-js";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));

// FIND BY NAME
const found = await elo.call("findFirstSords", {
  findInfo: { findByIndex: { name: "pg-lab-e2e-js" } },
  max: 5, sordZ: { bset: ALL },
});
console.log("found:", (found.sords || []).map((s) => [s.id, s.name]));
await elo.call("findClose", { searchId: found.searchId });

// RENAME
const got = (await elo.call("checkoutSord", {
  objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
got.name = "pg-lab-e2e-js (renamed)";
await elo.call("checkinSord", { sord: got, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });
console.log("renamed", objId);

// CLEAN UP
await elo.call("deleteSord", { parentId: String(PARENT), objId, deleteOptions: { deleteFinally: false } });
await elo.call("deleteSord", { parentId: String(PARENT), objId, deleteOptions: { deleteFinally: true } });
console.log("deleted:", objId);
```

## 3. Copy a GRP (index) field value into a MAP field

`sord.objKeys` holds the mask's indexed fields; a MAP field is free-form
key/value storage on the same object. Read one, write the other.

```python
from elo_playground import connect

elo = connect()
ALL = "449304431574384639"

obj_id = "4711"   # a document with indexed fields

sord = elo.call("checkoutSord", {"objId": obj_id,
                                 "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]

# pull one GRP field by its group name (objKeys entries are {name, data:[...]})
grp = {k["name"]: (k.get("data") or [None])[0] for k in sord.get("objKeys", [])}
invoice_no = grp.get("INVOICE_NO")
print("GRP INVOICE_NO =", invoice_no)

# write it into a MAP field (checkinMap: data = list of {key, value}; int objId)
elo.call("checkinMap", {"mapId": "objId", "id": int(obj_id),
                        "items": None,
                        "data": [{"key": "copy_of_invoice_no", "value": str(invoice_no)}]})
print("wrote MAP copy_of_invoice_no")

# read the MAP back
back = elo.call("checkoutMap", {"mapId": "objId", "id": int(obj_id), "keys": ["copy_of_invoice_no"]})
print("MAP now:", back)
```

> `checkinMap` on this test box accepts the write but `checkoutMap` can read
> back empty unless a MAP domain is registered for the object type - treat this
> block as the shape, not a guarantee.
