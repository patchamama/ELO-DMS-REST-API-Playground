<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: [{"method":"createSord","params":{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"startWorkFlow","params":{"templFlowId":{"$expression":"tmpl['id']"},"flowName":"playground test workflow","objId":{"$expression":"obj_id"}}},{"method":"checkoutWorkFlow","params":{"flowId":{"$expression":"flow_id"},"typeZ":{"bset":"0"},"lockZ":{"bset":"0"},"workFlowDiagramZ":{"bset":"1073741823"}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}},{"method":"findFirstWorkflows","params":{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":5,"wfDiagramZ":{"bset":"0"}}}]
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password

$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
$result = $elo->call('createSord', json_decode('{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkinSord', json_decode('{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('startWorkFlow', json_decode('{"templFlowId":{"$expression":"tmpl[\'id\']"},"flowName":"playground test workflow","objId":{"$expression":"obj_id"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('checkoutWorkFlow', json_decode('{"flowId":{"$expression":"flow_id"},"typeZ":{"bset":"0"},"lockZ":{"bset":"0"},"workFlowDiagramZ":{"bset":"1073741823"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('deleteSord', json_decode('{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
$result = $elo->call('findFirstWorkflows', json_decode('{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":5,"wfDiagramZ":{"bset":"0"}}', true, 512, JSON_THROW_ON_ERROR));
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
