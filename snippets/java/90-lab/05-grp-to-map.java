// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkinMap","params":{"objId":{"$expression":"int(obj_id)"},"domainName":"objekte","data":[{"key":"grp_copy","value":{"$expression":"source_value"}}],"unlockZ":{"bset":"1"}}},{"method":"checkoutMap","params":{"objId":{"$expression":"int(obj_id)"},"id":{"$expression":"obj_id"},"domainName":"objekte","keyNames":["*"],"lockZ":{"bset":"0"}}},{"method":"createSord","params":{"parentId":{"$expression":"str(PARENT)"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"checkoutSord","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"deleteSord","params":{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"obj_id"},"deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"obj_id"},"deleteOptions":{"deleteFinally":true}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("checkinMap", "{\"objId\":{\"$expression\":\"int(obj_id)\"},\"domainName\":\"objekte\",\"data\":[{\"key\":\"grp_copy\",\"value\":{\"$expression\":\"source_value\"}}],\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("checkoutMap", "{\"objId\":{\"$expression\":\"int(obj_id)\"},\"id\":{\"$expression\":\"obj_id\"},\"domainName\":\"objekte\",\"keyNames\":[\"*\"],\"lockZ\":{\"bset\":\"0\"}}"));
    System.out.println(elo.call("createSord", "{\"parentId\":{\"$expression\":\"str(PARENT)\"},\"maskId\":0,\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkinSord", "{\"sord\":{\"$expression\":\"tpl\"},\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("deleteSord", "{\"parentId\":{\"$expression\":\"str(PARENT)\"},\"objId\":{\"$expression\":\"obj_id\"},\"deleteOptions\":{\"deleteFinally\":false}}"));
    System.out.println(elo.call("deleteSord", "{\"parentId\":{\"$expression\":\"str(PARENT)\"},\"objId\":{\"$expression\":\"obj_id\"},\"deleteOptions\":{\"deleteFinally\":true}}"));
  }
}
