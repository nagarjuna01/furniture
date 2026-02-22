from partisoproduct.utils.quote_calculator import QuoteCalculator
from partisoproduct.models import QuotePartDetail
from decimal import Decimal

class MvpQuoteRequestService:
    def __init__(self, quote):
        self.quote = quote
        self.calculator = QuoteCalculator(quote)
        self.tenant = getattr(quote, "tenant", None)

    def evaluate(self, material_map: dict, edge_map: dict):
        results = []

        for part in self.quote.modular_product.parts.all():
            if getattr(part, "tenant", None) and part.tenant != self.tenant:
                raise ValueError(f"Part {part.id} belongs to a different tenant")

            selected_material = material_map.get(part.id)
            edge_dict = edge_map.get(part.id, {
                'top': part.part_edgematerial_top,
                'left': part.part_edgematerial_left,
                'right': part.part_edgematerial_right,
                'bottom': part.part_edgematerial_bottom,
            })

            calc = self.calculator.calculate_part(part, selected_material, edge_dict)

            part_detail = QuotePartDetail.objects.create(
                quote=self.quote,
                part_template=part,
                part_name=part.name,
                selected_material=selected_material,
                evaluated_dimensions={
                    "length": float(calc["length"]),
                    "width": float(calc["width"])
                },
                evaluated_qty=calc["quantity"],
                evaluated_area=calc["area_sft"],
                material_cost=calc["pp"],
                edge_cost=Decimal(calc.get("edge_cost", 0)),
                hardware_cost=Decimal(calc.get("hardware_cost", 0)),
                total_cost=Decimal(calc["pp"]) + Decimal(calc.get("edge_cost", 0)) + Decimal(calc.get("hardware_cost", 0)),
            )

            results.append(part_detail)

        return results

