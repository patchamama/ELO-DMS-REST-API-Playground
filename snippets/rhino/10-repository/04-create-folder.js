/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.createSord.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
function RF_playground_repository_create_folder(ec, args) {
  args = args || {};
  var parentId = String(args.parentId || "");
  var name = String(args.name || "");
  if (!parentId || !name) throw "parentId and name are required";
  // Deployment policy must validate the parent against an approved scratch root.
  var sord = ixConnect.ix().createSord(parentId, "", EditInfoC.mbSord).sord;
  sord.name = name;
  sord = ixConnect.ix().checkinSord(sord, SordC.mbAll, LockC.NO);
  return { id: String(sord.id), name: String(sord.name) };
}
