// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"findInfo":{"findByIndex":{"name":"Administration*"}},"max":10,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res.get('searchId')"}}},{"method":"checkoutSord","params":{"objId":2,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutSord","params":{"objId":{"$expression":"by_id['guid']"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("findFirstSords", "{\"findInfo\":{\"findByIndex\":{\"name\":\"Administration*\"}},\"max\":10,\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}"));
    System.out.println(elo.call("findClose", "{\"searchId\":{\"$expression\":\"res.get('searchId')\"}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":2,\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"by_id['guid']\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
  }
}
