import unittest
from decimal import Decimal

from modular_calc.evaluation.geometry_validator import (
    GeometryValidator,
    GeometryValidationError,
)


class TestGeometryValidation(unittest.TestCase):

    def test_valid_geometry_passes(self):
        parts = [{
            "name": "Side Panel",
            "length_eq": Decimal("2100"),
            "width_eq": Decimal("600"),
            "thickness": Decimal("18"),
            "quantity": 2,
        }]

        GeometryValidator.validate_parts(parts)

    def test_missing_length_fails(self):
        parts = [{
            "name": "Shelf",
            "length_eq": Decimal("0"),
            "width_eq": Decimal("450"),
            "thickness": Decimal("18"),
        }]

        with self.assertRaises(GeometryValidationError) as ctx:
            GeometryValidator.validate_parts(parts)

        self.assertIn("length", str(ctx.exception).lower())

    def test_missing_width_fails(self):
        parts = [{
            "name": "Back Panel",
            "length_eq": Decimal("1800"),
            "width_eq": Decimal("0"),
            "thickness": Decimal("9"),
        }]

        with self.assertRaises(GeometryValidationError):
            GeometryValidator.validate_parts(parts)

    def test_negative_dimension_fails(self):
        parts = [{
            "name": "Top Panel",
            "length_eq": Decimal("-600"),
            "width_eq": Decimal("450"),
            "thickness": Decimal("18"),
        }]

        with self.assertRaises(GeometryValidationError):
            GeometryValidator.validate_parts(parts)

    def test_non_numeric_dimension_fails(self):
        parts = [{
            "name": "Bottom Panel",
            "length_eq": "six hundred",
            "width_eq": Decimal("450"),
            "thickness": Decimal("18"),
        }]

        with self.assertRaises(GeometryValidationError):
            GeometryValidator.validate_parts(parts)


if __name__ == "__main__":
    unittest.main()
