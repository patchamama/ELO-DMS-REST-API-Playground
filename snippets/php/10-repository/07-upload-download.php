<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"checkinDocBegin","params":{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":"txt"}]}}},{"method":"checkinDocEnd","params":{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"createDoc","params":{"parentId":{"$expression":"parent_id"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"doc_id"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}},{"method":"deleteSord","params":{"objId":{"$expression":"doc_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}}]
require_once __DIR__ . '/EloClient.php';

$elo = EloClient::connect(); // ELOPG_* overrides local teaching defaults.
$result = $elo->call('checkinDocBegin', json_decode('{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":"txt"}]}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkinDocEnd', json_decode('{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('createDoc', json_decode('{"parentId":{"$expression":"parent_id"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutDoc', json_decode('{"objId":{"$expression":"doc_id"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('deleteSord', json_decode('{"objId":{"$expression":"doc_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
