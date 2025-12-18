from django.test import TestCase
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError

# Import models from the 'products' app (your main app for these tests)
from products.models import (
    Part, PartHardware, ModulePart,
    ModularProduct, ModularProductModule, ModularProductMaterialOverride,
    Constraint, GlobalSetting, Module
)

# Import models from the 'material' app (where Category, WoodEn, etc. reside)
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware,HardwareGroup
from material.models.brand import Brand
from material.models.category import Category,CategoryModel,CategoryTypes

# Import mocks for external functions (assuming mock_dependencies.py is in products/tests/)
from .mock_dependencies import (
    mock_calculate_optimal_material_usage,
    MockAstevalInterpreter,
    mock_calculate_curved_area,
    mock_calculate_curved_edge_band_cost
)

# Patch asteval.Interpreter globally for tests in this file
# This ensures that whenever Interpreter() is called, our mock is used.
patch('asteval.Interpreter', MockAstevalInterpreter).start()


class ModelSetupMixin:
    """
    A mixin to create common test data for models.
    This helps reduce redundancy in test setups.
    """
    def setUp(self):
        super().setUp() # Call parent setUp if overriding
        self.brand_a = Brand.objects.create(name="BRAND A")
        self.brand_b = Brand.objects.create(name="BRAND B")

        self.cat_wood = Category.objects.create(name="WOOD")
        self.cat_type_ply = CategoryTypes.objects.create(category=self.cat_wood, name="PLYWOOD")
        self.cat_model_mr = CategoryModel.objects.create(model_category=self.cat_type_ply, name="MR GRADE")
        self.cat_model_bwr = CategoryModel.objects.create(model_category=self.cat_type_ply, name="BWR GRADE")

        # WoodEn Material 1 (standard)
        self.wooden_material_1 = WoodMaterial.objects.create(
            material_grp=self.cat_wood,
            material_type=self.cat_type_ply,
            material_model=self.cat_model_mr,
            name="MR Plywood 18mm",
            brand=self.brand_a, # <--- ADDED/CONFIRMED
            length=2440, # mm
            length_unit='mm',
            width=1220,  # mm
            width_unit='mm',
            thickness=18.0, # mm
            thickness_unit='mm',
            cost_price=Decimal('2500.00'), # Panel price
            costprice_type='panel',
            sell_price=Decimal('3000.00'), # Panel price
            sellprice_type='panel',
            color='Light Brown',
            is_sheet=True
        )
        self.wooden_material_1.save()

        # WoodEn Material 2 (per sqft pricing, different thickness)
        self.wooden_material_2 = WoodMaterial.objects.create(
            material_grp=self.cat_wood,
            material_type=self.cat_type_ply,
            material_model=self.cat_model_bwr,
            name="BWR Plywood 12mm",
            brand=self.brand_b, # <--- ADDED/CONFIRMED
            length=2440,
            length_unit='mm',
            width=1220,
            width_unit='mm',
            thickness=12.0,
            thickness_unit='mm',
            cost_price=Decimal('75.00'), # Price per sqft
            costprice_type='sft',
            sell_price=Decimal('90.00'), # Price per sqft
            sellprice_type='sft',
            color='Dark Brown',
            is_sheet=True
        )
        self.wooden_material_2.save()

        # Edge Bands
        self.eb_white_1mm = EdgeBand.objects.create(
            name="White 1mm",
            edge_depth=22,
            e_thickness=1.0,
            brand=self.brand_a, # <--- ADDED/CONFIRMED
            p_price=Decimal('10.00'), # Per meter
            s_price=Decimal('15.00')  # Per meter
        )
        self.eb_wood_2mm = EdgeBand.objects.create(
            name="Wood Grain 2mm",
            edge_depth=45,
            e_thickness=2.0,
            brand=self.brand_b, # <--- ADDED/CONFIRMED
            p_price=Decimal('25.00'), # Per meter
            s_price=Decimal('35.00')  # Per meter
        )

        # Hardware
        self.hg_hinges = HardwareGroup.objects.create(name="HINGES")
        self.hg_handles = HardwareGroup.objects.create(name="HANDLES")

        self.hardware_hinge = Hardware.objects.create(
            h_group=self.hg_hinges,
            h_name="SOFT CLOSE HINGE",
            brand=self.brand_a, # <--- ADDED/CONFIRMED
            unit='set',
            p_price=Decimal('50.00'),
            s_price=Decimal('70.00')
        )
        self.hardware_handle = Hardware.objects.create(
            h_group=self.hg_handles,
            h_name="CABINET PULL",
            brand=self.brand_b, # <--- ADDED/CONFIRMED
            unit='each',
            p_price=Decimal('200.00'),
            s_price=Decimal('280.00')
        )

        # Parts
        # Assuming Part also inherits from Product or has a direct brand FK
        self.part_side_panel = Part.objects.create(
            name="Side Panel",
            part_length_formula="H", # Height from product constraint
            part_width_formula="D",  # Depth from product constraint
            part_thickness_mm=self.wooden_material_1.thickness, # Will be set by save()
            material=self.wooden_material_1,
            top_edge_band=self.eb_white_1mm,
            bottom_edge_band=self.eb_white_1mm,
            cutting_cost_per_meter=Decimal('5.00'),
            grooving_cost_per_meter=Decimal('2.00'),
            edgeband_cutting_cost_per_meter=Decimal('1.00'),
            brand=self.brand_a # <--- ADDED THIS LINE
        )
        self.part_side_panel.save()

        self.part_shelf = Part.objects.create(
            name="Shelf",
            part_length_formula="W - 100", # Width from product constraint
            part_width_formula="D - 50",   # Depth from product constraint
            material=self.wooden_material_2,
            left_edge_band=self.eb_wood_2mm,
            right_edge_band=self.eb_wood_2mm,
            part_quantity_formula="Q_SHELF", # Variable quantity
            cutting_cost_per_meter=Decimal('6.00'),
            brand=self.brand_b # <--- ADDED THIS LINE
        )
        self.part_shelf.save()

        # PartHardware (no direct brand field, relies on Part)

        # Module (just a placeholder module)
        # Assuming Module also inherits from Product or has a brand FK
        self.module_cabinet = Module.objects.create(
            name="Standard Cabinet",
            description="A standard base cabinet module",
            length_mm=Decimal('600'), # Changed from default_length_mm
            width_mm=Decimal('300'),  # Changed from default_width_mm
            height_mm=Decimal('720'),
            brand=self.brand_a # <--- ADDED THIS LINE
        )

        # ModulePart (no direct brand field, relies on Module and Part)

        # ModularProduct (A product that uses modules)
        self.modular_product_kitchen_base = ModularProduct.objects.create(
            name="Kitchen Base Unit",
            brand=self.brand_a # <--- THIS IS THE MOST CRITICAL ADDITION BASED ON TRACEBACK
        )

        # ModularProductModule (linking module to product)
        ModularProductModule.objects.create(
            modular_product=self.modular_product_kitchen_base,
            module=self.module_cabinet,
            quantity=1
        )

        # Constraints for the ModularProduct
        self.constraint_H = Constraint.objects.create(
            product=self.modular_product_kitchen_base, abbreviation='H', value=Decimal('720')
        )
        self.constraint_W = Constraint.objects.create(
            product=self.modular_product_kitchen_base, abbreviation='W', value=Decimal('600')
        )
        self.constraint_D = Constraint.objects.create(
            product=self.modular_product_kitchen_base, abbreviation='D', value=Decimal('580')
        )
        self.constraint_Q_SHELF = Constraint.objects.create(
            product=self.modular_product_kitchen_base, abbreviation='Q_SHELF', value=Decimal('2')
        ) # Override shelf quantity

        # ModularProductMaterialOverride
        self.override_bwr_material = ModularProductMaterialOverride.objects.create(
            modular_product=self.modular_product_kitchen_base,
            wooden_material=self.wooden_material_2, # BWR Plywood 12mm
            override_purchase_price_sft=Decimal('70.00'), # Cheaper override
            override_selling_price_sft=Decimal('85.00')
        )

        # Global Settings
        GlobalSetting.objects.create(
            name='CUTTING_COST_PER_SHEET',
            decimal_value=Decimal('150.00') # Example cutting cost
        )
        GlobalSetting.objects.create(
            name='DEFAULT_BLADE_SIZE_MM',
            decimal_value=Decimal('4.0')
        )