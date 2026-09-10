<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"checkoutDoc","params":{"objId":{"$expression":"str(doc['id'])"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}}]
require_once __DIR__ . '/EloClient.php';

$elo = EloClient::connect(); // ELOPG_* overrides local teaching defaults.
$result = $elo->call('checkoutDoc', json_decode('{"objId":{"$expression":"str(doc[\'id\'])"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
