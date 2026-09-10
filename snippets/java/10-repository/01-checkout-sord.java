// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkoutSord","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"1","sordZ":{"bset":"449304431574384639"}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":\"449304431574384639\"}}}"));
  }
}
