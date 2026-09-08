// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Create a folder (write)
// category: Repository & objects
// id:       repository.create-folder

const elo = await connect();
const ALL = "449304431574384639";

const tmpl = await elo.call("createSord", {
  parentId: 1, maskId: 1,
  editInfoZ: { bset: "1", sordZ: { bset: ALL } },
});
const sord = tmpl.sord;
sord.name = "Playground test folder";
const newId = await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });
console.log("created folder id:", newId);
