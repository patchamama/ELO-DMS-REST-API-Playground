/**
 * Run one Node snippet in a child `node` process and capture its output.
 *
 * The snippet is written to a temp file under the project's own `runtime/`
 * directory (NOT the OS temp dir) so that a bare import resolves:
 *
 *     import { connect } from "elo-playground";
 *
 * Node resolves a bare specifier by walking up the directory tree FROM THE
 * SNIPPET FILE, so the file must sit somewhere below the project root, where
 * `node_modules/elo-playground` was linked (see the root package.json).
 *
 * `execFile` buffers stdout/stderr for us (bounded by `maxBuffer`) - there is
 * no unbounded streaming pipe to deadlock.
 */
import { execFile } from "node:child_process";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const PROJECT_ROOT = fileURLToPath(new URL("../../", import.meta.url));
const RUN_ROOT = join(PROJECT_ROOT, "runtime", "node-run");

/**
 * @param {object} opts
 * @param {string} opts.code
 * @param {boolean} opts.mock
 * @param {object|null} opts.mockData      mock map (fixtures/ix/default.json + topic mock:)
 * @param {object|null} opts.credentials   {base_url, user, password, tls_verify}
 * @param {number} opts.timeoutMs
 * @param {number} opts.outputCap
 */
export async function runNodeSnippet({
  code,
  mock,
  mockData,
  credentials,
  attachment = null,
  timeoutMs = 15000,
  outputCap = 262144,
}) {
  await mkdir(RUN_ROOT, { recursive: true });
  const dir = await mkdtemp(join(RUN_ROOT, "run-"));
  const snippetPath = join(dir, "snippet.mjs");
  await writeFile(snippetPath, code, "utf-8");

  // Build the child environment the same way the Python runner does.
  const env = { ...process.env };
  delete env.ELOPG_MOCK;
  delete env.ELOPG_MOCK_DATA;
  delete env.ELOPG_ATTACH;
  delete env.ELOPG_ATTACH_NAME;
  if (mock) {
    env.ELOPG_MOCK = "1";
    const mockPath = join(dir, "mock.json");
    await writeFile(mockPath, JSON.stringify(mockData ?? {}), "utf-8");
    env.ELOPG_MOCK_DATA = mockPath;
  } else if (credentials) {
    env.ELOPG_ELO_BASE_URL = credentials.base_url;
    env.ELOPG_ELO_USER = credentials.user;
    env.ELOPG_ELO_PASSWORD = credentials.password ?? "";
    env.ELOPG_TLS_VERIFY = credentials.tls_verify ? "1" : "0";
  }
  if (attachment && typeof attachment.b64 === "string") {
    const raw = Buffer.from(attachment.b64, "base64").subarray(0, 12 * 1024 * 1024);
    const safe = (attachment.name || "attachment").split(/[\\/]/).pop() || "attachment";
    const attPath = join(dir, safe);
    await writeFile(attPath, raw);
    env.ELOPG_ATTACH = attPath;
    env.ELOPG_ATTACH_NAME = attachment.name || safe;
  }

  const started = Date.now();
  const result = await new Promise((resolve) => {
    execFile(
      process.execPath,
      [snippetPath],
      { cwd: dir, env, timeout: timeoutMs, maxBuffer: outputCap, killSignal: "SIGKILL" },
      (err, stdout, stderr) => {
        const durationMs = Date.now() - started;
        const clip = (s) => String(s || "").slice(0, outputCap);
        if (err && err.killed) {
          resolve({
            ok: false,
            stdout: clip(stdout),
            stderr: clip(stderr),
            exitCode: null,
            durationMs,
            detail: `timed out after ${timeoutMs / 1000}s`,
          });
          return;
        }
        resolve({
          ok: !err,
          stdout: clip(stdout),
          stderr: clip(stderr),
          exitCode: err && typeof err.code === "number" ? err.code : err ? 1 : 0,
          durationMs,
          detail: "",
        });
      }
    );
  });

  await rm(dir, { recursive: true, force: true });
  return result;
}
