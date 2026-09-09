// import the shared client:  import { connect } from "elo-playground";
// topic:    Create a folder (write)
// category: Repository & objects
// id:       repository.create-folder

import { connect, EloError } from "elo-playground";

const elo = await connect();
const ALL = "449304431574384639"; // SordC.mbAllIndex

// 1) blank Sord template under parent 1, "Ordner" mask (id 1).
//    sordZ goes INSIDE editInfoZ, exactly like checkoutSord.
const tmpl = await elo.call("createSord", {
  parentId: 1,
  maskId: 1,
  editInfoZ: { bset: "1", sordZ: { bset: ALL } },
});
const sord = tmpl.sord;
sord.name = "Playground test folder";

// 2) persist it - sordZ here is the WRITE mask, so use a full bitset
const newId = String(await elo.call("checkinSord", {
  sord,
  sordZ: { bset: ALL },
  unlockZ: { bset: "1" },
}));
console.log("created folder id:", newId);

// 3) clean up so re-running this stays tidy (see repository.delete-sord)
try {
  for (const step of [false, true]) {
    await elo.call("deleteSord", { objId: newId, parentId: "1", deleteOptions: { deleteFinally: step } });
  }
  console.log("removed the test folder again");
} catch (exc) {
  if (exc instanceof EloError) console.log("could not remove the test folder:", exc.message);
  else throw exc;
} finally {
  elo.close();
}
