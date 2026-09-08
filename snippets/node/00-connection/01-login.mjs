// import the shared client:  import { connect } from "elo-playground";
// topic:    Log in and open a session
// category: Connection & session
// id:       connection.login

import { connect } from "elo-playground";

// connect({login:false}) builds the client from ELOPG_* env vars but does
// NOT log in yet - so we can call login() ourselves and read the result.
const elo = await connect({ login: false });

const user = await elo.login();    // -> POST /rest/IXServicePortIF/login
console.log("logged in as:", user.name, `(id ${user.id})`);
console.log("member of groups:", user.groupList);

elo.close();
