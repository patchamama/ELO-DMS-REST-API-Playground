// import the shared client:  import { connect } from "elo-playground";
// topic:    Decode a user's rights bitset
// category: Users & groups
// id:       users.permissions

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

// AccessC right bits (ELO 25) -> readable label
const ACCESS = [
  [1, "main administrator (all rights)"], [2, "edit configuration"],
  [4, "edit structure"], [8, "edit documents"], [16, "change password"],
  [128, "edit workflows"], [256, "start workflows"], [512, "delete documents"],
  [8192, "import"], [16384, "export"], [32768, "edit masks"],
  [65536, "edit scripts"], [2097152, "edit ACL"], [536870912, "author"],
];
const rights = (flags = 0) =>
  flags & 1 ? ["main administrator (all rights)"] : ACCESS.filter(([b]) => flags & b).map(([, l]) => l);

const users = await elo.call("checkoutUsers", { ids: [0, 1], checkoutUsersZ: { bset: "513" } });
for (const u of users) {
  console.log(`${u.name}: ${rights(u.flags).join(", ") || "(none)"}`);
}
