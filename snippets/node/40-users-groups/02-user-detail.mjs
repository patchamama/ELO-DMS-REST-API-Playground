// import the shared client:  import { connect } from "elo-playground";
// topic:    Read a user's full record
// category: Users & groups
// id:       users.user-detail

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });

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
