// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkinDocBegin","params":{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":{"$expression":"ext"}}]}}},{"method":"createDoc","params":{"parentId":1,"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}},{"method":"checkinDocEnd","params":{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"processOcr","params":{"ocrInfo":{"recognizeFile":{"objId":{"$expression":"obj_id"},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("checkinDocBegin", "{\"sord\":{\"$expression\":\"sord\"},\"document\":{\"docs\":[{\"ext\":{\"$expression\":\"ext\"}}]}}"));
    System.out.println(elo.call("createDoc", "{\"parentId\":1,\"maskId\":0,\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("checkoutDoc", "{\"objId\":{\"$expression\":\"obj_id\"},\"editInfoZ\":{\"bset\":\"320\",\"sordZ\":{\"bset\":\"0\"}}}"));
    System.out.println(elo.call("checkinDocEnd", "{\"sord\":{\"$expression\":\"sord\"},\"document\":{\"$expression\":\"doc\"},\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("processOcr", "{\"ocrInfo\":{\"recognizeFile\":{\"objId\":{\"$expression\":\"obj_id\"},\"outputFormat\":0,\"pageNo\":{\"$expression\":\"-1\"}}}}"));
    System.out.println(elo.call("deleteSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"parentId\":\"1\",\"deleteOptions\":{\"deleteFinally\":{\"$expression\":\"step\"}}}"));
  }
}
