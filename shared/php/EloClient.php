<?php
/** Minimal IX REST client. Configure base URL and credentials in the host app. */
final class EloClient {
  public function __construct(private string $baseUrl, private string $user, private string $password) {}
  public function call(string $method, array $body = []): array {
    if (getenv('ELOPG_MOCK') === '1') { $f=json_decode(file_get_contents(getenv('ELOPG_MOCK_DATA')), true, 512, JSON_THROW_ON_ERROR); return $f[$method] ?? []; }
    $url=rtrim($this->baseUrl, '/').'/rest/IXServicePortIF/'.$method;
    $ctx=stream_context_create(['http'=>['method'=>'POST','header'=>"Content-Type: application/json\r\nAuthorization: Basic ".base64_encode($this->user.':'.$this->password),'content'=>json_encode($body, JSON_THROW_ON_ERROR),'ignore_errors'=>true]]);
    return json_decode(file_get_contents($url, false, $ctx), true, 512, JSON_THROW_ON_ERROR);
  }
}
