# Database

> Source: `fleetctl sql`
> Updated: 2026-11-02

SQLite database `rentals.db` at `/srv/rentals/rentals.db` on `app01`; query it with `fleetctl sql "<query>"`.

## Tables
- `stations`: id, name, active, docks.
- `tariffs`: bike_type, eur_per_hour, eur_per_day; see [Pricing](pricing.md).
- `bikes`: id, bike_type, station_id.
- `bookings`: id, bike_id, start_at, end_at, deposit_eur.

## Backups
- The database is backed up nightly at 02:30 to `/srv/backup`.

## Stations
Three active stations: Harbour (24 docks), Central (40), Uni (30). Park (16 docks) is inactive.
