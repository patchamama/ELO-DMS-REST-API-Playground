# import the shared client:  from elo_playground import connect
# topic:    Start a workflow on an object (write)
# category: Workflows (advanced)
# id:       workflows.start

from elo_playground import connect, EloError

elo = connect()
ALL = "449304431574384639"

# provision a throwaway object to run the workflow on
tpl = elo.call("createSord", {"parentId": "1", "maskId": 0,
                              "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
tpl["name"] = "pg-workflow-target"
obj_id = str(elo.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL},
                                      "unlockZ": {"bset": "1"}}))
flow_id = None
try:
    # 1) pick a real template (ids are not guaranteed to start at 1)
    tmpls = elo.call("findFirstWorkflows", {
        "findInfo": {"type": {"bset": "2"}, "inclHidden": True},
        "max": 5, "wfDiagramZ": {"bset": "0"},
    }).get("workflows") or []
    if not tmpls:
        print("no workflow templates on this repository - nothing to start")
    else:
        tmpl = tmpls[0]
        print(f"using template {tmpl['id']} ({tmpl['name']})")

        # 2) start it (needs the 'start workflow' right)
        try:
            flow_id = elo.call("startWorkFlow", {
                "templFlowId": tmpl["id"],
                "flowName": "playground test workflow",
                "objId": obj_id,
            })
            print("started workflow id:", flow_id)

            # 3) read the running instance back (there is no getWorkFlowStatus)
            res = elo.call("checkoutWorkFlow", {
                "flowId": flow_id,
                "typeZ": {"bset": "0"},          # 0 = running instance (2 = template)
                "lockZ": {"bset": "0"},
                "workFlowDiagramZ": {"bset": "1073741823"},
            })
            wf = res.get("workflow", res)
            nodes = [n.get("nodeName") or n.get("name") for n in wf.get("nodes", [])]
            print("workflow:", wf.get("name"), " nodes:", [n for n in nodes if n][:8])
        except EloError as exc:
            print("could not start the workflow:", exc)
finally:
    # tidy up: cancel + delete the workflow, then the folder
    if flow_id is not None:
        for method in ("terminateWorkFlow", "deleteWorkFlow"):
            try:
                elo.call(method, {"flowId": flow_id})
            except EloError:
                pass
    for step in (False, True):
        try:
            elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                                    "deleteOptions": {"deleteFinally": step}})
        except EloError:
            pass
    elo.close()
