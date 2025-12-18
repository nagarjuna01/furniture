from django.core.management.base import BaseCommand
from standprod.models import MeasurementUnit

UNITS = [
    # LENGTH (base: meter)
    ("Meter", "m", "SI", None, 1),
    ("Centimeter", "cm", "SI", "m", 0.01),
    ("Millimeter", "mm", "SI", "m", 0.001),
    ("Inch", "in", "IMPERIAL", "m", 0.0254),
    ("Foot", "ft", "IMPERIAL", "m", 0.3048),
]

class Command(BaseCommand):
    help = "Load system SI + Imperial measurement units"

    def handle(self, *args, **kwargs):
        unit_map = {}

        # First create base units
        for name, code, system, base_code, factor in UNITS:
            unit, _ = MeasurementUnit.objects.get_or_create(
                tenant=None,
                code=code,
                defaults={
                    "name": name,
                    "symbol": code,
                    "system": system,
                    "factor": factor,
                }
            )
            unit_map[code] = unit

        # Link base units
        for name, code, system, base_code, factor in UNITS:
            if base_code:
                unit = unit_map[code]
                unit.base_unit = unit_map.get(base_code)
                unit.factor = factor
                unit.save(update_fields=["base_unit", "factor"])

        self.stdout.write(self.style.SUCCESS("Measurement units loaded"))
