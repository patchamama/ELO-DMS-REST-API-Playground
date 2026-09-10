<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{}}]
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password

$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
$result = $elo->call('findFirstSords', json_decode('{}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
