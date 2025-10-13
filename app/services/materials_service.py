from app.models.material import Material
from app.extensions import db


def list_active_materials():
    """Return all active materials, ordered by type then description."""
    return (
        Material.query.filter_by(is_active=True)
        .order_by(Material.material_type, Material.item_description)
        .all()
    )
