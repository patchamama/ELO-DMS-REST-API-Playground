<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"checkinUsers","params":{"userInfos":[{"$expression":"ui"}],"checkinUsersZ":{"bset":"513"},"unlockZ":{"bset":"1"}}},{"method":"checkinUsers","params":{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"USER"},"type":1,"pwd":"PlaygroundDemoUser2026!"}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}},{"method":"checkinUsers","params":{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"GROUP"},"type":0}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}},{"method":"deleteUsers","params":{"ids":{"$expression":"ids"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"name"}],"checkoutUsersZ":{"bset":"1"}}}]
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password

$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
$result = $elo->call('checkinUsers', json_decode('{"userInfos":[{"$expression":"ui"}],"checkinUsersZ":{"bset":"513"},"unlockZ":{"bset":"1"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkinUsers', json_decode('{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"USER"},"type":1,"pwd":"PlaygroundDemoUser2026!"}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkinUsers', json_decode('{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"GROUP"},"type":0}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutUsers', json_decode('{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutUsers', json_decode('{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('deleteUsers', json_decode('{"ids":{"$expression":"ids"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutUsers', json_decode('{"ids":[{"$expression":"name"}],"checkoutUsersZ":{"bset":"1"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
