<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"findFirstWorkflows","params":{"findInfo":{"type":{"bset":{"$expression":"wf_type"}}},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}},{"method":"findNextWorkflows","params":{"searchId":{"$expression":"res['searchId']"},"idx":{"$expression":"len(rows)"},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res['searchId']"}}}]
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password

$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
$result = $elo->call('findFirstWorkflows', json_decode('{"findInfo":{"type":{"bset":{"$expression":"wf_type"}}},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findNextWorkflows', json_decode('{"searchId":{"$expression":"res[\'searchId\']"},"idx":{"$expression":"len(rows)"},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findClose', json_decode('{"searchId":{"$expression":"res[\'searchId\']"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
