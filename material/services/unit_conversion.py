from decimal import Decimal, InvalidOperation
from material.models import MeasurementUnit


class UnitConversionError(Exception):
    pass


class UnitConversionService:
    """
    Centralized measurement unit conversion service.
    Works across SI, Imperial and Custom units.
    """

    @staticmethod
    def to_base(value, unit: MeasurementUnit) -> Decimal:
        """
        Convert a value to its base unit.
        """
        try:
            value = Decimal(value)
        except (TypeError, InvalidOperation):
            raise UnitConversionError(f"Invalid value: {value}")

        if unit.factor is None:
            raise UnitConversionError(f"Unit {unit.code} has no factor defined")

        return value * unit.factor

    @staticmethod
    def convert(value, from_unit: MeasurementUnit, to_unit: MeasurementUnit) -> Decimal:
        """
        Convert value from one MeasurementUnit to another.
        """

        if from_unit.system != to_unit.system:
            raise UnitConversionError(
                f"Cross system conversion not allowed: {from_unit.system} → {to_unit.system}"
            )

        value_in_base = UnitConversionService.to_base(value, from_unit)

        if to_unit.factor is None or to_unit.factor == 0:
            raise UnitConversionError(f"Invalid target unit factor: {to_unit.code}")

        return (value_in_base / to_unit.factor).quantize(Decimal("0.0001"))

    @staticmethod
    def normalize_to_base(value, unit: MeasurementUnit):
        """
        Normalize value to base unit and return (value, base_unit)
        """
        base_unit = unit.base_unit or unit
        normalized_value = UnitConversionService.to_base(value, unit)
        return normalized_value, base_unit
