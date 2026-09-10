/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.checkinDocBegin.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
function RF_playground_ocr_archived(ec, args) {
  args = args || {};
  var objId = String(args.objId || "");
  if (!objId) throw "objId is required";
  // Document byte transfer and OCR must be configured server-side, not received as code.
  var sord = ixConnect.ix().checkoutSord(objId, SordC.mbAllIndex, LockC.NO);
  return { id: String(sord.id), name: String(sord.name), mask: String(sord.maskName || "") };
}
