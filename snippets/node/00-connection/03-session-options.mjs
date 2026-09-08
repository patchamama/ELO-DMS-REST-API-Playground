// import the shared client:  import { connect } from "elo-playground";
// topic:    List session options
// category: Connection & session
// id:       connection.session-options

import { connect } from "elo-playground";

const elo = await connect();

const res = await elo.call("getSessionOptions", {});
const options = res.options || (Array.isArray(res) ? res : []);

console.log(`${options.length} session options`);
for (const opt of options.slice(0, 10)) {
  console.log(`  ${opt.key} = ${opt.value}`);
}
