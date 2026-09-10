/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.deleteSord.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
var ELO_BASE_URL = java.lang.System.getenv("ELOPG_ELO_BASE_URL") || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
var ELO_USER = java.lang.System.getenv("ELOPG_ELO_USER") || "Administrator"; // ELOPG_DEFAULT:user
var ELO_PASS = java.lang.System.getenv("ELOPG_ELO_PASSWORD") || "elo"; // ELOPG_DEFAULT:password

function RF_playground_repository_delete_sord(ec, args) {
  args = args || {};
  var objId = String(args.objId || "");
  if (!objId || args.confirm !== true) throw "objId and confirm=true are required";
  // Only a dedicated test-root policy may permit destructive operations.
  ixConnect.ix().deleteSord(null, objId, LockC.NO, null);
  return { deletedId: objId };
}
