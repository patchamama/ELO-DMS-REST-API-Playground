# import the shared client:  from elo_playground import connect
# topic:    Browse folders and preview the newest files
# category: Testing lab
# id:       lab.recent-files

import os
from datetime import datetime, timedelta
from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

# Only the Sord members the listing needs - paging stays fast. SordC bits:
# 5 name, 7 IDateIso (modified), 17 ownerName, 54 docVersion, 59 refPaths.
LEAN = str((1 << 5) | (1 << 7) | (1 << 17) | (1 << 54) | (1 << 59))
FOLDER_ID = "2"          # the folder to look below ("1" = repository root)
DAYS_BACK = 30

# An indexed range search on the modification date. There is no cheap
# "recursive children, newest first" in IX: findChildren endLevel -1 walks
# the whole subtree server-side and sortOrder does not sort by date.
since = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y%m%d%H%M%S")
until = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d%H%M%S")
res = elo.call("findFirstSords", {
    "findInfo": {"findByIndex": {"iDateIso": f"{since}...{until}"}, "findByType": {"typeDocuments": True}},
    "max": 500,
    "sordZ": {"bset": LEAN},
})
rows = list(res.get("sords") or [])
while res.get("moreResults"):
    res = elo.call("findNextSords", {"searchId": res["searchId"], "idx": len(rows), "max": 500, "sordZ": {"bset": LEAN}})
    page = res.get("sords") or []
    if not page:
        break
    rows.extend(page)
if res.get("searchId"):
    elo.call("findClose", {"searchId": res["searchId"]})


def path_of(row):
    """refPaths[0].path = the folders from below the root down to the parent."""
    first = (row.get("refPaths") or [{}])[0]
    return [(str(p["id"]), p["name"]) for p in (first.get("path") or [])]


# keep documents that sit in FOLDER_ID or anywhere below it
hits = [r for r in rows if FOLDER_ID == "1" or FOLDER_ID in [i for i, _ in path_of(r)] or str(r.get("parentId")) == FOLDER_ID]
hits.sort(key=lambda r: r.get("IDateIso", ""), reverse=True)
print(f"newest documents below folder {FOLDER_ID} (last {DAYS_BACK} days, {len(hits)} found):")
for r in hits[:50]:
    dv = r.get("docVersion") or {}
    d = r["IDateIso"]
    print(f"{d[:4]}-{d[4:6]}-{d[6:8]} {d[8:10]}:{d[10:12]}  {dv.get('ext', ''):5} {int(dv.get('size', 0)):>8} B  {r['name'][:40]:40} {' / '.join(n for _, n in path_of(r))}")

# preview the newest one: checkoutDoc hands out a download URL for this session
if hits:
    doc = hits[0]
    info = elo.call("checkoutDoc", {"objId": str(doc["id"]), "editInfoZ": {"bset": "320", "sordZ": {"bset": "0"}}})
    first = (info.get("document") or {}).get("docs", [{}])[0]
    try:
        data = elo.download(first["url"], max_bytes=200_000)
        text = data.decode("utf-8-sig", "replace")
        print(f"\n--- {doc['name']} ({first.get('ext')}) ---\n" + "\n".join(text.splitlines()[:10]))
    except EloError as exc:
        print("could not download:", exc)

elo.close()
