// import the shared client:  import { connect } from "elo-playground";
// topic:    Read and write a Sord's index fields (write)
// category: Metadata masks
// id:       masks.read-write-fields

import { connect } from "elo-playground";

const elo = await connect();
const ALL = "449304431574384639";

const tmpl = await elo.call("createSord", {
  parentId: 1, maskId: 34,
  editInfoZ: { bset: "1", sordZ: { bset: ALL } },
});
const sord = tmpl.sord;
sord.name = "playground fields demo";

const fields = (s) =>
  Object.fromEntries((s.objKeys || []).filter((k) => k.data && k.data.length).map((k) => [k.name, k.data]));

console.log("before:", fields(sord));

const wanted = { BS_CONFIG_NAME: ["playground-value"], BS_CONFIG_VERSION: ["1.0"] };
for (const key of sord.objKeys) if (wanted[key.name]) key.data = wanted[key.name];

const newId = await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });

const check = (await elo.call("checkoutSord", {
  objId: newId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log("after: ", fields(check));
