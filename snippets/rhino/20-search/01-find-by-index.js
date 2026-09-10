/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.findFirstSords.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
var ELO_BASE_URL = java.lang.System.getenv("ELOPG_ELO_BASE_URL") || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
var ELO_USER = java.lang.System.getenv("ELOPG_ELO_USER") || "Administrator"; // ELOPG_DEFAULT:user
var ELO_PASS = java.lang.System.getenv("ELOPG_ELO_PASSWORD") || "elo"; // ELOPG_DEFAULT:password

function RF_playground_search_find_by_index(ec, args) {
  args = args || {};
  var query = String(args.query || "");
  if (!query) throw "query is required";
  var findInfo = new FindInfo();
  findInfo.findByIndex = new FindByIndex();
  findInfo.findByIndex.name = query;
  var page = ixConnect.ix().findFirstSords(findInfo, 20, SordC.mbLean);
  try { return { count: page.sords.length, ids: page.sords.map(function (s) { return String(s.id); }) }; }
  finally { ixConnect.ix().findClose(page.searchId); }
}
