// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkoutDoc","params":{"objId":{"$expression":"str(doc['id'])"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("checkoutDoc", "{\"objId\":{\"$expression\":\"str(doc['id'])\"},\"editInfoZ\":{\"bset\":\"320\",\"sordZ\":{\"bset\":\"0\"}}}"));
  }
}
