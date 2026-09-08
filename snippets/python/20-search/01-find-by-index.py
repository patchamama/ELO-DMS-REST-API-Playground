# import the shared client:  from elo_playground import connect
# topic:    Find objects by index field
# category: Search
# id:       search.find-by-index

from elo_playground import connect

elo = connect()

rows = elo.find_all(
    "findFirstSords", "findNextSords", "sords",
    {
        "findInfo": {"findByIndex": {
            "name": "Invoice *",        # wildcard match on the object name
            "exactName": False,
        }},
        "max": 50,
        "sordZ": {"bset": "449304431574384639"},
    },
)

print(f"{len(rows)} matches")
for s in rows:
    print(f"  {s['name']}  (mask: {s.get('maskName')})")
