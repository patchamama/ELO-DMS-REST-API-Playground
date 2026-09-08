// import the shared client:  import { connect } from "elo-playground";
// topic:    List users (and groups)
// category: Users & groups
// id:       users.find-users

import { connect } from "elo-playground";

const elo = await connect();

const users = await elo.findAll(
  "findFirstUsers", "findNextUsers", "sortedResult",
  { findUserInfo: { onlyUsers: true }, max: 200 },
);

console.log(`${users.length} users`);
for (const u of users) {
  console.log(`  [${String(u.id).padStart(5)}] ${u.name.padEnd(16)} ${u.displayName || ""}`);
}
