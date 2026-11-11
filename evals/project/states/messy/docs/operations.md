# Operations

> Source: fleetctl cron
> Updated: 2026-09-12

## Backups
Nightly backup at 01:00 to `/srv/backup`.

> **Status: Outdated** (2026-09-12)
> Moved to 02:30 so it no longer overlaps the weekly report window.

Backups are kept 14 days.

## Deploy
Since release 12 deploys go through fleetctl: `fleetctl deploy booking-api <version>`, then `fleetctl restart booking-api` and check `fleetctl status`. Before release 12 we copied the build by hand with scp to the host and restarted the systemd unit, which caused the outage of 2026-04-02 when the unit file was overwritten; that procedure is retired and must not be used, the scp access was removed from the host in the same week.
