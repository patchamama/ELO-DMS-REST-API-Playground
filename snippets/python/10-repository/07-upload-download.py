# import the shared client:  from elo_playground import connect
# topic:    Upload and download a document (write)
# category: Repository & objects
# id:       repository.upload-download

from elo_playground import connect, EloError

elo = connect()
ALL = "449304431574384639"

parent_id = 1                 # a folder to file the document under
payload = b"hello from the playground\n"

# 1) a Sord template for the new document
sord = elo.call("createDoc", {"parentId": parent_id, "maskId": 0,
                              "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
sord["name"] = "pg-hello.txt"

# 2) ask for an upload URL
doc = elo.call("checkinDocBegin", {"sord": sord, "document": {"docs": [{"ext": "txt"}]}})

# 3) POST the bytes and record the server's upload token
doc["docs"][0]["uploadResult"] = elo.upload(doc["docs"][0]["url"], payload)

# 4) commit
res = elo.call("checkinDocEnd", {"sord": sord, "document": doc,
                                 "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})
doc_id = str(res["objId"])
print("uploaded doc id:", doc_id)

try:
    # --- read it back ---
    info = elo.call("checkoutDoc", {"objId": doc_id,
                                    "editInfoZ": {"bset": "320", "sordZ": {"bset": "0"}}})
    url = info["document"]["docs"][0]["url"]
    print("round-trip content:", elo.download(url).decode().strip())
except EloError as exc:
    print("download failed:", exc)
finally:
    for step in (False, True):
        try:
            elo.call("deleteSord", {"objId": doc_id, "parentId": "1",
                                    "deleteOptions": {"deleteFinally": step}})
        except EloError:
            pass
    elo.close()
