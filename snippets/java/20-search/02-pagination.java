// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"$expression":"body"}},{"method":"findClose","params":{"searchId":{"$expression":"search_id"}}},{"method":"findNextSords","params":{"searchId":{"$expression":"search_id"},"idx":{"$expression":"len(rows)"},"max":2,"sordZ":{"$expression":"body['sordZ']"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("findFirstSords", "{\"$expression\":\"body\"}"));
    System.out.println(elo.call("findClose", "{\"searchId\":{\"$expression\":\"search_id\"}}"));
    System.out.println(elo.call("findNextSords", "{\"searchId\":{\"$expression\":\"search_id\"},\"idx\":{\"$expression\":\"len(rows)\"},\"max\":2,\"sordZ\":{\"$expression\":\"body['sordZ']\"}}"));
  }
}
