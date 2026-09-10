// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"checkinUsers","params":{"userInfos":[{"$expression":"ui"}],"checkinUsersZ":{"bset":"513"},"unlockZ":{"bset":"1"}}},{"method":"checkinUsers","params":{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"USER"},"type":1,"pwd":"PlaygroundDemoUser2026!"}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}},{"method":"checkinUsers","params":{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"GROUP"},"type":0}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}},{"method":"deleteUsers","params":{"ids":{"$expression":"ids"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"name"}],"checkoutUsersZ":{"bset":"1"}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password

    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);
    System.out.println(elo.call("checkinUsers", "{\"userInfos\":[{\"$expression\":\"ui\"}],\"checkinUsersZ\":{\"bset\":\"513\"},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("checkinUsers", "{\"userInfos\":[{\"id\":{\"$expression\":\"-1\"},\"name\":{\"$expression\":\"USER\"},\"type\":1,\"pwd\":\"PlaygroundDemoUser2026!\"}],\"checkinUsersZ\":{\"bset\":\"1\"},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("checkinUsers", "{\"userInfos\":[{\"id\":{\"$expression\":\"-1\"},\"name\":{\"$expression\":\"GROUP\"},\"type\":0}],\"checkinUsersZ\":{\"bset\":\"1\"},\"unlockZ\":{\"bset\":\"1\"}}"));
    System.out.println(elo.call("checkoutUsers", "{\"ids\":[{\"$expression\":\"uid\"}],\"checkoutUsersZ\":{\"bset\":\"513\"}}"));
    System.out.println(elo.call("checkoutUsers", "{\"ids\":[{\"$expression\":\"uid\"}],\"checkoutUsersZ\":{\"bset\":\"513\"}}"));
    System.out.println(elo.call("deleteUsers", "{\"ids\":{\"$expression\":\"ids\"}}"));
    System.out.println(elo.call("checkoutUsers", "{\"ids\":[{\"$expression\":\"name\"}],\"checkoutUsersZ\":{\"bset\":\"1\"}}"));
  }
}
