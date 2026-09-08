// import the shared client:  import { connect } from "elo-playground";
// topic:    Resolve a GUID to an object (Sord)
// category: Repository & objects
// id:       repository.checkout-sord

import { connect } from "elo-playground";

const elo = await connect();

// objId can be an int id OR a "(GUID)" copied from the ELO client.
// 2 is a real folder on a stock repository, so this runs anywhere.
const objId = 2; // e.g. "(4A5B6C7D-8E9F-0A1B-2C3D-4E5F60718293)"

const res = await elo.call("checkoutSord", {
  objId,
  // checkoutSord answers with an EditInfo; sordZ goes INSIDE editInfoZ,
  // and editInfoZ.bset "1" (mbSord) makes it fill in result.sord.
  editInfoZ: { bset: "1", sordZ: { bset: "449304431574384639" } },
});
const sord = res.sord;

// ELO type: 254..998 = document, below = folder (repo root uses 9999).
const t = Number(sord.type || 0);
const kind = t >= 254 && t < 999 ? "document" : "folder";
console.log(`${kind}: ${sord.name}  (id ${sord.id}, mask: ${sord.maskName})`);
