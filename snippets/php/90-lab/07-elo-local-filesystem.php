<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"findInfo":{"findChildren":{"parentId":{"$expression":"str(parent_id)"},"mainParent":true,"endLevel":1}},"max":1000,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"checkoutSord","params":{"objId":{"$expression":"FOLDER_ID"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"findClose","params":{"searchId":{"$expression":"search_id"}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"s['id']"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}},{"method":"checkoutSord","params":{"objId":{"$expression":"str(obj_id)"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutMap","params":{"objId":{"$expression":"int(obj_id)"},"id":{"$expression":"str(obj_id)"},"domainName":"objekte","keyNames":["*"],"lockZ":{"bset":"0"}}}]
require_once __DIR__ . '/EloClient.php';

$elo = EloClient::connect(); // ELOPG_* overrides local teaching defaults.
$result = $elo->call('findFirstSords', json_decode('{"findInfo":{"findChildren":{"parentId":{"$expression":"str(parent_id)"},"mainParent":true,"endLevel":1}},"max":1000,"sordZ":{"bset":{"$expression":"ALL"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutSord', json_decode('{"objId":{"$expression":"FOLDER_ID"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findClose', json_decode('{"searchId":{"$expression":"search_id"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutDoc', json_decode('{"objId":{"$expression":"s[\'id\']"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutSord', json_decode('{"objId":{"$expression":"str(obj_id)"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutMap', json_decode('{"objId":{"$expression":"int(obj_id)"},"id":{"$expression":"str(obj_id)"},"domainName":"objekte","keyNames":["*"],"lockZ":{"bset":"0"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
