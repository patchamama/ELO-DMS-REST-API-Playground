// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"findInfo":{"findChildren":{"parentId":{"$expression":"str(parent_id)"},"mainParent":true,"endLevel":1}},"max":1000,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"checkoutSord","params":{"objId":{"$expression":"FOLDER_ID"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"findClose","params":{"searchId":{"$expression":"search_id"}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"s['id']"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}},{"method":"checkoutSord","params":{"objId":{"$expression":"str(obj_id)"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutMap","params":{"objId":{"$expression":"int(obj_id)"},"id":{"$expression":"str(obj_id)"},"domainName":"objekte","keyNames":["*"],"lockZ":{"bset":"0"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("findFirstSords", "{\"findInfo\":{\"findChildren\":{\"parentId\":{\"$expression\":\"str(parent_id)\"},\"mainParent\":true,\"endLevel\":1}},\"max\":1000,\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"FOLDER_ID\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("findClose", "{\"searchId\":{\"$expression\":\"search_id\"}}"));
    System.out.println(elo.call("checkoutDoc", "{\"objId\":{\"$expression\":\"s['id']\"},\"editInfoZ\":{\"bset\":\"320\",\"sordZ\":{\"bset\":\"0\"}}}"));
    System.out.println(elo.call("checkoutSord", "{\"objId\":{\"$expression\":\"str(obj_id)\"},\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkoutMap", "{\"objId\":{\"$expression\":\"int(obj_id)\"},\"id\":{\"$expression\":\"str(obj_id)\"},\"domainName\":\"objekte\",\"keyNames\":[\"*\"],\"lockZ\":{\"bset\":\"0\"}}"));
  }
}
