# import the shared client:  from elo_playground import connect
# topic:    Full-text search
# category: Search
# id:       search.fulltext

from elo_playground import connect

elo = connect()

rows = elo.find_all(
    "findFirstSords", "findNextSords", "sords",
    {
        "findInfo": {"findByFulltext": {"fulltext": "agreement", "isTree": False}},
        "max": 50,
        "sordZ": {"bset": "449304431574384639"},
    },
)

print(f"{len(rows)} documents match 'agreement'")
for s in rows:
    print(f"  {s['name']}")
if not rows:
    print("  (0 hits usually means the ELO full-text service is not running "
          "or has not finished indexing on this instance)")
