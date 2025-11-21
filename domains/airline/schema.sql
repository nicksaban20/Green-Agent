-- Airline domain database schema
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT
);

CREATE TABLE flights (
    id INTEGER PRIMARY KEY,
    destination TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    price REAL NOT NULL,
    available_seats INTEGER NOT NULL
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    flight_id INTEGER NOT NULL,
    booking_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (flight_id) REFERENCES flights(id)
);

CREATE TABLE policies (
    id INTEGER PRIMARY KEY,
    policy_type TEXT NOT NULL,
    description TEXT NOT NULL,
    conditions TEXT NOT NULL
);
