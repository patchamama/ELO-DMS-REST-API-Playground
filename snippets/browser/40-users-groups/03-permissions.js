// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Decode a user's rights bitset
// category: Users & groups
// id:       users.permissions

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });
const ACCESS = [
  [1, "main administrator (all rights)"], [8, "edit documents"],
  [256, "start workflows"], [536870912, "author"],
];
const rights = (f = 0) => (f & 1 ? ["main administrator (all rights)"] : ACCESS.filter(([b]) => f & b).map(([, l]) => l));
const users = await elo.call("checkoutUsers", { ids: [0, 1], checkoutUsersZ: { bset: "513" } });
users.forEach((u) => console.log(`${u.name}: ${rights(u.flags).join(", ") || "(none)"}`));
