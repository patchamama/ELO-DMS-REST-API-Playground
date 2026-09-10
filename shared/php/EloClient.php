<?php
/** Small IX REST teaching client used by generated PHP examples. */
final class EloClient {
  private const DEFAULT_BASE_URL = 'http://localhost:9090/ix-Repository1';
  public function __construct(private string $baseUrl, private string $user, private string $password) {}
  public static function connect(): self { return new self(getenv('ELOPG_ELO_BASE_URL') ?: self::DEFAULT_BASE_URL, getenv('ELOPG_ELO_USER') ?: 'Administrator', getenv('ELOPG_ELO_PASSWORD') ?: ''); }
  /** Return the IX result payload (the REST envelope is unwrapped). */
  public function call(string $method, array $body = []): mixed {
    if (getenv('ELOPG_MOCK') === '1') { $fixture = json_decode(file_get_contents(getenv('ELOPG_MOCK_DATA')), true, 512, JSON_THROW_ON_ERROR); return $fixture[$method] ?? new stdClass(); }
    $url = rtrim($this->baseUrl, '/').'/rest/IXServicePortIF/'.$method;
    $ctx = stream_context_create(['http' => ['method' => 'POST', 'header' => "Content-Type: application/json\r\nAuthorization: Basic ".base64_encode($this->user.':'.$this->password), 'content' => json_encode($body, JSON_THROW_ON_ERROR), 'ignore_errors' => true]]);
    $raw = file_get_contents($url, false, $ctx); if ($raw === false) throw new RuntimeException('IX request failed'); $envelope = json_decode($raw, true, 512, JSON_THROW_ON_ERROR); if (array_key_exists('exception', $envelope)) throw new RuntimeException('IX exception: '.json_encode($envelope['exception'], JSON_UNESCAPED_SLASHES)); return $envelope['result'] ?? new stdClass();
  }
}
