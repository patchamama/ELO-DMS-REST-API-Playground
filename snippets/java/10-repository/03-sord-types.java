// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkoutSordTypes","params":{"id":{"$expression":"-1"},"sordTypeZ":{"bset":"31"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("checkoutSordTypes", "{\"id\":{\"$expression\":\"-1\"},\"sordTypeZ\":{\"bset\":\"31\"}}"));
  }
}
