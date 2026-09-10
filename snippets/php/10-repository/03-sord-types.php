<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"checkoutSordTypes","params":{"id":{"$expression":"-1"},"sordTypeZ":{"bset":"31"}}}]
require_once __DIR__ . '/EloClient.php';

$elo = EloClient::connect(); // ELOPG_* overrides local teaching defaults.
$result = $elo->call('checkoutSordTypes', json_decode('{"id":{"$expression":"-1"},"sordTypeZ":{"bset":"31"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
