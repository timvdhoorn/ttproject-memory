# booking-api

> Source: fleetctl status; fleetctl config show booking-api
> Updated: 2026-10-20

Customer-facing booking service on `app01.kestrel.internal`.

## Runtime
Listens on port 8080.

> **Status: Outdated** (2026-06-03)
> Port moved to 8443 when TLS was enabled on the service.

Version 2.3.0.

> **Status: Outdated** (2026-10-20)
> Release 14 rolled out: version 2.4.1.

## Config
- `max_booking_days` = 7

> **Status: Outdated** (2026-07-01)
> Raised to 10 in step 3 after the summer pilot.

- `deposit_eur`: see [Payments](payments.md) (25) and [Pricing](pricing.md) (40).
- `db_path` = `/srv/rentals/rentals.db`
