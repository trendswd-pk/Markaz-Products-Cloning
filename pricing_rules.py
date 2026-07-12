MARKAZ_PRICE_THRESHOLD = 2000
LOW_VARIANT_ADDITION = 500.0
HIGH_VARIANT_ADDITION = 1500.0
COMPARE_AT_EXTRA = 1500.0


def get_default_price_adjustments(markaz_price):
    """Return (variant_adjustment, compare_at_adjustment) for a Markaz price."""
    price = float(markaz_price or 0)
    if price < MARKAZ_PRICE_THRESHOLD:
        variant_adjustment = LOW_VARIANT_ADDITION
    else:
        variant_adjustment = HIGH_VARIANT_ADDITION

    compare_at_adjustment = variant_adjustment + COMPARE_AT_EXTRA
    return variant_adjustment, compare_at_adjustment
