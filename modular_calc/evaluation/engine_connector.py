# # modular_calc/evaluation/engine_connector.py
# from typing import List, Dict
# from decimal import Decimal
# from .cutlist_optimizer import CutlistOptimizer, PartRect

# class EngineConnector:
#     """
#     Bridges BOM parts to the Cutlist Optimizer.
#     Resolves sheet dimensions and runs material-wise nesting.
#     """
    
#     @staticmethod
#     def run_optimization(bom_parts: List[Dict], kerf: float = 3.0) -> Dict:
#         optimizer = CutlistOptimizer(kerf_mm=kerf)
#         rects_to_optimize = []

#         # 1. Map BOM parts to PartRects
#         for part in bom_parts:
#             # NO SILENT KILLER: Ensure material_id exists
#             m_id = part.get("material_id")
#             if not m_id:
#                 continue # Or raise error if strict integrity is needed

#             # We need to fetch sheet dimensions (Usually passed in context or fetched here)
#             # For this logic, we assume the BOM already has raw sheet dims from material resolution
#             rects_to_optimize.append(PartRect(
#                 width=Decimal(str(part["cutting_dims"]["w"])),
#                 height=Decimal(str(part["cutting_dims"]["l"])),
#                 quantity=int(part["quantity"]),
#                 name=part["name"],
#                 grain=part["grain"]["direction"],
#                 material_id=m_id,
#                 sheet_width=Decimal(str(part.get("sheet_w", 2440))), # Fallback to standard 8x4
#                 sheet_height=Decimal(str(part.get("sheet_l", 1220))),
#                 trim_mm=Decimal("10.0")
#             ))

#         # 2. Execute Math
#         return optimizer.optimize(rects_to_optimize)