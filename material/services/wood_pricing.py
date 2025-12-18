from decimal import Decimal, InvalidOperation
from material.models import MeasurementUnit, BillingUnit
from material.services.unit_conversion import UnitConversionService


class WoodPricingError(Exception):
    pass


class WoodPricingService:
    """
    Handles wood material pricing logic:
    PANEL ⇄ SFT using physical area.
    """

    @staticmethod
    def area_in_sft(length_value, length_unit: MeasurementUnit,
                    width_value, width_unit: MeasurementUnit):
        """
        Converts length & width to square feet.
        """

        try:
            length_value = Decimal(length_value)
            width_value = Decimal(width_value)
        except (TypeError, InvalidOperation):
            raise WoodPricingError("Invalid length or width value")

        # convert to meters
        length_m = UnitConversionService.to_base(
            length_value, length_unit
        )
        width_m = UnitConversionService.to_base(
            width_value, width_unit
        )

        # meter → feet
        meter_to_feet = Decimal("3.28084")
        length_ft = length_m * meter_to_feet
        width_ft = width_m * meter_to_feet

        area_sft = length_ft * width_ft

        if area_sft <= 0:
            raise WoodPricingError("Invalid area calculation")

        return area_sft.quantize(Decimal("0.0001"))

    # -------------------------
    # COST PRICE
    # -------------------------

    @staticmethod
    def cost_price_per_sft(wood):
        """
        Returns cost price per SFT (calculated if needed).
        """

        if wood.cost_unit.code == "SFT":
            return wood.cost_price

        if wood.cost_unit.code == "PANEL":
            area = WoodPricingService.area_in_sft(
                wood.length_value, wood.length_unit,
                wood.width_value, wood.width_unit
            )
            return (wood.cost_price / area).quantize(Decimal("0.01"))

        raise WoodPricingError(
            f"Unsupported cost billing unit {wood.cost_unit.code}"
        )

    @staticmethod
    def cost_price_per_panel(wood):
        """
        Returns cost price per PANEL.
        """

        if wood.cost_unit.code == "PANEL":
            return wood.cost_price

        if wood.cost_unit.code == "SFT":
            area = WoodPricingService.area_in_sft(
                wood.length_value, wood.length_unit,
                wood.width_value, wood.width_unit
            )
            return (wood.cost_price * area).quantize(Decimal("0.01"))

        raise WoodPricingError(
            f"Unsupported cost billing unit {wood.cost_unit.code}"
        )

    # -------------------------
    # SELL PRICE
    # -------------------------

    @staticmethod
    def sell_price_per_sft(wood):
        if wood.sell_unit.code == "SFT":
            return wood.sell_price

        if wood.sell_unit.code == "PANEL":
            area = WoodPricingService.area_in_sft(
                wood.length_value, wood.length_unit,
                wood.width_value, wood.width_unit
            )
            return (wood.sell_price / area).quantize(Decimal("0.01"))

        raise WoodPricingError(
            f"Unsupported sell billing unit {wood.sell_unit.code}"
        )

    @staticmethod
    def sell_price_per_panel(wood):
        if wood.sell_unit.code == "PANEL":
            return wood.sell_price

        if wood.sell_unit.code == "SFT":
            area = WoodPricingService.area_in_sft(
                wood.length_value, wood.length_unit,
                wood.width_value, wood.width_unit
            )
            return (wood.sell_price * area).quantize(Decimal("0.01"))

        raise WoodPricingError(
            f"Unsupported sell billing unit {wood.sell_unit.code}"
        )
