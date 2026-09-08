// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Read a user's full record
// category: Users & groups
// id:       users.user-detail

const elo = await connect();

const res = await elo.call("checkoutUsers", {
  ids: [0, 12],
  checkoutUsersZ: { bset: "513" },
});
const users = Array.isArray(res) ? res : res.users || [];
users.forEach((u) => console.log(`${u.name}: groups ${JSON.stringify(u.groupList)}`));
