from decimal import Decimal
from rest_framework import serializers
from quoting.models import QuoteRequest


class QuotePDFSerializer(serializers.ModelSerializer):
    solutions = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = QuoteRequest
        fields = [
            "quote_number",
            "customer_display_name",
            "created_at",
            "total_cp",
            "total_sp",
            "tax_amount",
            "shipping_charges",
            "grand_total",
            "solutions",
        ]

    def get_tax_amount(self, obj):
        return (
            obj.total_sp * (obj.tax_percentage / Decimal("100"))
        ).quantize(Decimal("1.00"))

    def get_grand_total(self, obj):
        return (
            obj.total_sp
            + self.get_tax_amount(obj)
            + (obj.shipping_charges or Decimal("0.00"))
        )

    def get_solutions(self, obj):
        return [
            {
                "name": sol.name,
                "total_cp": sol.total_cp,
                "total_sp": sol.total_sp,
                "products": [
                    {
                        "product": p.product_template.name,
                        "dimensions": {
                            "L": p.length_mm,
                            "W": p.width_mm,
                            "H": p.height_mm,
                        },
                        "quantity": p.quantity,
                        "total_cp": p.total_cp,
                        "total_sp": p.total_sp,
                        "parts": [
                            {
                                "part": part.part_name,
                                "dimensions": {
                                    "L": part.length_mm,
                                    "W": part.width_mm,
                                    "T": part.thickness_mm,
                                },
                                "material": (
                                    part.material.name if part.material else None
                                ),
                                "quantity": part.part_qty,
                                "total_cp": part.total_part_cp,
                                "total_sp": part.total_part_sp,
                                "hardware": [
                                    {
                                        "name": hw.hardware.name,
                                        "qty": hw.quantity,
                                        "total_sp": hw.total_sp,
                                    }
                                    for hw in part.hardware.all()
                                ],
                            }
                            for part in p.parts.all()
                        ],
                    }
                    for p in sol.products.all()
                ],
            }
            for sol in obj.solutions.all()
        ]
