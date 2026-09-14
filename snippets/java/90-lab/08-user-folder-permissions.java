// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkoutUsers","params":{"ids":{"$expression":"[u['id'] for u in users]"},"checkoutUsersZ":{"bset":"513"}}},{"method":"findFirstSords","params":{"findInfo":{"findChildren":{"parentId":{"$expression":"str(parent_id)"},"mainParent":true,"endLevel":1}},"max":1000,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res['searchId']"}}},{"method":"checkoutSord","params":{"objId":{"$expression":"str(folder_id)"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("checkoutUsers", "{\"ids\":{\"$expression\":\"[u['id'] for u in users]\"},\"checkoutUsersZ\":{\"bset\":\"513\"}}"));
    System.out.println(elo.call("findFirstSords", "{\"findInfo\":{\"findChildren\":{\"parentId\":{\"$expression\":\"str(parent_id)\"},\"mainParent\":true,\"endLevel\":1}},\"max\":1000,\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}"));
    System.out.println(elo.call("findClose", "{\"searchId\":{\"$expression\":\"res['searchId']\"}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"str(folder_id)\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
  }
}
