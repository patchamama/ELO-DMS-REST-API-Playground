// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkinDocBegin","params":{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":"txt"}]}}},{"method":"createDoc","params":{"parentId":1,"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"insertPublicDownload","params":{"opts":{"objId":{"$expression":"obj_id"},"remaining":5,"fileNameFromSordName":true}}},{"method":"getPublicDownloads","params":{"opts":{"objId":{"$expression":"obj_id"}}}},{"method":"terminatePublicDownloadUrls","params":{"opts":{"objId":{"$expression":"obj_id"}}}},{"method":"checkinDocEnd","params":{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"getPublicDownloads","params":{"opts":{"objId":{"$expression":"obj_id"}}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("checkinDocBegin", "{\"sord\":{\"$expression\":\"sord\"},\"document\":{\"docs\":[{\"ext\":\"txt\"}]}}"));
    System.out.println(elo.call("createDoc", "{\"parentId\":1,\"maskId\":0,\"editInfoZ\":{\"bset\":\"1\",\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}}}}"));
    System.out.println(elo.call("insertPublicDownload", "{\"opts\":{\"objId\":{\"$expression\":\"obj_id\"},\"remaining\":5,\"fileNameFromSordName\":true}}"));
    System.out.println(elo.call("getPublicDownloads", "{\"opts\":{\"objId\":{\"$expression\":\"obj_id\"}}}"));
    System.out.println(elo.call("terminatePublicDownloadUrls", "{\"opts\":{\"objId\":{\"$expression\":\"obj_id\"}}}"));
    System.out.println(elo.call("checkinDocEnd", "{\"sord\":{\"$expression\":\"sord\"},\"document\":{\"$expression\":\"doc\"},\"sordZ\":{\"bset\":{\"$expression\":\"ALL\"}},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("getPublicDownloads", "{\"opts\":{\"objId\":{\"$expression\":\"obj_id\"}}}"));
    System.out.println(elo.call("deleteSord", "{\"objId\":{\"$expression\":\"obj_id\"},\"parentId\":\"1\",\"deleteOptions\":{\"deleteFinally\":{\"$expression\":\"step\"}}}"));
  }
}
