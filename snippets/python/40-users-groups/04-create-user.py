# import the shared client:  from elo_playground import connect
# topic:    Create a user and a group, link them (write)
# category: Users & groups
# id:       users.create

from elo_playground import connect

elo = connect()

# 1) create a user (type 1) - id -1 means "new"
user_ids = elo.call("checkinUsers", {
    "userInfos": [{"id": -1, "name": "pg.demo.user", "type": 1,
                   "pwd": "PlaygroundDemoUser2026!"}],
    "checkinUsersZ": {"bset": "1"},
    "unlockZ": {"bset": "1"},
})
uid = user_ids[0]
print("created user id:", uid)

# 2) create a group (type 0)
group_ids = elo.call("checkinUsers", {
    "userInfos": [{"id": -1, "name": "pg.demo.group", "type": 0}],
    "checkinUsersZ": {"bset": "1"},
    "unlockZ": {"bset": "1"},
})
gid = group_ids[0]
print("created group id:", gid)

# 3) add the user to the group (edit its groupList)
ui = elo.call("checkoutUsers", {"ids": [uid], "checkoutUsersZ": {"bset": "513"}})[0]
ui["groupList"] = sorted(set((ui.get("groupList") or []) + [gid]))
elo.call("checkinUsers", {"userInfos": [ui], "checkinUsersZ": {"bset": "513"},
                          "unlockZ": {"bset": "1"}})

back = elo.call("checkoutUsers", {"ids": [uid], "checkoutUsersZ": {"bset": "513"}})[0]
print("user is now in groups:", back.get("groupList"))
