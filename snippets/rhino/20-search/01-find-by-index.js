/**
 * IndexServer Rhino script example, NOT Web Client injection.
 * Register this script through ELO administration/deployment, review it, then invoke
 * it using IXServicePortIF.executeScript. Incoming args are data, never code.
 */
function RF_playground_readMetadata(ec, args) {
  var objId = String((args && args.objId) || "");
  if (!objId) throw "objId is required";
  var sord = ixConnect.ix().checkoutSord(objId, SordC.mbAllIndex, LockC.NO);
  return { id: String(sord.id), name: String(sord.name), mask: String(sord.maskName || "") };
}
