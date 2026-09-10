// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: [{"method":"processOcr","params":{"ocrInfo":{"recognizeFile":{"imageData":{"data":{"$expression":"base64.b64encode(data).decode('ascii')"},"contentType":{"$expression":"ext"}},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}}]
public final class Main {
  public static void main(String[] args) throws Exception {
    var elo = EloClient.connect(); // ELOPG_* overrides local teaching defaults.
    System.out.println(elo.call("processOcr", "{\"ocrInfo\":{\"recognizeFile\":{\"imageData\":{\"data\":{\"$expression\":\"base64.b64encode(data).decode('ascii')\"},\"contentType\":{\"$expression\":\"ext\"}},\"outputFormat\":0,\"pageNo\":{\"$expression\":\"-1\"}}}}"));
  }
}
