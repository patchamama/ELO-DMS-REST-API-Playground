# import the shared client:  from elo_playground import connect
# topic:    List workflow templates and their diagram
# category: Workflows
# id:       workflows.templates

from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(user=ELO_USER, password=ELO_PASS)

res = elo.call("findFirstWorkflows", {
    "findInfo": {"type": {"bset": "2"}, "inclHidden": True},   # 2 = TEMPLATE
    "max": 100,
    "wfDiagramZ": {"bset": "1073741823"},                      # all diagram bits
})
workflows = sorted(res.get("workflows", []), key=lambda w: w.get("id", 0))
print(f"{len(workflows)} templates. First few:")

for wf in workflows[:5]:                          # keep the output readable
    nodes = [n.get("nodeName") or n.get("name") for n in wf.get("nodes", [])]
    assocs = (wf.get("matrix") or {}).get("assocs", [])
    print(f"  [{wf['id']}] {wf['name']}  -  {len(nodes)} nodes, {len(assocs)} connections")
    for n in nodes[:6]:
        print(f"        - {n}")
