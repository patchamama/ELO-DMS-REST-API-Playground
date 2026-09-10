/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.deleteSord.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
function RF_playground_repository_delete_sord(ec, args) {
  args = args || {};
  var objId = String(args.objId || "");
  if (!objId || args.confirm !== true) throw "objId and confirm=true are required";
  // Only a dedicated test-root policy may permit destructive operations.
  ixConnect.ix().deleteSord(null, objId, LockC.NO, null);
  return { deletedId: objId };
}
