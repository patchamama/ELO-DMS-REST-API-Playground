# import the shared client:  from elo_playground import connect
# topic:    Generate an ELO structure on the local filesystem (and back)
# category: Testing lab
# id:       lab.fs-sync

from elo_playground import connect, EloError
import os
import shutil
import xml.etree.ElementTree as ET

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1")
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator")
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "")

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"

FOLDER_ID = "1"                  # the ELO folder to mirror (1 = repository root)
DEST = "elo-archiv-structure"    # local target; the panel above uses sandbox/<this>
MAX_BYTES = 25 * 1024 * 1024     # per-document cap; download() truncates at 200 KB by default

# the picked folder itself becomes the top directory of the mirror
sord = elo.call("checkoutSord", {"objId": FOLDER_ID,
    "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}}).get("sord") or {}
top = "".join(c if c not in '<>:"/\\|?*' else "_" for c in str(sord.get("name") or "")).strip()
DEST_ROOT = os.path.join(DEST, top or ("folder-" + FOLDER_ID))

def write_meta(obj_id, folder):
    # metadata.opf: mask + GRP/MAP field values + dates, for a later re-import
    try:
        sd = elo.call("checkoutSord", {"objId": str(obj_id),
            "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}}).get("sord") or {}
    except EloError as exc:
        print("meta skip", obj_id, "-", exc)
        return
    try:
        mp = elo.call("checkoutMap", {"objId": int(obj_id), "id": str(obj_id),
            "domainName": "objekte", "keyNames": ["*"], "lockZ": {"bset": "0"}}).get("items") or []
    except EloError:
        mp = []
    root = ET.Element("eloContainer", {"generator": "elo-api-playground"})
    ET.SubElement(root, "source", {"objId": str(sd.get("id", "")), "guid": str(sd.get("guid", ""))})
    node = ET.SubElement(root, "sord")
    ET.SubElement(node, "name").text = str(sd.get("name") or "")
    ET.SubElement(node, "desc").text = str(sd.get("desc") or "")
    ET.SubElement(node, "mask", {"id": str(sd.get("mask", "")), "name": str(sd.get("maskName", ""))})
    ET.SubElement(node, "dates", {"iDateIso": str(sd.get("IDateIso", "")),
                                 "xDateIso": str(sd.get("XDateIso", ""))})
    gf = ET.SubElement(root, "groupFields")
    for k in sd.get("objKeys") or []:
        if k.get("name"):
            fe = ET.SubElement(gf, "field", {"name": str(k["name"])})
            for v in k.get("data") or []:
                ET.SubElement(fe, "value").text = str(v)
    mf = ET.SubElement(root, "mapFields")
    for it in mp:
        fe = ET.SubElement(mf, "field", {"key": str(it.get("key"))})
        ET.SubElement(fe, "value").text = str(it.get("value") or "")
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(os.path.join(folder, "metadata.opf"),
                               encoding="utf-8", xml_declaration=True)

def children(parent_id):
    res = elo.call("findFirstSords", {
        "findInfo": {"findChildren": {"parentId": str(parent_id),
                                     "mainParent": True, "endLevel": 1}},
        "max": 1000, "sordZ": {"bset": ALL},
    })
    rows = res.get("sords", []) if isinstance(res, dict) else []
    search_id = res.get("searchId") if isinstance(res, dict) else None
    if search_id:
        try:
            elo.call("findClose", {"searchId": search_id})
        except EloError:
            pass
    return rows

folders = docs = 0

def mirror(parent_id, path):
    global folders, docs
    os.makedirs(path, exist_ok=True)
    write_meta(parent_id, path)                           # one metadata.opf per container
    for s in children(parent_id):
        name = str(s.get("name") or s.get("id")).replace("/", "_").replace("\\", "_")
        if int(s.get("type", 0) or 0) < 254:                 # folder
            folders += 1
            mirror(s["id"], os.path.join(path, name))
        else:                                                # document
            try:
                info = elo.call("checkoutDoc", {"objId": s["id"],
                    "editInfoZ": {"bset": "320", "sordZ": {"bset": "0"}}})
                dl = ((info.get("document") or {}).get("docs")) or []
                if not dl or not dl[0].get("url"):
                    continue
                ext = str(dl[0].get("ext") or "").lstrip(".")
                body = elo.download(dl[0]["url"], max_bytes=MAX_BYTES)
                if isinstance(body, str):
                    body = body.encode("utf-8")
                fname = name if ("." in name or not ext) else name + "." + ext
                with open(os.path.join(path, fname), "wb") as fh:
                    fh.write(body)
                docs += 1
            except EloError as exc:
                print("skip", name, "-", exc)

try:
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    mirror(FOLDER_ID, DEST_ROOT)
    print("mirrored", FOLDER_ID, "->", DEST_ROOT,
          "(", folders + 1, "folders,", docs, "docs, +metadata.opf )")
except EloError as exc:
    print("mirror failed:", exc)
finally:
    elo.close()
