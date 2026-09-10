/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.getServerInfo.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
function RF_playground_connection_server_info(ec, args) {
  args = args || {};
  var objId = String(args.objId || "");
  if (!objId) throw "objId is required";
  var sord = ixConnect.ix().checkoutSord(objId, SordC.mbAllIndex, LockC.NO);
  return { id: String(sord.id), name: String(sord.name), mask: String(sord.maskName || "") };
}
