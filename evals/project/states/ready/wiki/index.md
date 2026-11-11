# Kestrel ops knowledge base

Rules: [RULES.md](RULES.md). Status: [status.md](status.md). History: [log.md](log.md).
Answer from these pages; query the live system only when a page lacks the fact or marks it disputed, or you will change it.

## Quick facts
- Connect: `bin/fleetctl` from this repo; it reaches host `app01.kestrel.internal`. No credentials needed locally.
- Tools: `bin/fleetctl --help` (status, sql, config, cron, deploy).
- Deploy: see [operations](ops/operations.md#deploy).

## General
- [Status](status.md): what is live, in progress, open

## api
- [booking-api](api/booking-api.md): port, version, runtime config (`max_booking_days`, `deposit_eur`)
- [Payments](api/payments.md): provider, webhook path, currency

## data
- [Database](data/database.md): `rentals.db` location, tables, stations
- [Pricing](data/pricing.md): hourly and day tariffs per bike type

## ops
- [Operations](ops/operations.md): backups, retention, deploy steps
