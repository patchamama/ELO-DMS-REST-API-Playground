# import the shared client:  from elo_playground import connect
# topic:    OCR a file and show the recognised text
# category: OCR & text extraction
# id:       ocr.extract

import base64
from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

# A tiny "invoice" as plain-text bytes so this snippet is self-contained.
# For a real scan: open("examples/invoices/invoice-2026-0042-acme.pdf","rb")
# .read() and set contentType to "pdf".
payload = (
    "INVOICE 2026-0042\n"
    "Acme GmbH\n"
    "Net:   1,234.56 EUR\n"
    "VAT 19%: 234.57 EUR\n"
    "Total: 1,469.13 EUR\n"
).encode("utf-8")

try:
    res = elo.call("processOcr", {"ocrInfo": {
        "recognizeFile": {
            "imageData": {
                "data": base64.b64encode(payload).decode("ascii"),
                "contentType": "txt",        # "pdf" / "tiff" for a real scan
            },
            "outputFormat": 0,               # OcrInfoC.TEXT
            "pageNo": -1,                     # -1 = every page
        },
    }})
except EloError as exc:
    # e.g. "[ELOIX:10] ... Unknown ticket" when the OCR module is not running
    print("OCR call failed:", exc)
else:
    rf = res.get("recognizeFile")
    if not rf or res.get("exception"):
        print("OCR returned no text:", res.get("exception") or "(empty result)")
    else:
        print("--- recognised text ---")
        print((rf.get("text") or "").strip())
finally:
    elo.close()
