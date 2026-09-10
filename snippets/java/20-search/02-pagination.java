// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"$expression":"body"}},{"method":"findClose","params":{"searchId":{"$expression":"search_id"}}},{"method":"findNextSords","params":{"searchId":{"$expression":"search_id"},"idx":{"$expression":"len(rows)"},"max":2,"sordZ":{"$expression":"body['sordZ']"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("findFirstSords", "{\"$expression\":\"body\"}"));
    System.out.println(elo.call("findClose", "{\"searchId\":{\"$expression\":\"search_id\"}}"));
    System.out.println(elo.call("findNextSords", "{\"searchId\":{\"$expression\":\"search_id\"},\"idx\":{\"$expression\":\"len(rows)\"},\"max\":2,\"sordZ\":{\"$expression\":\"body['sordZ']\"}}"));
  }
}
