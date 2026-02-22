# cutlist_optimizer_tier5.py
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
# import matplotlib.pyplot as plt

@dataclass
class PartRect:
    width: Decimal
    height: Decimal
    quantity: int
    name: str
    grain: str
    material_id: int
    sheet_width: Decimal
    sheet_height: Decimal
    trim_mm: Decimal = Decimal("10.0")


@dataclass
class Sheet:
    width: Decimal
    height: Decimal
    material_id: int
    parts: List[Dict]
    used_area: Decimal = Decimal("0")
    raw_width: Decimal = Decimal("0")
    raw_height: Decimal = Decimal("0")

    def remaining_area(self) -> Decimal:
        return (self.width * self.height) - self.used_area


class CutlistOptimizer:

    def __init__(self, kerf_mm: float = 3.0):
        self.kerf = Decimal(str(kerf_mm))
        self.sheets: List[Sheet] = []

    def optimize(self, parts: List[PartRect], visualize: bool = True) -> Dict:
        """Main guillotine-based placement"""
        rects = []
        for p in parts:
            for _ in range(int(p.quantity)):
                rects.append({
                    "name": p.name,
                    "w": p.width,
                    "h": p.height,
                    "grain": p.grain,
                    "material_id": p.material_id,
                    "raw_w": p.sheet_width,
                    "raw_h": p.sheet_height,
                    "trim": p.trim_mm
                })

        # Sort descending by area for better guillotine packing
        rects.sort(key=lambda r: r["w"] * r["h"], reverse=True)

        for rect in rects:
            placed = False
            for sheet in self.sheets:
                if sheet.material_id == rect["material_id"]:
                    pos = self._guillotine_place(sheet, rect)
                    if pos:
                        placed = True
                        break

            if not placed:
                # Create a new sheet if needed
                new_sheet = Sheet(
                    width=rect["raw_w"] - 2 * rect["trim"],
                    height=rect["raw_h"] - 2 * rect["trim"],
                    material_id=rect["material_id"],
                    raw_width=rect["raw_w"],
                    raw_height=rect["raw_h"],
                    parts=[]
                )
                if not self._guillotine_place(new_sheet, rect):
                    raise ValueError(f"Part {rect['name']} too large for sheet")
                self.sheets.append(new_sheet)

        # Build material report
        report = self._build_report()
        # if visualize:
        #     self._draw_sheets()
        return report

    def _allowed_orientations(self, rect):
        if rect["grain"] == "none":
            return [(rect["w"], rect["h"]), (rect["h"], rect["w"])]
        elif rect["grain"] == "vertical":
            return [(rect["w"], rect["h"])]
        elif rect["grain"] == "horizontal":
            return [(rect["h"], rect["w"])]
        return [(rect["w"], rect["h"])]

    def _guillotine_place(self, sheet: Sheet, rect: Dict) -> Optional[Tuple[Decimal, Decimal]]:
        """Basic guillotine placement: top-left first"""
        # empty sheet
        if not sheet.parts:
            sheet.parts.append({
                "name": rect["name"], "x": Decimal(0), "y": Decimal(0),
                "w": rect["w"], "h": rect["h"], "grain": rect["grain"]
            })
            sheet.used_area += rect["w"] * rect["h"]
            return 0, 0

        # try existing free spaces (simplified)
        free_rects = self._compute_free_rects(sheet)
        for fx, fy, fw, fh in free_rects:
            for ow, oh in self._allowed_orientations(rect):
                if ow <= fw and oh <= fh:
                    sheet.parts.append({
                        "name": rect["name"], "x": fx, "y": fy,
                        "w": ow, "h": oh, "grain": rect["grain"]
                    })
                    sheet.used_area += ow * oh
                    return fx, fy
        return None

    def _compute_free_rects(self, sheet: Sheet) -> List[Tuple[Decimal, Decimal, Decimal, Decimal]]:
        """Compute available rectangles on sheet (simplified guillotine)"""
        free = [(Decimal(0), Decimal(0), sheet.width, sheet.height)]
        for p in sheet.parts:
            new_free = []
            for fx, fy, fw, fh in free:
                # subtract occupied rectangle (p)
                if not (p["x"] >= fx+fw or p["x"]+p["w"] <= fx or
                        p["y"] >= fy+fh or p["y"]+p["h"] <= fy):
                    # Split free rect into up to 2 (right and bottom)
                    right_w = fx+fw - (p["x"]+p["w"])
                    if right_w > 0:
                        new_free.append((p["x"]+p["w"], fy, right_w, fh))
                    bottom_h = fy+fh - (p["y"]+p["h"])
                    if bottom_h > 0:
                        new_free.append((fx, p["y"]+p["h"], fw, bottom_h))
                else:
                    new_free.append((fx, fy, fw, fh))
            free = new_free
        return free

    def _build_report(self) -> Dict:
        total_used = sum(s.used_area for s in self.sheets)
        total_raw = sum(s.raw_width*s.raw_height for s in self.sheets)
        return {
            "sheets": [{
                "material_id": s.material_id,
                "raw_dims": {"w": float(s.raw_width), "h": float(s.raw_height)},
                "usable_dims": {"w": float(s.width), "h": float(s.height)},
                "used_area": float(s.used_area),
                "waste_percent": float(((1 - s.used_area/(s.raw_width*s.raw_height))*100).quantize(Decimal("0.01"))),
                "parts": s.parts
            } for s in self.sheets],
            "total_sheets": len(self.sheets),
            "total_waste_avg": float(((1 - total_used/total_raw)*100).quantize(Decimal("0.01"))) if total_raw else 0
        }

    # def _draw_sheets(self):
    #     """Draw each sheet with parts using matplotlib"""
    #     for i, s in enumerate(self.sheets):
    #         fig, ax = plt.subplots()
    #         ax.set_title(f"Sheet {i+1} - Material {s.material_id}")
    #         ax.set_xlim(0, float(s.width))
    #         ax.set_ylim(0, float(s.height))
    #         for p in s.parts:
    #             rect = plt.Rectangle((float(p["x"]), float(p["y"])), float(p["w"]), float(p["h"]),
    #                                  edgecolor="black", facecolor="lightblue" if p["grain"]=="none" else "lightgreen")
    #             ax.add_patch(rect)
    #             ax.text(float(p["x"]+p["w"]/2), float(p["y"]+p["h"]/2), p["name"],
    #                     ha="center", va="center", fontsize=8)
    #         plt.gca().invert_yaxis()
    #         plt.show()
