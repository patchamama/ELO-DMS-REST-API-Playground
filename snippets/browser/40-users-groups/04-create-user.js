// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Create a user and a group, link them (write)
// category: Users & groups
// id:       users.create

const elo = await connect();
const [uid] = await elo.call("checkinUsers", {
  userInfos: [{ id: -1, name: "pg.demo.user", type: 1, pwd: "PlaygroundDemoUser2026!" }],
  checkinUsersZ: { bset: "1" }, unlockZ: { bset: "1" },
});
console.log("created user id:", uid);
