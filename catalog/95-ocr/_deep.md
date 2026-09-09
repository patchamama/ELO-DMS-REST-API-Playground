# OCR & text extraction - deep dive

Turn recognised text into structured fields. The blocks below OCR a few
plain-text payloads (stand-ins for the PDFs in `examples/invoices/`) and pull
out the invoice number, date and total with regular expressions - the same
shape you would feed into `checkinSord` to index a document.

## 1. OCR several files and extract invoice fields

```python
import base64
import re
from elo_playground import connect, EloError

elo = connect()

SAMPLES = {
    "acme":   "RECHNUNG / INVOICE\nRechnungsnummer / Invoice no.: 2026-0042\nRechnungsdatum / Invoice date: 2026-02-14\nGesamtbetrag / Total: 1.469,13 EUR\n",
    "globex": "INVOICE\nInvoice no.: 2026-0043\nInvoice date: 2026-03-01\nTotal due: 545.00 USD\n",
    "initech":"RECHNUNG\nRechnungsnummer: 2026-0044\nRechnungsdatum: 2026-03-18\nRechnungsbetrag: 1.351,25 CHF\n",
}

NUM  = re.compile(r"(?:Invoice no\.|Rechnungsnummer)[^\d]*([\d-]+)", re.I)
DATE = re.compile(r"(?:Invoice date|Rechnungsdatum)[^\d]*(\d{4}-\d{2}-\d{2})", re.I)
TOTAL = re.compile(r"(?:Total(?: due)?|Gesamtbetrag|Rechnungsbetrag)[^\d]*([\d.,]+ ?[A-Z]{3})", re.I)

def field(rx, text):
    m = rx.search(text)
    return m.group(1).strip() if m else "?"

for name, body in SAMPLES.items():
    try:
        res = elo.call("processOcr", {"ocrInfo": {"recognizeFile": {
            "imageData": {"data": base64.b64encode(body.encode()).decode(), "contentType": "txt"},
            "outputFormat": 0,
        }}})
    except EloError as exc:
        print(f"{name:8} OCR failed: {exc}")
        continue
    text = (res.get("recognizeFile") or {}).get("text") or ""
    print(f"{name:8} no={field(NUM, text):10} date={field(DATE, text):12} total={field(TOTAL, text)}")

elo.close()
```

## 2. Index the extracted total back onto the document

Once you have a value, write it to a GRP field with the read / modify /
`checkinSord` cycle (see *Testing lab -> CRUD*). Sketch:

```python
from elo_playground import connect

elo = connect()
ALL = "449304431574384639"
obj_id = "5001"          # the document you OCR'd

sord = elo.call("checkoutSord", {
    "objId": obj_id, "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
})["sord"]

sord.setdefault("objKeys", [])
for k in sord["objKeys"]:
    if k.get("name") == "INVOICE_TOTAL":
        k["data"] = ["1.469,13 EUR"]
        break
else:
    sord["objKeys"].append({"name": "INVOICE_TOTAL", "data": ["1.469,13 EUR"]})

elo.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})
print("indexed INVOICE_TOTAL on", obj_id)
elo.close()
```
