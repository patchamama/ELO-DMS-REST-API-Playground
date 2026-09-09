# import the shared client:  from elo_playground import connect
# topic:    Link two objects (and remove the link)
# category: Testing lab
# id:       lab.links

from elo_playground import connect, EloError

elo = connect()
ALL = "449304431574384639"
PARENT = 1

def make_folder(name):
    tpl = elo.call("createSord", {"parentId": str(PARENT), "maskId": 0,
                                  "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
    tpl["name"] = name
    return str(elo.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL},
                                        "unlockZ": {"bset": "1"}}))

a = b = None
try:
    a, b = make_folder("pg-link-A"), make_folder("pg-link-B")
    print(f"created A={a}  B={b}")

    elo.call("linkSords", {"fromId": a, "toIds": [b], "linkZ": {"bset": "1"}})
    out = elo.call("checkoutSord", {"objId": a,
                                    "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
    print("linked  -> A.linksGoOut =", [l["id"] for l in out.get("linksGoOut", [])])

    elo.call("unlinkSords", {"fromId": a, "toIds": [b], "linkZ": {"bset": "1"}})
    print("unlinked")
except EloError as exc:
    print("link operation failed:", exc)
finally:
    for oid in (a, b):
        if oid:
            try:
                elo.call("deleteSord", {"parentId": str(PARENT), "objId": oid,
                                        "deleteOptions": {"deleteFinally": False}})
                elo.call("deleteSord", {"parentId": str(PARENT), "objId": oid,
                                        "deleteOptions": {"deleteFinally": True}})
            except EloError as exc:
                print("cleanup of", oid, "failed:", exc)
    print("cleaned up")
    elo.close()
