// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Create a user and a group, link them (write)
// category: Users & groups
// id:       users.create

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const USER = "pg.demo.user";

const drop = async (name) => {
  try {
    const ids = (await elo.call("checkoutUsers", { ids: [name], checkoutUsersZ: { bset: "1" } }))
      .map((u) => u.id);
    if (ids.length) await elo.call("deleteUsers", { ids });
  } catch (e) { /* not there */ }
};

try {
  await drop(USER);
  const [uid] = await elo.call("checkinUsers", {
    userInfos: [{ id: -1, name: USER, type: 1, pwd: "PlaygroundDemoUser2026!" }],
    checkinUsersZ: { bset: "1" }, unlockZ: { bset: "1" },
  });
  console.log("created user id:", uid);
} catch (exc) {
  console.log("user operation failed:", exc.message);
} finally {
  await drop(USER);
  console.log("cleaned up");
}
