# import the shared client:  from elo_playground import connect
# topic:    Start a workflow on an object (write)
# category: Workflows (advanced)
# id:       workflows.start

from elo_playground import connect

elo = connect()

# 1) pick a real template (ids are not guaranteed to start at 1)
tmpls = elo.call("findFirstWorkflows", {
    "findInfo": {"type": {"bset": "2"}, "inclHidden": True},
    "max": 5, "wfDiagramZ": {"bset": "0"},
})["workflows"]
tmpl = tmpls[0]
print(f"using template {tmpl['id']} ({tmpl['name']})")

# 2) start it on an object. objId must be a real archive object - use a
#    throwaway folder; this starts a REAL workflow instance.
obj_id = 1        # replace with a throwaway object's id

flow_id = elo.call("startWorkFlow", {
    "templFlowId": tmpl["id"],
    "flowName": "playground test workflow",
    "objId": str(obj_id),
})
print("started workflow id:", flow_id)

# 3) read the running instance back (there is no getWorkFlowStatus)
res = elo.call("checkoutWorkFlow", {
    "flowId": flow_id,
    "typeZ": {"bset": "0"},                 # 0 = running instance (2 would read it as a template)
    "lockZ": {"bset": "0"},                 # no lock
    "workFlowDiagramZ": {"bset": "1073741823"},
})
wf = res.get("workflow", res)
nodes = [n.get("nodeName") or n.get("name") for n in wf.get("nodes", [])]
print("workflow:", wf.get("name"), " nodes:", [n for n in nodes if n][:8])
