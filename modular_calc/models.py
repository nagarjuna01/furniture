#C:\Users\USER\furniture\modular_calc\models.py
import uuid
from django.db import models
from accounts.models.base import TenantModel, GlobalOrTenantModel
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware

class ModularProductCategory(GlobalOrTenantModel):
    name = models.CharField(max_length=255)
    class Meta:
        unique_together = ('tenant','name')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)
    
class ModularProductType(GlobalOrTenantModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ModularProductCategory, on_delete=models.CASCADE)
    class Meta:
        unique_together = ("tenant","category", "name")
        ordering =['name']
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)

class ModularProductModel(GlobalOrTenantModel):
    name = models.CharField(max_length=255)
    type = models.ForeignKey(ModularProductType, on_delete=models.CASCADE)
    class Meta:
        unique_together = ("tenant","type", "name")
        ordering = ['name']
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)

class ModularProduct(TenantModel):

    """
    Template of a modular product; only expressions & metadata live here.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ModularProductCategory,on_delete=models.PROTECT,blank=False,null=False)
    type = models.ForeignKey(ModularProductType,on_delete=models.SET_NULL,blank=True,null=True)
    productmodel = models.ForeignKey(ModularProductModel,on_delete=models.SET_NULL,blank=True,null=True)
    is_public = models.BooleanField(default=False,help_text="If checked, this product will appear in the public Lead-Gen marketplace.")
    product_validation_expression = models.TextField(blank=True,help_text="e.g., '600 <= product_width <= 2400 and 300 <= product_depth <= 700'")
    three_d_asset = models.FileField(upload_to="3d/", blank=True, null=True)  # GLB/GLTF
    two_d_template_svg = models.TextField(blank=True, help_text="SVG template with {{placeholders}}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant","productmodel", "name")
        ordering = ["name"]
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)

class ProductParameter(TenantModel):
    product = models.ForeignKey(ModularProduct,on_delete=models.CASCADE, related_name="parameters",help_text="The product this parameter belongs to.")
    name = models.CharField(max_length=50, help_text="The variable name used in equations (e.g., 'product_length', 'unit_gap').")
    abbreviation = models.CharField(max_length=10, help_text="A short abbreviation for display (e.g., 'L', 'W', 'H').")
    default_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="A default value for the parameter.")
    description = models.TextField(blank=True,help_text="Explains the purpose and constraints of this parameter.")

    class Meta:
        unique_together = ("tenant","product", "name")
        ordering = ["product", "name"]

    def __str__(self):
        return f"{self.product.name} / {self.name} ({self.abbreviation})"
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        self.abbreviation = self.abbreviation.upper()
        super().save(*args, **kwargs)

class PartTemplate(TenantModel):
    
    product = models.ForeignKey(ModularProduct, on_delete=models.CASCADE, related_name="part_templates")
    name = models.CharField(max_length=255)
    shape_type = models.CharField(max_length=50, default='RECT')
    part_length_equation = models.CharField(max_length=255)   # e.g. "product_height"
    part_width_equation  = models.CharField(max_length=255)   # e.g. "product_depth - part_thickness"
    part_qty_equation    = models.CharField(max_length=255, default="1")
    param1_eq = models.CharField(max_length=255, null=True, blank=True)
    param2_eq = models.CharField(max_length=255, null=True, blank=True)
    shape_wastage_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    three_d_asset = models.FileField(upload_to="3d/parts/", blank=True, null=True)  # GLB/GLTF
    two_d_template_svg = models.TextField(blank=True)

    class Meta:
        unique_together = ("product", "name","tenant")
        ordering = ["product__name", "name"]

    def __str__(self):
        return f"{self.product.name} / {self.name}"
    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)


class PartMaterialWhitelist(TenantModel):
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
    material_selection = models.ForeignKey(PartMaterialWhitelist, related_name="edgeband_options", on_delete=models.CASCADE)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    edgeband = models.ForeignKey(EdgeBand, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)
    class Meta:
        unique_together = ("material_selection","side", "edgeband","tenant")


class ProductHardwareRule(TenantModel):
    product = models.ForeignKey(ModularProduct, on_delete=models.CASCADE, related_name="hardware_rules")
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE)
    quantity_equation = models.CharField(max_length=255,blank= True,null=True)
    applicability_condition = models.CharField(max_length=255, blank=True, default="")

class PartHardwareRule(TenantModel):
    part_template = models.ForeignKey(PartTemplate, on_delete=models.CASCADE, related_name="hardware_rules")
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE)
    quantity_equation = models.CharField(max_length=255, default="1") 
    applicability_condition = models.TextField(blank=True) 
    class Meta:
        unique_together = ("part_template", "hardware","tenant")