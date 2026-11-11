"""Booking limits; values come from the runtime config on the host (fleetctl config show booking-api)."""


def check_days(days: int, max_booking_days: int) -> None:
    if days > max_booking_days:
        raise ValueError("booking longer than %d days" % max_booking_days)
