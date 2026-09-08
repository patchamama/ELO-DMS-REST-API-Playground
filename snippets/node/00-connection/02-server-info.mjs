// import the shared client:  import { connect } from "elo-playground";
// topic:    Read server info and licence
// category: Connection & session
// id:       connection.server-info

import { connect } from "elo-playground";

const elo = await connect();                 // env vars + login() already done

const info = await elo.call("getServerInfo", {});
const server = (info.indexServers || [{}])[0];
const lic = (info.license || {}).licenseOptions || {};

console.log("repository :", server.arcName);
console.log("IX version :", info.version);
console.log("database   :", info.databaseEngine);
console.log("product    :", lic.product, "/ users:", lic.usercount1);
