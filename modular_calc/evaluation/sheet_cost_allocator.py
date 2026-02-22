from decimal import Decimal


class SheetCostAllocator:
    """
    CP authority when sheet-based pricing is enabled.
    """

    def __init__(self, cutlist: dict, sheet_price: Decimal):
        self.cutlist = cutlist
        self.sheet_price = sheet_price

    def allocate(self) -> dict:
        total_sheets = Decimal(str(self.cutlist["total_sheets"]))
        total_cp = total_sheets * self.sheet_price

        return {
            "total_sheets": total_sheets,
            "total_sheet_cp": total_cp.quantize(Decimal("1.00")),
            "waste_percent": self.cutlist.get("total_waste_percent", Decimal("0")),
        }
