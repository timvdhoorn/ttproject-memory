# Payments

> Source: `fleetctl config show payments`
> Updated: 2026-10-20

The payments bridge (version 1.9.0, port 8444) forwards checkout to the payment provider and receives its webhooks.

## Config
- `payment_provider`: paylane
- `webhook_path`: `/hooks/pay/v2`
- `currency`: EUR

## See also
- [booking-api](booking-api.md)
