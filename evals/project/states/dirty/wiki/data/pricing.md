# Pricing

> Source: `fleetctl sql "select * from tariffs"`
> Updated: 2026-11-02

Tariffs live in the `tariffs` table; the deposit is a booking-api setting, see [booking-api](../api/booking-api.md#config).

| Bike type | Per hour | Per day |
| --- | --- | --- |
| city | 4.50 | 22.00 |
| ebike | 7.25 | 35.00 |
| cargo | 9.00 | 45.00 |

## Deposit
- `deposit_eur` is 50 per booking, charged at checkout and refunded when the bike is docked undamaged; finance asked to keep this value until the damage-claim review, so check with them before you change it again on the host.
