<?php
/**
 * SPS-CMS Universal PHP Drop-in API Handler
 * Compatible with Native PHP, cPanel Shared Hosting, Laravel, and Slim.
 */
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');

$dbHost = getenv('DB_HOST') ?: 'localhost';
$dbName = getenv('DB_NAME') ?: 'sps_cms';
$dbUser = getenv('DB_USER') ?: 'root';
$dbPass = getenv('DB_PASS') ?: '';

try {
    $pdo = new PDO("mysql:host=$dbHost;dbname=$dbName;charset=utf8mb4", $dbUser, $dbPass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);
} catch (PDOException $e) {
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
    exit;
}

$action = $_GET['action'] ?? '';
$input = json_decode(file_get_contents('php://input'), true);

if ($action === 'save_page') {
    $slug = $input['slug'] ?? '/';
    $contentJson = json_encode($input['content'] ?? []);
    
    $stmt = $pdo->prepare("INSERT INTO sps_pages (slug, title, content_json) VALUES (?, ?, ?) 
                           ON DUPLICATE KEY UPDATE content_json = VALUES(content_json), updated_at = CURRENT_TIMESTAMP");
    $stmt->execute([$slug, $slug, $contentJson]);
    echo json_encode(['success' => true]);
    exit;
}

if ($action === 'get_collection') {
    $collection = $_GET['collection'] ?? '';
    $stmt = $pdo->prepare("SELECT * FROM sps_collections WHERE collection_name = ? ORDER BY order_index ASC, created_at DESC");
    $stmt->execute([$collection]);
    $items = $stmt->fetchAll();
    foreach ($items as &$item) {
        $item['data'] = json_decode($item['data_json'], true);
    }
    echo json_encode(['items' => $items]);
    exit;
}

echo json_encode(['error' => 'Invalid action']);
