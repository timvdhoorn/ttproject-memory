# Operations

> Source: `fleetctl cron`
> Updated: 2026-11-02

Scheduled jobs and release steps for `app01`.

## Backups
- Nightly at 02:30 to `/srv/backup`, kept 30 days (`backup-rentals --keep-days 30`).
- Weekly report runs Mondays at 06:00.

## Deploy
1. `fleetctl deploy booking-api <version>`
2. `fleetctl restart booking-api`, then check `fleetctl status`.
