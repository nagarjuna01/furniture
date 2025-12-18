# evaluation/cutlist_optimizer.py

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from decimal import Decimal


# -------------------------------------------------------------------------
# DATA CLASSES
# -------------------------------------------------------------------------
@dataclass
class PartRect:
    width: Decimal       # mm
    height: Decimal      # mm
    quantity: int
    name: str
    grain: str           # "vertical", "horizontal", "none"


@dataclass
class Sheet:
    width: Decimal
    height: Decimal
    parts: List[Dict]
    used_area: Decimal = Decimal("0")

    def remaining_area(self) -> Decimal:
        return (self.width * self.height) - self.used_area


# -------------------------------------------------------------------------
# CUTLIST OPTIMIZER (SKYLINE + GRAIN + KERF)
# -------------------------------------------------------------------------
class CutlistOptimizer:

    def __init__(self, sheet_width_mm=2440, sheet_height_mm=1220, kerf_mm=3):
        self.sheet_width = Decimal(str(sheet_width_mm))
        self.sheet_height = Decimal(str(sheet_height_mm))
        self.kerf = Decimal(str(kerf_mm))

    # ---------------------------------------------------------------------
    # PUBLIC ENTRY
    # ---------------------------------------------------------------------
    def optimize(self, parts: List[PartRect]) -> Dict:
        sheets: List[Sheet] = []

        # Expand quantity → individual rectangles
        rects = []
        for p in parts:
            for _ in range(p.quantity):
                rects.append({
                    "name": p.name,
                    "width": p.width,
                    "height": p.height,
                    "grain": p.grain
                })

        # Sort largest-first
        rects.sort(key=lambda r: (r["width"] * r["height"]), reverse=True)

        # Place rectangles
        for rect in rects:
            placed = False
            for sheet in sheets:
                if self._place_part(sheet, rect):
                    placed = True
                    break

            if not placed:
                new_sheet = Sheet(self.sheet_width, self.sheet_height, parts=[])
                self._place_part(new_sheet, rect)
                sheets.append(new_sheet)

        # Compute sheet waste
        total_area = len(sheets) * (self.sheet_width * self.sheet_height)
        used_area = sum(s.used_area for s in sheets)
        waste = (1 - (used_area / total_area)) * Decimal("100")

        return {
            "sheets": [
                {
                    "sheet_index": i + 1,
                    "width": s.width,
                    "height": s.height,
                    "used_area": s.used_area,
                    "remaining_area": s.remaining_area(),
                    "waste_percent": ((1 - (s.used_area / (s.width * s.height))) * 100).quantize(Decimal("1.00")),
                    "cuts": s.parts,
                }
                for i, s in enumerate(sheets)
            ],
            "total_sheets": len(sheets),
            "total_waste_percent": waste.quantize(Decimal("1.00")),
        }

    # ---------------------------------------------------------------------
    # PLACE PART WITH SKYLINE LOGIC
    # ---------------------------------------------------------------------
    def _place_part(self, sheet: Sheet, rect: Dict) -> bool:

        w = rect["width"]
        h = rect["height"]

        # Grain -> allowed orientations
        orientations = self._allowed_orientations(rect["grain"], w, h)

        # Try each orientation
        for (ow, oh) in orientations:
            pos = self._find_space_on_sheet(sheet, ow, oh)
            if pos:
                x, y = pos
                sheet.parts.append({
                    "name": rect["name"],
                    "x": x,
                    "y": y,
                    "width": ow,
                    "height": oh,
                    "grain": rect["grain"]
                })
                sheet.used_area += (ow * oh)
                return True

        return False

    # ---------------------------------------------------------------------
    # ALLOWED ORIENTATIONS BY GRAIN
    # ---------------------------------------------------------------------
    def _allowed_orientations(self, grain: str, w: Decimal, h: Decimal):
        if grain == "none":
            return [(w, h), (h, w)]  # rotation allowed
        if grain == "vertical":
            return [(w, h)]          # height must stay vertical
        if grain == "horizontal":
            return [(w, h)]          # width must stay horizontal
        return [(w, h)]

    # ---------------------------------------------------------------------
    # FIND POSITION USING SIMPLE ROW-BASED SKYLINE
    # ---------------------------------------------------------------------
    def _find_space_on_sheet(self, sheet: Sheet, w: Decimal, h: Decimal) -> Optional[Tuple[Decimal, Decimal]]:

        # If sheet is empty
        if not sheet.parts:
            if w <= sheet.width and h <= sheet.height:
                return Decimal("0"), Decimal("0")
            return None

        # Try placing in existing rows
        rows = self._build_rows(sheet)

        for row_y, row_height in rows:
            x = self._find_space_in_row(sheet, row_y, row_height, w, h)
            if x is not None:
                return x, row_y

        # Try starting a new row
        used_height = sum(r[1] + self.kerf for r in rows)
        new_row_y = used_height

        if new_row_y + h <= sheet.height:
            return Decimal("0"), new_row_y

        return None

    # ---------------------------------------------------------------------
    # BUILD ROWS FROM ALREADY-PLACED PARTS
    # ---------------------------------------------------------------------
    def _build_rows(self, sheet: Sheet):
        if not sheet.parts:
            return []

        rows = {}
        for p in sheet.parts:
            y = p["y"]
            rows.setdefault(y, Decimal("0"))
            rows[y] = max(rows[y], p["height"])

        # Convert to sorted list [(y, row_height), ...]
        return sorted([(y, rows[y]) for y in rows], key=lambda x: x[0])

    # ---------------------------------------------------------------------
    # FIND SPACE IN A SPECIFIC ROW
    # ---------------------------------------------------------------------
    def _find_space_in_row(self, sheet: Sheet, row_y: Decimal, row_height: Decimal,
                           w: Decimal, h: Decimal) -> Optional[Decimal]:
        """Try to place part in a row by scanning X axis."""

        if h > row_height:  
            return None  # too tall for this row

        # Scan x axis
        x = Decimal("0")
        while x + w <= sheet.width:
            if not self._overlaps(sheet, x, row_y, w, h):
                return x
            x += self.kerf + Decimal("1")  # small step to avoid infinite loop

        return None

    # ---------------------------------------------------------------------
    # OVERLAP CHECK
    # ---------------------------------------------------------------------
    def _overlaps(self, sheet: Sheet, x: Decimal, y: Decimal, w: Decimal, h: Decimal) -> bool:
        for p in sheet.parts:
            if (
                x < p["x"] + p["width"] and
                x + w > p["x"] and
                y < p["y"] + p["height"] and
                y + h > p["y"]
            ):
                return True
        return False
