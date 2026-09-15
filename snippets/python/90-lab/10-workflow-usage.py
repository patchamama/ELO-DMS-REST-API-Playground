# import the shared client:  from elo_playground import connect
# topic:    Most used workflows
# category: Testing lab
# id:       lab.workflow-usage

import os
from collections import defaultdict
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

# WFTypeC: 1 = active, 2 = template, 4 = finished (a WFTypeZ bitset, not an int).
# WFDiagramC bits: 0 id/name/version, 4 completionDateIso, 5 nodes,
# 9 startDateIso, 11 ownerName, 15 templateName, 23 objName.
TEMPLATE_Z = str((1 << 0) | (1 << 5) | (1 << 11))
INSTANCE_Z = str((1 << 0) | (1 << 4) | (1 << 9) | (1 << 11) | (1 << 15) | (1 << 23))


def find_workflows(wf_type, bset):
    """findFirstWorkflows / findNextWorkflows / findClose - rows in 'workflows'."""
    res = elo.call("findFirstWorkflows", {"findInfo": {"type": {"bset": wf_type}}, "max": 500, "wfDiagramZ": {"bset": bset}})
    rows = list(res.get("workflows") or [])
    while res.get("moreResults"):
        res = elo.call("findNextWorkflows", {"searchId": res["searchId"], "idx": len(rows), "max": 500, "wfDiagramZ": {"bset": bset}})
        if not res.get("workflows"):
            break
        rows.extend(res["workflows"])
    if res.get("searchId"):
        elo.call("findClose", {"searchId": res["searchId"]})
    return rows


templates = find_workflows("2", TEMPLATE_Z)
active = find_workflows("1", INSTANCE_Z)
finished = find_workflows("4", INSTANCE_Z)     # only what cleanup has not removed yet
print(f"{len(templates)} templates, {len(active)} active, {len(finished)} finished workflows on the server\n")

# ELO keeps no usage counter: count the instances per templateId ourselves.
stats = defaultdict(lambda: {"started": 0, "active": 0, "finished": 0, "last": "", "last_obj": ""})
names = {str(t["id"]): t["name"] for t in templates}
for kind, rows in (("active", active), ("finished", finished)):
    for w in rows:
        s = stats[str(w.get("templateId"))]
        s["started"] += 1
        s[kind] += 1
        if w.get("startDateIso", "") > s["last"]:
            s["last"], s["last_obj"] = w["startDateIso"], w.get("objName", "")
for t in templates:                      # unused templates still show up, with 0
    stats.setdefault(str(t["id"]), stats.default_factory())

ranked = sorted(stats.items(), key=lambda kv: (-kv[1]["started"], names.get(kv[0], kv[0]).lower()))
print(f" {'#':>2}  {'started':>7}  {'active':>6}  {'finished':>8}  {'last start':16}  {'template':40}  nodes")
for i, (tid, s) in enumerate(ranked[:25], 1):
    tpl = next((t for t in templates if str(t["id"]) == tid), {})
    d = s["last"]
    last = f"{d[:4]}-{d[4:6]}-{d[6:8]} {d[8:10]}:{d[10:12]}" if d else ""
    # templates carry no description field; the start node's comment is the closest thing
    desc = ((tpl.get("nodes") or [{}])[0].get("comment") or "").strip()
    print(f" {i:>2}  {s['started']:>7}  {s['active']:>6}  {s['finished']:>8}  {last:16}  {names.get(tid, tid)[:40]:40}  {len(tpl.get('nodes') or []):>5}" + (f"   {desc[:40]}" if desc else ""))

elo.close()
