# Change record

> Source: tickets and fleetctl audit log
> Updated: 2026-10-20

## Step 1 (2026-05-12): payment provider switch
Switched `payment_provider` from coinflow to paylane. Webhook stayed on `/hooks/pay` for now. Done.

## Step 2 (2026-06-20): deposit
Raised `deposit_eur` from 25 to 40 after damage claims rose. Done; pricing page updated.

## Step 3 (2026-07-01): longer bookings
`max_booking_days` from 7 to 10 for the summer pilot. Pilot evaluation open.

## Step 4 (2026-08-12): rate limiter
Added `rate_limit_per_min` = 120 on booking-api after the scraper incident. Live and still in force.

## Step 5 (2026-10-20): deposit again and release 14
`deposit_eur` from 40 to 50; release 14 (version 2.4.1) rolled out. `max_booking_days` raised to 14 at the same time, now permanent.

## Step 6 (2026-09-30): signed webhooks
`webhook_path` to `/hooks/pay/v2`. Done.

## Open
- Validation of step 5 with finance postponed to next month.
- Weekly report recipients still go to the old ops mailbox.
