import uuid
from django.db import models
from accounts.models.base import TenantModel, GlobalOrTenantModel
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware


class ModularProductCategory(GlobalOrTenantModel):
    name = models.CharField(max_length=255, unique= True)
    class Meta:
        unique_together = ('tenant','name')
        ordering = ['name']
    def __str__(self):
        return self.name
    
class ModularProductType(GlobalOrTenantModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ModularProductCategory, on_delete=models.CASCADE)
    class Meta:
        unique_together = ("tenant","category", "name")
        ordering =['name']
    def __str__(self):
        return self.name

class ModularProductModel(GlobalOrTenantModel):
    name = models.CharField(max_length=255)
    type = models.ForeignKey(ModularProductType, on_delete=models.CASCADE)
    class Meta:
        unique_together = ("tenant","type", "name")
        ordering = ['name']
    def __str__(self):
        return self.name

class ModularProduct(TenantModel):

    """
    Template of a modular product; only expressions & metadata live here.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ModularProductCategory,
    on_delete=models.PROTECT,
    blank=False,
    null=False
    )

    type = models.ForeignKey(
        ModularProductType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    productmodel = models.ForeignKey(
        ModularProductModel,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    
    product_validation_expression = models.TextField(
        blank=True,
        help_text="e.g., '600 <= product_width <= 2400 and 300 <= product_depth <= 700'"
    )

    # Optional 3D/2D assets at product level
    three_d_asset = models.FileField(upload_to="3d/", blank=True, null=True)  # GLB/GLTF
    two_d_template_svg = models.TextField(blank=True, help_text="SVG template with {{placeholders}}")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant","productmodel", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name

class ProductParameter(TenantModel):
    """
    Stores user-defined parameters/variables (name, value) for a specific ModularProduct.
    These are used as inputs to the geometry equations.
    """
    product = models.ForeignKey(
        ModularProduct, 
        on_delete=models.CASCADE, 
        related_name="parameters",
        help_text="The product this parameter belongs to."
    )
    
    # The variable name used in equations (e.g., 'product_length', 'product_width')
    name = models.CharField(
        max_length=50, 
        help_text="The variable name used in equations (e.g., 'product_length', 'unit_gap')."
    )
    
    # A short, unique abbreviation for use in UI/documentation (e.g., 'L', 'W')
    abbreviation = models.CharField(
        max_length=10, 
        help_text="A short abbreviation for display (e.g., 'L', 'W', 'H')."
    )
    
    # The default numerical value (optional, as the final value might come from user input)
    default_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="A default value for the parameter."
    )
    
    # Optional: A description to guide the user/admin
    description = models.TextField(
        blank=True,
        help_text="Explains the purpose and constraints of this parameter."
    )

    class Meta:
        unique_together = ("tenant","product", "name")
        ordering = ["product", "name"]

    def __str__(self):
        return f"{self.product.name} / {self.name} ({self.abbreviation})"

class PartTemplate(TenantModel):
    """
    LAYER 1: Geometry equations; LAYER 2: thickness/edgebands.
    Admin writes equations in terms of product_* and part_thickness.
    """
    product = models.ForeignKey(ModularProduct, on_delete=models.CASCADE, related_name="part_templates")
    name = models.CharField(max_length=255)

    # LAYER 1 (Equations)
    part_length_equation = models.CharField(max_length=255)   # e.g. "product_height"
    part_width_equation  = models.CharField(max_length=255)   # e.g. "product_depth - part_thickness"
    part_qty_equation    = models.CharField(max_length=255, default="1")

    # LAYER 2 (Thickness + edge bands)

    # Default (admin preselected) edge bands – optional per side
    edgeband_top    = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_bottom = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_left   = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_right  = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    shape_wastage_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    # Optional 3D/2D assets at part level (overrides product assets)
    three_d_asset = models.FileField(upload_to="3d/parts/", blank=True, null=True)  # GLB/GLTF
    two_d_template_svg = models.TextField(blank=True)

    class Meta:
        unique_together = ("product", "name","tenant")
        ordering = ["product__name", "name"]

    def __str__(self):
        return f"{self.product.name} / {self.name}"


class PartMaterialWhitelist(TenantModel):
    """
    Admin whitelists materials AFTER automatic thickness filtering.
    """
    part_template = models.ForeignKey(PartTemplate, on_delete=models.CASCADE, related_name="material_whitelist")
    material = models.ForeignKey(WoodMaterial, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("part_template", "material","tenant")


class PartEdgeBandWhitelist(TenantModel):
    SIDE_CHOICES = [
        ("top", "Top"),
        ("bottom", "Bottom"),
        ("left", "Left"),
        ("right", "Right"),
    ]
    part_template = models.ForeignKey(PartTemplate, on_delete=models.CASCADE, related_name="edgeband_whitelist")
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    edgeband = models.ForeignKey(EdgeBand, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("part_template","side", "edgeband","tenant")


class ProductHardwareRule(TenantModel):
    product = models.ForeignKey(
        ModularProduct, on_delete=models.CASCADE, related_name="hardware_rules"
    )
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE)

    quantity_equation = models.CharField(max_length=255,blank= True,null=True)

    applicability_condition = models.CharField(
        max_length=255, blank=True, default=""
    )

class PartHardwareRule(TenantModel):
    part_template = models.ForeignKey(PartTemplate, on_delete=models.CASCADE, related_name="hardware_rules")
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE)
    
    # Equation to calculate quantity (e.g., 'part_width / 600 * 2')
    quantity_equation = models.CharField(max_length=255, default="1") 
    
    # Optional: Condition for when this hardware applies (e.g., 'part_is_drawer == True')
    applicability_condition = models.TextField(blank=True) 

    class Meta:
        unique_together = ("part_template", "hardware","tenant")