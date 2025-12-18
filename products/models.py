# products/models.py
import asteval
import logging
from django.db import models
from django.utils import timezone
from django.conf import settings
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from asteval import Interpreter # For formula evaluation
from django.utils.html import format_html
from polymorphic.models import PolymorphicModel
from django.contrib.auth import get_user_model
from products.services.packing_service import calculate_optimal_material_usage


logger = logging.getLogger(__name__)
# --- Product Classification Hierarchy (Remains largely as is) ---
class ProductCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='productcategory_images/', null=True, blank=True)
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name
    @property
    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" width="50" height="50" />', self.image.url)
        return "No Image"

class Type(models.Model):
    category = models.ForeignKey(ProductCategory, related_name='types', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='type_images/', null=True, blank=True)
    class Meta:
        unique_together = ('category', 'name')
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.category.name} > {self.name}"

class Model(models.Model):
    type = models.ForeignKey(Type, related_name='models', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='model_images/', null=True, blank=True)
    class Meta:
        unique_together = ('type', 'name')
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.type.category.name} > {self.type.name} > {self.name}"

# --- Unit Model (Generic measurement units) ---
class Unit(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

# --- Product Base Class (Polymorphic) ---
class ProductType(models.TextChoices):
    STANDARD = 'Standard', ('Standard Product')
    MODULAR = 'Modular', ('Modular Product')
    CUSTOM = 'Custom', ('Custom Product')

class Product(PolymorphicModel):
    name = models.CharField(max_length=255)
    product_type = models.CharField(
        max_length=10,
        choices=ProductType.choices,
        default=ProductType.STANDARD,
        help_text="Defines the fundamental type of the product (e.g., Standard, Modular, Custom)."
    )
    category = models.ForeignKey(
        'ProductCategory',
        on_delete=models.PROTECT,
        related_name='%(class)s_products'
    )
    type = models.ForeignKey(
        'Type',
        on_delete=models.PROTECT,
        related_name='%(class)s_products'
    )
    model = models.ForeignKey(
        'Model',
        related_name='%(class)s_products',
        on_delete=models.CASCADE
    )
    brand = models.ForeignKey(
        'material.Brand',
        on_delete=models.PROTECT,
        related_name='%(class)s_products'
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- SEO Fields ---
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True,
                            help_text="A short, unique, human-readable identifier for use in URLs.")
    meta_title = models.CharField(max_length=255, blank=True, null=True,
                                  help_text="Title for search engines (max 60-70 characters).")
    meta_description = models.TextField(blank=True, null=True,
                                        help_text="Description for search engines (max 150-160 characters).")
    keywords = models.CharField(max_length=255, blank=True, null=True,
                                help_text="Comma-separated keywords for SEO.")
    child_models = (
        'StandardProduct', # Name of the child model class as a string
        'CustomProduct',   # Name of the child model class as a string
        'ModularProduct',  # Name of the child model class as a string
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.product_type})"

    @property
    def display_selling_price(self):
        if self.product_type == ProductType.STANDARD and hasattr(self, 'standardproduct'):
            return self.standardproduct.sl_price
        elif self.product_type == ProductType.MODULAR and hasattr(self, 'modularproduct'):
            return self.modularproduct.price or self.modularproduct.calculate_total_modular_product_selling_cost_derived()
        elif self.product_type == ProductType.CUSTOM and hasattr(self, 'customproduct'):
            return self.customproduct.manual_selling_price
        return Decimal('0.00')

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug and self.name:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
            # Ensure unique slug in case of duplicates
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

# --- Standard Product (Fixed Configuration) ---
class StandardProduct(Product):
    section = models.CharField(max_length=30, choices=[('DESKING', 'DESKING'), ('PARTITION', 'PARTITION'), ('COMBO', 'COMBO')], default='DESKING')
    material_description = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="General description of the material/finish (e.g., 'Melamine White', 'Solid Oak')"
    )
    color = models.CharField(max_length=50, blank=True, null=True)
    length_mm = models.DecimalField(max_digits=10, decimal_places=2)
    width_mm = models.DecimalField(max_digits=10, decimal_places=2)
    height_mm = models.DecimalField(max_digits=10, decimal_places=2)

    s_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Inputted selling price for the standard product.")
    p_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Inputted purchase price for the standard product (cost to you).")
    sl_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Calculated selling price (e.g., P_Price * 1.20).")
    price_unit = models.ForeignKey('Unit', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.material_description or ''} ({self.length_mm}x{self.width_mm}x{self.height_mm}mm)"

    def save(self, *args, **kwargs):
        self.sl_price = self.p_price * Decimal('1.20') if self.p_price is not None else Decimal('0')
        super().save(*args, **kwargs)

    def calculate_break_even_amount_standard(self):
        effective_selling_price = self.sl_price if self.sl_price is not None else Decimal('0.00')
        purchase_cost = self.p_price if self.p_price is not None else Decimal('0.00')
        if effective_selling_price <= Decimal('0.00'):
            return None
        profit_loss = effective_selling_price - purchase_cost
        return profit_loss

    def calculate_profit_margin_percentage_value_standard(self):
        effective_selling_price = self.sl_price if self.sl_price is not None else Decimal('0.00')
        purchase_cost = self.p_price if self.p_price is not None else Decimal('0.00')
        if effective_selling_price <= Decimal('0.00'):
            return None
        profit_loss = effective_selling_price - purchase_cost
        if effective_selling_price > Decimal('0.00'):
            margin = (profit_loss / effective_selling_price) * Decimal('100')
            return margin
        return Decimal('0.00')

    @property
    def formatted_break_even_status_standard(self):
        profit_loss = self.calculate_break_even_amount_standard()
        if profit_loss is None:
            return "N/A (Selling price not set or zero)"
        elif profit_loss > Decimal('0.00'):
            return f"Profit: ${profit_loss:.2f}"
        elif profit_loss < Decimal('0.00'):
            return f"Loss: ${abs(profit_loss):.2f} (Below Break-Even)"
        else:
            return "Break-Even (Zero Profit)"

    @property
    def formatted_profit_margin_standard(self):
        margin_value = self.calculate_profit_margin_percentage_value_standard()
        if margin_value is None:
            return "N/A (Selling price not set or zero)"
        else:
            return f"{margin_value:.2f}%"

class StandardProductImage(models.Model):
    standard_product = models.ForeignKey(StandardProduct, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='standard_product_images/')
    def __str__(self):
        return f"Image for {self.standard_product.name}"

# --- Custom Product (Flexible/Manual) ---
class CustomProduct(Product):
    manual_purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    manual_selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    design_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Custom: {self.name}"

# --- Part (Generic Part Blueprint - NO direct link to ModularProduct or Module here) ---
class Part(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    
    part_length_formula = models.CharField(max_length=255, null=True, blank=True, help_text="Formula for length in mm, e.g., 'L - 50'")
    part_width_formula = models.CharField(max_length=255, null=True, blank=True, help_text="Formula for width in mm, e.g., 'W - 50'")
    part_thickness_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Fixed thickness in mm")
    part_quantity_formula = models.CharField(max_length=255, null=True, blank=True, default='1', help_text="Formula for quantity, e.g., '1' or '2 * (L / 100)'")
    
    material = models.ForeignKey(WoodMaterial, related_name='parts_using_this_wood', on_delete=models.SET_NULL, null=True, blank=True)
    
    # --- Wastage Factor ---
    wastage_factor = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('1.00'), 
        help_text="Factor to account for material wastage (e.g., 1.05 for 5% wastage)."
    )

    top_edge_band = models.ForeignKey(EdgeBand, related_name='parts_with_top_eb', on_delete=models.SET_NULL, null=True, blank=True)
    left_edge_band = models.ForeignKey(EdgeBand, related_name='parts_with_left_eb', on_delete=models.SET_NULL, null=True, blank=True)
    bottom_edge_band = models.ForeignKey(EdgeBand, related_name='parts_with_bottom_eb', on_delete=models.SET_NULL, null=True, blank=True)
    right_edge_band = models.ForeignKey(EdgeBand, related_name='parts_with_right_eb', on_delete=models.SET_NULL, null=True, blank=True)
    
    cutting_cost_per_meter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    grooving_cost_per_meter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    edgeband_cutting_cost_per_meter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    
    shape_type = models.CharField(max_length=50, choices=[
        ('rectangular', 'Rectangular'), ('l_shape', 'L Shape'), ('trapezoid', 'Trapezoid'),
        ('curved', 'Curved'), ('custom', 'Custom')
    ], default='rectangular')
    geometry_features = models.JSONField(null=True, blank=True, help_text="Specific dimensions/parameters for complex shapes (e.g., {'radius': 500, 'angle': 90} for curved)")
    orientation = models.CharField(max_length=20, choices=[('horizontal', 'Horizontal'), ('vertical', 'Vertical')], default='horizontal')

    threed_model_file = models.FileField(
        upload_to='part_3d_models/', 
        null=True, 
        blank=True, 
        help_text="Upload a 3D model file (e.g., .obj, .gltf) for this part blueprint."
    )
    # --- 3D / Spatial Features (Commented for future use) ---
    # model_3d_file = models.FileField(
    #     upload_to='part_3d_models/',
    #     null=True, blank=True,
    #     help_text="Automatically generated 3D model file (e.g., GLB, OBJ) for this part."
    # )
    # # Potentially store a hash or timestamp to check if the model_3d_file needs regeneration
    # geometry_hash = models.CharField(max_length=64, null=True, blank=True,
    #     help_text="Hash of geometry_features, part_length_formula, etc., to detect changes.")
    #
    # # For more advanced modular design, parts might have predefined connection points
    # # E.g., for attaching hardware, other parts, or defining wall corners.
    # # connection_points = models.JSONField(
    # #     null=True, blank=True,
    # #     help_text="Defined points/planes for connecting other parts, e.g., {'top_center': [0, 0, Z_max]}"
    # # )

    def __str__(self):
        return self.name
     # @property
    # def get_3d_model_url(self):
    #     """
    #     Returns the URL to the 3D model file.
    #     This could trigger generation if the model is outdated/missing.
    #     """
    #     if self.model_3d_file:
    #         # Consider adding logic here to check geometry_hash and trigger regeneration
    #         # if self.geometry_hash != self._calculate_current_geometry_hash():
    #         #    self._generate_3d_model() # This would be a background task
    #         return self.model_3d_file.url
    #     # else:
    #         # Consider triggering _generate_3d_model() if no file exists
    #     return None

    # def _calculate_current_geometry_hash(self):
    #     """Helper to calculate a hash based on relevant geometry fields."""
    #     # Implement logic to create a hash from a combination of:
    #     # self.part_length_formula, self.part_width_formula, self.part_thickness_mm,
    #     # self.shape_type, self.geometry_features, self.orientation,
    #     # and potentially material thickness if it affects geometry.
    #     # Use hashlib.sha256 on a sorted/serialized string representation.
    #     pass

    # def _generate_3d_model(self):
    #     """
    #     Placeholder for triggering 3D model generation.
    #     This would likely be an async task (e.g., Celery) calling external 3D libraries.
    #     """
    #     # Example: call a utility function or send a task
    #     # from some_3d_generation_module import generate_glb_for_part_async
    #     # generate_glb_for_part_async.delay(self.id)
    #     pass

    # --- NEW: Override save method to populate part_thickness_mm ---
    def save(self, *args, **kwargs):
        if self.material and self.material.thickness is not None:
            # Ensure the material's thickness is converted to Decimal if it's not already
            self.part_thickness_mm = Decimal(str(self.material.thickness))
        
        # If no material or thickness is provided, you might want to default it to 0 or leave as null
        # if self.material is None or self.material.thickness is None:
        #     self.part_thickness_mm = None # Or Decimal('0.00')

        super().save(*args, **kwargs) # Call the original save method

    # --- Existing methods (evaluate_formula, calculate_material_cost, etc.) below ---
    def evaluate_formula(self, formula, local_vars=None):
        aeval = Interpreter()
        if local_vars:
            aeval.symtable.update({k: float(v) for k, v in local_vars.items()})
        try:
            result = aeval(formula)
            return Decimal(str(result)) if result is not None else Decimal('0.00')
        except Exception as e:
            print(f"Error evaluating formula '{formula}' with vars {local_vars}: {e}")
            return Decimal('0.00')

    def calculate_material_cost(self, local_vars=None, modular_product_instance=None):
        if not self.material:
            return {'purchase_cost': Decimal('0.00'), 'selling_cost': Decimal('0.00')}

        part_length_mm = self.evaluate_formula(self.part_length_formula, local_vars)
        part_width_mm = self.evaluate_formula(self.part_width_formula, local_vars)
        part_quantity = self.evaluate_formula(self.part_quantity_formula, local_vars)

        if part_length_mm <= 0 or part_width_mm <= 0 or part_quantity <= 0:
            return {'purchase_cost': Decimal('0.00'), 'selling_cost': Decimal('0.00')}
        
        # Calculate area in sqft, applying wastage factor
        area_ft2 = (part_length_mm / Decimal(304.8)) * (part_width_mm / Decimal(304.8)) * self.wastage_factor

        material_purchase_price_sft = self.material.p_price_sft or Decimal('0.00')
        material_selling_price_sft = self.material.s_price_sft or Decimal('0.00')

        # This part requires ModularProductMaterialOverride model, ensure it's imported
        try:
            from .models import ModularProductMaterialOverride # Adjust this import path
            if modular_product_instance:
                try:
                    override = modular_product_instance.material_overrides.get(wooden_material=self.material)
                    if override.override_purchase_price_sft is not None:
                        material_purchase_price_sft = override.override_purchase_price_sft
                    if override.override_selling_price_sft is not None:
                        material_selling_price_sft = override.override_selling_price_sft
                except ModularProductMaterialOverride.DoesNotExist:
                    pass
        except ImportError:
            print("Warning: ModularProductMaterialOverride not found. Material overrides will not apply.")


        purchase_cost = area_ft2 * material_purchase_price_sft * part_quantity
        selling_cost = area_ft2 * material_selling_price_sft * part_quantity

        return {'purchase_cost': purchase_cost, 'selling_cost': selling_cost}

    def calculate_edge_band_cost(self, local_vars=None):
        total_purchase = Decimal('0.00')
        total_selling = Decimal('0.00')
        
        part_length_mm = self.evaluate_formula(self.part_length_formula, local_vars)
        part_width_mm = self.evaluate_formula(self.part_width_formula, local_vars)
        quantity = self.evaluate_formula(self.part_quantity_formula, local_vars)
        
        if part_length_mm <= 0 or part_width_mm <= 0 or quantity <= 0:
            return {'purchase_cost': Decimal('0.00'), 'selling_cost': Decimal('0.00')}
        
        # Convert to meters for edge banding cost, applying wastage factor
        length_m = (part_length_mm / Decimal(1000)) * self.wastage_factor # Apply wastage to linear length too
        width_m = (part_width_mm / Decimal(1000)) * self.wastage_factor

        if self.top_edge_band:
            total_purchase += length_m * (self.top_edge_band.p_price or Decimal('0.00'))
        if self.bottom_edge_band:
            total_purchase += length_m * (self.bottom_edge_band.p_price or Decimal('0.00'))
        if self.left_edge_band:
            total_purchase += width_m * (self.left_edge_band.p_price or Decimal('0.00'))
        if self.right_edge_band:
            total_purchase += width_m * (self.right_edge_band.p_price or Decimal('0.00'))

        total_selling = (
            (length_m * (self.top_edge_band.s_price or Decimal('0.00')) if self.top_edge_band else Decimal('0.00')) +
            (length_m * (self.bottom_edge_band.s_price or Decimal('0.00')) if self.bottom_edge_band else Decimal('0.00')) +
            (width_m * (self.left_edge_band.s_price or Decimal('0.00')) if self.left_edge_band else Decimal('0.00')) +
            (width_m * (self.right_edge_band.s_price or Decimal('0.00')) if self.right_edge_band else Decimal('0.00'))
        )
        
        return {
            'purchase_cost': total_purchase * quantity,
            'selling_cost': total_selling * quantity
        }

    def calculate_cutting_cost(self, local_vars=None):
        if self.cutting_cost_per_meter is None: return Decimal('0.00')
        length_mm = self.evaluate_formula(self.part_length_formula, local_vars)
        if length_mm <= 0: return Decimal('0.00')
        return (length_mm / Decimal(1000)) * self.cutting_cost_per_meter

    def calculate_grooving_cost(self, local_vars=None):
        if self.grooving_cost_per_meter is None: return Decimal('0.00')
        length_mm = self.evaluate_formula(self.part_length_formula, local_vars)
        width_mm = self.evaluate_formula(self.part_width_formula, local_vars)
        if length_mm <= 0 or width_mm <= 0: return Decimal('0.00')
        total_length_m = 2 * ((length_mm + width_mm) / Decimal(1000))
        return total_length_m * self.grooving_cost_per_meter

    def calculate_edgeband_cutting_cost(self, local_vars=None):
        if self.edgeband_cutting_cost_per_meter is None: return Decimal('0.00')
        length_mm = self.evaluate_formula(self.part_length_formula, local_vars)
        width_mm = self.evaluate_formula(self.part_width_formula, local_vars)
        if length_mm <= 0 or width_mm <= 0: return Decimal('0.00')
        total_length_m = 2 * ((length_mm + width_mm) / Decimal(1000))
        return total_length_m * self.edgeband_cutting_cost_per_meter

    def calculate_total_labor_cost(self, local_vars=None):
        return (
            self.calculate_cutting_cost(local_vars) +
            self.calculate_grooving_cost(local_vars) +
            self.calculate_edgeband_cutting_cost(local_vars)
        )

    def calculate_hardware_cost(self, module_part_instance=None):
        cost = Decimal('0.00')
        if module_part_instance:
            for ph in self.required_hardware.all(): # Assuming required_hardware is a ManyToMany with PartHardware
                cost += (ph.hardware.p_price or Decimal('0.00')) * ph.quantity_required * module_part_instance.quantity
        return cost
    def calculate_part_costs_breakdown(self, local_vars=None, modular_product_instance=None, module_part_instance=None):
        """
        Calculates and returns a detailed breakdown of costs for a single part instance.
        """
        # Ensure local_vars is a dictionary
        local_vars = local_vars if local_vars is not None else {}

        # Material Costs (purchase and selling)
        material_costs = self.calculate_material_cost(local_vars, modular_product_instance)
        
        # Edge Band Costs (purchase and selling)
        edge_band_costs = self.calculate_edge_band_cost(local_vars)
        
        # Labor Costs (only one value needed as you only calculate total_labor_cost)
        total_labor_cost = self.calculate_total_labor_cost(local_vars)

        # Hardware Costs (only one value needed)
        hardware_cost = self.calculate_hardware_cost(module_part_instance)
        
        # Part quantity as evaluated by the part's formula (e.g., if a "part" blueprint itself represents 2 items)
        part_internal_quantity = self.evaluate_formula(self.part_quantity_formula, local_vars)
        if part_internal_quantity <= 0: part_internal_quantity = Decimal('0.00')

        # Aggregate for this single part instance (including its internal quantity)
        purchase_breakdown = {
            'material_cost': material_costs['purchase_cost'],
            'edge_band_cost': edge_band_costs['purchase_cost'],
            'labor_cost': total_labor_cost * part_internal_quantity, # Labor costs are per part instance, so multiply by internal quantity
            'hardware_cost': hardware_cost, # Hardware cost already considers quantity within calculate_hardware_cost
            'total_purchase_cost': material_costs['purchase_cost'] + edge_band_costs['purchase_cost'] + (total_labor_cost * part_internal_quantity) + hardware_cost
        }

        selling_breakdown = {
            'material_cost': material_costs['selling_cost'],
            'edge_band_cost': edge_band_costs['selling_cost'],
            'labor_cost': total_labor_cost * part_internal_quantity, # Same for selling
            'hardware_cost': hardware_cost, # Hardware cost is usually same for purchase/selling unless you define it separately
            'total_selling_cost': material_costs['selling_cost'] + edge_band_costs['selling_cost'] + (total_labor_cost * part_internal_quantity) + hardware_cost
        }
        
        return {
            'purchase': purchase_breakdown,
            'selling': selling_breakdown
        }


    def calculate_part_total_purchase_cost(self, local_vars=None, modular_product_instance=None, module_part_instance=None):
        # Now just calls the breakdown method and returns the total
        costs = self.calculate_part_costs_breakdown(local_vars, modular_product_instance, module_part_instance)
        return costs['purchase']['total_purchase_cost']

    def calculate_part_total_selling_cost(self, local_vars=None, modular_product_instance=None, module_part_instance=None):
        # Now just calls the breakdown method and returns the total
        costs = self.calculate_part_costs_breakdown(local_vars, modular_product_instance, module_part_instance)
        return costs['selling']['total_selling_cost']
    def calculate_curved_area(self, local_vars=None):
        if not self.geometry_features or self.shape_type != 'curved':
            return Decimal('0.00')
        try:
            radius = Decimal(str(self.geometry_features.get('radius', 0)))
            angle_deg = Decimal(str(self.geometry_features.get('angle', 0)))
            thickness = self.part_thickness_mm or Decimal('0.00')

            if radius <=0 or angle_deg <= 0 or thickness <= 0: return Decimal('0.00')

            angle_rad = angle_deg * Decimal('3.1415926535') / Decimal('180')
            arc_length = radius * angle_rad
            area = arc_length * thickness
            return area / Decimal('92903.04') * self.wastage_factor # Apply wastage factor
        except Exception as e:
            print(f"Error calculating curved area: {e}")
            return Decimal('0.00')
    
    def calculate_curved_edge_band_cost(self, local_vars=None):
        if not self.geometry_features or self.shape_type != 'curved' or not self.top_edge_band:
            return Decimal('0.00')
        try:
            radius = Decimal(str(self.geometry_features.get('radius', 0)))
            angle_deg = Decimal(str(self.geometry_features.get('angle', 0)))
            quantity = self.evaluate_formula(self.part_quantity_formula, local_vars)
            
            if radius <= 0 or angle_deg <= 0 or quantity <= 0: return Decimal('0.00')

            angle_rad = angle_deg * Decimal('3.1415926535') / Decimal('180')
            arc_length_m = (radius * angle_rad) / Decimal('1000') * self.wastage_factor # Apply wastage factor

            edge_band = self.top_edge_band
            if edge_band:
                return arc_length_m * (edge_band.p_price or Decimal('0.00')) * quantity
            return Decimal('0.00')
        except Exception as e:
            print(f"Error calculating curved edge band cost: {e}")
            return Decimal('0.00')

# --- PartHardware (Links a Part blueprint to Hardware blueprint, specifying quantity) ---
class PartHardware(models.Model):
    part = models.ForeignKey(Part, related_name='required_hardware', on_delete=models.CASCADE)
    hardware = models.ForeignKey(Hardware, related_name='used_in_parts', on_delete=models.CASCADE)
    quantity_required = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('part', 'hardware')
        verbose_name = "Part Hardware Requirement"
        verbose_name_plural = "Part Hardware Requirements"

    def __str__(self):
        return f"{self.quantity_required}x {self.hardware.h_name} for Part: {self.part.name}"

DEFAULT_STATIC_CONSTRAINTS = {
    'DEFAULT_BLADE_SIZE_MM': Decimal('3.0'),
    'MIN_PANEL_DIMENSION_MM': Decimal('100.0'),
    'STANDARD_DRILL_BIT_DIA_MM': Decimal('5.0'),
    # Add any other global constants you use in formulas or calculations
}

class Module(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='module_images/', null=True, blank=True)
    length_mm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width_mm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height_mm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    threed_model_file = models.FileField(
        upload_to='module_3d_models/',
        null=True,
        blank=True,
        help_text="Upload a 3D model file (e.g., .obj, .gltf) for this module blueprint."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def _get_local_vars_for_parts(self, modular_product_instance=None, live_constraints=None):
        """
        Gathers and returns a dictionary of local variables and constraints
        needed for part generation and calculations.

        Args:
            modular_product_instance (ModularProduct, optional): The ModularProduct
                instance associated with this Module, if applicable. Defaults to None.
            live_constraints (dict, optional): A dictionary of dynamic constraints
                that override default or global settings. Defaults to None.

        Returns:
            dict: A dictionary of local variables and constraints.
        """
        local_vars = {}

        # 1. Module's own dimensions (always present)
        local_vars['L'] = float(self.length_mm) if self.length_mm is not None else 0.0
        local_vars['W'] = float(self.width_mm) if self.width_mm is not None else 0.0
        local_vars['H'] = float(self.height_mm) if self.height_mm is not None else 0.0

        # 2. Application-wide Global Settings (fetched from GlobalSetting model)
        # Ensure 'default' values passed to get_setting match what you expect if DB is empty
        # Note: Using .get_setting(name_as_string, default_value, type_string)
        local_vars['STANDARD_LABOR_RATE_PER_SQFT'] = float(GlobalSetting.get_setting('STANDARD_LABOR_RATE_PER_SQFT', default=Decimal('50.00'), value_type='decimal'))
        local_vars['STANDARD_PACKING_COST_PER_MODULE'] = float(GlobalSetting.get_setting('STANDARD_PACKING_COST_PER_MODULE', default=Decimal('100.00'), value_type='decimal'))
        local_vars['STANDARD_INSTALLATION_COST_PER_MODULE'] = float(GlobalSetting.get_setting('STANDARD_INSTALLATION_COST_PER_MODULE', default=Decimal('200.00'), value_type='decimal'))
        local_vars['CUTTING_COST_PER_SHEET'] = float(GlobalSetting.get_setting('CUTTING_COST_PER_SHEET', default=Decimal('115.00'), value_type='decimal'))
        local_vars['DEFAULT_BLADE_SIZE_MM'] = float(GlobalSetting.get_setting('DEFAULT_BLADE_SIZE_MM', default=Decimal('4.0'), value_type='decimal'))
        local_vars['BLADE_SIZE_MM'] = float(GlobalSetting.get_setting('BLADE_SIZE_MM', default=Decimal('4.0'), value_type='decimal')) # This will be overridden by live_constraints if present
        local_vars['MIN_PANEL_DIMENSION_MM'] = float(GlobalSetting.get_setting('MIN_PANEL_DIMENSION_MM', default=Decimal('100.0'), value_type='decimal'))
        local_vars['STANDARD_DRILL_BIT_DIA_MM'] = float(GlobalSetting.get_setting('STANDARD_DRILL_BIT_DIA_MM', default=Decimal('5.0'), value_type='decimal'))

        # Internal dimensions (often derived or from global settings)
        local_vars['DEFAULT_W_INT'] = float(GlobalSetting.get_setting('DEFAULT_W_INT', default=Decimal('364'), value_type='decimal'))
        local_vars['DEFAULT_H_INT'] = float(GlobalSetting.get_setting('DEFAULT_H_INT', default=Decimal('684'), value_type='decimal'))
        local_vars['DEFAULT_D_INT'] = float(GlobalSetting.get_setting('DEFAULT_D_INT', default=Decimal('560'), value_type='decimal'))
        local_vars['L_INT'] = float(GlobalSetting.get_setting('DEFAULT_L_INT', default=Decimal('764'), value_type='decimal'))

        # 3. Include thickness values for specific part types associated with this module
        for module_part in self.module_parts.all():
            part = module_part.part
            if part and part.part_thickness_mm is not None:
                thickness_key = f"{part.name.replace(' ', '_').upper()}_THICKNESS"
                local_vars[thickness_key] = float(part.part_thickness_mm)

        # 4. Apply ModularProduct-specific Constraints (if instance provided)
        if modular_product_instance:
            for constraint in modular_product_instance.constraints.all():
                local_vars[constraint.abbreviation] = float(constraint.value)

        # 5. Apply Live Constraints (these override all previous values)
        if live_constraints:
            for key, value in live_constraints.items():
                try:
                    local_vars[key] = float(value)
                except (TypeError, ValueError):
                    local_vars[key] = value

        return local_vars

    def calculate_module_total_purchase_cost(self, modular_product_instance=None, live_constraints=None):
        """Calculates the total purchase cost of all parts within the module."""
        total_cost = Decimal('0.00')
        local_vars_for_parts = self._get_local_vars_for_parts(modular_product_instance, live_constraints)

        for module_part in self.module_parts.all():
            part_total_cost_per_set = module_part.part.calculate_part_total_purchase_cost(
                local_vars=local_vars_for_parts,
                modular_product_instance=modular_product_instance,
                module_part_instance=module_part
            )
            total_cost += part_total_cost_per_set * Decimal(module_part.quantity)

        return total_cost.quantize(Decimal('0.01'))

    def calculate_module_total_selling_cost(self, modular_product_instance=None, live_constraints=None):
        """Calculates the total selling cost of all parts within the module."""
        total_cost = Decimal('0.00')
        local_vars_for_parts = self._get_local_vars_for_parts(modular_product_instance, live_constraints)

        for module_part in self.module_parts.all():
            part_total_cost_per_set = module_part.part.calculate_part_total_selling_cost(
                local_vars=local_vars_for_parts,
                modular_product_instance=modular_product_instance,
                module_part_instance=module_part
            )
            total_cost += part_total_cost_per_set * Decimal(module_part.quantity)

        return total_cost.quantize(Decimal('0.01'))

    def get_module_detailed_cost_breakdown(self, modular_product_instance=None, live_constraints=None):
        """
        Aggregates detailed cost breakdowns for all parts within this module.
        This method provides the base blueprint costs (material, edgeband, labor, hardware),
        excluding any wastage costs derived from sheet optimization.
        """
        total_purchase_breakdown = {
            'material_cost': Decimal('0.00'),
            'edge_band_cost': Decimal('0.00'),
            'labor_cost': Decimal('0.00'),
            'hardware_cost': Decimal('0.00'),
            'total_purchase_cost': Decimal('0.00')
        }
        total_selling_breakdown = {
            'material_cost': Decimal('0.00'),
            'edge_band_cost': Decimal('0.00'),
            'labor_cost': Decimal('0.00'),
            'hardware_cost': Decimal('0.00'),
            'total_selling_cost': Decimal('0.00')
        }

        local_vars_for_parts = self._get_local_vars_for_parts(modular_product_instance, live_constraints)

        for module_part in self.module_parts.all():
            part_breakdown = module_part.part.calculate_part_costs_breakdown(
                local_vars=local_vars_for_parts,
                modular_product_instance=modular_product_instance,
                module_part_instance=module_part
            )

            for key, value in part_breakdown['purchase'].items():
                total_purchase_breakdown[key] += value * Decimal(module_part.quantity)

            for key, value in part_breakdown['selling'].items():
                total_selling_breakdown[key] += value * Decimal(module_part.quantity)

        for cost_type_dict in [total_purchase_breakdown, total_selling_breakdown]:
            for key, value in cost_type_dict.items():
                if isinstance(value, Decimal):
                    cost_type_dict[key] = value.quantize(Decimal('0.01'))

        total_purchase_breakdown['total_purchase_cost'] = (
            total_purchase_breakdown['material_cost'] +
            total_purchase_breakdown['edge_band_cost'] +
            total_purchase_breakdown['labor_cost'] +
            total_purchase_breakdown['hardware_cost']
        ).quantize(Decimal('0.01'))

        total_selling_breakdown['total_selling_cost'] = (
            total_selling_breakdown['material_cost'] +
            total_selling_breakdown['edge_band_cost'] +
            total_selling_breakdown['labor_cost'] +
            total_selling_breakdown['hardware_cost']
        ).quantize(Decimal('0.01'))


        final_breakdown = {
            'purchase_breakdown': total_purchase_breakdown,
            'selling_breakdown': total_selling_breakdown
        }

        return final_breakdown

    def calculate_detailed_cost_breakdown_blueprint(self):
        """
        A convenience method for serializers to fetch the base blueprint cost breakdown.
        This method is intended for the module's default blueprint, hence no dynamic args.
        """
        return self.get_module_detailed_cost_breakdown()


    # --- Cost Comparison and Packing Analysis Methods ---

    def get_module_cost_comparison_with_sheets(self, modular_product_instance=None, live_constraints=None, rotation_allowed=True, blade_size_mm=None): # Changed blade_size_mm default to None
        """
        Calculates a detailed comparison of costs based on WoodEn sheet usage (from packing analysis).
        This method also calculates and returns total wastage costs (purchase and selling)
        to be added to the main blueprint totals by the serializer.
        """
        print(f"DEBUG: get_module_cost_comparison_with_sheets called with blade_size_mm={blade_size_mm}")
        packing_live_constraints = live_constraints.copy() if live_constraints else {}

        # Prioritize the blade_size_mm passed to this method, then check live_constraints, then GlobalSetting
        if blade_size_mm is not None:
            packing_live_constraints['BLADE_SIZE_MM'] = Decimal(str(blade_size_mm))
        elif 'BLADE_SIZE_MM' not in packing_live_constraints:
            # Fallback to default if not provided via method parameter or live_constraints
            # Assuming GlobalSetting.get_setting('DEFAULT_BLADE_SIZE_MM', ...) is the correct way
            packing_live_constraints['BLADE_SIZE_MM'] = GlobalSetting.get_setting('DEFAULT_BLADE_SIZE_MM', default=Decimal('4.0'), value_type='decimal')

        # 1. Get the packing analysis results for this module
        # Pass all relevant parameters to the packing analysis
        packing_analysis_results = self.get_module_packing_analysis(
            modular_product_instance=modular_product_instance,
            live_constraints=packing_live_constraints, # This is now correctly passed
            rotation_allowed=rotation_allowed,
            blade_size_mm=packing_live_constraints.get('BLADE_SIZE_MM', Decimal('4.0')) # Pass the determined blade size
        )

        # Initialize structures for comparison breakdown and wastage accumulators
        comparison_breakdown = {
            "total_cost_from_sheets": Decimal('0.00'),
            "details_by_material": {}
        }
        total_purchase_wastage_across_all_materials = Decimal('0.00')
        total_selling_wastage_across_all_materials = Decimal('0.00')

        # Retrieve cutting cost from GlobalSetting. Use correct setting name.
        # Your _get_local_vars_for_parts uses 'CUTTING_COST_PER_SHEET',
        # but your comment uses 'sheet_cutting_cost'. Ensure consistency.
        # Sticking to 'CUTTING_COST_PER_SHEET' as it's used in local_vars for parts.
        CUTTING_COST_PER_SHEET = GlobalSetting.get_setting('CUTTING_COST_PER_SHEET', Decimal('115.00'), 'decimal')
        print(f"DEBUG: Retrieved CUTTING_COST_PER_SHEET from settings: {CUTTING_COST_PER_SHEET}")

        for material_name, material_packing_data in packing_analysis_results.items():
            sheets_used = material_packing_data.get('total_sheets_used', 0)
            calculated_wastage_percentage = Decimal(str(material_packing_data.get('calculated_wastage_percentage', '0.00')))

            if sheets_used > 0:
                representative_sheet = None
                try:
                    # Filter WoodEn instances by their 'name' field, which should match material_name
                    # Make sure WoodEn is imported from material.models
                    from material.models import WoodEn # Temporary import for demonstration
                    representative_sheet = WoodEn.objects.filter(name=material_name).first()

                    if representative_sheet:
                        print(f"DEBUG: Found representative sheet for '{material_name}'. ID: {representative_sheet.id}, Name: {representative_sheet.name}, Cost Price in DB: {representative_sheet.cost_price}, Sell Price in DB: {representative_sheet.sell_price}")
                    else:
                        print(f"WARNING: No WoodEn sheet found in DB matching '{material_name}' (via its 'name' field).")

                except Exception as e:
                    print(f"ERROR: Could not retrieve representative sheet for material '{material_name}': {e}")
                    representative_sheet = None

                sheet_purchase_cost_per_unit = Decimal('0.00')
                sheet_selling_cost_per_unit = Decimal('0.00')

                if representative_sheet:
                    if representative_sheet.cost_price is not None:
                        sheet_purchase_cost_per_unit = representative_sheet.cost_price
                    else:
                        print(f"WARNING: No cost_price found for WoodEn sheets of material '{material_name}'. Assuming 0 purchase cost.")

                    if representative_sheet.sell_price is not None:
                        sheet_selling_cost_per_unit = representative_sheet.sell_price
                    else:
                        print(f"WARNING: No sell_price found for WoodEn sheets of material '{material_name}'. Assuming 0 selling cost.")
                else:
                    print(f"WARNING: No WoodEn sheet found for material '{material_name}'. Assuming 0 purchase/selling cost.")


                # Calculate component costs for the 'cost_comparison_with_sheets' section's breakdown
                cost_of_sheets_used = sheet_purchase_cost_per_unit * Decimal(sheets_used)
                cutting_cost = CUTTING_COST_PER_SHEET * Decimal(sheets_used)

                # Calculate wastage costs separately
                purchase_wastage_for_material = cost_of_sheets_used * (calculated_wastage_percentage / Decimal('100.00'))
                total_purchase_wastage_across_all_materials += purchase_wastage_for_material

                selling_cost_of_sheets_used = sheet_selling_cost_per_unit * Decimal(sheets_used)
                selling_wastage_for_material = selling_cost_of_sheets_used * (calculated_wastage_percentage / Decimal('100.00'))
                total_selling_wastage_across_all_materials += selling_wastage_for_material

                total_cost_for_material_no_wastage = (cost_of_sheets_used + cutting_cost).quantize(Decimal('0.01'))

                comparison_breakdown["details_by_material"][material_name] = {
                    "sheets_used": sheets_used,
                    "cost_of_sheets_used": cost_of_sheets_used.quantize(Decimal('0.01')),
                    "cutting_cost": cutting_cost.quantize(Decimal('0.01')),
                    "wastage_cost_info_only": purchase_wastage_for_material.quantize(Decimal('0.01')),
                    "total_cost_for_material": total_cost_for_material_no_wastage
                }
                comparison_breakdown["total_cost_from_sheets"] += total_cost_for_material_no_wastage

        comparison_breakdown["total_cost_from_sheets"] = comparison_breakdown["total_cost_from_sheets"].quantize(Decimal('0.01'))

        module_purchase_base_total = self.calculate_module_total_purchase_cost(modular_product_instance, live_constraints).quantize(Decimal('0.01'))
        module_sell_base_total = self.calculate_module_total_selling_cost(modular_product_instance, live_constraints).quantize(Decimal('0.01'))

        final_comparison_results = {
            "comparison_breakdown_data": comparison_breakdown,
            "total_purchase_wastage": total_purchase_wastage_across_all_materials.quantize(Decimal('0.01')),
            "total_selling_wastage": total_selling_wastage_across_all_materials.quantize(Decimal('0.01')),
            "module_cost_blueprint_base_total": module_purchase_base_total,
            "module_sell_blueprint_base_total": module_sell_base_total,
            "blade_size_used_mm": blade_size_mm, # This will be the parameter passed in
            "note": "Wastage costs (total_purchase_wastage, total_selling_wastage) are now returned separately to be added to the 'detailed_cost_breakdown_blueprint'. The 'total_cost_for_material' within 'comparison_breakdown_data' does not include wastage."
        }
        print(f"DEBUG: get_module_cost_comparison_with_sheets returning: {final_comparison_results}")
        return final_comparison_results

    # UPDATED: get_module_packing_analysis to accept new parameters
    def get_module_packing_analysis(self, modular_product_instance=None, live_constraints=None, rotation_allowed=True, blade_size_mm=0.0):
        """
        Performs a packing analysis for the module's parts, considering material sheets.
        Returns a dictionary with packing details for each material.
        Args:
            modular_product_instance (ModularProduct, optional): The ModularProduct instance.
            live_constraints (dict, optional): A dictionary of dynamic constraints.
            rotation_allowed (bool, optional): Whether rotation of parts is allowed in packing.
            blade_size_mm (float, optional): The blade size to use for packing calculations.
        """
        from products.services.packing_service import calculate_optimal_material_usage # Import here to avoid circular dependencies if any
        # You might also need to import Material or WoodEn if it's used within this method
        # from material.models import WoodEn # Example import if needed

        self.aeval = asteval.Interpreter()

        parts_data = []
        material_sheets_data = []
        processed_material_sheet_dimensions = set()

        # Pass live_constraints to get_local_vars_for_parts so it can apply overrides
        local_vars = self._get_local_vars_for_parts(modular_product_instance, live_constraints)
        print(f"DEBUG: get_module_packing_analysis local_vars: {local_vars}")

        # Determine the actual blade_size_mm to use for the packing algorithm.
        # It should prioritize the 'blade_size_mm' argument passed directly,
        # then the 'BLADE_SIZE_MM' from live_constraints (which _get_local_vars_for_parts would have applied),
        # otherwise fall back to a default/global setting.
        # Since _get_local_vars_for_parts already applies live_constraints,
        # the BLADE_SIZE_MM in local_vars should be the correct one.
        actual_blade_size_for_packing = float(local_vars.get('BLADE_SIZE_MM', Decimal('4.0')))
        print(f"DEBUG: Using blade_size_mm for packing: {actual_blade_size_for_packing}")


        for module_part in self.module_parts.all():
            part = module_part.part
            if not part:
                continue

            try:
                part_length_str = str(part.part_length_formula).strip()
                part_width_str = str(part.part_width_formula).strip()
                part_quantity_str = str(part.part_quantity_formula).strip()

                part_length = Decimal(self.aeval.eval(part_length_str, local_vars))
                print(f"DEBUG: Part '{part.name}', Length Formula: '{part.part_length_formula}', Evaluated Length: {part_length}")
                part_width = Decimal(self.aeval.eval(part_width_str, local_vars))
                print(f"DEBUG: Part '{part.name}', Width Formula: '{part.part_width_formula}', Evaluated Width: {part_width}")
                part_quantity = Decimal(self.aeval.eval(part_quantity_str, local_vars))
                print(f"DEBUG: Part '{part.name}', Quantity Formula: '{part.part_quantity_formula}', Evaluated Quantity: {part_quantity}")

            except (InvalidOperation, ValueError) as e:
                print(f"WARNING: Could not evaluate formula for part {part.name}: {e}")
                part_length = Decimal('0')
                part_width = Decimal('0')
                part_quantity = Decimal('0')
            except Exception as e:
                print(f"ERROR: Unexpected error evaluating formula for part {part.name}: {e}")
                part_length = Decimal('0')
                part_width = Decimal('0')
                part_quantity = Decimal('0')

            part_length = max(Decimal('0'), part_length)
            part_width = max(Decimal('0'), part_width)

            if part_length > 0 and part_width > 0 and part_quantity > 0:
                parts_data.append({
                    'id': part.id,
                    'name': part.name,
                    'material_id': part.material_id,
                    'length_mm': float(part_length),
                    'width_mm': float(part_width),
                    'thickness_mm': float(part.part_thickness_mm) if part.part_thickness_mm is not None else 0.0,
                    'quantity': int(module_part.quantity * part_quantity),
                })

                if part.material and part.material.is_sheet:
                    sheet_dims = (float(part.material.length), float(part.material.width))
                    if sheet_dims not in processed_material_sheet_dimensions:
                        material_sheets_data.append({
                            'material_id': part.material_id,
                            'length_mm': sheet_dims[0],
                            'width_mm': sheet_dims[1],
                            'material_name': part.material.name,
                        })
                        processed_material_sheet_dimensions.add(sheet_dims)

        print(f"DEBUG: Calling calculate_optimal_material_usage with parts_data: {parts_data}")
        print(f"DEBUG: Calling calculate_optimal_material_usage with material_sheets_data: {material_sheets_data}")
        print(f"DEBUG: Calling calculate_optimal_material_usage with blade_size_mm: {actual_blade_size_for_packing}")
        print(f"DEBUG: Calling calculate_optimal_material_usage with rotation_allowed: {rotation_allowed}") # Pass this if packing_service supports it

        # This is the line that calls the function being patched
        packed_material_results = calculate_optimal_material_usage(
            parts_data, material_sheets_data, actual_blade_size_for_packing, rotation_allowed=rotation_allowed # Pass rotation_allowed
        )
        print("DEBUG: calculate_optimal_material_usage was called and returned results.")

        module_packing_analysis = {}
        for material_name, results in packed_material_results.items():
            module_packing_analysis[material_name] = {
                'total_sheets_used': results.get('total_sheets_used', 0),
                'calculated_wastage_percentage': results.get('calculated_wastage_percentage', Decimal('0.00')),
                'total_material_area_packed_sq_mm': results.get('total_material_area_packed_sq_mm', Decimal('0.00')),
                'total_sheets_area_used_sq_mm': results.get('total_sheets_area_used_sq_mm', Decimal('0.00')),
                'layout': results.get('layout', []),
            }
        return module_packing_analysis

# Your ModulePart model is already correct:
class ModulePart(models.Model):
    module = models.ForeignKey(Module, related_name='module_parts', on_delete=models.CASCADE)
    part = models.ForeignKey(Part, related_name='used_in_modules', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('module', 'part')
        verbose_name = "Module Part"
        verbose_name_plural = "Module Parts"

    def __str__(self):
        return f"{self.quantity}x {self.part.name} for {self.module.name}"

# --- ModularProduct (The top-level configurable product blueprint) ---
class ModularProduct(Product):
    description = models.TextField(blank=True, null=True, help_text="A general description of this modular product blueprint.")
    # --- 3D / Spatial Features (Commented for future use) ---
    # # This will be the main entry point for the "building" or "layout" visualization.
    # # It would store the generated 3D scene that combines all its modules and parts.
    # assembled_model_3d_file = models.FileField(
    #     upload_to='assembled_product_3d_models/',
    #     null=True, blank=True,
    #     help_text="Combined 3D model file (e.g., GLB) for the assembled product."
    # )
    # # A hash to check if the assembled model needs regeneration
    # assembly_hash = models.CharField(max_length=64, null=True, blank=True,
    #     help_text="Hash based on all included modules, parts, constraints, and overrides.")
    length_mm_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    length_mm_max = models.DecimalField(max_digits=10, decimal_places=2, default=99999)
    width_mm_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    width_mm_max = models.DecimalField(max_digits=10, decimal_places=2, default=99999)
    height_mm_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    height_mm_max = models.DecimalField(max_digits=10, decimal_places=2, default=99999)

    modules = models.ManyToManyField(Module, through='ModularProductModule', related_name='used_in_products')

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Optional: Manual selling price for the modular product blueprint. If not set, it's derived from module costs + markup.")
    
    # --- 3D Model Integration for Modular Product ---
    # This could be a primary 3D model for the whole product assembly,
    # or simply serve as a flag indicating it's a configurable 3D product.
    threed_model_assembly_file = models.FileField(
        upload_to='modular_product_3d_assemblies/', 
        null=True, 
        blank=True, 
        help_text="Upload a base 3D assembly file (e.g., .gltf) for this product."
    )
    # Potentially store configuration parameters for 3D visualization here too (JSONField)
    threed_config_json = models.JSONField(
        null=True, 
        blank=True, 
        help_text="JSON configuration for 3D viewer (e.g., camera defaults, light settings)."
    )


    def __str__(self):
        return self.name
    
    
    def calculate_total_modular_product_purchase_cost(self):
        total_purchase_cost = Decimal('0.00')
        product_constraints_dict = {c.abbreviation: c.value for c in self.constraints.all()}
        
        for ppm in self.modular_product_modules.all():
            total_purchase_cost += ppm.module.calculate_module_total_purchase_cost(
                modular_product_instance=self
            ) * ppm.quantity
        return total_purchase_cost

    def calculate_total_modular_product_purchase_cost_with_dynamic_constraints(self, live_constraints=None):
        total_purchase_cost = Decimal('0.00')
        for ppm in self.modular_product_modules.all():
            total_purchase_cost += ppm.module.calculate_module_total_purchase_cost(
                modular_product_instance=self,
                live_constraints=live_constraints # Pass live constraints
            ) * ppm.quantity
        return total_purchase_cost

    def calculate_total_modular_product_selling_cost_derived_with_dynamic_constraints(self, live_constraints=None):
        if self.price is not None:
            return self.price

        total_selling_cost_derived = Decimal('0.00')
        for ppm in self.modular_product_modules.all():
            total_selling_cost_derived += ppm.module.calculate_module_total_selling_cost(
                modular_product_instance=self,
                live_constraints=live_constraints # Pass live constraints
            ) * ppm.quantity
        return total_selling_cost_derived
    
    
    def calculate_total_modular_product_selling_cost_derived(self):
        if self.price is not None:
            return self.price

        total_selling_cost_derived = Decimal('0.00')
        product_constraints_dict = {c.abbreviation: c.value for c in self.constraints.all()}

        for ppm in self.modular_product_modules.all():
            total_selling_cost_derived += ppm.module.calculate_module_total_selling_cost(
                modular_product_instance=self
            ) * ppm.quantity
        return total_selling_cost_derived
    
    @property
    def calculate_taxable_base_price(self):
        base_cost = self.calculate_total_modular_product_purchase_cost()
        return base_cost * Decimal('1.20')

    def calculate_break_even_amount(self):
        product_selling_price = self.calculate_total_modular_product_selling_cost_derived()
        total_production_cost = self.calculate_total_modular_product_purchase_cost()

        if product_selling_price <= Decimal('0.00'):
            return None
        
        profit_loss = product_selling_price - total_production_cost
        return profit_loss

    def calculate_profit_margin_percentage_value(self):
        product_selling_price = self.calculate_total_modular_product_selling_cost_derived()
        total_production_cost = self.calculate_total_modular_product_purchase_cost()

        if product_selling_price <= Decimal('0.00'):
            return None

        profit_loss = product_selling_price - total_production_cost
        
        if product_selling_price > Decimal('0.00'):
            margin = (profit_loss / product_selling_price) * Decimal('100')
            return margin
        return Decimal('0.00')

    @property
    def formatted_break_even_status(self):
        profit_loss = self.calculate_break_even_amount()
        if profit_loss is None:
            return "N/A (Selling price not set or zero)"
        elif profit_loss > Decimal('0.00'):
            return f"Profit: ${profit_loss:.2f}"
        elif profit_loss < Decimal('0.00'):
            return f"Loss: ${abs(profit_loss):.2f} (Below Break-Even)"
        else:
            return "Break-Even (Zero Profit)"

    @property
    def formatted_profit_margin(self):
        margin_value = self.calculate_profit_margin_percentage_value()
        if margin_value is None:
            return "N/A (Selling price not set or zero)"
        else:
            return f"{margin_value:.2f}%"

    def calculate_metal_cost(self):
        total_cost = Decimal('0.00')
        return total_cost

    def apply_coupon(self, coupon_code):
        pass

# --- ModularProductModule (Intermediary: Links ModularProduct to Module, specifying quantity and position) ---
class ModularProductModule(models.Model):
    modular_product = models.ForeignKey(ModularProduct, related_name='modular_product_modules', on_delete=models.CASCADE)
    module = models.ForeignKey(Module, related_name='module_product_usages', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, help_text="Number of this module used in the product.")
    
    # --- 3D Positioning Data for Module within Product ---
    # These coordinates are relative to the ModularProduct's origin.
    position_x = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="X position (mm) of the module within the product assembly.")
    position_y = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Y position (mm) of the module within the product assembly.")
    position_z = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Z position (mm) of the module within the product assembly.")
    orientation_roll = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Roll rotation (degrees) for 3D visualization.")
    orientation_pitch = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Pitch rotation (degrees) for 3D visualization.")
    orientation_yaw = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Yaw rotation (degrees) for 3D visualization.")
    
    class Meta:
        verbose_name = "Modular Product Module Component"
        verbose_name_plural = "Modular Product Module Components"

    def __str__(self):
        return f"{self.quantity}x {self.module.name} in {self.modular_product.name}"

     # @property
    # def get_assembled_3d_model_url(self):
    #     """
    #     Returns the URL to the assembled 3D model file.
    #     This could trigger regeneration if the model is outdated/missing.
    #     """
    #     if self.assembled_model_3d_file:
    #         # Logic to check assembly_hash and trigger async regeneration
    #         return self.assembled_model_3d_file.url
    #     return None

    # def _calculate_current_assembly_hash(self):
    #     """Helper to calculate a hash for the entire assembly."""
    #     # Combine hashes/IDs of all related ModularProductModules,
    #     # their Modules, their Parts, and all Constraints and Overrides.
    #     pass

    # def _generate_assembled_3d_model(self):
    #     """
    #     Placeholder for triggering the full assembly 3D model generation.
    #     This would involve fetching all child Parts, their specific dimensions based on constraints,
    #     generating individual part models (if not already generated), and then
    #     assembling them into a single scene, applying transformations (position, rotation).
    #     """
    #     # from some_3d_assembly_module import assemble_glb_for_product_async
    #     # assemble_glb_for_product_async.delay(self.id)
    #     pass

# --- Constraint (Product-level variables for formulas) ---
class Constraint(models.Model):
    product = models.ForeignKey('ModularProduct', related_name='constraints', on_delete=models.CASCADE)
    abbreviation = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('product', 'abbreviation')
        verbose_name = "Product Constraint"
        verbose_name_plural = "Product Constraints"

    def __str__(self):
        return f"{self.product.name}: {self.abbreviation} = {self.value}"

# --- ModularProductMaterialOverride (Product-specific material pricing) ---
class ModularProductMaterialOverride(models.Model):
    modular_product = models.ForeignKey(
        'ModularProduct',
        on_delete=models.CASCADE,
        related_name='material_overrides',
        help_text="The modular product this override applies to."
    )
    wooden_material = models.ForeignKey(
        WoodMaterial,
        on_delete=models.PROTECT,
        related_name='product_material_overrides',
        help_text="The specific WoodEn material being overridden or specified."
    )
    is_default = models.BooleanField(default=False)
    override_purchase_price_sft = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Negotiated purchase price per square foot for this material ONLY for this product."
    )
    override_selling_price_sft = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Negotiated selling price per square foot for this material ONLY for this product."
    )
    is_preferred = models.BooleanField(
        default=True,
        help_text="Is this material explicitly preferred or allowed for this product?"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any specific notes about this material override."
    )

    class Meta:
        unique_together = ('modular_product', 'wooden_material')
        verbose_name = "Modular Product Material Override"
        verbose_name_plural = "Modular Product Material Overrides"

    def __str__(self):
        return (f"{self.modular_product.name} - {self.wooden_material.name} "
                f"(P: ${self.override_purchase_price_sft or 'Default'} / S: ${self.override_selling_price_sft or 'Default'})")

# --- Coupon Model ---
class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until
    
    def __str__(self):
        return f"{self.code} ({self.discount_percentage}%)"

# --- Review Model ---
class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

class GlobalSetting(models.Model):
    name = models.CharField(max_length=255, unique=True)
    decimal_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    string_value = models.CharField(max_length=255, null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_setting(cls, setting_name, default, value_type='string'):
        try:
            # FIX: Change 'setting_name=setting_name' to 'name=setting_name'
            setting = cls.objects.get(name=setting_name)
            if value_type == 'decimal':
                return setting.decimal_value if setting.decimal_value is not None else default
            elif value_type == 'boolean':
                return setting.boolean_value if setting.boolean_value is not None else default
            return setting.string_value if setting.string_value is not None else default
        except cls.DoesNotExist:
            print(f"WARNING: GlobalSetting '{setting_name}' not found. Using default value: {default}")
            return default
        except Exception as e:
            # Added more specific error logging for the global setting retrieval
            print(f"An unexpected ERROR occurred retrieving setting '{setting_name}': {e}")
            return default
# --- New Models for Layout/Rooms (Commented for future use) ---
# class Building(models.Model):
#     name = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)
#     # total_area_sqft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     # address = models.CharField(max_length=255, blank=True, null=True)
#     # owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     # ... other building-level properties ...
#     # layout_2d_image = models.ImageField(upload_to='building_layouts/', null=True, blank=True,
#     #     help_text="Optional 2D blueprint/layout image for reference.")
#     # final_3d_model = models.FileField(upload_to='building_3d_models/', null=True, blank=True,
#     #     help_text="The complete 3D model of the building/layout (e.g., GLB).")
#
#     # def __str__(self):
#     #     return self.name
#
# class Floor(models.Model):
#     building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
#     floor_number = models.PositiveIntegerField(default=1)
#     height_mm = models.DecimalField(max_digits=10, decimal_places=2, help_text="Default floor height in mm")
#     # ... other floor-level properties ...
#
#     class Meta:
#         unique_together = ('building', 'floor_number')
#         ordering = ['floor_number']
#
#     # def __str__(self):
#     #     return f"{self.building.name} - Floor {self.floor_number}"
#
# class Room(models.Model):
#     floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
#     name = models.CharField(max_length=255)
#     # Type of room, links to a "Module" that defines its typical contents (e.g., "Kitchen Module")
#     room_module_type = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True,
#         help_text="The type of module this room represents (e.g., Kitchen, Bathroom).")
#
#     # Spatial positioning and dimensions of the room within the floor plan
#     # Using a simple 2D bounding box for initial layout
#     x_position_mm = models.DecimalField(max_digits=10, decimal_places=2)
#     y_position_mm = models.DecimalField(max_digits=10, decimal_places=2)
#     length_mm = models.DecimalField(max_digits=10, decimal_places=2)
#     width_mm = models.DecimalField(max_digits=10, decimal_places=2)
#     height_mm = models.DecimalField(max_digits=10, decimal_places=2,
#         help_text="Specific height for this room, overrides floor default if set.",
#         null=True, blank=True)
#
#     # Additional properties for room specific constraints or features
#     # custom_constraints = models.JSONField(null=True, blank=True,
#     #     help_text="Specific constraints for this room, overriding module defaults.")
#
#     # Reference to the actual ModularProduct instance that represents the content of this room
#     # This ModularProduct would have its own constraints derived from the Room's dimensions.
#     # associated_modular_product = models.OneToOneField(ModularProduct, on_delete=models.SET_NULL, null=True, blank=True,
#     #     help_text="The generated modular product representing the detailed interior of this room.")
#
#     # def __str__(self):
#     #     return f"{self.name} on Floor {self.floor.floor_number} of {self.floor.building.name}"
#
# # Potentially a model for connecting rooms, or defining openings
# # class Doorway(models.Model):
# #     room1 = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='doorways_from')
# #     room2 = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='doorways_to', null=True, blank=True) # Can connect to exterior
# #     # position (x, y along wall segment), width, height
# #     # door_part = models.ForeignKey(Part, on_delete=models.SET_NULL, null=True, blank=True, help_text="The actual door part/component")
# #     pass