// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkoutUsers","params":{"ids":[0,1],"checkoutUsersZ":{"bset":"513"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("checkoutUsers", "{\"ids\":[0,1],\"checkoutUsersZ\":{\"bset\":\"513\"}}"));
  }
}
