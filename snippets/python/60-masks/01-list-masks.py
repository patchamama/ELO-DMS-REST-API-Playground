# import the shared client:  from elo_playground import connect
# topic:    List metadata masks and their fields
# category: Metadata masks
# id:       masks.list

from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(user=ELO_USER, password=ELO_PASS)

# DocMaskLine.type -> readable kind (ELO 25 DOC_MASK_LINE constants, abridged)
KINDS = {3000: "text", 3001: "date", 3002: "number", 3004: "iso-date",
         3005: "keyword-list", 3006: "user", 3013: "integer"}

masks = elo.find_all(
    "findFirstDocMasks", "findNextDocMasks", "docMasks",
    {"findInfo": {"packageGuid": "", "maskIdsOrNames": []}, "max": 500},
)

for m in masks:
    fields = [f"{ln.get('name')} [{KINDS.get(ln.get('type'), ln.get('type'))}]"
              for ln in (m.get("lines") or [])]
    print(f"{m['name']} ({len(fields)} fields): {', '.join(fields)}")
