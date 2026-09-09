// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List users (and groups)
// category: Users & groups
// id:       users.find-users

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });

const users = await elo.findAll(
  "findFirstUsers", "findNextUsers", "sortedResult",
  { findUserInfo: { onlyUsers: true }, max: 200 },
);
console.log(`${users.length} users`);
users.forEach((u) => console.log(`  [${u.id}] ${u.name}  ${u.displayName || ""}`));
