from partisoproduct.utils.quote_calculator import QuoteCalculator
from partisoproduct.models import QuotePartDetail

class QuoteRequestService:
    def __init__(self, quote):
        self.quote = quote
        self.calculator = QuoteCalculator(quote)

    def evaluate(self, material_map: dict, edge_map: dict):
        """
        material_map: {part_id: WoodEn instance}
        edge_map: {part_id: {"top": EdgeBand, "left": ..., ...}}
        """

        results = []

        for part in self.quote.modular_product.parts.all():
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
                edge_cost=Decimal('0.00'),  # Optional: break out edge cost separately
                total_cost=calc["pp"],      # You can expand this later with hardware etc.
            )

            results.append(part_detail)

        return results
