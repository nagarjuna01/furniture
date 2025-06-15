# products/services/packing_service.py
from decimal import Decimal

def calculate_optimal_material_usage(parts_data, material_sheets_data, rotation_allowed=True, blade_size_mm=0.0):
    """
    Calculates optimal material usage for a list of parts on given material sheets using a custom,
    simplified greedy 2D packing algorithm, accounting for blade size (kerf).

    Args:
        parts_data (list): List of dictionaries, each representing a part group.
                           Example: [{'width_mm': 100, 'length_mm': 200, 'quantity': 2}]
        material_sheets_data (list): List of dictionaries, each representing a sheet.
                                     Example: [{'width_mm': 1000, 'length_mm': 2000}]
        rotation_allowed (bool): Whether parts can be rotated by 90 degrees.
        blade_size_mm (float): The thickness of the saw blade, for kerf allowance.

    Returns:
        dict: A dictionary containing packing analysis results and layout.
    """

    # --- Helper function for checking rectangle intersection ---
    def intersects(rect1, rect2):
        """
        Checks if two rectangles intersect.
        rect = (x, y, w, h)
        """
        r1_x1, r1_y1, r1_w, r1_h = rect1
        r1_x2, r1_y2 = r1_x1 + r1_w, r1_y1 + r1_h

        r2_x1, r2_y1, r2_w, r2_h = rect2
        r2_x2, r2_y2 = r2_x1 + r2_w, r2_y1 + r2_h

        return not (r1_x2 <= r2_x1 or r1_x1 >= r2_x2 or
                    r1_y2 <= r2_y1 or r1_y1 >= r2_y2)

    # --- Helper function to find a placement on a sheet ---
    def find_placement(sheet_width, sheet_length, occupied_rects_with_kerf,
                       part_actual_w, part_actual_l, allow_rotation, current_blade_size_mm):
        """
        Finds the lowest-leftmost available position for a part on a sheet,
        considering blade size.
        Returns (x, y, placed_actual_w, placed_actual_l, rotated_bool) or None if no spot found.
        """
        # Dimensions for collision detection (part + kerf allowance)
        part_w_with_kerf = part_actual_w + current_blade_size_mm
        part_l_with_kerf = part_actual_l + current_blade_size_mm

        # Max search grid for x,y (can be optimized, but functional for now)
        # We need to ensure there's enough space for the part AND its kerf.
        max_x = int(sheet_width - current_blade_size_mm) # Don't place part leading edge too close to sheet edge
        max_y = int(sheet_length - current_blade_size_mm) # Similarly for y

        # Iterate through potential (x,y) coordinates on the sheet
        for y_coord in range(max_y + 1): # Iterate up to and including max_y
            for x_coord in range(max_x + 1): # Iterate up to and including max_x
                
                # Try original orientation first
                test_w_actual, test_l_actual = part_actual_w, part_actual_l
                test_w_with_kerf = part_w_with_kerf
                test_l_with_kerf = part_l_with_kerf
                is_rotated = False

                # Check if this placement fits within sheet boundaries (with kerf)
                if (x_coord + test_w_with_kerf <= sheet_width and
                    y_coord + test_l_with_kerf <= sheet_length):
                    
                    current_test_rect_with_kerf = (x_coord, y_coord, test_w_with_kerf, test_l_with_kerf)
                    
                    overlap = False
                    for existing_rect_with_kerf in occupied_rects_with_kerf:
                        if intersects(current_test_rect_with_kerf, existing_rect_with_kerf):
                            overlap = True
                            break
                    if not overlap:
                        # Found a fit with original orientation
                        return (x_coord, y_coord, test_w_actual, test_l_actual, is_rotated) 

                # Try rotated orientation if allowed and dimensions are different
                if allow_rotation and (part_actual_w != part_actual_l):
                    test_w_actual, test_l_actual = part_actual_l, part_actual_w # Swapped actual dimensions
                    test_w_with_kerf = test_w_actual + current_blade_size_mm
                    test_l_with_kerf = test_l_actual + current_blade_size_mm

                    if (x_coord + test_w_with_kerf <= sheet_width and
                        y_coord + test_l_with_kerf <= sheet_length):
                        
                        current_test_rect_rotated_with_kerf = (x_coord, y_coord, test_w_with_kerf, test_l_with_kerf)
                        
                        overlap_rotated = False
                        for existing_rect_with_kerf in occupied_rects_with_kerf:
                            if intersects(current_test_rect_rotated_with_kerf, existing_rect_with_kerf):
                                overlap_rotated = True
                                break
                        if not overlap_rotated:
                            # Found a fit with rotated orientation
                            return (x_coord, y_coord, test_w_actual, test_l_actual, True) # True for rotated
        return None # No position found

    # --- Main Packing Logic ---

    total_material_area_packed = Decimal('0.00')
    total_sheets_area_used = Decimal('0.00')
    final_layout = [] # List of layouts for each used sheet

    # 1. Prepare a flat list of all individual parts to be packed
    all_individual_parts = []
    for part_group in parts_data:
        # Ensure dimensions are float for calculation
        part_w = float(part_group['width_mm'])
        part_l = float(part_group['length_mm'])
        for _ in range(int(part_group['quantity'])):
            all_individual_parts.append({'width_mm': part_w, 'length_mm': part_l})
    
    # Sort parts by largest dimension first (a common greedy heuristic for better packing)
    all_individual_parts.sort(key=lambda p: max(p['width_mm'], p['length_mm']), reverse=True)

    # 2. Sort sheets by smallest area first (to try and use fewer sheets)
    sorted_sheets = sorted(material_sheets_data, key=lambda s: float(s['width_mm']) * float(s['length_mm']))

    unpacked_parts = list(all_individual_parts) # Copy for modification
    
    # 3. Iterate through sheets and try to pack parts
    for sheet_data in sorted_sheets:
        if not unpacked_parts:
            break # All parts have been packed

        current_sheet_width = float(sheet_data['width_mm'])
        current_sheet_length = float(sheet_data['length_mm'])

        # Store occupied rectangles WITH blade size added for collision detection
        current_sheet_occupied_rects_with_kerf = [] 
        current_sheet_layout_items = []   # Stores dicts for final output (actual dimensions)

        # Iterate through unpacked parts and try to fit them on the current sheet
        part_idx = 0
        while part_idx < len(unpacked_parts):
            part = unpacked_parts[part_idx]
            
            # Find placement considering actual part dimensions and blade size
            placement_result = find_placement(
                current_sheet_width, current_sheet_length, current_sheet_occupied_rects_with_kerf,
                part['width_mm'], part['length_mm'], rotation_allowed, blade_size_mm
            )

            if placement_result:
                # Part was successfully placed
                px, py, placed_actual_w, placed_actual_l, rotated = placement_result
                
                # Add the rectangle WITH kerf to our occupied list for future collision checks
                placed_rect_with_kerf = (px, py, placed_actual_w + blade_size_mm, placed_actual_l + blade_size_mm)
                current_sheet_occupied_rects_with_kerf.append(placed_rect_with_kerf)
                
                # Add the ACTUAL part details to the layout for output
                current_sheet_layout_items.append({
                    'width_mm': placed_actual_w,
                    'length_mm': placed_actual_l,
                    'x_pos_mm': px,
                    'y_pos_mm': py,
                    'rotated': rotated
                })
                
                # Remove the packed part from the list of unpacked parts
                unpacked_parts.pop(part_idx)
                # DO NOT increment part_idx as list has shrunk, next item is at current index
            else:
                # This part doesn't fit on the current sheet (or at any tested position)
                # Move to the next part in the unpacked_parts list
                part_idx += 1
        
        # If any part was packed on this sheet, add this sheet's layout to the final results
        if current_sheet_layout_items:
            final_layout.append({
                'sheet_dimensions_mm': {'width': current_sheet_width, 'length': current_sheet_length},
                'packed_rects': current_sheet_layout_items
            })
            # Accumulate the area of this used sheet
            total_sheets_area_used += Decimal(str(current_sheet_width)) * Decimal(str(current_sheet_length))

    # Calculate total_material_area_packed from all packed items in the final layout
    for sheet_data in final_layout:
        for packed_rect in sheet_data['packed_rects']:
            total_material_area_packed += Decimal(str(packed_rect['width_mm'])) * Decimal(str(packed_rect['length_mm']))

    # Calculate wastage percentage
    calculated_wastage_percentage = Decimal('0.00')
    if total_sheets_area_used > 0:
        calculated_wastage_percentage = ((total_sheets_area_used - total_material_area_packed) / total_sheets_area_used) * Decimal('100.00')
    elif len(all_individual_parts) > 0 and len(final_layout) == 0:
        # Scenario where parts exist but no sheets could fit them at all.
        calculated_wastage_percentage = Decimal('100.00')

    return {
        'total_sheets_used': len(final_layout),
        'total_material_area_packed_sq_mm': total_material_area_packed,
        'total_sheets_area_used_sq_mm': total_sheets_area_used,
        'calculated_wastage_percentage': calculated_wastage_percentage.quantize(Decimal('0.01')),
        'layout': final_layout
    }