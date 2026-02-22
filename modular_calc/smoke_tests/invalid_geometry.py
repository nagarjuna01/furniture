from modular_calc.evaluation.geometry_validator import GeometryValidator, GeometryValidationError

bom = {
    "parts": [
        {
            "name": "Missing Length",
            "length_eq": 0,
            "width_eq": 500,
            "quantity": 1,
        },
        {
            "name": "Negative Width",
            "length_eq": 1000,
            "width_eq": -300,
            "quantity": 1,
        },
        {
            "name": "Zero Quantity",
            "length_eq": 1200,
            "width_eq": 600,
            "quantity": 0,
        }
    ]
}

try:
    GeometryValidator.validate_parts(bom["parts"])
    print("❌ ERROR: Geometry validation should have failed but did not")
except GeometryValidationError as e:
    print("✅ Geometry validation failed correctly:")
    print(e)
