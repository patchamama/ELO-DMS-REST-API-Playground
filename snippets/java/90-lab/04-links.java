// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"linkSords","params":{"fromId":{"$expression":"a"},"toIds":[{"$expression":"b"}],"linkZ":{"bset":"1"}}},{"method":"unlinkSords","params":{"fromId":{"$expression":"a"},"toIds":[{"$expression":"b"}],"linkZ":{"bset":"1"}}},{"method":"createSord","params":{"parentId":{"$expression":"str(PARENT)"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"checkoutSord","params":{"objId":{"$expression":"a"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"deleteSord","params":{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"oid"},"deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"oid"},"deleteOptions":{"deleteFinally":true}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("linkSords", "{\"fromId\":{\"$expression\":\"a\"},\"toIds\":[{\"$expression\":\"b\"}],\"linkZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("unlinkSords", "{\"fromId\":{\"$expression\":\"a\"},\"toIds\":[{\"$expression\":\"b\"}],\"linkZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("createSord", "{\"parentId\":{\"$expression\":\"str(PARENT)\"},\"maskId\":0,\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkinSord", "{\"sord\":{\"$expression\":\"tpl\"},\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"a\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("deleteSord", "{\"parentId\":{\"$expression\":\"str(PARENT)\"},\"objId\":{\"$expression\":\"oid\"},\"deleteOptions\":{\"deleteFinally\":false}}"));
    System.out.println(elo.call("deleteSord", "{\"parentId\":{\"$expression\":\"str(PARENT)\"},\"objId\":{\"$expression\":\"oid\"},\"deleteOptions\":{\"deleteFinally\":true}}"));
  }
}
