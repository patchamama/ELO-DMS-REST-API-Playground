// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Read a user's full record
// category: Users & groups
// id:       users.user-detail

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });

const res = await elo.call("checkoutUsers", {
  ids: [0, 12],
  checkoutUsersZ: { bset: "513" },
});
const users = Array.isArray(res) ? res : res.users || [];
users.forEach((u) => console.log(`${u.name}: groups ${JSON.stringify(u.groupList)}`));
