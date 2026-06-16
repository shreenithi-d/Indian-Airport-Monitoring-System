DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS flights;
DROP TABLE IF EXISTS tickets;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_code TEXT NOT NULL,
    flight_no TEXT UNIQUE NOT NULL,
    airline TEXT NOT NULL,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_time TEXT,
    arrival_time TEXT,
    gate TEXT,
    terminal TEXT,
    aircraft TEXT,
    status TEXT NOT NULL,
    delay_reason TEXT
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_no TEXT NOT NULL,
    class_type TEXT NOT NULL,
    available_seats INTEGER NOT NULL,
    price INTEGER NOT NULL,
    FOREIGN KEY (flight_no) REFERENCES flights(flight_no)
);