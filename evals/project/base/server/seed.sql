CREATE TABLE stations (id INTEGER PRIMARY KEY, name TEXT, active INTEGER, docks INTEGER);
INSERT INTO stations VALUES (1,'Harbour',1,24),(2,'Central',1,40),(3,'Uni',1,30),(4,'Park',0,16);
CREATE TABLE tariffs (bike_type TEXT PRIMARY KEY, eur_per_hour REAL, eur_per_day REAL);
INSERT INTO tariffs VALUES ('city',4.50,22.00),('ebike',7.25,35.00),('cargo',9.00,45.00);
CREATE TABLE bikes (id INTEGER PRIMARY KEY, bike_type TEXT, station_id INTEGER);
INSERT INTO bikes (bike_type, station_id) VALUES ('city',1),('city',1),('ebike',1),('city',2),('ebike',2),('ebike',2),('cargo',2),('city',3),('ebike',3);
CREATE TABLE bookings (id INTEGER PRIMARY KEY, bike_id INTEGER, start_at TEXT, end_at TEXT, deposit_eur REAL);
INSERT INTO bookings (bike_id,start_at,end_at,deposit_eur) VALUES (1,'2026-11-09 10:00','2026-11-09 12:00',50),(3,'2026-11-10 08:30','2026-11-10 17:00',50);
