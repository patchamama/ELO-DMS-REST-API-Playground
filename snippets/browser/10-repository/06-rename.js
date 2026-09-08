// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Rename an object (write)
// category: Repository & objects
// id:       repository.rename

const elo = await connect();
const ALL = "449304431574384639";
const objId = 5390;

const sord = (await elo.call("checkoutSord", {
  objId, editInfoZ: { bset: "1", sordZ: { bset: ALL }, lockZ: { bset: "1" } },
})).sord;
console.log("before:", sord.name);
sord.name = "playground new name";
await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });
console.log("renamed");
