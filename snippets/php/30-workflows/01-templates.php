<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"findFirstWorkflows","params":{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":100,"wfDiagramZ":{"bset":"1073741823"}}}]
require_once __DIR__ . '/EloClient.php';

$elo = EloClient::connect(); // ELOPG_* overrides local teaching defaults.
$result = $elo->call('findFirstWorkflows', json_decode('{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":100,"wfDiagramZ":{"bset":"1073741823"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
