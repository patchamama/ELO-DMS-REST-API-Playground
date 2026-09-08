# import the shared client:  from elo_playground import connect
# topic:    List users (and groups)
# category: Users & groups
# id:       users.find-users

from elo_playground import connect

elo = connect()

users = elo.find_all(
    "findFirstUsers", "findNextUsers", "sortedResult",
    {"findUserInfo": {"onlyUsers": True}, "max": 200},
)

print(f"{len(users)} users")
for u in users:
    print(f"  [{u['id']:>5}] {u['name']:<16} {u.get('displayName', '')}")
