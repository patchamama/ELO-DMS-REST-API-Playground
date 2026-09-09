# import the shared client:  from elo_playground import connect
# topic:    Get the text of a document already in the archive
# category: OCR & text extraction
# id:       ocr.archived

from elo_playground import connect, EloError

elo = connect()
ALL = "449304431574384639"

try:
    # 1) find the first document in the archive to work on
    res = elo.call("findFirstSords", {
        "findInfo": {"findByType": {"typeMin": 254, "typeMax": 998}},
        "max": 1, "sordZ": {"bset": ALL},
    })
    docs = res.get("sords") or []
    if res.get("searchId"):
        elo.call("findClose", {"searchId": res["searchId"]})
    if not docs:
        print("no documents in this archive - nothing to OCR")
    else:
        obj_id = str(docs[0]["id"])
        print(f'working on document {obj_id}  "{docs[0].get("name")}"')

        # 2) OCR it now
        try:
            ocr = elo.call("processOcr", {"ocrInfo": {
                "recognizeFile": {"objId": obj_id, "outputFormat": 0, "pageNo": -1},
            }})
            text = ((ocr.get("recognizeFile") or {}).get("text") or "").strip()
            print("OCR text (first 120 chars):", text[:120] or "(empty)")
        except EloError as exc:
            print("processOcr failed:", exc)

        # 3) or read the text the fulltext pipeline already extracted
        doc = elo.call("checkoutDoc", {
            "objId": obj_id,
            "editInfoZ": {"bset": "1", "sordZ": {"bset": "0"}},
        })
        versions = ((doc.get("document") or {}).get("docs")) or []
        ftc = versions[0].get("fulltextContent") if versions else None
        print("fulltext index text     :",
              (ftc.get("data") if isinstance(ftc, dict) else None) or "(not indexed on this archive)")
finally:
    elo.close()
