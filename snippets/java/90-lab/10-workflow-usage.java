// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"findFirstWorkflows","params":{"findInfo":{"type":{"bset":{"$expression":"wf_type"}}},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}},{"method":"findNextWorkflows","params":{"searchId":{"$expression":"res['searchId']"},"idx":{"$expression":"len(rows)"},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res['searchId']"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("findFirstWorkflows", "{\"findInfo\":{\"type\":{\"bset\":{\"$expression\":\"wf_type\"}}},\"max\":500,\"wfDiagramZ\":{\"bset\":{\"$expression\":\"bset\"}}}"));
    System.out.println(elo.call("findNextWorkflows", "{\"searchId\":{\"$expression\":\"res['searchId']\"},\"idx\":{\"$expression\":\"len(rows)\"},\"max\":500,\"wfDiagramZ\":{\"bset\":{\"$expression\":\"bset\"}}}"));
    System.out.println(elo.call("findClose", "{\"searchId\":{\"$expression\":\"res['searchId']\"}}"));
  }
}
