from decimal import Decimal
from material.models.edgeband import EdgeBand

def resolve_edgebands_for_material(material):
    T = Decimal(material.thickness_value)

    # 1. Filter using the parent's depth
    whitelisted = EdgeBand.objects.filter(
        edgeband_name__depth__gte=T,
        edgeband_name__depth__lte=T + 5,
        tenant=material.tenant
    )

    if not whitelisted.exists():
        return whitelisted.none(), None

    # 2. Order by: 
    # Width (parent depth) -> Gauge (thickness) -> Price (sell_price)
    default = (
        whitelisted
        .order_by(
            'edgeband_name__depth', 
            'thickness',      # Changed from e_thickness to thickness
            'sell_price'
        )
        .first()
    )

    return whitelisted, default
