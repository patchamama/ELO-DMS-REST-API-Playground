# import the shared client:  from elo_playground import connect
# topic:    Get the text of a document that is in the archive
# category: OCR & text extraction
# id:       ocr.archived

from elo_playground import connect, EloError, attachment

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"

# --- provision: upload a document ("Choose file" above, else a sample) ---
picked = attachment()
if picked:
    doc_name, body = picked
else:
    doc_name = "pg-ocr-doc.txt"
    body = b"INVOICE 2026-0042\nAcme GmbH\nTotal: 1,469.13 EUR\n"
ext = doc_name.rsplit(".", 1)[-1].lower() if "." in doc_name else "txt"
sord = elo.call("createDoc", {"parentId": 1, "maskId": 0,
                              "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})["sord"]
sord["name"] = doc_name
doc = elo.call("checkinDocBegin", {"sord": sord, "document": {"docs": [{"ext": ext}]}})
doc["docs"][0]["uploadResult"] = elo.upload(doc["docs"][0]["url"], body)
obj_id = str(elo.call("checkinDocEnd", {"sord": sord, "document": doc,
                                        "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})["objId"])
print("uploaded doc", obj_id)

try:
    # 1) OCR it now
    try:
        ocr = elo.call("processOcr", {"ocrInfo": {
            "recognizeFile": {"objId": obj_id, "outputFormat": 0, "pageNo": -1},
        }})
        text = " ".join(((ocr.get("recognizeFile") or {}).get("text") or "").split())
        print("OCR text (first 120):", text[:120] or "(empty)")
    except EloError as exc:
        print("processOcr failed:", exc)

    # 2) or read the already-extracted fulltext
    info = elo.call("checkoutDoc", {"objId": obj_id,
                                    "editInfoZ": {"bset": "320", "sordZ": {"bset": "0"}}})
    docs = ((info.get("document") or {}).get("docs")) or []
    ftc = docs[0].get("fulltextContent") if docs else None
    print("fulltext index text :",
          (ftc.get("data") if isinstance(ftc, dict) else None) or "(not indexed on this archive)")
finally:
    for step in (False, True):
        try:
            elo.call("deleteSord", {"objId": obj_id, "parentId": "1",
                                    "deleteOptions": {"deleteFinally": step}})
        except EloError:
            pass
    print("cleaned up")
    elo.close()
