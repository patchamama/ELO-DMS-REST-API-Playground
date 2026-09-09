# import the shared client:  from elo_playground import connect
# topic:    Send a document to the Textreader and get its text
# category: Testing lab
# id:       lab.extract-text

from elo_playground import connect
# import base64

elo = connect()

obj_id = "4711"     # an archived document to run OCR on

res = elo.call("processOcr", {"ocrInfo": {
    "recognizeFile": {
        "objId": obj_id,        # ...OR: "imageData": {"data": base64.b64encode(pdf_bytes).decode(),
        "outputFormat": 0,      #                        "contentType": "application/pdf"}
        "pageNo": -1,           # -1 = every page
    },
}})

rf = res.get("recognizeFile") or {}
if res.get("exception"):
    print("OCR error:", res["exception"])
else:
    print("OCR text:")
    print((rf.get("text") or "").strip())
