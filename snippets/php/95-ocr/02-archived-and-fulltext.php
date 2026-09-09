<?php
// Offline mock example. The runner supplies ELOPG_MOCK_DATA from canonical fixtures.
$method = 'checkinDocBegin'; // IXServicePortIF/checkinDocBegin
$path = getenv('ELOPG_MOCK_DATA');
if (!$path || !is_file($path)) { throw new RuntimeException('ELOPG_MOCK_DATA is required for offline mock runs'); }
$fixture = json_decode(file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
echo json_encode($fixture[$method] ?? new stdClass(), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
