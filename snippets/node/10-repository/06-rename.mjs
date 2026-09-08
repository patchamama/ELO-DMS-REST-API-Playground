// import the shared client:  import { connect } from "elo-playground";
// topic:    Rename an object (write)
// category: Repository & objects
// id:       repository.rename

import { connect } from "elo-playground";

const elo = await connect();
const ALL = "449304431574384639";

const objId = 5390; // a throwaway object's id

// 1) check it out (with a lock)
const sord = (await elo.call("checkoutSord", {
  objId,
  editInfoZ: { bset: "1", sordZ: { bset: ALL }, lockZ: { bset: "1" } },
})).sord;
console.log("before:", sord.name);

// 2) change the name
sord.name = "playground new name";

// 3) check it back in and release the lock
await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });

const after = (await elo.call("checkoutSord", {
  objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log("after: ", after.name);
