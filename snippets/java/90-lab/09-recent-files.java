// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"findInfo":{"findByIndex":{"iDateIso":{"$expression":"f'{since}...{until}'"}},"findByType":{"typeDocuments":true}},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}},{"method":"findNextSords","params":{"searchId":{"$expression":"res['searchId']"},"idx":{"$expression":"len(rows)"},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res['searchId']"}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"str(doc['id'])"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("findFirstSords", "{\"findInfo\":{\"findByIndex\":{\"iDateIso\":{\"$expression\":\"f'{since}...{until}'\"}},\"findByType\":{\"typeDocuments\":true}},\"max\":500,\"sordZ\":{\"bset\":{\"$expression\":\"LEAN\"}}}"));
    System.out.println(elo.call("findNextSords", "{\"searchId\":{\"$expression\":\"res['searchId']\"},\"idx\":{\"$expression\":\"len(rows)\"},\"max\":500,\"sordZ\":{\"bset\":{\"$expression\":\"LEAN\"}}}"));
    System.out.println(elo.call("findClose", "{\"searchId\":{\"$expression\":\"res['searchId']\"}}"));
    System.out.println(elo.call("checkoutDoc", "{\"objId\":{\"$expression\":\"str(doc['id'])\"},\"editInfoZ\":{\"bset\":\"320\",\"sordZ\":{\"bset\":\"0\"}}}"));
  }
}
