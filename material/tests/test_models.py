# material/tests/test_models.py
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from material.models import (
    Brand, EdgeBand, Category, CategoryTypes, CategoryModel,
    WoodEn, HardwareGroup, Hardware
)

class BrandModelTest(TestCase):
    def test_create_brand(self):
        brand = Brand.objects.create(name='test brand')
        self.assertEqual(brand.name, 'TEST BRAND') # Should be uppercase
        self.assertIsNotNone(brand.created_at)
        self.assertEqual(str(brand), 'TEST BRAND')

    def test_brand_name_case_conversion_on_save(self):
        brand = Brand(name='another brand')
        brand.save()
        self.assertEqual(brand.name, 'ANOTHER BRAND')

class EdgeBandModelTest(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name='EdgeBrandCo')

    def test_create_edgeband(self):
        edgeband = EdgeBand.objects.create(
            name='White Edge 1mm',
            edge_depth=Decimal('22.00'),
            e_thickness=Decimal('1.00'),
            brand=self.brand,
            p_price=Decimal('10.50'),
            s_price=Decimal('15.00')
        )
        self.assertIsNotNone(edgeband.id)
        self.assertEqual(edgeband.name, 'White Edge 1mm')
        self.assertEqual(edgeband.edge_depth, Decimal('22.00'))
        self.assertEqual(edgeband.e_thickness, Decimal('1.00'))
        self.assertEqual(edgeband.brand, self.brand)
        self.assertEqual(edgeband.p_price, Decimal('10.50'))
        self.assertEqual(edgeband.s_price, Decimal('15.00'))
        self.assertEqual(str(edgeband), 'White Edge 1mm')
        self.assertEqual(edgeband.sl_price, (Decimal('10.50') * Decimal('1.2')).quantize(Decimal('0.01')))

    def test_edgeband_str_representation_without_name(self):
        edgeband = EdgeBand.objects.create(
            edge_depth=Decimal('25.00'),
            e_thickness=Decimal('2.00'),
            brand=self.brand,
            p_price=Decimal('12.00'),
            s_price=Decimal('18.00'),
            name='' # No name
        )
        self.assertEqual(str(edgeband), 'EdgeBand 25.00mm X 2.00mm')

    def test_edgeband_sl_price_property(self):
        edgeband = EdgeBand.objects.create(
            edge_depth=Decimal('22.00'), e_thickness=Decimal('1.00'),
            brand=self.brand, p_price=Decimal('10.00'), s_price=Decimal('15.00')
        )
        self.assertEqual(edgeband.sl_price, Decimal('12.00'))

        edgeband.p_price = Decimal('0.00')
        edgeband.save() # Need to save for property to potentially re-evaluate, though it's dynamic
        self.assertEqual(edgeband.sl_price, Decimal('0.00'))

    def test_edgeband_clean_method_negative_prices(self):
        edgeband = EdgeBand(
            edge_depth=Decimal('22.00'), e_thickness=Decimal('1.00'),
            brand=self.brand, p_price=Decimal('-10.00'), s_price=Decimal('15.00')
        )
        with self.assertRaisesMessage(ValidationError, "Purchase price cannot be negative."):
            edgeband.full_clean()

        edgeband = EdgeBand(
            edge_depth=Decimal('22.00'), e_thickness=Decimal('1.00'),
            brand=self.brand, p_price=Decimal('10.00'), s_price=Decimal('-15.00')
        )
        with self.assertRaisesMessage(ValidationError, "Selling price cannot be negative."):
            edgeband.full_clean()
    
    def test_edgeband_clean_method_negative_dimensions(self):
        edgeband = EdgeBand(
            edge_depth=Decimal('-22.00'), e_thickness=Decimal('1.00'),
            brand=self.brand, p_price=Decimal('10.00'), s_price=Decimal('15.00')
        )
        with self.assertRaisesMessage(ValidationError, "Edge depth cannot be negative."):
            edgeband.full_clean()

        edgeband = EdgeBand(
            edge_depth=Decimal('22.00'), e_thickness=Decimal('-1.00'),
            brand=self.brand, p_price=Decimal('10.00'), s_price=Decimal('15.00')
        )
        with self.assertRaisesMessage(ValidationError, "Edge band thickness cannot be negative."):
            edgeband.full_clean()

class CategoryModelTest(TestCase):
    def test_create_category(self):
        category = Category.objects.create(name='wood')
        self.assertEqual(category.name, 'WOOD')
        self.assertEqual(str(category), 'WOOD')

    def test_category_name_case_conversion_on_save(self):
        category = Category(name='laminates')
        category.save()
        self.assertEqual(category.name, 'LAMINATES')

    def test_category_unique_name(self):
        Category.objects.create(name='plywood')
        with self.assertRaises(Exception): # Expecting IntegrityError or similar
            Category.objects.create(name='plywood') # Django's unique constraint handles this

class CategoryTypesModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='material_category')

    def test_create_category_type(self):
        cat_type = CategoryTypes.objects.create(category=self.category, name='solid wood')
        self.assertEqual(cat_type.name, 'SOLID WOOD')
        self.assertEqual(cat_type.category, self.category)
        self.assertEqual(str(cat_type), 'SOLID WOOD')

    def test_category_type_name_case_conversion_on_save(self):
        cat_type = CategoryTypes(category=self.category, name='mdf')
        cat_type.save()
        self.assertEqual(cat_type.name, 'MDF')

class CategoryModelModelTest(TestCase): # Renamed to avoid confusion with django.db.models.Model
    def setUp(self):
        self.category = Category.objects.create(name='wood')
        self.category_type = CategoryTypes.objects.create(category=self.category, name='plywood')

    def test_create_category_model(self):
        cat_model = CategoryModel.objects.create(model_category=self.category_type, name='mr grade')
        self.assertEqual(cat_model.name, 'MR GRADE')
        self.assertEqual(cat_model.model_category, self.category_type)
        self.assertEqual(str(cat_model), 'MR GRADE')

    def test_category_model_name_case_conversion_on_save(self):
        cat_model = CategoryModel(model_category=self.category_type, name='bwr grade')
        cat_model.save()
        self.assertEqual(cat_model.name, 'BWR GRADE')


class WoodEnModelTest(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name='LuxeWoods')
        self.category = Category.objects.create(name='Wood')
        self.category_type = CategoryTypes.objects.create(category=self.category, name='Plywood')
        self.category_model = CategoryModel.objects.create(model_category=self.category_type, name='BWR Grade')
        self.edgeband_test = EdgeBand.objects.create(
            name='Test Edgeband', edge_depth=Decimal('22'), e_thickness=Decimal('1'),
            brand=self.brand, p_price=Decimal('10'), s_price=Decimal('15')
        )
        # No need for _original_convert_to_mm / _original_convert_to_feet or tearDown
        # when using patch as a context manager. patch handles restoring.

    from unittest.mock import patch
from decimal import Decimal

def test_create_wooden_panel_price(self):
    with patch('material.models.WoodEn.convert_to_mm', side_effect=lambda val, unit: Decimal(val)) as mock_to_mm, \
         patch('material.models.WoodEn.convert_to_feet', side_effect=lambda val, unit: Decimal(val) / Decimal('304.8')) as mock_to_ft:

        wooden = WoodEn.objects.create(
            material_grp=self.category,
            material_type=self.category_type,
            material_model=self.category_model,
            name='BWR Plywood 18mm',
            brand=self.brand,
            length=2440,
            length_unit='mm',
            width=1220,
            width_unit='mm',
            thickness=18.0,
            thickness_unit='mm',
            cost_price=Decimal('2000.00'),
            costprice_type='panel',
            sell_price=Decimal('2500.00'),
            sellprice_type='panel',
            color='Brown',
            is_sheet=True
        )

        self.assertEqual(mock_to_mm.call_count, 3)
        self.assertEqual(mock_to_ft.call_count, 2)

        expected_area_sft = (Decimal('2440') / Decimal('304.8')) * (Decimal('1220') / Decimal('304.8'))

        self.assertEqual(wooden.length, 2440)
        self.assertEqual(wooden.width, 1220)
        self.assertEqual(wooden.thickness, Decimal('18.00'))
        self.assertEqual(wooden.length_unit, 'mm')
        self.assertEqual(wooden.width_unit, 'mm')
        self.assertEqual(wooden.thickness_unit, 'mm')

        self.assertEqual(wooden.p_price, Decimal('2000.00'))
        self.assertAlmostEqual(wooden.p_price_sft, Decimal('2000.00') / expected_area_sft, places=4)
        self.assertEqual(wooden.s_price, Decimal('2500.00'))
        self.assertAlmostEqual(wooden.s_price_sft, Decimal('2500.00') / expected_area_sft, places=4)

def test_create_wooden_sft_price(self):
    with patch('material.models.WoodEn.convert_to_mm', side_effect=lambda val, unit: Decimal(val)) as mock_to_mm, \
         patch('material.models.WoodEn.convert_to_feet', side_effect=lambda val, unit: Decimal(val) / Decimal('304.8')) as mock_to_ft:

        wooden = WoodEn.objects.create(
            material_grp=self.category,
            material_type=self.category_type,
            material_model=self.category_model,
            name='MDF 12mm',
            brand=self.brand,
            length=2440,
            length_unit='mm',
            width=1220,
            width_unit='mm',
            thickness=12.0,
            thickness_unit='mm',
            cost_price=Decimal('50.00'),
            costprice_type='sft',
            sell_price=Decimal('70.00'),
            sellprice_type='sft',
            color='Light Brown',
            is_sheet=True
        )

        expected_area_sft = (Decimal('2440') / Decimal('304.8')) * (Decimal('1220') / Decimal('304.8'))

        self.assertAlmostEqual(wooden.p_price, Decimal('50.00') * expected_area_sft, places=4)
        self.assertEqual(wooden.p_price_sft, Decimal('50.00'))
        self.assertAlmostEqual(wooden.s_price, Decimal('70.00') * expected_area_sft, places=4)
        self.assertEqual(wooden.s_price_sft, Decimal('70.00'))

    def test_wooden_clean_method_negative_prices(self):
        wooden = WoodEn(
            material_grp=self.category, material_type=self.category_type,
            material_model=self.category_model, name='Test Neg Price', brand=self.brand,
            length=1000, width=1000, thickness=10, cost_price=Decimal('-10.00'), sell_price=Decimal('100.00')
        )
        with self.assertRaisesMessage(ValidationError, "Prices cannot be negative."):
            wooden.full_clean()

        wooden = WoodEn(
            material_grp=self.category, material_type=self.category_type,
            material_model=self.category_model, name='Test Neg Price', brand=self.brand,
            length=1000, width=1000, thickness=10, cost_price=Decimal('10.00'), sell_price=Decimal('-100.00')
        )
        with self.assertRaisesMessage(ValidationError, "Prices cannot be negative."):
            wooden.full_clean()

    def test_wooden_m2m_compatible_edgebands(self):
        wooden = WoodEn.objects.create(
            material_grp=self.category, material_type=self.category_type,
            material_model=self.category_model, name='Test Wood M2M', brand=self.brand,
            length=1000, length_unit='mm', width=1000, width_unit='mm', thickness=18.0, thickness_unit='mm',
            cost_price=Decimal('100.00'), costprice_type='panel', sell_price=Decimal('150.00'), sellprice_type='panel'
        )
        wooden.compatible_edgebands.add(self.edgeband_test)
        self.assertIn(self.edgeband_test, wooden.compatible_edgebands.all())
        self.assertEqual(wooden.compatible_edgebands.count(), 1)


class HardwareGroupModelTest(TestCase):
    def test_create_hardware_group(self):
        hg = HardwareGroup.objects.create(name='Handles')
        self.assertEqual(hg.name, 'HANDLES')
        self.assertEqual(str(hg), 'HANDLES')

    def test_hardware_group_name_case_conversion_on_save(self):
        hg = HardwareGroup(name='hinges')
        hg.save()
        self.assertEqual(hg.name, 'HINGES')

class HardwareModelTest(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name='HardwareBrand')
        self.hg = HardwareGroup.objects.create(name='Knobs')

    def test_create_hardware(self):
        hardware = Hardware.objects.create(
            h_group=self.hg,
            h_name='Door Knob',
            brand=self.brand,
            unit='each',
            p_price=Decimal('50.00'),
            s_price=Decimal('75.00')
        )
        self.assertIsNotNone(hardware.id)
        self.assertEqual(hardware.h_name, 'DOOR KNOB')
        self.assertEqual(hardware.h_group, self.hg)
        self.assertEqual(hardware.brand, self.brand)
        self.assertEqual(hardware.unit, 'each')
        self.assertEqual(hardware.p_price, Decimal('50.00'))
        self.assertEqual(hardware.s_price, Decimal('75.00'))
        self.assertEqual(str(hardware), 'DOOR KNOB (KNOBS)')
        self.assertEqual(hardware.sl_price, (Decimal('50.00') * Decimal('1.2')).quantize(Decimal('0.01')))

    def test_hardware_sl_price_property(self):
        hardware = Hardware.objects.create(
            h_group=self.hg, h_name='Drawer Slide', brand=self.brand,
            p_price=Decimal('100.00'), s_price=Decimal('150.00')
        )
        self.assertEqual(hardware.sl_price, Decimal('120.00'))

        hardware.p_price = Decimal('0.00')
        hardware.save()
        self.assertEqual(hardware.sl_price, Decimal('0.00'))
    
    def test_hardware_clean_method_negative_prices(self):
        hardware = Hardware(
            h_group=self.hg, h_name='Invalid Hardware', brand=self.brand,
            p_price=Decimal('-10.00'), s_price=Decimal('50.00')
        )
        with self.assertRaisesMessage(ValidationError, "Purchase price cannot be negative."):
            hardware.full_clean()

        hardware = Hardware(
            h_group=self.hg, h_name='Invalid Hardware', brand=self.brand,
            p_price=Decimal('10.00'), s_price=Decimal('-50.00')
        )
        with self.assertRaisesMessage(ValidationError, "Sale price cannot be negative."):
            hardware.full_clean()