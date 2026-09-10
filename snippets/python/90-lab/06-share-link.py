# import the shared client:  from elo_playground import connect
# topic:    Create a public share link for a document
# category: Testing lab
# id:       lab.share-link

import os
from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1")
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator")
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "")

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"

# --- provision: upload a throwaway document ---
body = b"public share demo\n"
sord = elo.call("createDoc", {"parentId": 1, "maskId": 0,
                              "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
sord["name"] = "pg-share.txt"
doc = elo.call("checkinDocBegin", {"sord": sord, "document": {"docs": [{"ext": "txt"}]}})
doc["docs"][0]["uploadResult"] = elo.upload(doc["docs"][0]["url"], body)
obj_id = str(elo.call("checkinDocEnd", {"sord": sord, "document": doc,
                                        "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})["objId"])
print("uploaded doc", obj_id)

try:
    # 1) mint a public download link (5 downloads, no expiry)
    pd = elo.call("insertPublicDownload", {"opts": {
        "objId": obj_id, "remaining": 5, "fileNameFromSordName": True,
    }})
    print("share url :", pd.get("url"))
    print("remaining :", pd.get("remaining"))

    # 2) list the links for this object
    links = elo.call("getPublicDownloads", {"opts": {"objId": obj_id}})
    print("links now :", len(links))

    # 3) revoke them
    elo.call("terminatePublicDownloadUrls", {"opts": {"objId": obj_id}})
    print("after revoke:", len(elo.call("getPublicDownloads", {"opts": {"objId": obj_id}})))
except EloError as exc:
    print("share-link operation failed:", exc)
finally:
    for step in (False, True):
        try:
            elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                                    "deleteOptions": {"deleteFinally": step}})
        except EloError:
            pass
    print("cleaned up")
    elo.close()
