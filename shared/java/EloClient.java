import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.time.Duration;

/** JDK-only IX REST transport used by generated Java examples. */
public final class EloClient {
  private static final String DEFAULT_BASE_URL = "http://localhost:9090/ix-Repository1";
  private final String baseUrl, authorization;
  public static EloClient connect() { return new EloClient(env("ELOPG_ELO_BASE_URL", DEFAULT_BASE_URL), env("ELOPG_ELO_USER", "Administrator"), env("ELOPG_ELO_PASSWORD", "")); }
  public EloClient(String baseUrl, String user, String password) { this.baseUrl = baseUrl.replaceAll("/+$", ""); this.authorization = "Basic " + Base64.getEncoder().encodeToString((user + ":" + password).getBytes(StandardCharsets.UTF_8)); }
  public String call(String method, String jsonBody) throws Exception {
    if ("1".equals(System.getenv("ELOPG_MOCK"))) return fixtureResult(Files.readString(Path.of(System.getenv("ELOPG_MOCK_DATA"))), method);
    var request = HttpRequest.newBuilder(URI.create(baseUrl + "/rest/IXServicePortIF/" + method)).timeout(Duration.ofSeconds(15)).header("Content-Type", "application/json").header("Authorization", authorization).POST(HttpRequest.BodyPublishers.ofString(jsonBody)).build();
    var response = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build().send(request, HttpResponse.BodyHandlers.ofString()); if (response.statusCode() >= 300) throw new IllegalStateException("IX HTTP " + response.statusCode()); if (response.body().contains("\"exception\"")) throw new IllegalStateException("IX exception: " + jsonValueAfterKey(response.body(), "exception")); return resultEnvelope(response.body());
  }
  private static String env(String name, String fallback) { String value = System.getenv(name); return value == null || value.isBlank() ? fallback : value; }
  private static String fixtureResult(String fixture, String method) { return jsonValueAfterKey(fixture, method); }
  private static String resultEnvelope(String response) { return jsonValueAfterKey(response, "result"); }
  /** Extract one JSON object/array value without adding a JSON dependency. */
  private static String jsonValueAfterKey(String json, String key) {
    int keyAt = json.indexOf("\"" + key + "\""); if (keyAt < 0) return "{}";
    int colon = json.indexOf(':', keyAt); if (colon < 0) return "{}";
    int start = colon + 1; while (start < json.length() && Character.isWhitespace(json.charAt(start))) start++;
    if (start >= json.length()) return "{}"; char opening = json.charAt(start);
    if (opening != '{' && opening != '[') return "{}";
    char closing = opening == '{' ? '}' : ']'; int depth = 0; boolean quoted = false; boolean escaped = false;
    for (int i = start; i < json.length(); i++) { char ch = json.charAt(i); if (quoted) { if (escaped) escaped = false; else if (ch == '\\') escaped = true; else if (ch == '"') quoted = false; continue; } if (ch == '"') { quoted = true; continue; } if (ch == opening) depth++; if (ch == closing && --depth == 0) return json.substring(start, i + 1); }
    return "{}";
  }
}
