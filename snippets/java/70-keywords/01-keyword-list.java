// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkoutKeywordList","params":{"kwid":"ELOSTDSWL","max":500,"keywordZ":{"bset":"7"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("checkoutKeywordList", "{\"kwid\":\"ELOSTDSWL\",\"max\":500,\"keywordZ\":{\"bset\":\"7\"}}"));
  }
}
