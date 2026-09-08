// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List session options
// category: Connection & session
// id:       connection.session-options

const elo = await connect();

const res = await elo.call("getSessionOptions", {});
const options = res.options || (Array.isArray(res) ? res : []);
console.log(`${options.length} session options`);
options.slice(0, 10).forEach((o) => console.log(`  ${o.key} = ${o.value}`));
