# import the shared client:  from elo_playground import connect
# topic:    Create a user and a group, link them (write)
# category: Users & groups
# id:       users.create

import os
from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1")
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator")
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "")

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
USER, GROUP = "pg.demo.user", "pg.demo.group"

def drop(*names):
    """Delete principals by name if they exist (tidy up a previous run)."""
    for name in names:
        try:
            ids = [u["id"] for u in elo.call("checkoutUsers",
                                             {"ids": [name], "checkoutUsersZ": {"bset": "1"}})]
            if ids:
                elo.call("deleteUsers", {"ids": ids})
        except EloError:
            pass

uid = gid = None
try:
    drop(USER, GROUP)                       # start from a clean slate

    # 1) create a user (type 1) - id -1 means "new"
    uid = elo.call("checkinUsers", {
        "userInfos": [{"id": -1, "name": USER, "type": 1, "pwd": "PlaygroundDemoUser2026!"}],
        "checkinUsersZ": {"bset": "1"}, "unlockZ": {"bset": "1"},
    })[0]
    print("created user id:", uid)

    # 2) create a group (type 0)
    gid = elo.call("checkinUsers", {
        "userInfos": [{"id": -1, "name": GROUP, "type": 0}],
        "checkinUsersZ": {"bset": "1"}, "unlockZ": {"bset": "1"},
    })[0]
    print("created group id:", gid)

    # 3) add the user to the group (edit its groupList)
    ui = elo.call("checkoutUsers", {"ids": [uid], "checkoutUsersZ": {"bset": "513"}})[0]
    ui["groupList"] = sorted(set((ui.get("groupList") or []) + [gid]))
    elo.call("checkinUsers", {"userInfos": [ui], "checkinUsersZ": {"bset": "513"},
                              "unlockZ": {"bset": "1"}})

    back = elo.call("checkoutUsers", {"ids": [uid], "checkoutUsersZ": {"bset": "513"}})[0]
    print("user is now in groups:", back.get("groupList"))
except EloError as exc:
    print("user/group operation failed:", exc)
finally:
    drop(USER, GROUP)                       # remove the demo principals
    print("cleaned up")
    elo.close()
