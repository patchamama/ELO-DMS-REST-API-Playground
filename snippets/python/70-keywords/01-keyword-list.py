# import the shared client:  from elo_playground import connect
# topic:    Read a keyword list
# category: Keyword lists
# id:       keywords.list

from elo_playground import connect

elo = connect()

res = elo.call("checkoutKeywordList", {
    "kwid": "ELOSTDSWL",
    "max": 500,
    "keywordZ": {"bset": "7"},
})

def walk(nodes, depth=0):
    for n in nodes or []:
        print("  " * (depth + 1) + "- " + (n.get("text") or "(no text)"))
        walk(n.get("children"), depth + 1)

top = res.get("children") or []
print(f"{res.get('id')}: {len(top)} top-level entries")
walk(top[:8])                       # first few, with any nesting
