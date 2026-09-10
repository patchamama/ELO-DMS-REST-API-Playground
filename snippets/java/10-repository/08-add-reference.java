// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"createSord","params":{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"refSord","params":{"objId":{"$expression":"obj_id"},"oldParentId":"1","newParentId":{"$expression":"new_parent"}}},{"method":"findFirstSords","params":{"findInfo":{"findChildren":{"parentId":{"$expression":"new_parent"},"mainParent":false,"endLevel":1}},"max":20,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"deleteSord","params":{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":true}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("createSord", "{\"parentId\":\"1\",\"maskId\":0,\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkinSord", "{\"sord\":{\"$expression\":\"tpl\"},\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("refSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"oldParentId\":\"1\",\"newParentId\":{\"$expression\":\"new_parent\"}}"));
    System.out.println(elo.call("findFirstSords", "{\"findInfo\":{\"findChildren\":{\"parentId\":{\"$expression\":\"new_parent\"},\"mainParent\":false,\"endLevel\":1}},\"max\":20,\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}"));
    System.out.println(elo.call("deleteSord", "{\"objId\":{\"$expression\":\"oid\"},\"parentId\":\"1\",\"deleteOptions\":{\"deleteFinally\":false}}"));
    System.out.println(elo.call("deleteSord", "{\"objId\":{\"$expression\":\"oid\"},\"parentId\":\"1\",\"deleteOptions\":{\"deleteFinally\":true}}"));
  }
}
