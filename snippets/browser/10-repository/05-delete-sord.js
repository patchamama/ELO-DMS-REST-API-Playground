// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Delete an object (write, two steps)
// category: Repository & objects
// id:       repository.delete-sord

const elo = await connect();
const objId = "5361";

await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: false } });
console.log("step 1 (to recycle bin): ok");
await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: true } });
console.log("step 2 (purge): ok");
