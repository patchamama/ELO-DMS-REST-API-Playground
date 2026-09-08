// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Read server info and licence
// category: Connection & session
// id:       connection.server-info

const elo = await connect();

const info = await elo.call("getServerInfo", {});
const server = (info.indexServers || [{}])[0];
console.log("repository :", server.arcName);
console.log("IX version :", info.version);
console.log("database   :", info.databaseEngine);
