# material/serializers.py

from rest_framework import serializers
from decimal import Decimal, InvalidOperation # Keep Decimal and InvalidOperation for validation
from .models import ( # Import all necessary models from your material app
    Brand, EdgeBand, Category, CategoryTypes, CategoryModel,
    WoodEn, HardwareGroup, Hardware
)

# --------------------- BRAND ---------------------
class BrandSerializer(serializers.ModelSerializer):
    """
    Unified serializer for the Brand model.
    Handles both reading and writing Brand instances.
    """
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at'] # Typically, creation timestamp is read-only

# --------------------- CATEGORY STRUCTURE ---------------------
class CategorySerializer(serializers.ModelSerializer):
    """
    Unified serializer for the Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'name']

class CategoryTypesSerializer(serializers.ModelSerializer):
    """
    Unified serializer for CategoryTypes.
    Allows setting 'category' by ID during writes, and nesting 'Category' for reads.
    """
    category = CategorySerializer(read_only=True) # Nested for read operations (GET)
    category_id = serializers.PrimaryKeyRelatedField( # For write operations (POST/PUT/PATCH)
        queryset=Category.objects.all(), 
        source='category', # Maps to the 'category' ForeignKey field
        write_only=True,   # Only used for writing
        required=True      # Category is likely required for CategoryTypes
    )

    class Meta:
        model = CategoryTypes
        fields = ['id', 'name', 'category', 'category_id'] # Include both
        # 'category' is implicitly read-only because it's a nested serializer
        # 'category_id' is explicitly write-only

class CategoryModelSerializer(serializers.ModelSerializer):
    """
    Unified serializer for CategoryModel.
    Allows setting 'model_category' by ID during writes, and nesting 'CategoryTypes' for reads.
    """
    model_category = CategoryTypesSerializer(read_only=True) # Nested for read operations (GET)
    model_category_id = serializers.PrimaryKeyRelatedField( # For write operations (POST/PUT/PATCH)
        queryset=CategoryTypes.objects.all(), 
        source='model_category', # Maps to the 'model_category' ForeignKey field
        write_only=True,
        required=True # Model Category is likely required
    )

    class Meta:
        model = CategoryModel
        fields = ['id', 'name', 'model_category', 'model_category_id'] # Include both


# --------------------- EDGEBAND ---------------------
class EdgeBandSerializer(serializers.ModelSerializer):
    """
    Unified serializer for EdgeBand.
    Handles both input (brand_id) and output (nested brand, sl_price).
    """
    brand = BrandSerializer(read_only=True) # Nested serializer for brand on read
    brand_id = serializers.PrimaryKeyRelatedField( # Writable field for brand's ID
        queryset=Brand.objects.all(), 
        source='brand', 
        write_only=True, 
        required=False, 
        allow_null=True # Allow null if your EdgeBand.brand field allows it
    )
    sl_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True) # Assuming sl_price is a model property/calculated field

    class Meta:
        model = EdgeBand
        fields = [
            'id', 'edge_depth', 'e_thickness', 
            'brand', 'brand_id', # Include both read-only and write-only versions
            'p_price', 's_price', 'sl_price' # sl_price is read_only
        ]
        # If 'name' is also a field in EdgeBand, make sure to include it.
        # e.g., fields = ['id', 'name', 'edge_depth', ...]

    # Keep validation methods from your original EdgeBandInputSerializer
    def validate_p_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Purchase price must be non-negative.")
        return value

    def validate_s_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Selling price must be non-negative.")
        return value


# --------------------- WOODEN ---------------------
class WoodEnSerializer(serializers.ModelSerializer):
    """
    Unified serializer for WoodEn.
    Handles complex nested relationships for read, and ID-based setting for write.
    """
    # Nested serializers for read-only display
    material_grp = CategorySerializer(read_only=True)
    material_type = CategoryTypesSerializer(read_only=True)
    material_model = CategoryModelSerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    
    # Use the unified EdgeBandSerializer for nested representation
    compatible_edgebands = EdgeBandSerializer(many=True, read_only=True) 

    # Writable fields for setting relationships by ID
    material_grp_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='material_grp', write_only=True, required=False, allow_null=True
    )
    material_type_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoryTypes.objects.all(), source='material_type', write_only=True, required=False, allow_null=True
    )
    material_model_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoryModel.objects.all(), source='material_model', write_only=True, required=False, allow_null=True
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(), source='brand', write_only=True, required=False, allow_null=True
    )
    # For ManyToMany relationships, use a PrimaryKeyRelatedField with many=True
    compatible_edgebands_ids = serializers.PrimaryKeyRelatedField(
        queryset=EdgeBand.objects.all(), 
        source='compatible_edgebands', # Maps to the ManyToMany field
        many=True, 
        write_only=True, 
        required=False
    )

    # Assuming these fields are direct model fields that are computed/stored
    # And p_price, p_price_sft, s_price, s_price_sft are properties/methods
    p_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    p_price_sft = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    s_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    s_price_sft = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


    class Meta:
        model = WoodEn
        fields = [
            'id', 'name', # Assuming 'name' is a field on WoodEn
            'length', 'width', 'thickness', 'cost_price', 'sell_price',
            # Read-only nested fields
            'material_grp', 'material_type', 'material_model', 'brand', 'compatible_edgebands',
            # Writable ID fields for relationships
            'material_grp_id', 'material_type_id', 'material_model_id', 'brand_id', 'compatible_edgebands_ids',
            # Read-only calculated price fields
            'p_price', 'p_price_sft', 's_price', 's_price_sft'
        ]

    # Keep validation from your original WoodEnInputSerializer
    def validate(self, data):
        for field in ['length', 'width', 'thickness', 'cost_price', 'sell_price']:
            if field in data and isinstance(data[field], str): # Check if field is present and is a string
                try:
                    data[field] = Decimal(data[field])
                except InvalidOperation:
                    raise serializers.ValidationError({field: "Invalid number format. Must be a valid decimal."})
        
        # Add any other WoodEn specific validation logic here if needed
        # Example: Ensure length, width, thickness are positive
        if 'length' in data and data['length'] <= 0:
            raise serializers.ValidationError({"length": "Length must be positive."})
        if 'width' in data and data['width'] <= 0:
            raise serializers.ValidationError({"width": "Width must be positive."})
        if 'thickness' in data and data['thickness'] <= 0:
            raise serializers.ValidationError({"thickness": "Thickness must be positive."})
        
        return data


# --------------------- HARDWARE ---------------------
class HardwareGroupSerializer(serializers.ModelSerializer):
    """
    Unified serializer for HardwareGroup.
    """
    class Meta:
        model = HardwareGroup
        fields = ['id', 'name']

class HardwareSerializer(serializers.ModelSerializer):
    """
    Unified serializer for Hardware.
    Handles both input (h_group_id, brand_id) and output (nested h_group, brand, sl_price).
    """
    h_group = HardwareGroupSerializer(read_only=True) # Nested for read
    brand = BrandSerializer(read_only=True) # Nested for read
    sl_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True) # Assuming sl_price is a model property/calculated field

    h_group_id = serializers.PrimaryKeyRelatedField( # Writable field for h_group's ID
        queryset=HardwareGroup.objects.all(), 
        source='h_group', 
        write_only=True, 
        required=False, 
        allow_null=True
    )
    brand_id = serializers.PrimaryKeyRelatedField( # Writable field for brand's ID
        queryset=Brand.objects.all(), 
        source='brand', 
        write_only=True, 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = Hardware
        fields = [
            'id', 'h_name', 'unit', 'p_price', 's_price', 'sl_price',
            'h_group', 'h_group_id', # Include both read-only and write-only versions
            'brand', 'brand_id'      # Include both read-only and write-only versions
        ]
        # Make sure 'h_name' is included if it's the primary display field
        # e.g., fields = ['id', 'h_name', 'h_group', 'h_group_id', ...]

    # Keep validation from your original HardwareInputSerializer
    def validate(self, data):
        # Ensure prices are converted to Decimal before comparison
        p_price = data.get('p_price')
        s_price = data.get('s_price')

        if p_price is not None and s_price is not None:
            if not isinstance(p_price, Decimal):
                try: p_price = Decimal(str(p_price))
                except InvalidOperation: raise serializers.ValidationError({"p_price": "Invalid number format."})
            if not isinstance(s_price, Decimal):
                try: s_price = Decimal(str(s_price))
                except InvalidOperation: raise serializers.ValidationError({"s_price": "Invalid number format."})

            if s_price < p_price:
                raise serializers.ValidationError("Sell price must be greater than or equal to purchase price.")
        return data

