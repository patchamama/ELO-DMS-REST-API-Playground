// import the shared client:  import { connect } from "elo-playground";
// topic:    Create a user and a group, link them (write)
// category: Users & groups
// id:       users.create

import { connect } from "elo-playground";

const elo = await connect();

// 1) create a user (type 1) - id -1 means "new"
const [uid] = await elo.call("checkinUsers", {
  userInfos: [{ id: -1, name: "pg.demo.user", type: 1, pwd: "PlaygroundDemoUser2026!" }],
  checkinUsersZ: { bset: "1" },
  unlockZ: { bset: "1" },
});
console.log("created user id:", uid);

// 2) create a group (type 0)
const [gid] = await elo.call("checkinUsers", {
  userInfos: [{ id: -1, name: "pg.demo.group", type: 0 }],
  checkinUsersZ: { bset: "1" },
  unlockZ: { bset: "1" },
});
console.log("created group id:", gid);

// 3) add the user to the group (edit its groupList)
const ui = (await elo.call("checkoutUsers", { ids: [uid], checkoutUsersZ: { bset: "513" } }))[0];
ui.groupList = [...new Set([...(ui.groupList || []), gid])].sort((a, b) => a - b);
await elo.call("checkinUsers", { userInfos: [ui], checkinUsersZ: { bset: "513" }, unlockZ: { bset: "1" } });

const back = (await elo.call("checkoutUsers", { ids: [uid], checkoutUsersZ: { bset: "513" } }))[0];
console.log("user is now in groups:", back.groupList);
