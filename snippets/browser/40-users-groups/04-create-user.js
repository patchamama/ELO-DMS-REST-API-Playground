// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Create a user and a group, link them (write)
// category: Users & groups
// id:       users.create

const elo = await connect();
const USER = "pg.demo.user";

const drop = async (name) => {
  try {
    const ids = (await elo.call("checkoutUsers", { ids: [name], checkoutUsersZ: { bset: "1" } }))
      .map((u) => u.id);
    if (ids.length) await elo.call("deleteUsers", { ids });
  } catch (e) { /* not there */ }
};

try {
  await drop(USER);
  const [uid] = await elo.call("checkinUsers", {
    userInfos: [{ id: -1, name: USER, type: 1, pwd: "PlaygroundDemoUser2026!" }],
    checkinUsersZ: { bset: "1" }, unlockZ: { bset: "1" },
  });
  console.log("created user id:", uid);
} catch (exc) {
  console.log("user operation failed:", exc.message);
} finally {
  await drop(USER);
  console.log("cleaned up");
}
