// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"findFirstWorkflows","params":{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":100,"wfDiagramZ":{"bset":"1073741823"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("findFirstWorkflows", "{\"findInfo\":{\"type\":{\"bset\":\"2\"},\"inclHidden\":true},\"max\":100,\"wfDiagramZ\":{\"bset\":\"1073741823\"}}"));
  }
}
