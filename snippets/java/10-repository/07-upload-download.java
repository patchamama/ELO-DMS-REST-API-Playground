// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkinDocBegin","params":{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":"txt"}]}}},{"method":"checkinDocEnd","params":{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"createDoc","params":{"parentId":{"$expression":"parent_id"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"doc_id"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}},{"method":"deleteSord","params":{"objId":{"$expression":"doc_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String eloBaseUrl = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String eloUser = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String eloPass = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password
    var elo = EloClient.connect(eloBaseUrl, eloUser, eloPass);
    System.out.println(elo.call("checkinDocBegin", "{\"sord\":{\"$expression\":\"sord\"},\"document\":{\"docs\":[{\"ext\":\"txt\"}]}}"));
    System.out.println(elo.call("checkinDocEnd", "{\"sord\":{\"$expression\":\"sord\"},\"document\":{\"$expression\":\"doc\"},\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("createDoc", "{\"parentId\":{\"$expression\":\"parent_id\"},\"maskId\":0,\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkoutDoc", "{\"objId\":{\"$expression\":\"doc_id\"},\"editInfoZ\":{\"bset\":\"320\",\"sordZ\":{\"bset\":\"0\"}}}"));
    System.out.println(elo.call("deleteSord", "{\"objId\":{\"$expression\":\"doc_id\"},\"parentId\":\"1\",\"deleteOptions\":{\"deleteFinally\":{\"$expression\":\"step\"}}}"));
  }
}
