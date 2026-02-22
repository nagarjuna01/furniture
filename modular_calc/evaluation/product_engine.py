from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from modular_calc.evaluation.geometry_validator import GeometryValidator, GeometryValidationError
from .bom_builder import BOMBuilder
from .cost_calculator import CostCalculator
from modular_calc.evaluation.cutlist_optimizer import PartRect, CutlistOptimizer
from .pricing_resolver import PricingResolver
from .context import ProductContext

class ProductEngine:
    def __init__(self, engine_payload: Dict[str, Any]):
        self.product = engine_payload.get("product")
        self.product_dims = engine_payload.get("product_dims", {})
        self.parameters = engine_payload.get("parameters", {})
        self.quantities = engine_payload.get("quantities", [1])
        self.selected_material = engine_payload.get("selected_material")
        self.material_selections = engine_payload.get("material_selections", {})
        if not self.selected_material:
            raise ValueError("[ENGINE_FATAL] No material selected. Tier 5 requires explicit material context.")
        
        # Material-driven defaults for the main product (if applicable)
        # self.sheet_price: Decimal | None = engine_payload.get("sheet_price")
        if self.selected_material:
            self.sheet_length = Decimal(str(self.selected_material.length_mm))
            self.sheet_width = Decimal(str(self.selected_material.width_mm))
            self.sheet_thickness = Decimal(str(self.selected_material.thickness_mm))
            self.sheet_price = Decimal(str(self.selected_material.sell_price_panel))
            

        self.bom: Dict | None = None
        self.cutlist: Dict | None = None
        self.pricing: Dict | None = None

    def run(self) -> Dict[str, Any]:
        """Executes the full product evaluation pipeline."""
        self._build_bom()
        self._validate_geometry()
        self._optimize_cutlist()
        self._resolve_pricing()
        return self._build_response()

    def _build_bom(self) -> None:
        total_qty = int(self.quantities[0]) if self.quantities else 1
        pc = ProductContext(product_dims=self.product_dims,parameters=self.parameters )
        part_templates = self.product.part_templates.all().prefetch_related('material_whitelist__material')
        for pt in part_templates:
            mat_id = self.material_selections.get(pt.id)
            mw = None
            if mat_id:
                mw = pt.material_whitelist.filter(material_id=mat_id).first()
            if not mw:
                mw = pt.material_whitelist.filter(is_default=True).first() or \
                     pt.material_whitelist.first()
            if mw and mw.material:
                val = float(mw.material.thickness_value or 0)
                pc.inject_material_thickness(pt.name, val)
        full_context = pc.get_context() 
        builder = BOMBuilder(
            product=self.product,
            product_dims=self.product_dims,
            parameters=full_context, # Pass the resolved dict here
            material_selections=self.material_selections,
            
            stateful_context=pc,
            quantity=total_qty 
        )
        try:
            
            self.bom = builder.build_bom()
        except Exception as e:
                # This will bubble up the NameError (e.g., "Missing variable: side_panel_length")
            raise ValueError(f"BOM Builder failed: {str(e)} | Available keys: {list(full_context.keys())}")
        if not self.bom.get("parts"):
            raise ValueError(f"BOM Generation Failed for {self.product.name}. Check equations.")
    def _validate_geometry(self) -> None:
        if not getattr(self, "bom", None):
            raise ValueError("Cannot validate geometry: BOM not built yet.")
        raw_parts = self.bom.get("parts", [])
        if not raw_parts:
            return
        normalized_parts = []
        for p in raw_parts:
            finished = p.get("finished_dims", {})
            cutting = p.get("cutting_dims", {})

            # We normalize to Decimal for strict validation
            normalized_parts.append({
                "name": p.get("name", "Unknown"),
                "net_length": Decimal(str(finished.get("l", 0))),
                "net_width": Decimal(str(finished.get("w", 0))),
                "cut_length": Decimal(str(cutting.get("l", finished.get("l", 0)))),
                "cut_width": Decimal(str(cutting.get("w", finished.get("w", 0)))),
                "quantity": Decimal(str(p.get("quantity"))),
                "shape_type": p.get("shape_type", "RECT"),
                "p1": Decimal(str(p.get("p1", 0))),
                "p2": Decimal(str(p.get("p2", 0))),
            })
        
        GeometryValidator.validate_parts(normalized_parts)
    def _optimize_cutlist(self) -> None:
        raw_parts = self.bom.get("parts", []) if self.bom else []
        total_order_qty = int(self.quantities[0]) if self.quantities else 1
        
        if not raw_parts:
            self.cutlist = {"total_sheets": 0, "sheets": []}
            return

        part_rects = []
        for p in raw_parts:
            total_parts_to_cut = int(p.get("quantity")) 
            
            # 1. DRILL INTO NESTED DICTS (Matches your BOMBuilder structure)
            c_dims = p.get("cutting_dims", {})
            f_dims = p.get("finished_dims", {})

            # 2. RESOLVE RAW VALUES (PRIORITY: CUTTING -> FINISHED)
            # We extract the value first to avoid Decimal(str(None))
            raw_w = c_dims.get("w") or f_dims.get("w") or p.get("width")
            raw_h = c_dims.get("l") or f_dims.get("l") or p.get("length")

            # 3. NO SILENT KILLERS: RAISE EXPLICIT ERROR IF DATA IS MISSING
            if raw_w is None or raw_h is None:
                raise ValueError(f"Data Integrity Error: Part '{p.get('name')}' has no valid width or length.")

            part_rects.append(
                PartRect(
                    name=str(p.get("name")),
                    # 4. SAFE CASTING
                    width=Decimal(str(raw_w)),
                    height=Decimal(str(raw_h)),
                    quantity=total_parts_to_cut,
                    grain=str(p.get("grain", {}).get("direction", "none")), # Updated for your nested grain dict
                    material_id=self.selected_material.id,
                    sheet_width=self.sheet_width,
                    sheet_height=self.sheet_length,
                )
            )
        
        optimizer = CutlistOptimizer(kerf_mm=3.0)
        self.cutlist = optimizer.optimize(part_rects)

    def _resolve_pricing(self) -> None:
        total_qty = int(self.quantities[0]) if self.quantities else 1
        
        # TRACE 1: Context Verification
        print(f"\n[ENGINE_TRACE] Starting Pricing Phase...")
        print(f" > Sheets from Cutlist: {self.cutlist.get('total_sheets', 'MISSING')}")
        print(f" > Sheet Price Input: {self.sheet_price}")
        print(f" > Batch Quantity: {total_qty}")

        pricing_resolver = PricingResolver(
            bom=self.bom,
            cost_calculator=CostCalculator(self.bom),
            cutlist=self.cutlist,
            sheet_price=self.sheet_price,
            quantity=total_qty
        )

        # TRACE 2: Execution
        self.pricing = pricing_resolver.resolve()

        # KILLER CHECK: Validate structure and values
        recommended = self.pricing.get('recommended')
        options = self.pricing.get('pricing_options', {})
        
        if not recommended or not options:
            print(f"!!! CRITICAL ERROR: PricingResolver returned empty structure: {self.pricing}")
            raise ValueError("[PRICING_NULL] Engine failed to generate pricing options.")

        final_sp = options.get(recommended, {}).get('sp', 0)

        # TRACE 3: Final Integrity Check
        if final_sp <= 0:
            print(f"!!! SILENT KILLER DETECTED: SP is {final_sp} !!!")
            print(f" > Raw Data Dump: {options.get(recommended)}")
            # We raise a ValueError to prevent a 0-value quote from ever reaching the DB
            raise ValueError(f"Integrity Failure: {self.product.name} calculated at 0.00. Check Material Prices.")
        
        
    def _build_response(self) -> Dict[str, Any]:
        return {
            "product": {
                "id": getattr(self.product, "id", None),
                "name": getattr(self.product, "name", None),
            },
            "bom": self.bom,
            "cutlist": self.cutlist,
            "pricing": self.pricing,
            "material_info": {
                "sheet_length": float(self.sheet_length),
                "sheet_width": float(self.sheet_width),
                "sheet_price": float(self.sheet_price),
                "material_name": getattr(self.selected_material, "name", "Default")
            }
        }