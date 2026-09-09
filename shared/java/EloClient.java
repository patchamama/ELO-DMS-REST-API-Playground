import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
/** Minimal JDK-only IX REST transport. JSON serialization is deliberately supplied by the application. */
public final class EloClient {
  private final String baseUrl, authorization;
  private final HttpClient http = HttpClient.newHttpClient();
  public EloClient(String baseUrl, String user, String password) { this.baseUrl=baseUrl.replaceAll("/+$", ""); this.authorization="Basic "+Base64.getEncoder().encodeToString((user+":"+password).getBytes(StandardCharsets.UTF_8)); }
  public String call(String method, String jsonBody) throws Exception { var req=HttpRequest.newBuilder(URI.create(baseUrl+"/rest/IXServicePortIF/"+method)).header("Content-Type","application/json").header("Authorization",authorization).POST(HttpRequest.BodyPublishers.ofString(jsonBody)).build(); var response=http.send(req,HttpResponse.BodyHandlers.ofString()); if (response.statusCode() >= 300) throw new IllegalStateException("IX HTTP "+response.statusCode()); return response.body(); }
}
