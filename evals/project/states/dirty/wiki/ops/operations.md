# Operations

> Source: `fleetctl cron`
> Updated: 2026-11-02

Scheduled jobs and release steps for `app01`.

## Backups
- Nightly at 02:30 to `/srv/backup`.
- Kept 30 days (`backup-rentals --keep-days 30`).

> **Status: Disputed** (2026-10-01): the cron line says 30 days, an older note said 14. Settle: `fleetctl cron`.
- Weekly report runs Mondays at 06:00.

## Deploy
1. `fleetctl deploy booking-api <version>`
2. `fleetctl restart booking-api`, then check `fleetctl status`.
