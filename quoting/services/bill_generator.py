class QuoteDetailCollector:
    def __init__(self, quote):
        self.quote = quote

    def get_bill_elements(self):
        elements = []

        # 1. Collect Standard Products (Path A)
        for item in self.quote.items.all():
            elements.append({
                'type': 'STANDARD',
                'name': item.variant.sku,
                'description': f"Size: {item.variant.width}x{item.variant.height}",
                'quantity': item.quantity,
                'unit_price': item.unit_sp,
                'total': item.line_total_sp,
                'image': item.variant.images.first().image.url if item.variant.images.exists() else None
            })

        # 2. Collect Modular Solutions (Path B)
        for solution in self.quote.solutions.all():
            for q_prod in solution.products.all():
                # The "Cylinder" logic: Collect all materials as a description string
                materials = ", ".join([f"{p.part_name} ({p.quantity})" for p in q_prod.parts.all()])
                
                elements.append({
                    'type': 'MODULAR',
                    'name': q_prod.product_name,
                    'description': materials, # This is your List of Materials
                    'quantity': q_prod.quantity,
                    'unit_price': q_prod.total_sp / q_prod.quantity if q_prod.quantity else 0,
                    'total': q_prod.total_sp,
                    'image': None # Usually 3D renders go here
                })

        # 3. Add Labour & Service Charges
        if self.quote.labour_charges > 0:
            elements.append({
                'type': 'SERVICE',
                'name': 'Labour & Installation',
                'description': 'On-site assembly and fitting',
                'quantity': 1,
                'unit_price': self.quote.labour_charges,
                'total': self.quote.labour_charges,
                'image': None
            })

        return elements