// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Log in and open a session
// category: Connection & session
// id:       connection.login

// connect() is preloaded by the playground. In the browser the call goes
// to the playground backend, which holds the real ELO connection and
// forwards the RPC (or answers from mock data).
const elo = await connect({ login: false });

const user = await elo.login();    // -> POST /api/elo/proxy -> IX login
console.log("logged in as:", user.name, `(id ${user.id})`);
console.log("member of groups:", user.groupList);
