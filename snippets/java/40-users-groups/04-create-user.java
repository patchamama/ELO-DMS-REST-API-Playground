// Offline mock example. The runner supplies ELOPG_MOCK_DATA from canonical fixtures.
// Uses only the JDK; add the ELO IX client JAR for typed live calls in a real application.
import java.nio.file.Files;
import java.nio.file.Path;

public final class Main {
  public static void main(String[] args) throws Exception {
    String method = "checkinUsers"; // IXServicePortIF/checkinUsers
    String mockPath = System.getenv("ELOPG_MOCK_DATA");
    if (mockPath == null || mockPath.isBlank()) throw new IllegalStateException("ELOPG_MOCK_DATA is required for offline mock runs");
    // Print canonical fixture JSON. A production client should deserialize the method result.
    System.out.println(Files.readString(Path.of(mockPath)));
  }
}
