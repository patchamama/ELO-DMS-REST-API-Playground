/**
 * Static check for the Node and browser snippets: every identifier that is
 * *read* must be declared in the snippet, imported, or a known global. Catches
 * "x is not defined" before anyone hits Run.
 *
 *   node scripts/check_snippets_js.mjs
 *
 * Exit 0 = clean, exit 1 = something is undefined.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import * as acorn from "acorn";

const ROOT = fileURLToPath(new URL("..", import.meta.url));

// globals available to every snippet (browser: connect/EloClient/EloError are
// injected by the run iframe; node: imported from "elo-playground")
const GLOBALS = new Set([
  "connect", "EloClient", "EloError",
  "console", "JSON", "Object", "Array", "Boolean", "Number", "String", "Math",
  "Date", "RegExp", "Error", "TypeError", "RangeError", "Promise", "Set", "Map",
  "WeakMap", "WeakSet", "Symbol", "Proxy", "Reflect", "BigInt", "Intl",
  "parseInt", "parseFloat", "isNaN", "isFinite", "encodeURIComponent",
  "decodeURIComponent", "structuredClone", "queueMicrotask",
  "setTimeout", "clearTimeout", "setInterval", "clearInterval",
  "NaN", "Infinity", "undefined", "globalThis",
  // browser
  "window", "document", "navigator", "fetch", "btoa", "atob", "URL",
  "URLSearchParams", "TextEncoder", "TextDecoder", "crypto", "location",
  // node
  "process", "Buffer", "global", "__dirname", "__filename", "require", "module",
  "exports",
]);

function walkFiles(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walkFiles(p));
    else if (/\.(mjs|js)$/.test(name)) out.push(p);
  }
  return out;
}

// collect every binding name introduced anywhere in the tree (snippets are
// small and flat, so we don't need precise per-scope resolution)
function collectBindings(node, bound) {
  if (!node || typeof node.type !== "string") return;
  switch (node.type) {
    case "VariableDeclarator":
      collectPattern(node.id, bound);
      break;
    case "FunctionDeclaration":
    case "FunctionExpression":
    case "ArrowFunctionExpression":
      if (node.id) bound.add(node.id.name);
      for (const p of node.params) collectPattern(p, bound);
      break;
    case "ClassDeclaration":
    case "ClassExpression":
      if (node.id) bound.add(node.id.name);
      break;
    case "CatchClause":
      if (node.param) collectPattern(node.param, bound);
      break;
    case "ImportDefaultSpecifier":
    case "ImportNamespaceSpecifier":
    case "ImportSpecifier":
      bound.add(node.local.name);
      break;
  }
  for (const key of Object.keys(node)) {
    const v = node[key];
    if (Array.isArray(v)) v.forEach((c) => collectBindings(c, bound));
    else if (v && typeof v.type === "string") collectBindings(v, bound);
  }
}

function collectPattern(pat, bound) {
  if (!pat) return;
  if (pat.type === "Identifier") bound.add(pat.name);
  else if (pat.type === "ObjectPattern")
    for (const prop of pat.properties)
      collectPattern(prop.type === "RestElement" ? prop.argument : prop.value, bound);
  else if (pat.type === "ArrayPattern")
    for (const el of pat.elements) collectPattern(el, bound);
  else if (pat.type === "AssignmentPattern") collectPattern(pat.left, bound);
  else if (pat.type === "RestElement") collectPattern(pat.argument, bound);
}

// collect identifiers that are *read* (not property keys, not declarations)
function collectReads(node, reads, parent, key) {
  if (!node || typeof node.type !== "string") return;
  if (node.type === "Identifier") {
    const isMemberProp =
      parent && parent.type === "MemberExpression" && key === "property" && !parent.computed;
    const isPropKey =
      parent && parent.type === "Property" && key === "key" && !parent.computed;
    const isLabel =
      parent && (parent.type === "LabeledStatement" || parent.type === "BreakStatement" || parent.type === "ContinueStatement");
    if (!isMemberProp && !isPropKey && !isLabel) reads.add(node.name);
    return;
  }
  // skip binding positions
  const skip = new Set();
  if (node.type === "VariableDeclarator") skip.add("id");
  if (/Function/.test(node.type)) skip.add("params");
  if (node.type === "CatchClause") skip.add("param");
  if (node.type === "ImportSpecifier" || node.type === "ImportDefaultSpecifier" || node.type === "ImportNamespaceSpecifier") skip.add("local");
  for (const k of Object.keys(node)) {
    if (skip.has(k)) continue;
    const v = node[k];
    if (Array.isArray(v)) v.forEach((c) => collectReads(c, reads, node, k));
    else if (v && typeof v.type === "string") collectReads(v, reads, node, k);
  }
}

let problems = 0;

function checkSource(src, label) {
  let ast;
  try {
    ast = acorn.parse(src, { ecmaVersion: "latest", sourceType: "module", allowAwaitOutsideFunction: true });
  } catch (e) {
    console.log(`SYNTAX  ${label}: ${e.message}`);
    problems++;
    return;
  }
  const bound = new Set();
  collectBindings(ast, bound);
  const reads = new Set();
  collectReads(ast, reads, null, null);
  for (const name of reads) {
    if (bound.has(name) || GLOBALS.has(name)) continue;
    console.log(`UNDEFINED  ${label}: '${name}'`);
    problems++;
  }
}

for (const dir of ["snippets/node", "snippets/browser"]) {
  for (const file of walkFiles(join(ROOT, dir))) {
    checkSource(readFileSync(file, "utf-8"), relative(ROOT, file));
  }
}

// fenced js/javascript blocks in the "Deep dive" docs are runnable too
for (const file of walkFiles(join(ROOT, "catalog"))) {
  if (!file.endsWith("_deep.md")) continue;
  const md = readFileSync(file, "utf-8");
  const re = /```(?:js|javascript)\n([\s\S]*?)```/g;
  let m;
  let i = 0;
  while ((m = re.exec(md))) checkSource(m[1], `${relative(ROOT, file)}#js${i++}`);
}

if (problems === 0) console.log("check_snippets_js: all Node/browser snippets reference only defined names");
process.exit(problems === 0 ? 0 : 1);
