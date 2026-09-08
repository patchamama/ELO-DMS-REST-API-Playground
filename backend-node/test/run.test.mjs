/**
 * Tests for the Node snippet runner. Offline: every snippet runs in mock mode.
 * Run with:  node --test backend-node/test/
 */
import assert from "node:assert/strict";
import { test } from "node:test";

import { runNodeSnippet } from "../src/runner.mjs";

test("runs a trivial snippet and captures stdout", async () => {
  const r = await runNodeSnippet({
    code: 'console.log("hello from node");',
    mock: true,
    mockData: {},
  });
  assert.equal(r.ok, true);
  assert.equal(r.exitCode, 0);
  assert.match(r.stdout, /hello from node/);
});

test("a throwing snippet reports failure and stderr", async () => {
  const r = await runNodeSnippet({
    code: 'throw new Error("boom");',
    mock: true,
    mockData: {},
  });
  assert.equal(r.ok, false);
  assert.notEqual(r.exitCode, 0);
  assert.match(r.stderr, /boom/);
});

test("the shared client resolves and returns mock data", async () => {
  const r = await runNodeSnippet({
    code: [
      'import { connect } from "elo-playground";',
      "const elo = await connect();",
      'const info = await elo.call("getServerInfo", {});',
      "console.log(info.version);",
    ].join("\n"),
    mock: true,
    mockData: { login: { user: { id: 0, name: "Administrator" } }, getServerInfo: { version: "25.00.999" } },
  });
  assert.equal(r.ok, true, r.stderr);
  assert.match(r.stdout, /25\.00\.999/);
});

test("times out a runaway snippet", async () => {
  const r = await runNodeSnippet({
    code: "while (true) {}",
    mock: true,
    mockData: {},
    timeoutMs: 1500,
  });
  assert.equal(r.ok, false);
  assert.match(r.detail, /timed out/);
});
