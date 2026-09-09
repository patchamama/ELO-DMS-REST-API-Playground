// Paste any snippet from the Catalog (or snippets/) over this file, then re-run:
//   node sandbox/example.mjs

import { connect } from "elo-playground";

// connect({login:false}) builds the client from ELOPG_* env vars but does
// NOT log in yet - so we can call login() ourselves and read the result.
const elo = await connect({ login: false });

const user = await elo.login();    // -> POST /rest/IXServicePortIF/login
console.log("logged in as:", user.name, `(id ${user.id})`);
console.log("member of groups:", user.groupList);

elo.close();
