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

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
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

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
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

## 3. Generate an ELO structure on disk (and back)

The **"Generate an ELO structure on the local filesystem"** topic in this
category is an interactive panel, not just a snippet. A few things worth knowing
about how it works:

- **One level per click.** The tree calls `findFirstSords` with
  `findChildren.endLevel = 1`, so each `+` fetches exactly one level. `type < 254`
  is a folder, `254..998` is a document, `9999` is the repository root.

```text
findFirstSords { findInfo.findChildren { parentId, mainParent: true, endLevel: 1 },
                 max: 1000, sordZ.bset "449304431574384639" }  ->  { sords, searchId }
findClose      { searchId }
```

- **Document bytes.** `checkoutDoc` with `editInfoZ.bset "320"` returns
  `document.docs[0].url`; then `download(url, max_bytes=…)`. The shared client's
  `download()` defaults to **200 KB and truncates silently** - the panel passes an
  explicit 25 MB cap. The Node client's `download()` returns text, not raw bytes,
  so binary files come out clean only from the Python side.
- **Mirror target.** `sandbox/elo-archiv-structure/` is **deleted and recreated**
  on every run (the `shutil.rmtree` + recreate pattern). The backend then reveals
  it with `os.startfile` / `open` / `xdg-open` - which only makes sense when the
  app runs on your own machine.
- **The reverse** walks a local folder (a path on the backend host, or a folder
  picked with the browser directory button) and recreates it as
  `createSord`/`checkinSord` folders + `createDoc` -> `checkinDocBegin` ->
  `upload` -> `checkinDocEnd` documents. Both directions are capped by object
  count and per-file size, and each ELO error is caught so one bad object does
  not abort the run.
- **`metadata.opf` per folder.** On export every container also gets an XML
  sidecar with its mask (`sord.mask` / `maskName`), GRP fields (`sord.objKeys`),
  MAP fields (`checkoutMap`, domain `objekte`), dates (`IDateIso` / `XDateIso` /
  `TStamp`), owner and ACL. On import a `metadata.opf` is read (never uploaded
  as a document): its mask id is used at `createSord`, then `desc`, dates,
  colour (`kind`) and the GRP / MAP field values are written back with
  `checkinSord` + `checkinMap`. Owner and ACL are recorded for reference only -
  they are not re-applied (ids rarely match across repositories).

```text
metadata.opf  (one per container)
  <eloContainer generator="elo-api-playground" exportedIso="...">
    <source repository="..." objId="2" guid="(...)" parentId="1" />
    <sord><name/><desc/><type/><mask id="1" name="Ordner"/><kind/>
          <owner id="0" name="Administrator"/>
          <dates iDateIso="..." xDateIso="" tStamp="..."/></sord>
    <groupFields><field name="..."><value>...</value></field></groupFields>
    <mapFields><field key="..."><value>...</value></field></mapFields>
    <acl><entry id="9998" type="0" name="..." access="63"/></acl>
  </eloContainer>
```

## 4. Where to go next

Copying a GRP (index) field into a MAP field, symmetric links between objects,
and public share URLs each have their own topic in this category.
