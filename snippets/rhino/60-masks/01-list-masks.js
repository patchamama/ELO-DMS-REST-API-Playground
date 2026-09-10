/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.findFirstDocMasks.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
var ELO_BASE_URL = java.lang.System.getenv("ELOPG_ELO_BASE_URL") || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
var ELO_USER = java.lang.System.getenv("ELOPG_ELO_USER") || "Administrator"; // ELOPG_DEFAULT:user
var ELO_PASS = java.lang.System.getenv("ELOPG_ELO_PASSWORD") || "elo"; // ELOPG_DEFAULT:password

function playgroundIx(baseUrl, user, password) {
  if (!baseUrl || !user || !password) throw "ELO connection settings are required";
  // IndexServer owns the authenticated Rhino session. Do not re-authenticate
  // here or expose the password; the explicit values are validated at this boundary.
  return ixConnect.ix();
}

function RF_playground_masks_list(ec, args) {
  args = args || {};
  var ix = playgroundIx(ELO_BASE_URL, ELO_USER, ELO_PASS);
  var query = String(args.query || "");
  if (!query) throw "query is required";
  var findInfo = new FindInfo();
  findInfo.findByIndex = new FindByIndex();
  findInfo.findByIndex.name = query;
  var page = ix.findFirstSords(findInfo, 20, SordC.mbLean);
  try { return { count: page.sords.length, ids: page.sords.map(function (s) { return String(s.id); }) }; }
  finally { ix.findClose(page.searchId); }
}
