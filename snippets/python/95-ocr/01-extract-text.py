# import the shared client:  from elo_playground import connect
# topic:    OCR a file and show the recognised text
# category: OCR & text extraction
# id:       ocr.extract

import base64
import os
from elo_playground import connect, EloError, attachment

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

# "Choose file" above picks a real scan; without it a tiny built-in invoice
# is sent so the snippet is self-contained.
picked = attachment()
if picked:
    name, data = picked
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else "txt"
else:
    name, ext = "invoice.txt", "txt"
    data = (
        "INVOICE 2026-0042\n"
        "Acme GmbH\n"
        "Net:   1,234.56 EUR\n"
        "VAT 19%: 234.57 EUR\n"
        "Total: 1,469.13 EUR\n"
    ).encode("utf-8")
print(f"sending {name}  ({len(data)} bytes, contentType={ext})")

try:
    res = elo.call("processOcr", {"ocrInfo": {
        "recognizeFile": {
            "imageData": {"data": base64.b64encode(data).decode("ascii"), "contentType": ext},
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
