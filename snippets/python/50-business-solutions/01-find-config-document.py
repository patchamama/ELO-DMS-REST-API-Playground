# import the shared client:  from elo_playground import connect
# topic:    Find a Business Solution config document
# category: Business Solutions
# id:       business-solutions.find-config

import json
from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(user=ELO_USER, password=ELO_PASS)

# 1) find "*.config.json" documents (type >= 254 is a document, not a folder)
hits = elo.find_all(
    "findFirstSords", "findNextSords", "sords",
    {"findInfo": {"findByIndex": {"name": "*.config.json"}}, "max": 50,
     "sordZ": {"bset": "449304431574384639"}},
)
docs = [s for s in hits if int(s.get("type", 0)) >= 254]
doc = docs[0]
print("config document:", doc["name"], "id", doc["id"])

# 2) check it out to get an authenticated download URL
info = elo.call("checkoutDoc", {"objId": str(doc["id"]),
                                "editInfoZ": {"bset": "320", "sordZ": {"bset": "0"}}})
url = ((info.get("document") or {}).get("docs") or [{}])[0].get("url")

# 3) download the bytes on the same session and parse the JSON
cfg = json.loads(elo.download(url, max_bytes=100_000))
print("top-level keys:", list(cfg)[:10])
