from decimal import Decimal, ROUND_HALF_UP
from asteval import Interpreter
from material.models import WoodEn, EdgeBand

MM2_TO_SQFT = Decimal('0.0000107639')

def quantize(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class QuoteCalculator:
    def __init__(self, quote):
        self.quote = quote
        self.aeval = Interpreter()
        self.context = {
            "product_length": float(quote.length_mm),
            "product_width": float(quote.width_mm),
            "product_height": float(quote.height_mm),
        }
        for c in quote.modular_product.product_parameters.all():
            self.context[c.abbreviation] = float(c.value)

    def evaluate(self, expression):
        self.aeval.symtable.update(self.context)
        return self.aeval(expression)

    def calculate_part(self, part_template, selected_material: WoodEn, edges: dict):
        try:
            length = Decimal(self.evaluate(part_template.part_length_equation))
            width = Decimal(self.evaluate(part_template.part_width_equation))
            quantity = int(self.evaluate(part_template.part_qty_equation))
        except Exception:
            length, width, quantity = Decimal('0'), Decimal('0'), 0

        area_mm2 = length * width * quantity
        area_sft = area_mm2 * MM2_TO_SQFT

        # Material cost
        pp = area_sft * selected_material.purchase_price_sft
        sp = area_sft * selected_material.selling_price_sft

        # Edge Banding cost
        edge_cost_pp = Decimal('0')
        edge_cost_sp = Decimal('0')
        edge_lengths = {'top': length, 'bottom': length, 'left': width, 'right': width}

        for side, edge_band in edges.items():
            if edge_band:
                length_mm = edge_lengths[side]
                edge_cost_pp += length_mm * edge_band.cost_price_per_mm * quantity
                edge_cost_sp += length_mm * edge_band.sell_price_per_mm * quantity

        # Grooving
        grooving_cost = part_template.edge_band_grooving_cost * quantity

        # Total cost
        total_pp = pp + edge_cost_pp + grooving_cost
        total_sp = sp + edge_cost_sp + grooving_cost

        return {
            "length": length,
            "width": width,
            "quantity": quantity,
            "area_sft": area_sft.quantize(Decimal('0.0001')),
            "pp": quantize(total_pp),
            "sp": quantize(total_sp),
        }
