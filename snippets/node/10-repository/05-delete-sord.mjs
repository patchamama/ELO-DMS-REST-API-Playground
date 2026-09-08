// import the shared client:  import { connect } from "elo-playground";
// topic:    Delete an object (write, two steps)
// category: Repository & objects
// id:       repository.delete-sord

import { connect, EloError } from "elo-playground";

const elo = await connect();

const objId = "5361"; // a throwaway object's id

// step 1 - move it to the recycle bin
await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: false } });
console.log("step 1 (to recycle bin): ok");

// step 2 - purge it for good
await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: true } });
console.log("step 2 (purge):          ok");

// confirm it is gone
try {
  await elo.call("checkoutSord", { objId, editInfoZ: { bset: "1", sordZ: { bset: "0" } } });
  console.log("gone: false");
} catch (e) {
  console.log("gone: true");
}
