// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"createSord","params":{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"checkoutColors","params":{"checkoutInfo":{}}},{"method":"checkinSord","params":{"sord":{"$expression":"sord"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"checkoutSord","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutSord","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":true}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String eloBaseUrl = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String eloUser = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String eloPass = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password
    var elo = EloClient.connect(eloBaseUrl, eloUser, eloPass);
    System.out.println(elo.call("createSord", "{\"parentId\":\"1\",\"maskId\":0,\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkinSord", "{\"sord\":{\"$expression\":\"tpl\"},\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("checkoutColors", "{\"checkoutInfo\":{}}"));
    System.out.println(elo.call("checkinSord", "{\"sord\":{\"$expression\":\"sord\"},\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("deleteSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"parentId\":\"1\",\"deleteOptions\":{\"deleteFinally\":false}}"));
    System.out.println(elo.call("deleteSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"parentId\":\"1\",\"deleteOptions\":{\"deleteFinally\":true}}"));
  }
}
