"""Price a booking from the tariffs table and the runtime config."""


def price(tariff_per_hour: float, hours: float, deposit_eur: float) -> dict:
    rental = round(tariff_per_hour * hours, 2)
    return {"rental": rental, "deposit": deposit_eur, "total": round(rental + deposit_eur, 2)}
