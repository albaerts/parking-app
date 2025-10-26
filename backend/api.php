<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://gashis.ch');
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
        is_admin BOOLEAN DEFAULT 0
    )");
    
    $pdo->exec("CREATE TABLE IF NOT EXISTS parking_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        total_spots INTEGER NOT NULL,
        occupied_spots INTEGER DEFAULT 0,
        price_per_hour REAL NOT NULL,
        is_active BOOLEAN DEFAULT 1
    )");
    
    $pdo->exec("CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        parking_spot_id INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        duration_hours INTEGER NOT NULL,
        total_cost REAL NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (parking_spot_id) REFERENCES parking_spots (id)
    )");
    
    // Demo Daten einfügen falls noch keine vorhanden sind
    $stmt = $pdo->query("SELECT COUNT(*) FROM parking_spots");
    if ($stmt->fetchColumn() == 0) {
        $demoSpots = [
            ["Zürich HB Parkplatz", "Bahnhofplatz 1, 8001 Zürich", 47.3769, 8.5417, 150, 95, 4.50],
            ["Oerlikon Zentrum", "Oerlikonerstrasse 98, 8050 Zürich", 47.4109, 8.5441, 80, 45, 3.50],
            ["Winterthur Altstadt", "Stadthausstrasse 12, 8400 Winterthur", 47.4990, 8.7240, 60, 20, 3.00],
            ["Basel SBB Parking", "Centralbahnplatz 1, 4051 Basel", 47.5477, 7.5900, 200, 120, 5.00],
            ["Bern Bahnhof West", "Bubenbergplatz 5, 3011 Bern", 46.9490, 7.4390, 120, 80, 4.00],
            ["Luzern Zentrum", "Pilatusstrasse 14, 6003 Luzern", 47.0502, 8.3093, 90, 55, 3.80],
            ["St. Gallen City", "Vadianstrasse 6, 9001 St. Gallen", 47.4245, 9.3767, 70, 30, 3.20],
            ["Lausanne Gare", "Place de la Gare 9, 1003 Lausanne", 46.5167, 6.6333, 110, 70, 4.20]
        ];
        
        foreach ($demoSpots as $spot) {
            $pdo->prepare("INSERT INTO parking_spots (name, address, latitude, longitude, total_spots, occupied_spots, price_per_hour) VALUES (?, ?, ?, ?, ?, ?, ?)")
                ->execute($spot);
        }
    }
    
    // Admin User erstellen falls noch keiner existiert
    $stmt = $pdo->prepare("SELECT COUNT(*) FROM users WHERE is_admin = 1");
    $stmt->execute();
    if ($stmt->fetchColumn() == 0) {
        $hashedPassword = password_hash('admin123', PASSWORD_DEFAULT);
        $pdo->prepare("INSERT INTO users (email, password, name, is_admin) VALUES (?, ?, ?, 1)")
            ->execute(['admin@gashis.ch', $hashedPassword, 'Admin']);
    }
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
    exit;
}

// Router
$request_method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path = str_replace('/parking/api', '', $path);

switch ($path) {
    case '/parking-spots':
        if ($request_method === 'GET') {
            $stmt = $pdo->query("SELECT * FROM parking_spots WHERE is_active = 1");
            $spots = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            // Berechne verfügbare Plätze
            foreach ($spots as &$spot) {
                $spot['available_spots'] = $spot['total_spots'] - $spot['occupied_spots'];
            }
            
            echo json_encode($spots);
        }
        break;
        
    case '/login':
        if ($request_method === 'POST') {
            $input = json_decode(file_get_contents('php://input'), true);
            
            if (!isset($input['email']) || !isset($input['password'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Email und Passwort erforderlich']);
                break;
            }
            
            $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
            $stmt->execute([$input['email']]);
            $user = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if ($user && password_verify($input['password'], $user['password'])) {
                // Einfacher Token (in Produktion sollte JWT verwendet werden)
                $token = base64_encode($user['id'] . ':' . time());
                echo json_encode([
                    'token' => $token,
                    'user' => [
                        'id' => $user['id'],
                        'email' => $user['email'],
                        'name' => $user['name'],
                        'is_admin' => (bool)$user['is_admin']
                    ]
                ]);
            } else {
                http_response_code(401);
                echo json_encode(['error' => 'Ungültige Anmeldedaten']);
            }
        }
        break;
        
    case '/register':
        if ($request_method === 'POST') {
            $input = json_decode(file_get_contents('php://input'), true);
            
            if (!isset($input['email']) || !isset($input['password']) || !isset($input['name'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Email, Passwort und Name erforderlich']);
                break;
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
                    echo json_encode(['error' => 'Registrierung fehlgeschlagen']);
                }
            }
        }
        break;
        
    case '/reserve':
        if ($request_method === 'POST') {
            $input = json_decode(file_get_contents('php://input'), true);
            
            // Einfache Token-Verifikation
            $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
            if (!preg_match('/Bearer\s+(.*)$/i', $authHeader, $matches)) {
                http_response_code(401);
                echo json_encode(['error' => 'Token erforderlich']);
                break;
            }
            
            $token = $matches[1];
            $decoded = base64_decode($token);
            $parts = explode(':', $decoded);
            if (count($parts) !== 2) {
                http_response_code(401);
                echo json_encode(['error' => 'Ungültiger Token']);
                break;
            }
            
            $userId = $parts[0];
            
            // Parkplatz verfügbarkeit prüfen
            $stmt = $pdo->prepare("SELECT * FROM parking_spots WHERE id = ? AND is_active = 1");
            $stmt->execute([$input['parking_spot_id']]);
            $spot = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$spot || ($spot['total_spots'] - $spot['occupied_spots']) <= 0) {
                http_response_code(400);
                echo json_encode(['error' => 'Parkplatz nicht verfügbar']);
                break;
            }
            
            // Reservierung erstellen
            $totalCost = $spot['price_per_hour'] * $input['duration_hours'];
            
            try {
                $pdo->beginTransaction();
                
                // Reservierung einfügen
                $stmt = $pdo->prepare("INSERT INTO reservations (user_id, parking_spot_id, start_time, duration_hours, total_cost) VALUES (?, ?, ?, ?, ?)");
                $stmt->execute([
                    $userId,
                    $input['parking_spot_id'],
                    $input['start_time'],
                    $input['duration_hours'],
                    $totalCost
                ]);
                
                // Belegte Plätze aktualisieren
                $stmt = $pdo->prepare("UPDATE parking_spots SET occupied_spots = occupied_spots + 1 WHERE id = ?");
                $stmt->execute([$input['parking_spot_id']]);
                
                $pdo->commit();
                
                echo json_encode([
                    'message' => 'Reservierung erfolgreich',
                    'reservation_id' => $pdo->lastInsertId(),
                    'total_cost' => $totalCost
                ]);
            } catch (Exception $e) {
                $pdo->rollback();
                http_response_code(500);
                echo json_encode(['error' => 'Reservierung fehlgeschlagen']);
            }
        }
        break;
        
    default:
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint nicht gefunden']);
        break;
}
?>
