DEFAULT_DELIVERY_CHARGES = 215.0
DEFAULT_MARGIN_PERCENT = 25.0
COMPARE_AT_MULTIPLIER = 2.0


def get_default_price_adjustments(
    markaz_price,
    delivery_charges=None,
    margin_percent=None,
):
    """Return (variant_adjustment, compare_at_adjustment) for a Markaz price.

    Sale price = (Markaz + Delivery) × (1 + Margin%)
    Compare-at = Markaz × 2

    Adjustments are stored relative to Markaz so existing CSV/publish code
    (final = Markaz + adjustment) keeps working.
    """
    price = float(markaz_price or 0)
    delivery = float(
        DEFAULT_DELIVERY_CHARGES if delivery_charges is None else delivery_charges
    )
    margin = float(
        DEFAULT_MARGIN_PERCENT if margin_percent is None else margin_percent
    )

    sale_price = round((price + delivery) * (1 + margin / 100.0), 2)
    compare_at_price = round(price * COMPARE_AT_MULTIPLIER, 2)

    variant_adjustment = round(sale_price - price, 2)
    compare_at_adjustment = round(compare_at_price - price, 2)
    return variant_adjustment, compare_at_adjustment


def compute_final_prices(markaz_price, delivery_charges=None, margin_percent=None):
    """Return (sale_price, compare_at_price) using the current formula."""
    price = float(markaz_price or 0)
    variant_adj, compare_adj = get_default_price_adjustments(
        price,
        delivery_charges=delivery_charges,
        margin_percent=margin_percent,
    )
    return round(price + variant_adj, 2), round(price + compare_adj, 2)
