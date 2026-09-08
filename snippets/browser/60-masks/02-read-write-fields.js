// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Read and write a Sord's index fields (write)
// category: Metadata masks
// id:       masks.read-write-fields

const elo = await connect();
const ALL = "449304431574384639";

const tmpl = await elo.call("createSord", {
  parentId: 1, maskId: 34, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
});
const sord = tmpl.sord;
sord.name = "playground fields demo";
for (const key of sord.objKeys) if (key.name === "BS_CONFIG_NAME") key.data = ["playground-value"];
const newId = await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });
const check = (await elo.call("checkoutSord", { objId: newId, editInfoZ: { bset: "1", sordZ: { bset: ALL } } })).sord;
console.log((check.objKeys || []).filter((k) => k.data && k.data.length).map((k) => `${k.name}=${k.data}`));
