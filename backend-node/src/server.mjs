/**
 * backend-node - the "real Node backend" of the playground.
 *
 * Two jobs:
 *   1. POST /run           run a Node snippet, return {ok, stdout, stderr, ...}
 *                          (the Python backend proxies here for `language: "node"`)
 *   2. GET  /elo/example/* a couple of endpoints that talk to ELO NATIVELY through
 *                          the shared Node client - proof that this backend really
 *                          calls ELO, not just executes strings.
 *
 * Start: `npm install` then `npm start` in the project root (port 8787).
 */
import express from "express";
import { connect } from "elo-playground";

import { runNodeSnippet } from "./runner.mjs";

const PORT = Number(process.env.ELOPG_NODE_PORT || 8787);

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/health", (_req, res) => res.json({ ok: true, service: "backend-node" }));

// ---- snippet runner ------------------------------------------------- //
app.post("/run", async (req, res) => {
  const { code, mock, mockData, credentials, timeoutMs, outputCap } = req.body ?? {};
  if (typeof code !== "string") {
    res.status(400).json({ ok: false, detail: "missing 'code'" });
    return;
  }
  try {
    const result = await runNodeSnippet({
      code,
      mock: !!mock,
      mockData: mockData ?? null,
      credentials: credentials ?? null,
      timeoutMs: Number(timeoutMs) || 15000,
      outputCap: Number(outputCap) || 262144,
    });
    res.json(result);
  } catch (err) {
    res.status(500).json({ ok: false, detail: `runner error: ${err.message}` });
  }
});

// ---- native ELO example endpoints -------------------------------- //
// These use the shared client directly, the same way a snippet would. The
// caller passes ?mock=1 or real credentials via the ELOPG_* env of this
// process (set from .env). They exist so the frontend can show that the Node
// backend genuinely reaches ELO.
async function withClient(query, fn, res) {
  if (String(query.mock ?? "") === "1") process.env.ELOPG_MOCK = "1";
  try {
    const elo = await connect();
    res.json({ ok: true, data: await fn(elo) });
  } catch (err) {
    res.json({ ok: false, error: String(err.message || err) });
  } finally {
    delete process.env.ELOPG_MOCK;
  }
}

app.get("/elo/example/server-info", (req, res) =>
  withClient(req.query, (elo) => elo.call("getServerInfo", {}), res)
);

app.get("/elo/example/whoami", (req, res) =>
  withClient(req.query, async (elo) => elo.user, res)
);

app.listen(PORT, "127.0.0.1", () => {
  console.log(`backend-node listening on http://127.0.0.1:${PORT}`);
});
