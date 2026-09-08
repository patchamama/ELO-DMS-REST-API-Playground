# import the shared client:  from elo_playground import connect
# topic:    Search by an index-field value
# category: Search
# id:       search.by-field-value

from elo_playground import connect

elo = connect()

field = "ELO_FNAME"        # a metadata field key (mask line "Group" name)
value = "*.js"             # wildcards allowed

rows = elo.find_all(
    "findFirstSords", "findNextSords", "sords",
    {
        "findInfo": {"findByIndex": {"objKeys": [{"name": field, "data": [value]}]}},
        "max": 50,
        "sordZ": {"bset": "449304431574384639"},
    },
)

print(f"{len(rows)} objects where {field} matches {value!r}")
for s in rows[:10]:
    print(f"  - {s['name']}")
