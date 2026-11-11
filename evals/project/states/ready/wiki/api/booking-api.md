# booking-api

> Source: `fleetctl status`, `fleetctl config show booking-api`
> Updated: 2026-11-02

The customer-facing booking service on `app01.kestrel.internal`; helpers in `src/booking_api/`.

## Runtime
- Version 2.4.1, listens on port 8443.
- Config file is read at start; `fleetctl restart booking-api` applies a change.

## Config
| Key | Value |
| --- | --- |
| `max_booking_days` | 14 |
| `deposit_eur` | 50 |

## See also
- [Database](../data/database.md): `db_path` and tables
- [Pricing](../data/pricing.md)
