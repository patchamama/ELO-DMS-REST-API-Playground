// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List Sord types (the entry icons)
// category: Repository & objects
// id:       repository.sord-types

const elo = await connect();

const res = await elo.call("checkoutSordTypes", { id: -1, sordTypeZ: { bset: "31" } });
const types = Array.isArray(res) ? res : res.sordTypes || [];
console.log(`${types.length} Sord types`);
types.forEach((t) => console.log(`  [${t.id}] ${t.name}`));
