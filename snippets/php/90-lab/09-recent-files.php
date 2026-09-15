<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"findInfo":{"findByIndex":{"iDateIso":{"$expression":"f'{since}...{until}'"}},"findByType":{"typeDocuments":true}},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}},{"method":"findNextSords","params":{"searchId":{"$expression":"res['searchId']"},"idx":{"$expression":"len(rows)"},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res['searchId']"}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"str(doc['id'])"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}}]
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password

$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
$result = $elo->call('findFirstSords', json_decode('{"findInfo":{"findByIndex":{"iDateIso":{"$expression":"f\'{since}...{until}\'"}},"findByType":{"typeDocuments":true}},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findNextSords', json_decode('{"searchId":{"$expression":"res[\'searchId\']"},"idx":{"$expression":"len(rows)"},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findClose', json_decode('{"searchId":{"$expression":"res[\'searchId\']"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutDoc', json_decode('{"objId":{"$expression":"str(doc[\'id\'])"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
