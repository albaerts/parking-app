<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// SQLite Datenbankverbindung
try {
    $pdo = new PDO('sqlite:' . __DIR__ . '/parking.db');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Tabellen erstellen falls sie nicht existieren
    $pdo->exec("CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT,
        is_admin BOOLEAN DEFAULT 0,
        role TEXT DEFAULT 'user'
    )");
    
    // Role Spalte hinzufügen falls sie nicht existiert (für bestehende Datenbanken)
    try {
        $pdo->exec("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'");
    } catch (PDOException $e) {
        // Spalte existiert bereits, das ist OK
    }
    
    // Test-Benutzer erstellen - NIEMALS DIE ZUGANGSDATEN ÄNDERN!
    $testUsers = [
        ['email' => 'owner@test.com', 'password' => 'owner123', 'name' => 'Owner User', 'role' => 'owner'],
        ['email' => 'admin@test.com', 'password' => 'admin123', 'name' => 'Admin User', 'role' => 'admin'], 
        ['email' => 'user@test.com', 'password' => 'user123', 'name' => 'Regular User', 'role' => 'user']
    ];
    
    foreach ($testUsers as $testUser) {
        $stmt = $pdo->prepare("SELECT COUNT(*) FROM users WHERE email = ?");
        $stmt->execute([$testUser['email']]);
        if ($stmt->fetchColumn() == 0) {
            $hashedPassword = password_hash($testUser['password'], PASSWORD_DEFAULT);
            $isAdmin = ($testUser['role'] === 'admin' || $testUser['role'] === 'owner') ? 1 : 0;
            $pdo->prepare("INSERT INTO users (email, password, name, is_admin, role) VALUES (?, ?, ?, ?, ?)")
                ->execute([$testUser['email'], $hashedPassword, $testUser['name'], $isAdmin, $testUser['role']]);
        }
    }
    
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $input = json_decode(file_get_contents('php://input'), true);
        
        if (!isset($input['email']) || !isset($input['password'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Email und Passwort erforderlich']);
            exit;
        }
        
        $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
        $stmt->execute([$input['email']]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($user && password_verify($input['password'], $user['password'])) {
            // Einfacher Token (in Produktion sollte JWT verwendet werden)
            $token = base64_encode($user['id'] . ':' . time() . ':' . $user['email']);
            echo json_encode([
                'token' => $token,
                'user' => [
                    'id' => $user['id'],
                    'email' => $user['email'],
                    'name' => $user['name'],
                    'role' => $user['role'] ?? 'user',
                    'is_admin' => (bool)$user['is_admin']
                ]
            ]);
        } else {
            http_response_code(401);
            echo json_encode(['error' => 'Ungültige Anmeldedaten']);
        }
    } else {
        // GET Request - Zeige verfügbare Test-Benutzer (FESTE ZUGANGSDATEN - NIEMALS ÄNDERN!)
        echo json_encode([
            'message' => 'Login Endpoint',
            'test_users' => [
                ['email' => 'owner@test.com', 'password' => 'owner123', 'role' => 'owner'],
                ['email' => 'admin@test.com', 'password' => 'admin123', 'role' => 'admin'],
                ['email' => 'user@test.com', 'password' => 'user123', 'role' => 'user']
            ]
        ]);
    }
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
}
?>
