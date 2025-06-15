# products/tests/mock_dependencies.py

from decimal import Decimal

# Mock for asteval.Interpreter (assuming it's used for formula evaluation)
class MockAstevalInterpreter:
    def __init__(self, symtable=None):
        self.symtable = symtable if symtable is not None else {}

    def eval(self, expression):
        try:
            return eval(expression, {}, self.symtable)
        except (TypeError, NameError, SyntaxError) as e:
            print(f"MockAstevalInterpreter: Error evaluating '{expression}' with symtable {self.symtable}: {e}")
            raise

# Mock for packing service functions
def mock_calculate_optimal_material_usage(parts_data, material_sheets_data, blade_size_mm):
    """
    Mock implementation of calculate_optimal_material_usage.
    Returns predefined results to ensure test predictability.
    This mock is now dynamic based on the material_sheets_data passed in.
    """
    results = {}

    # Iterate through the material_sheets_data to identify which materials are being processed
    # and provide a consistent mocked output for them.
    for sheet_data in material_sheets_data:
        material_name = sheet_data['material_name']
        if material_name == 'Plywood for Logic Test':
            results[material_name] = {
                'total_sheets_used': 2,
                'calculated_wastage_percentage': Decimal('10.00'),
                'total_material_area_packed_sq_mm': Decimal('1000000'),
                'total_sheets_area_used_sq_mm': Decimal('2000000'),
                'layout': []
            }
        elif material_name == 'MR Plywood 12mm for Packing Test':
            results[material_name] = {
                'total_sheets_used': 1,
                'calculated_wastage_percentage': Decimal('5.00'),
                'total_material_area_packed_sq_mm': Decimal('500000'),
                'total_sheets_area_used_sq_mm': Decimal('1000000'),
                'layout': []
            }
    return results


def mock_calculate_curved_area(length_mm, width_mm, radius_mm):
    """Mock for curved area calculation."""
    return Decimal('10000.0') # Example fixed value

def mock_calculate_curved_edge_band_cost(length_mm, edge_depth_mm):
    """Mock for curved edge band cost calculation."""
    return Decimal('50.0') # Example fixed value