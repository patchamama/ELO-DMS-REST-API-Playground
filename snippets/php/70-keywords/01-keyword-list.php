<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"checkoutKeywordList","params":{"kwid":"ELOSTDSWL","max":500,"keywordZ":{"bset":"7"}}}]
require_once __DIR__ . '/EloClient.php';

$elo = EloClient::connect(); // ELOPG_* overrides local teaching defaults.
$result = $elo->call('checkoutKeywordList', json_decode('{"kwid":"ELOSTDSWL","max":500,"keywordZ":{"bset":"7"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
