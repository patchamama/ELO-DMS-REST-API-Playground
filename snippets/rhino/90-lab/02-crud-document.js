/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.createSord.
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

function RF_playground_lab_crud(ec, args) {
  args = args || {};
  var ix = playgroundIx(ELO_BASE_URL, ELO_USER, ELO_PASS);
  var parentId = String(args.parentId || "");
  var name = String(args.name || "");
  if (!parentId || !name) throw "parentId and name are required";
  // Deployment policy must validate the parent against an approved scratch root.
  var sord = ix.createSord(parentId, "", EditInfoC.mbSord).sord;
  sord.name = name;
  sord = ix.checkinSord(sord, SordC.mbAll, LockC.NO);
  return { id: String(sord.id), name: String(sord.name) };
}
