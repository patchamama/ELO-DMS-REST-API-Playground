# import the shared client:  from elo_playground import connect
# topic:    Resolve a GUID to an object (Sord)
# category: Repository & objects
# id:       repository.checkout-sord

from elo_playground import connect

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = "http://localhost:9090/ix-Repository1"
ELO_USER = "Administrator"
ELO_PASS = "elo"

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)

# objId can be an int id OR a "(GUID)" copied from the ELO client.
# 2 is a real folder on a stock repository, so this runs anywhere.
obj_id = 2   # e.g. "(4A5B6C7D-8E9F-0A1B-2C3D-4E5F60718293)"

res = elo.call("checkoutSord", {
    "objId": obj_id,
    # checkoutSord answers with an EditInfo; sordZ goes INSIDE editInfoZ,
    # and editInfoZ.bset "1" (mbSord) makes it fill in result.sord.
    "editInfoZ": {"bset": "1", "sordZ": {"bset": "449304431574384639"}},
})
sord = res["sord"]

# ELO type: 254..998 = document, below that = folder/structure
# (special containers like the repo root use 9999).
kind = "document" if 254 <= int(sord.get("type", 0)) < 999 else "folder"
print(f"{kind}: {sord['name']}  (id {sord['id']}, mask: {sord.get('maskName')})")
