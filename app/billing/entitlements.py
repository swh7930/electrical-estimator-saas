from typing import List
from flask import current_app

# Canonical feature keys
PRO_ENTITLEMENTS: List[str] = [
    "exports.pdf",
    "exports.csv",
    "assemblies.core",
    "libraries.manage",
    "customers.crud",
    "billing.portal",
]

ELITE_ENTITLEMENTS: List[str] = PRO_ENTITLEMENTS + [
    "assemblies.advanced",
    "priority.support",
    # future: "bluebeam.link", "team.roles", etc.
]

def resolve_entitlements(*, product_id: str | None, price_id: str | None) -> List[str]:
    """
    Determine entitlements from Stripe product/price.
    We deliberately key off known Price IDs in config to avoid brittle conditionals.
    """
    cfg = current_app.config

    pro_prices = {
        cfg.get("STRIPE_PRICE_PRO_MONTHLY"),
        cfg.get("STRIPE_PRICE_PRO_ANNUAL"),
    }
    elite_prices = {
        cfg.get("STRIPE_PRICE_ELITE_MONTHLY"),
        cfg.get("STRIPE_PRICE_ELITE_ANNUAL"),
    }

    if price_id in elite_prices:
        return ELITE_ENTITLEMENTS
    if price_id in pro_prices:
        return PRO_ENTITLEMENTS
    return []
