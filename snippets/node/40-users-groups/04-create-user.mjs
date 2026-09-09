// import the shared client:  import { connect } from "elo-playground";
// topic:    Create a user and a group, link them (write)
// category: Users & groups
// id:       users.create

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });
const USER = "pg.demo.user";
const GROUP = "pg.demo.group";

const drop = async (...names) => {
  for (const name of names) {
    try {
      const ids = (await elo.call("checkoutUsers", { ids: [name], checkoutUsersZ: { bset: "1" } }))
        .map((u) => u.id);
      if (ids.length) await elo.call("deleteUsers", { ids });
    } catch (e) { /* not there - fine */ }
  }
};

let uid = null;
let gid = null;
try {
  await drop(USER, GROUP); // start clean

  // 1) create a user (type 1) - id -1 means "new"
  [uid] = await elo.call("checkinUsers", {
    userInfos: [{ id: -1, name: USER, type: 1, pwd: "PlaygroundDemoUser2026!" }],
    checkinUsersZ: { bset: "1" }, unlockZ: { bset: "1" },
  });
  console.log("created user id:", uid);

  // 2) create a group (type 0)
  [gid] = await elo.call("checkinUsers", {
    userInfos: [{ id: -1, name: GROUP, type: 0 }],
    checkinUsersZ: { bset: "1" }, unlockZ: { bset: "1" },
  });
  console.log("created group id:", gid);

  // 3) add the user to the group (edit its groupList)
  const ui = (await elo.call("checkoutUsers", { ids: [uid], checkoutUsersZ: { bset: "513" } }))[0];
  ui.groupList = [...new Set([...(ui.groupList || []), gid])].sort((a, b) => a - b);
  await elo.call("checkinUsers", { userInfos: [ui], checkinUsersZ: { bset: "513" }, unlockZ: { bset: "1" } });

  const back = (await elo.call("checkoutUsers", { ids: [uid], checkoutUsersZ: { bset: "513" } }))[0];
  console.log("user is now in groups:", back.groupList);
} catch (exc) {
  if (exc instanceof EloError) console.log("user/group operation failed:", exc.message);
  else throw exc;
} finally {
  await drop(USER, GROUP);
  console.log("cleaned up");
  elo.close();
}
