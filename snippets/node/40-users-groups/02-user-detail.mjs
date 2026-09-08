// import the shared client:  import { connect } from "elo-playground";
// topic:    Read a user's full record
// category: Users & groups
// id:       users.user-detail

import { connect } from "elo-playground";

const elo = await connect();

const res = await elo.call("checkoutUsers", {
  ids: [0, 12],                        // Administrator + Max Muster
  checkoutUsersZ: { bset: "513" },     // CHECKOUT_USERS.BY_IDS
});
const users = Array.isArray(res) ? res : res.users || [];

for (const u of users) {
  console.log(`${u.name}:`);
  console.log(`    groups     : ${JSON.stringify(u.groupList)}`);
  console.log(`    last login : ${u.lastLoginIso || "-"}`);
  console.log(`    flags      : ${u.flags}`);
}
