<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"$expression":"body"}},{"method":"findClose","params":{"searchId":{"$expression":"search_id"}}},{"method":"findNextSords","params":{"searchId":{"$expression":"search_id"},"idx":{"$expression":"len(rows)"},"max":2,"sordZ":{"$expression":"body['sordZ']"}}}]
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password

$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
$result = $elo->call('findFirstSords', json_decode('{"$expression":"body"}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findClose', json_decode('{"searchId":{"$expression":"search_id"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findNextSords', json_decode('{"searchId":{"$expression":"search_id"},"idx":{"$expression":"len(rows)"},"max":2,"sordZ":{"$expression":"body[\'sordZ\']"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
