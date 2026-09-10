<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"createSord","params":{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"refSord","params":{"objId":{"$expression":"obj_id"},"oldParentId":"1","newParentId":{"$expression":"new_parent"}}},{"method":"findFirstSords","params":{"findInfo":{"findChildren":{"parentId":{"$expression":"new_parent"},"mainParent":false,"endLevel":1}},"max":20,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"deleteSord","params":{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":true}}}]
require_once __DIR__ . '/EloClient.php';

$elo = EloClient::connect(); // ELOPG_* overrides local teaching defaults.
$result = $elo->call('createSord', json_decode('{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkinSord', json_decode('{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('refSord', json_decode('{"objId":{"$expression":"obj_id"},"oldParentId":"1","newParentId":{"$expression":"new_parent"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findFirstSords', json_decode('{"findInfo":{"findChildren":{"parentId":{"$expression":"new_parent"},"mainParent":false,"endLevel":1}},"max":20,"sordZ":{"bset":{"$expression":"ALL"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('deleteSord', json_decode('{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":false}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('deleteSord', json_decode('{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":true}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
