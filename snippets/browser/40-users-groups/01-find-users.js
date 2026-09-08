// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List users (and groups)
// category: Users & groups
// id:       users.find-users

const elo = await connect();

const users = await elo.findAll(
  "findFirstUsers", "findNextUsers", "sortedResult",
  { findUserInfo: { onlyUsers: true }, max: 200 },
);
console.log(`${users.length} users`);
users.forEach((u) => console.log(`  [${u.id}] ${u.name}  ${u.displayName || ""}`));
