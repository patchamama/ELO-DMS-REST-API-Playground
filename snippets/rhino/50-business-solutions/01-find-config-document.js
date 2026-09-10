/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.findFirstSords.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
function RF_playground_business_solutions_find_config(ec, args) {
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
