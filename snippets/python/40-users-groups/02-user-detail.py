# import the shared client:  from elo_playground import connect
# topic:    Read a user's full record
# category: Users & groups
# id:       users.user-detail

from elo_playground import connect

elo = connect()

res = elo.call("checkoutUsers", {
    "ids": [0, 12],                       # Administrator + Max Muster
    "checkoutUsersZ": {"bset": "513"},    # CHECKOUT_USERS.BY_IDS
})
users = res if isinstance(res, list) else res.get("users", [])

for u in users:
    print(f"{u['name']}:")
    print(f"    groups     : {u.get('groupList')}")
    print(f"    last login : {u.get('lastLoginIso', '-')}")
    print(f"    flags      : {u.get('flags')}")
