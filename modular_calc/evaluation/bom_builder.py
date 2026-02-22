from typing import Dict, List, Optional, Any
from decimal import Decimal
from .part_evaluator import PartEvaluator
from .hardware_evaluator import HardwareEvaluator
from .context import ExpressionContext
from material.services.wood_pricing import WoodPricingService
from material.services.unit_conversion import UnitConversionService
from material.models.units import MeasurementUnit
from material.models.edgeband import EdgeBand
class BOMBuilder:
    """
    Generate full BOM. Separates technical quantity from financial calculations.
    """

    def __init__(self, product,product_dims: Dict[str, Decimal], parameters: Dict[str, Decimal],quantity: int, material_id: Optional[int] = None,
        material_selections: Optional[Dict] = None,stateful_context: Optional[Any] = None,**kwargs):
        if quantity < 1:
            raise ValueError("[BOM_FATAL] Invalid Quantity: Handshake requires at least 1 unit.")
        self.product = product
        self.product_dims = product_dims
        self.parameters = parameters
        self.selected_material_id = material_id
        self.material_selections = material_selections or {}
        self.eb_map = self._build_edgeband_price_map()
        self.stateful_context = stateful_context
        self.quantity = Decimal(str(quantity))
        
        self.kerf = Decimal("4.0")   # Saw blade width
        self.trim = Decimal("10.0")

    def build_bom(self) -> Dict:
        """The Main Orchestrator called by ProductEngine."""
        
        parts = self.build_parts()
        hardware_items = self.build_hardware(parts_list=parts)

        # Use Decimal("0") as seed to avoid float/decimal mixing
        total_cp = sum([Decimal(str(p["cp"])) for p in parts], Decimal("0")) 
        total_sp = sum([Decimal(str(p["sp"])) for p in parts], Decimal("0")) 
        max_discount = sum((Decimal(str(p.get('max_discount', 0))) for p in parts), Decimal("0"))
        
        return {
            "product_name": self.product.name,
            "parts": parts,
            "hardware": hardware_items,
            "total_cp": total_cp.quantize(Decimal("1.00")),
            "total_sp": total_sp.quantize(Decimal("1.00")),
            "max_discount": max_discount.quantize(Decimal("1.00")),
        }
    def _get_effective_material(self, part_template, material_id: Optional[int]):
        """Helper to get the actual material object for a part."""
        query = part_template.material_whitelist.select_related('material')
        if material_id:
            link = query.filter(material_id=material_id).first()
        else:
            link = query.filter(is_default=True).first()
        return link.material if link else None
    def _build_edgeband_price_map(self):
        """
        Build a dictionary:
        {
            edgeband_id: {
                "cost_price": Decimal,
                "sell_price": Decimal
            }
        }
        """

        eb_map = {}
        
        # You may filter by tenant if required
        edgebands = EdgeBand.objects.filter(
            tenant=self.product.tenant,
            is_active=True
        )

        for eb in edgebands:
            eb_map[eb.id] = {
                "cost_price": Decimal(str(eb.cost_price)),
                "sell_price": Decimal(str(eb.sell_price)),
            }

        return eb_map
    def build_parts(self) -> List[Dict]:
        parts = []
        all_templates = list(self.product.part_templates.all().order_by('id')) 
        exp_engine = ExpressionContext(self.stateful_context.get_context())
        batch_multiplier = self.quantity
        for part_template in all_templates:
            
            try:
                for key, value in self.stateful_context.get_context().items():
                    exp_engine.update_context(key, value)
                # 1. MATERIAL TAG RESOLUTION
                tag = getattr(part_template, 'material_tag', 'carcass')
                selected_material_id = self.material_selections.get(tag) or self.material_selections.get('default')
                material_obj = self._get_effective_material(part_template, selected_material_id)
                
                # 2. EVALUATE GEOMETRY (Finished Size)
                f_length = Decimal(str(exp_engine.evaluate(part_template.part_length_equation)))
                f_width = Decimal(str(exp_engine.evaluate(part_template.part_width_equation)))
                local_qty = Decimal(str(exp_engine.evaluate(part_template.part_qty_equation )))
                total_batch_qty = local_qty * batch_multiplier

                # 3. EDGEBAND DEDUCTION (The Offset Killer)
                # If we have 2mm EB, the cut must be 4mm smaller to reach the finished size
                eb_mat_id = self.material_selections.get(f"eb_{tag}")
                eb_obj = self._get_effective_material(part_template, eb_mat_id)
                eb_thickness = Decimal(str(getattr(eb_obj, 'thickness_mm', 0)))
                deduct_l = Decimal("0")
                if getattr(part_template, 'eb_top', False): deduct_l += eb_thickness
                if getattr(part_template, 'eb_bottom', False): deduct_l += eb_thickness
                deduct_w = Decimal("0")
                if getattr(part_template, 'eb_left', False): deduct_w += eb_thickness
                if getattr(part_template, 'eb_right', False): deduct_w += eb_thickness

                cut_l = f_length - deduct_l
                cut_w = f_width - deduct_w

                # 4. SKU & METADATA
                part_sku = f"{self.product.id}-{part_template.id}-{tag[:3].upper()}"
                mat_grain_code = getattr(material_obj, 'grain', 'NONE')
                has_grain_effect = mat_grain_code != "NONE"
                part_data = {
                    "sku": part_sku,
                    "name": part_template.name,
                    "material_id": material_obj.id if material_obj else None,
                    "tag": tag,
                    "finished_dims": {"l": float(f_length), "w": float(f_width)},
                    "cutting_dims": {"l": float(cut_l), "w": float(cut_w)},
                    "unit_qty": float(local_qty),
                    "quantity": float(total_batch_qty),

                    # "running_metrics": {
                    #     # LABOR_MODEL_HOOK: Total perimeter to be cut by saw/CNC
                    #     "total_cut_mm": float(running_feet_cutting * qty),
                    #     # LABOR_MODEL_HOOK: Total edge length to be processed by edgebander
                    #     "total_eb_mm": float(self._calculate_eb_linear_mm(part_template, f_length, f_width) * qty)
                    # },
                    "grain": {
                        "has_grain": has_grain_effect,
                        "direction": mat_grain_code,
                        "can_rotate": not has_grain_effect
                    }
                }

                # 5. FINANCIALS (Use Finished Area for Sales, but track Cutting Area for Waste)
                mat_cost = self._compute_material_cost(part_template, part_data, material_obj)
                eb_cost = self._compute_edgeband_cost(part_template, part_data['finished_dims']['l'], part_data['finished_dims']['w'], part_data['quantity'])
                hw_cost = self._compute_hardware_cost(part_template, total_batch_qty)
                
                pricing = self._compute_prices(part_data, mat_cost, eb_cost, hw_cost)
                part_data.update({
                    "material_cost": mat_cost,
                    "edgeband_cost": eb_cost,
                    "hardware_cost": hw_cost,
                    **pricing
                })
                
                parts.append(part_data)
                self.stateful_context.update_calculated_part(part_template.name, f_length, f_width)

            except Exception as e:
                raise ValueError(f"[BOM_FATAL] Error on {part_template.name}: {str(e)}")
              
        return parts

    def _calculate_eb_linear_mm(self, part_template, length: Decimal, width: Decimal) -> Decimal:
        total = Decimal("0")
        if getattr(part_template, 'eb_top', False): total += width
        if getattr(part_template, 'eb_bottom', False): total += width
        if getattr(part_template, 'eb_left', False): total += length
        if getattr(part_template, 'eb_right', False): total += length
        return total
    
    def _get_asset_url(self, part_template, field_name):
        for obj in [part_template, self.product]:
            field = getattr(obj, field_name, None)
            if field and hasattr(field, 'url'):
                try:
                    return field.url
                except ValueError:
                    continue
            elif field and isinstance(field, str):
                return field
        return None

    def build_hardware(self, parts_list: List[Dict] = None) -> List[Dict]:
        hardware_items = []
        product_context = {**self.product_dims, **self.parameters}

        for rule in self.product.hardware_rules.all():
            evaluator = HardwareEvaluator(rule, product_context)
            tech_data = evaluator.evaluate()
            if tech_data:
                hardware_items.append(self._format_hardware_item(tech_data))

        if parts_list:
            parts_map = {p.get("template_id"): p for p in parts_list}
            for pt in self.product.part_templates.all():
                part_data = parts_map.get(pt.id)
                if not part_data: continue
                
                part_context = {**product_context, **part_data}
                for rule in pt.hardware_rules.all():
                    evaluator = HardwareEvaluator(rule, part_context)
                    tech_data = evaluator.evaluate()
                    if tech_data:
                        hardware_items.append(self._format_hardware_item(tech_data))
        
        return hardware_items

    def _format_hardware_item(self, tech_data: Dict) -> Dict:
        hw = tech_data["hardware_obj"]
        qty = tech_data["quantity"]
        return {
            "name": hw.h_name,
            "quantity": qty,
            "cp": (Decimal(str(qty)) * hw.cost_price).quantize(Decimal("1.00")),
            "sp": (Decimal(str(qty)) * hw.sell_price).quantize(Decimal("1.00")),
        }

    def _compute_material_cost(self, part_template, part_data: Dict, mat: Optional[Any]) -> Dict[str, Decimal]:
        """
        Tier 5 Financial Logic: Calculates cost via area ratio using unit-normalized dimensions.
        """
        if not mat:
            
            # Avoid crashing the engine if a material is missing; return zeroed costs.
            return {"cp": Decimal("0.00"), "sp": Decimal("0.00")}

        # 1. Component Data (Already in MM from Evaluator)
        c_len = Decimal(str(part_data["finished_dims"]["l"]))
        c_wid = Decimal(str(part_data["finished_dims"]["w"]))
        c_qty = Decimal(str(part_data["quantity"]))
        comp_total_area_mm2 = c_len * c_wid * c_qty
        

        # 2. Master Sheet Dimensions resolution to MM
        # We pull raw values from model and convert to MM via Service
        try:
            mm_unit = MeasurementUnit.objects.get(code="MM")
            m_len = Decimal(str(UnitConversionService.convert(
                value=mat.length_value, from_unit=mat.length_unit, to_unit=mm_unit
            )))
            m_wid = Decimal(str(UnitConversionService.convert(
                value=mat.width_value, from_unit=mat.width_unit, to_unit=mm_unit
            )))
        except Exception:
            # Fallback to raw values if conversion fails (Assuming DB is MM as verified)
            m_len = Decimal(str(getattr(mat, "length_value", 0)))
            m_wid = Decimal(str(getattr(mat, "width_value", 0)))
        
        if m_len <= 0 or m_wid <= 0:
            
            return {"cp": Decimal("0.00"), "sp": Decimal("0.00")}

        sheet_area_mm2 = m_len * m_wid

        # 3. Rate Extraction & Ratio
        m_cp = Decimal(str(getattr(mat, "cost_price", 0)))
        m_sp = Decimal(str(getattr(mat, "sell_price", 0)))

        # Ratio is unit-agnostic as both numerator and denominator are now MM^2
        area_ratio = comp_total_area_mm2 / sheet_area_mm2
        
        return {
            "cp": (area_ratio * m_cp).quantize(Decimal("0.01")),
            "sp": (area_ratio * m_sp).quantize(Decimal("0.01"))
        }

    
    from decimal import Decimal


    def _compute_edgeband_cost(self, part_template, finished_l, finished_w, total_qty):
        """
        Compute edgeband cost per side using:
        - Selected material (wood_id)
        - Selected EB from payload (eb_id) if valid
        - Fallback to default EB
        - Side-based geometry
        """

        fin = {
            "cp": Decimal("0.00"),
            "sp": Decimal("0.00"),
            "mm": Decimal("0.00"),
        }

        qty = Decimal(str(total_qty))
        l = Decimal(str(finished_l))
        w = Decimal(str(finished_w))

        # 1️⃣ Resolve selected material
        material_id = getattr(self, "selected_material_id", None)

        whitelist = part_template.material_whitelist.all()

        material_entry = None

        # Payload material
        if material_id:
            material_entry = whitelist.filter(material_id=material_id).first()

        # Fallback to default material
        if not material_entry:
            material_entry = whitelist.filter(is_default=True).first()

        if not material_entry:
            return fin  # No material = no EB

        # 2️⃣ Resolve edgeband entry
        eb_whitelist = material_entry.edgeband_options.all()

        selected_eb_id = getattr(self, "selected_eb_id", None)

        eb_entry = None

        # Payload EB (only if whitelisted)
        if selected_eb_id:
            eb_entry = eb_whitelist.filter(edgeband_id=selected_eb_id).first()

        # Fallback to default EB
        if not eb_entry:
            eb_entry = eb_whitelist.filter(is_default=True).first()

        if not eb_entry:
            return fin  # No EB applied

        eb_id = eb_entry.edgeband_id
        pricing = self.eb_map.get(eb_id)

        if not pricing:
            return fin

        # 3️⃣ Apply side-based EB
        side = eb_entry.side.lower()

        if side in ["top", "bottom"]:
            length_mm = l
        elif side in ["left", "right"]:
            length_mm = w
        else:
            return fin

        length_m = length_mm / Decimal("1000")

        fin["cp"] += length_m * pricing["cost_price"] * qty
        fin["sp"] += length_m * pricing["sell_price"] * qty
        fin["mm"] += length_mm * qty

       

        return fin


    def _compute_hardware_cost(self, part_template, total_qty: Decimal) -> Dict[str, Decimal]:
        fin = {"cp": Decimal("0"), "sp": Decimal("0")}
        for rule in part_template.hardware_rules.select_related('hardware').all():
            evaluator = HardwareEvaluator(rule, {**self.product_dims, **self.parameters})
            tech_data = evaluator.evaluate()
            if tech_data:
                # You defined this...
                final_hw_qty = Decimal(str(tech_data["quantity"])) * total_qty
                hw = tech_data["hardware_obj"]
                
                # ...but you were calling 'qty' here. Corrected to 'final_hw_qty':
                fin["cp"] += final_hw_qty * hw.cost_price
                fin["sp"] += final_hw_qty * hw.sell_price
                
                
                
        return {k: v.quantize(Decimal("1.00")) for k, v in fin.items()}

    def _compute_prices(self, part_data: Dict, mat: Dict, eb: Dict, hw: Dict) -> Dict[str, Decimal]:
        cp = mat["cp"] + eb["cp"] + hw["cp"]
        sp = mat["sp"] + eb["sp"] + hw["sp"]
        floor = cp * Decimal("1.20")
        max_discount = max(Decimal("0"), sp - floor)
        

        return {
            "cp": cp.quantize(Decimal("1.00")),
            "sp": sp.quantize(Decimal("1.00")),
            "max_discount": max_discount.quantize(Decimal("1.00")),
        }

    def _clean_for_json(self, data):
        if isinstance(data, dict):
            return {
                k: self._clean_for_json(v) 
                for k, v in data.items() 
                if not hasattr(v, '_meta')
            }
        elif isinstance(data, list):
            return [self._clean_for_json(i) for i in data]
        elif isinstance(data, Decimal):
            return float(data)
        return data