// import the shared client:  import { connect } from "elo-playground";
// topic:    List users (and groups)
// category: Users & groups
// id:       users.find-users

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const users = await elo.findAll(
  "findFirstUsers", "findNextUsers", "sortedResult",
  { findUserInfo: { onlyUsers: true }, max: 200 },
);

console.log(`${users.length} users`);
for (const u of users) {
  console.log(`  [${String(u.id).padStart(5)}] ${u.name.padEnd(16)} ${u.displayName || ""}`);
}
