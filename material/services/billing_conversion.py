from decimal import Decimal, InvalidOperation
from material.models import BillingUnit


class BillingConversionError(Exception):
    pass


class BillingConversionService:
    """
    Billing unit conversion service.
    Used for pricing, procurement, quotation & inventory.
    """

    @staticmethod
    def normalize_to_base(value, unit: BillingUnit):
        """
        Convert a billing value to its base unit.
        Example: 2 dozen → 24 pcs
        """
        try:
            value = Decimal(value)
        except (TypeError, InvalidOperation):
            raise BillingConversionError(f"Invalid value: {value}")

        if unit.factor is None or unit.factor <= 0:
            raise BillingConversionError(
                f"Invalid factor for billing unit {unit.code}"
            )

        base_value = value * unit.factor
        return base_value

    @staticmethod
    def convert(value, from_unit: BillingUnit, to_unit: BillingUnit):
        """
        Convert between billing units.
        Example: 24 pcs → 2 dozen
        """

        base_value = BillingConversionService.normalize_to_base(
            value, from_unit
        )

        if to_unit.factor is None or to_unit.factor <= 0:
            raise BillingConversionError(
                f"Invalid target unit factor {to_unit.code}"
            )

        return (base_value / to_unit.factor).quantize(Decimal("0.0001"))
