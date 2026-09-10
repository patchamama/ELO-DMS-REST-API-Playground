// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkoutKeywordList","params":{"kwid":"ELOSTDSWL","max":500,"keywordZ":{"bset":"7"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("checkoutKeywordList", "{\"kwid\":\"ELOSTDSWL\",\"max\":500,\"keywordZ\":{\"bset\":\"7\"}}"));
  }
}
