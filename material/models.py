from django.db import models
from django.core.mail import send_mail
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField

class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)  # Optional, you can add a description
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Convert name to uppercase
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name
#edgeband


class EdgebandName(models.Model):
    depth = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Depth in mm, e.g., 2.00"
    )
    name = models.CharField(
        max_length=255,
        editable=False,
        unique=True
    )

    def save(self, *args, **kwargs):
        # Auto-generate name: "EDGEBAND <DEPTH>MM"
        self.name = f"EDGEBAND {self.depth}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class EdgeBand(models.Model):
    edgeband_name = models.ForeignKey('EdgebandName', on_delete=models.CASCADE)
    e_thickness = models.DecimalField(max_digits=5, decimal_places=2)
    brand = models.ForeignKey('Brand', on_delete=models.SET_NULL, null=True)
    p_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    s_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        unique_together = ('edgeband_name', 'e_thickness', 'brand')

    def clean(self):
        super().clean()
        if self.p_price is not None and self.p_price < 0:
            raise ValidationError("Purchase price cannot be negative.")
        if self.s_price is not None and self.s_price < 0:
            raise ValidationError("Selling price cannot be negative.")
        if self.e_thickness is not None and self.e_thickness < 0:
            raise ValidationError("Edge band thickness cannot be negative.")

    @property
    def sl_price(self):
        if self.p_price is not None:
            return (self.p_price * Decimal('1.2')).quantize(Decimal('0.01'))
        return Decimal('0.00')

    def __str__(self):
        return f"{self.edgeband_name} (Thickness {self.e_thickness}mm)"
    

class Category(models.Model):
    name = models.CharField(max_length=100, unique= True)
    
    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Convert name to uppercase
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name

class CategoryTypes(models.Model):
    category =  models.ForeignKey(Category, on_delete=models.CASCADE, related_name='models')   
    name = models.CharField(max_length=100)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['category', 'name'], name='unique_category_type_name')
        ]
    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Convert name to uppercase
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name

class CategoryModel(models.Model):
    model_category = models.ForeignKey(CategoryTypes, on_delete= models.CASCADE, related_name= 'Models')
    name = models.CharField(max_length=100)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['model_category', 'name'], 
                name='unique_model_name_per_category_type'
            )
        ]
    
    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Convert name to uppercase
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name
    

class WoodEn(models.Model):
    DIMENSION_UNITS = [
        ('mm', 'Millimeter'),
        ('cm', 'Centimeter'),
        ('m', 'Meter'),
        ('inch', 'Inch'),
        ('ft', 'Foot'),
    ]
    PRICE_CHOICES = [
        ('panel', 'Panel Price'),
        ('sft', 'Price Per Sqft'),
    ]
    material_grp = models.ForeignKey(Category, on_delete=models.PROTECT,related_name= 'wooden')
    material_type = models.ForeignKey(CategoryTypes, on_delete=models.PROTECT,related_name='wooden')
    material_model = models.ForeignKey(CategoryModel, on_delete=models.SET_NULL, related_name='wooden_models', null=True)
    name = models.CharField(max_length=255,blank=True,null=True)
    grain = models.CharField(max_length=3, choices=[('0', 'Horizontal'), ('1', 'None'), ('2', 'Vertical')], default= '2')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    length = models.IntegerField()
    length_unit = models.CharField(max_length=5, choices=DIMENSION_UNITS, default='mm')
    width = models.IntegerField()
    width_unit= models.CharField(max_length=5, choices=DIMENSION_UNITS, default='mm')
    thickness = models.DecimalField(max_digits=5, decimal_places=2)
    thickness_unit = models.CharField(max_length=5, choices=DIMENSION_UNITS, default='mm')
    p_price = models.DecimalField(max_digits=8, decimal_places=2, default=0,editable=False)  # Panel Cost Price (User input)
    p_price_sft = models.DecimalField(max_digits=8, decimal_places=2, default=0, editable=False)  # Price per Sqft Cost Price (Calculated)

    # Choices: Panel or Price per Sqft
    cost_price = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    costprice_type = models.CharField(max_length=10, choices=PRICE_CHOICES, default='panel')  # User selects: panel or per sq ft for cost price

    # Selling Prices
    s_price = models.DecimalField(max_digits=8, decimal_places=2, default=0,editable=False)  # Panel Selling Price (User input)
    s_price_sft = models.DecimalField(max_digits=8, decimal_places=2, default=0, editable=False)  # Price per Sqft Selling Price (Calculated)
    sell_price = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    sellprice_type = models.CharField(max_length=10, choices=PRICE_CHOICES, default='panel')  # User selects: panel or per sq ft for sell price
    color = models.CharField(max_length=50,default='no color')
    is_sheet = models.BooleanField(default=True, help_text="Is this WoodEn item a standard sheet material for cutting optimization?")

    class Meta:
        # Define the combination of fields that must be unique
        unique_together = ('name', 'material_grp', 'material_type', 'material_model', 'brand')
        
    def clean(self):
        if self.cost_price < 0 or self.sell_price < 0:
            raise ValidationError("Prices cannot be negative.")

    def convert_to_mm(self, value, unit):
        try:
            value = Decimal(value)
        except (TypeError, InvalidOperation):
            raise ValueError(f"Cannot convert value to Decimal: {value}")

        if unit == 'mm':
            return value
        elif unit == 'cm':
            return value * Decimal('10')
        elif unit == 'm':
            return value * Decimal('1000')
        elif unit == 'inch':
            return value * Decimal('25.4')
        elif unit == 'ft':
            return value * Decimal('304.8')
        else:
            raise ValueError("Unsupported unit")


    def convert_to_feet(self, value, unit):
        """Helper function to convert the value to feet (used for price calculations)."""
        if value is None:
            return Decimal('0.0') # Or raise ValueError("Cannot convert None to feet")

        unit_conversion = {
            'mm': 0.00328084,    # Millimeter to Feet
            'cm': 0.0328084,     # Centimeter to Feet
            'm': 3.28084,        # Meter to Feet
            'inch': 0.0833333,   # Inch to Feet
            'ft': 1,             # Foot to Foot
        }

        return Decimal(value) * Decimal(unit_conversion.get(unit, 1))

    # --- NEW `to_sft` method ---
    def to_sft(self):
        """
        Calculates the area of the WoodEn sheet in square feet based on its
        current length and width (which are stored in mm after save).
        """
        # Ensure dimensions are in Decimal for accurate calculations
        length_mm = Decimal(self.length)
        width_mm = Decimal(self.width)

        # Convert the millimeter dimensions to feet using the helper
        length_in_ft = self.convert_to_feet(length_mm, 'mm')
        width_in_ft = self.convert_to_feet(width_mm, 'mm')

        area_sft = length_in_ft * width_in_ft
        return area_sft
    # --- END NEW `to_sft` method ---


    def calculate_and_store_prices(self):

        if self.length is None or self.width is None or self.length_unit is None or self.width_unit is None:
            print("Length or width is None, cannot calculate area-based prices.")
            return # Exit the function if dimensions are missing

        # Use the new to_sft method to get the area
        area_sft = self.to_sft()
        # print(f"Calculated area for pricing: {area_sft} sq ft") # Moved debug print here

        # Now calculate the prices based on the chosen price type
        if self.costprice_type == 'panel':  # User entered panel price
            if self.cost_price != 0:  # If panel price is provided
                self.p_price = self.cost_price  # Store the panel price
                # Handle potential division by zero if area_sft is 0
                self.p_price_sft = self.cost_price / area_sft if area_sft != 0 else Decimal('0.00')
        elif self.costprice_type == 'sft':  # User entered price per square foot
            if self.cost_price != 0:  # If price per square foot is provided
                self.p_price = self.cost_price * area_sft  # Calculate panel price
                self.p_price_sft = self.cost_price  # Store price per square foot

    # ** Selling Price Calculation:**
        if self.sellprice_type == 'panel':  # User entered panel selling price
            if self.sell_price != 0:  # If panel selling price is provided
                self.s_price = self.sell_price  # Store the selling price
                # Handle potential division by zero if area_sft is 0
                self.s_price_sft = self.sell_price / area_sft if area_sft != 0 else Decimal('0.00')
        elif self.sellprice_type == 'sft':  # User entered selling price per square foot
            if self.sell_price != 0:  # If selling price per square foot is provided
                self.s_price = self.sell_price * area_sft  # Calculate panel selling price
                self.s_price_sft = self.sell_price  # Store selling price per square foot


    def save(self, *args, **kwargs):
        # Store length and width in mm for internal consistency before saving to the database
        # These conversions use the *original* length/width and their units
        self.length = self.convert_to_mm(self.length, self.length_unit)
        self.width = self.convert_to_mm(self.width, self.width_unit)
        self.thickness = self.convert_to_mm(self.thickness, self.thickness_unit)

        # Update the units to 'mm' since values are now stored in mm
        self.length_unit = 'mm'
        self.width_unit = 'mm'
        self.thickness_unit = 'mm'

        # Calculate prices (based on feet) before saving to the database
        self.calculate_and_store_prices()
        self.name = self.name.upper()
        # Save the data in the database (length, width, and thickness are stored in mm)
        super(WoodEn, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.material_grp}, {self.material_type}, {self.thickness}mm)'
    
class HardwareGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)  
            
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        # Ensure the name is uppercase
        self.name = self.name.upper()
        super().save(*args, **kwargs)

class Hardware(models.Model):
    h_group = models.ForeignKey(HardwareGroup, related_name='hardware_items', on_delete=models.CASCADE)
    h_name = models.CharField(max_length=50)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True) 
    unit = models.CharField(max_length=32, choices=[('set', 'set'), ('each', 'each')], default= 'each') 
    p_price = models.DecimalField(max_digits=8,decimal_places=2,default=0)
    s_price = models.DecimalField(max_digits=8,decimal_places=2,default=0)
    sl_price = models.DecimalField(max_digits=8,decimal_places=2,blank=True, null=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['h_group', 'h_name', 'brand'],
                name='unique_hardware_per_group_brand'
            )
        ]
    @property
    def sl_price(self):
        if self.p_price is not None:
            return (self.p_price * Decimal('1.20')).quantize(Decimal('0.01'))
        return Decimal('0.00')
    
    def save(self, *args, **kwargs):
        self.h_name = self.h_name.upper()
        # No need to calculate sl_price here if it's a @property
        super().save(*args, **kwargs)

    def clean(self):
        super().clean() # Call super's clean method
        if self.p_price is not None and self.p_price < 0:
            raise ValidationError("Purchase price cannot be negative.")
        if self.s_price is not None and self.s_price < 0:
            raise ValidationError("Sale price cannot be negative.")
        # If sl_price is a @property, you don't validate it here, as it's derived.
        # If it were a stored field, you would:
        # if self.sl_price is not None and self.sl_price < 0:
        #     raise ValidationError("Sale list price cannot be negative.")

    def __str__(self):
        return f"{self.h_name} ({self.h_group.name})" 

