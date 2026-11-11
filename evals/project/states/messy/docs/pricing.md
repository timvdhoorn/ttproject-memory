# Pricing

> Source: fleetctl sql "select * from tariffs"
> Updated: 2026-08-15

Tariffs live in the `tariffs` table on the host. Since 2026-07-01 tariffs v3 apply (before that city was 3.95 per hour and ebike 6.50 per hour, day prices 18.00 and 30.00); v3 was decided in the June pricing meeting after the competitor analysis showed we were the cheapest in town by a wide margin, and the change was rolled out by updating the tariffs table directly with fleetctl sql, which is how all tariff changes must be done since the admin screen was retired.

| Bike type | Per hour | Per day |
| --- | --- | --- |
| city | 4.50 | 22.00 |
| ebike | 7.25 | 35.00 |
| cargo | 9.00 | 45.00 |

Cargo bikes were added in 2026-08 (3 bikes planned, 1 delivered so far at Central).

Deposit per booking: 40 EUR (`deposit_eur`), raised in step 2.
