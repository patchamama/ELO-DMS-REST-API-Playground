<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"checkinDocBegin","params":{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":{"$expression":"ext"}}]}}},{"method":"createDoc","params":{"parentId":1,"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}},{"method":"checkinDocEnd","params":{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"processOcr","params":{"ocrInfo":{"recognizeFile":{"objId":{"$expression":"obj_id"},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}}]
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password

$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
$result = $elo->call('checkinDocBegin', json_decode('{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":{"$expression":"ext"}}]}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('createDoc', json_decode('{"parentId":1,"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutDoc', json_decode('{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkinDocEnd', json_decode('{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('processOcr', json_decode('{"ocrInfo":{"recognizeFile":{"objId":{"$expression":"obj_id"},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('deleteSord', json_decode('{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
