// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    File an object into a second folder (reference, write)
// category: Repository & objects
// id:       repository.add-reference

const elo = await connect();
await elo.call("refSord", { objId: "4711", oldParentId: "1", newParentId: "4712" });
console.log("reference added");
