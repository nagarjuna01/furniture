from decimal import Decimal

DEFAULT_BRAND = "Generic"
DEFAULT_GRAIN_DIRECTION = None  # Grain constraint off unless specified

def calculate_optimal_material_usage(parts_queryset, material_sheets_data, rotation_allowed=True, blade_size_mm=0.0):
    """
    Calculates optimal material usage for a list of parts with constraints using a 2D greedy algorithm.

    Args:
        parts_queryset: Django queryset of Part1 objects.
        material_sheets_data (list): [{'width_mm': 1200, 'length_mm': 2400, 'brand': 'XYZ'}]
        rotation_allowed (bool): Whether rotation of parts is allowed.
        blade_size_mm (float): Saw kerf size to leave between parts.

    Returns:
        dict: Packing result including layout, area used, wastage %, etc.
    """

    def intersects(rect1, rect2):
        r1_x1, r1_y1, r1_w, r1_h = rect1
        r1_x2, r1_y2 = r1_x1 + r1_w, r1_y1 + r1_h
        r2_x1, r2_y1, r2_w, r2_h = rect2
        r2_x2, r2_y2 = r2_x1 + r2_w, r2_y1 + r2_h
        return not (r1_x2 <= r2_x1 or r1_x1 >= r2_x2 or r1_y2 <= r2_y1 or r1_y1 >= r2_y2)

    def find_placement(sheet_w, sheet_l, occupied, w, l, allow_rotation, blade):
        w_k = w + blade
        l_k = l + blade
        max_x = int(sheet_w - blade)
        max_y = int(sheet_l - blade)

        for y in range(max_y + 1):
            for x in range(max_x + 1):
                # Try original
                if x + w_k <= sheet_w and y + l_k <= sheet_l:
                    new_rect = (x, y, w_k, l_k)
                    if not any(intersects(new_rect, r) for r in occupied):
                        return x, y, w, l, False

                # Try rotated
                if allow_rotation and w != l:
                    w_r, l_r = l, w
                    w_k_r = w_r + blade
                    l_k_r = l_r + blade
                    if x + w_k_r <= sheet_w and y + l_k_r <= sheet_l:
                        new_rect = (x, y, w_k_r, l_k_r)
                        if not any(intersects(new_rect, r) for r in occupied):
                            return x, y, w_r, l_r, True
        return None

    # --- Step 1: Build list of parts with metadata ---
    all_parts = []
    for part in parts_queryset:
        dims = part.compute_dimensions()
        brand = getattr(getattr(part.part_material, 'brand', None), 'name', DEFAULT_BRAND)
        grain = part.part_dimensions.get('grain_direction', DEFAULT_GRAIN_DIRECTION)
        for _ in range(dims['quantity']):
            all_parts.append({
                'width_mm': float(dims['width']),
                'length_mm': float(dims['length']),
                'material_brand': brand,
                'grain_direction': grain,
            })

    # Sort by largest dimension for better greedy fitting
    all_parts.sort(key=lambda p: max(p['width_mm'], p['length_mm']), reverse=True)

    total_material_area_packed = Decimal('0.00')
    total_sheets_area_used = Decimal('0.00')
    final_layout = []

    remaining_parts = list(all_parts)

    for sheet in material_sheets_data:
        if not remaining_parts:
            break

        sheet_w = float(sheet['width_mm'])
        sheet_l = float(sheet['length_mm'])
        sheet_brand = sheet.get('brand', DEFAULT_BRAND)

        sheet_occupied = []
        sheet_layout = []

        i = 0
        while i < len(remaining_parts):
            part = remaining_parts[i]

            # Filter: Brand match
            if part['material_brand'] != sheet_brand:
                i += 1
                continue

            # Filter: Grain direction constraint
            part_grain = part.get('grain_direction')
            rot_allowed = rotation_allowed
            if part_grain is not None:
                rot_allowed = False  # No rotation allowed if grain is specified

            result = find_placement(
                sheet_w, sheet_l, sheet_occupied,
                part['width_mm'], part['length_mm'],
                rot_allowed, blade_size_mm
            )

            if result:
                x, y, w, l, rotated = result
                sheet_occupied.append((x, y, w + blade_size_mm, l + blade_size_mm))
                sheet_layout.append({
                    'x_pos_mm': x,
                    'y_pos_mm': y,
                    'width_mm': w,
                    'length_mm': l,
                    'rotated': rotated,
                    'grain_direction': part_grain,
                    'material_brand': part['material_brand']
                })
                remaining_parts.pop(i)
            else:
                i += 1

        if sheet_layout:
            final_layout.append({
                'sheet_dimensions_mm': {'width': sheet_w, 'length': sheet_l, 'brand': sheet_brand},
                'packed_rects': sheet_layout
            })
            total_sheets_area_used += Decimal(str(sheet_w)) * Decimal(str(sheet_l))

    for sheet in final_layout:
        for rect in sheet['packed_rects']:
            total_material_area_packed += Decimal(str(rect['width_mm'])) * Decimal(str(rect['length_mm']))

    wastage_pct = Decimal('0.00')
    if total_sheets_area_used > 0:
        wastage_pct = ((total_sheets_area_used - total_material_area_packed) / total_sheets_area_used) * Decimal('100.00')
    elif all_parts and not final_layout:
        wastage_pct = Decimal('100.00')

    return {
        'total_sheets_used': len(final_layout),
        'total_material_area_packed_sq_mm': total_material_area_packed,
        'total_sheets_area_used_sq_mm': total_sheets_area_used,
        'calculated_wastage_percentage': wastage_pct.quantize(Decimal('0.01')),
        'layout': final_layout
    }
