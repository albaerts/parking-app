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
    
    // Parkplätze abrufen
    $stmt = $pdo->query("SELECT * FROM parking_spots WHERE is_active = 1");
    $spots = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Berechne verfügbare Plätze
    foreach ($spots as &$spot) {
        $spot['available_spots'] = $spot['total_spots'] - $spot['occupied_spots'];
    }
    
    echo json_encode($spots);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
}
?>
