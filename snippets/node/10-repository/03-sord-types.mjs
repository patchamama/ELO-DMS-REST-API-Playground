// import the shared client:  import { connect } from "elo-playground";
// topic:    List Sord types (the entry icons)
// category: Repository & objects
// id:       repository.sord-types

import { connect } from "elo-playground";

const elo = await connect();

const res = await elo.call("checkoutSordTypes", { id: -1, sordTypeZ: { bset: "31" } });
const types = Array.isArray(res) ? res : res.sordTypes || [];

console.log(`${types.length} Sord types`);
for (const t of types) {
  console.log(`  [${String(t.id).padStart(4)}] ${t.name}  (${t.icon ? "icon" : "no icon"})`);
}
