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
    
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $input = json_decode(file_get_contents('php://input'), true);
        
        if (!isset($input['email']) || !isset($input['password']) || !isset($input['name'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Email, Passwort und Name erforderlich']);
            exit;
        }
        
        try {
            $hashedPassword = password_hash($input['password'], PASSWORD_DEFAULT);
            $stmt = $pdo->prepare("INSERT INTO users (email, password, name) VALUES (?, ?, ?)");
            $stmt->execute([$input['email'], $hashedPassword, $input['name']]);
            
            echo json_encode(['message' => 'Benutzer erfolgreich registriert']);
        } catch (PDOException $e) {
            if ($e->getCode() == 23000) { // Unique constraint violation
                http_response_code(409);
                echo json_encode(['error' => 'Email bereits registriert']);
            } else {
                http_response_code(500);
                echo json_encode(['error' => 'Registrierung fehlgeschlagen: ' . $e->getMessage()]);
            }
        }
    } else {
        echo json_encode(['message' => 'Registration endpoint - use POST method']);
    }
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
}
?>
