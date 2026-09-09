// import the shared client:  import { connect } from "elo-playground";
// topic:    Log in and open a session
// category: Connection & session
// id:       connection.login

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

// login:false builds the client but does NOT log in yet, so we can call
// login() ourselves below and read what it returns.
const elo = await connect({ user: ELO_USER, password: ELO_PASS, login: false });

const user = await elo.login();    // -> POST /rest/IXServicePortIF/login
console.log("logged in as:", user.name, `(id ${user.id})`);
console.log("member of groups:", user.groupList);

elo.close();
