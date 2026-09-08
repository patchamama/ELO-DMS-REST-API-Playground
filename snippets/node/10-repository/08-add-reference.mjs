// import the shared client:  import { connect } from "elo-playground";
// topic:    File an object into a second folder (reference, write)
// category: Repository & objects
// id:       repository.add-reference

import { connect } from "elo-playground";

const elo = await connect();
const ALL = "449304431574384639";

const objId = 4711;      // the object to reference
const oldParent = 1;     // a folder it is already in
const newParent = 4712;  // the folder to also file it under

await elo.call("refSord", {
  objId: String(objId),
  oldParentId: String(oldParent),
  newParentId: String(newParent),
});
console.log("reference added");

const kids = (await elo.call("findFirstSords", {
  findInfo: { findChildren: { parentId: newParent, mainParent: false, endLevel: 1 } },
  max: 20,
  sordZ: { bset: ALL },
})).sords || [];
console.log("new parent now contains:", kids.map((k) => k.name));
