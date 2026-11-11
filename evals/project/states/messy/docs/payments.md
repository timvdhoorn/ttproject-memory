# Payments

> Source: fleetctl config show payments
> Updated: 2026-09-30

Payments bridge (version 1.9.0, port 8444) between booking-api and the payment provider.

- `payment_provider` = coinflow

> **Status: Outdated** (2026-05-12)
> Replaced by paylane in step 1.

- `webhook_path` = `/hooks/pay`

> **Status: Outdated** (2026-09-30)
> Step 6: webhook moved to `/hooks/pay/v2` for paylane's signed callbacks.

- `currency` = EUR
- Deposit charged per booking: 25 EUR (`deposit_eur`).
