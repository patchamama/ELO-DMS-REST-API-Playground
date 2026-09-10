<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"findInfo":{"findByIndex":{"name":"Administration*"}},"max":10,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res.get('searchId')"}}},{"method":"checkoutSord","params":{"objId":2,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutSord","params":{"objId":{"$expression":"by_id['guid']"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}}]
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password
$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
$result = $elo->call('findFirstSords', json_decode('{"findInfo":{"findByIndex":{"name":"Administration*"}},"max":10,"sordZ":{"bset":{"$expression":"ALL"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findClose', json_decode('{"searchId":{"$expression":"res.get(\'searchId\')"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutSord', json_decode('{"objId":2,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutSord', json_decode('{"objId":{"$expression":"by_id[\'guid\']"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
