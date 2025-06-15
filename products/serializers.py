# from rest_framework import serializers
# from decimal import Decimal, InvalidOperation

# from .models import (
#     ProductCategory, Type, Model, Unit,
#     Product, StandardProduct, CustomProduct, ModularProduct,
#     Part, PartHardware,
#     Module, ModulePart,
#     Constraint, ModularProductModule, ModularProductMaterialOverride,
#     Coupon, Review, StandardProductImage
# )
# from material.models import WoodEn, EdgeBand, Hardware, Brand

# # --- Minimal Material App Serializers (as provided) ---
# class WoodEnMinimalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WoodEn
#         fields = ['id', 'name', 'p_price_sft', 's_price_sft']

# class EdgeBandMinimalSerializer(serializers.ModelSerializer):
#     display_name = serializers.ReadOnlyField(source='__str__')
#     class Meta:
#         model = EdgeBand
#         fields = ['id', 'display_name', 'p_price', 's_price']

# class HardwareMinimalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Hardware
#         fields = ['id', 'h_name', 'p_price']

# class BrandMinimalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Brand
#         fields = ['id', 'name']


# # --- Basic Classification & Units Serializers (No changes) ---
# class ProductCategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductCategory
#         fields = '__all__'

# class TypeSerializer(serializers.ModelSerializer):
#     category = ProductCategorySerializer(read_only=True)
#     category_id = serializers.PrimaryKeyRelatedField(
#         queryset=ProductCategory.objects.all(),
#         source='category',
#         write_only=True # <--- This is the key!
#     )

#     class Meta:
#         model = Type
#         fields = '__all__'

# class ModelSerializer(serializers.ModelSerializer):
#     # This is for reading (when you GET a Model object, it will show the full Type object)
#     type = TypeSerializer(read_only=True) 

#     # This is for writing (when you POST/PUT/PATCH, it expects the Type ID)
#     type_id = serializers.PrimaryKeyRelatedField(
#         queryset=Type.objects.all(), # Ensure all Type objects are queryable
#         source='type',               # This tells DRF to map 'type_id' to the 'type' ForeignKey
#         write_only=True,             # This field will only be used for input, not output
#         required=True                # Make sure it's explicitly required for POST
#     )

#     class Meta:
#         model = Model
#         # Explicitly list the fields, including the new 'type_id'
#         # Ensure 'id', 'name', 'image', 'type', 'type_id' are all here
#         fields = ['id', 'name', 'image', 'type', 'type_id'] 
#         # If 'image' is optional (null=True, blank=True), you don't need to send it in POST initially.
#         extra_kwargs = {'id': {'read_only': False, 'required': False}} # Keep if you need to pass ID for updates

# class UnitSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Unit
#         fields = '__all__'

# class CouponSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Coupon
#         fields = '__all__'

# class ReviewSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField()
#     class Meta:
#         model = Review
#         fields = '__all__'
#         read_only_fields = ('user', 'created_at', 'updated_at')


# # --- Part & Module Serializers ---

# # Writable PartHardware Serializer (if you want to manage hardware directly when creating/updating Parts)
# # If PartHardware is only set in admin, keep PartHardwareSerializer's hardware as read_only=True
# class WritablePartHardwareSerializer(serializers.ModelSerializer):
#     hardware = serializers.PrimaryKeyRelatedField(queryset=Hardware.objects.all()) # Writable by ID
#     class Meta:
#         model = PartHardware
#         fields = ['id', 'hardware', 'quantity_required']
#         extra_kwargs = {'id': {'read_only': False, 'required': False}} # Allow ID for update/delete

# from rest_framework import serializers
# # Make sure to import your Part, WoodEn, EdgeBand models
# # from .models import Part
# # from material.models import WoodEn, EdgeBand # Adjust import path as needed
# # Also import any other serializers needed for nested read-only fields
# # from .serializers import WoodEnMinimalSerializer, EdgeBandMinimalSerializer, WritablePartHardwareSerializer # Ensure these are imported

# class PartSerializer(serializers.ModelSerializer):
#     # --- For Reading (Output) ---
#     material = WoodEnMinimalSerializer(read_only=True)
#     top_edge_band = EdgeBandMinimalSerializer(read_only=True)
#     left_edge_band = EdgeBandMinimalSerializer(read_only=True)
#     bottom_edge_band = EdgeBandMinimalSerializer(read_only=True)
#     right_edge_band = EdgeBandMinimalSerializer(read_only=True)
#     required_hardware = WritablePartHardwareSerializer(many=True, required=False) # Remains writable for nested hardware

#     # --- For Writing (Input) ---
#     # These fields accept IDs and map them to the corresponding ForeignKey
#     material_id = serializers.PrimaryKeyRelatedField(
#         queryset=WoodEn.objects.all(), source='material', write_only=True, required=False, allow_null=True # Allow null if material is not strictly required
#     )
#     top_edge_band_id = serializers.PrimaryKeyRelatedField(
#         queryset=EdgeBand.objects.all(), source='top_edge_band', write_only=True, required=False, allow_null=True
#     )
#     left_edge_band_id = serializers.PrimaryKeyRelatedField(
#         queryset=EdgeBand.objects.all(), source='left_edge_band', write_only=True, required=False, allow_null=True
#     )
#     bottom_edge_band_id = serializers.PrimaryKeyRelatedField(
#         queryset=EdgeBand.objects.all(), source='bottom_edge_band', write_only=True, required=False, allow_null=True
#     )
#     right_edge_band_id = serializers.PrimaryKeyRelatedField(
#         queryset=EdgeBand.objects.all(), source='right_edge_band', write_only=True, required=False, allow_null=True
#     )

#     class Meta:
#         model = Part
#         # Explicitly list ALL fields. This is crucial when mixing read_only nested and write_only PK fields.
#         fields = [
#             'id', 'name', 'description', 
#             'part_length_formula', 'part_width_formula', 'part_thickness_mm', 'part_quantity_formula',
#             'material', 'material_id', # 'material' for read, 'material_id' for write
#             'wastage_factor',
#             'top_edge_band', 'top_edge_band_id',
#             'left_edge_band', 'left_edge_band_id',
#             'bottom_edge_band', 'bottom_edge_band_id',
#             'right_edge_band', 'right_edge_band_id',
#             'cutting_cost_per_meter', 'grooving_cost_per_meter', 'edgeband_cutting_cost_per_meter',
#             'shape_type', 'geometry_features', 'orientation', 'threed_model_file',
#             'required_hardware' # This will be handled by the nested writable serializer
#         ]
#         extra_kwargs = {'id': {'read_only': False, 'required': False}} # Keep if you need to pass ID for updates
#      # fields = [
#         #     'id', 'name', 'part_length_formula', 'part_width_formula',
#         #     'part_thickness_mm', 'material', 'top_edge_band', 'bottom_edge_band',
#         #     'left_edge_band', 'right_edge_band', 'all_around_edge_band',
#         #     'part_quantity_formula', 'cutting_cost_per_meter', 'grooving_cost_per_meter',
#         #     'edgeband_cutting_cost_per_meter', 'wastage_factor',
#         #     'shape_type', 'geometry_features', 'orientation',
#         #     # 'model_3d_file', # If you want to allow direct upload/download of pre-existing models
#         #     # 'geometry_hash',
#         #     # 'get_3d_model_url', # Read-only property for client to fetch generated model
#         #     # 'connection_points',
#         # ]
#         # read_only_fields = ['part_thickness_mm', 'get_3d_model_url', 'geometry_hash']
#         # # If you want to trigger 3D model generation on save (more complex, consider signals/tasks)
#     # # def create(self, validated_data):
#     # #     instance = super().create(validated_data)
#     # #     # instance._generate_3d_model() # Trigger async generation
#     # #     return instance
#     #
#     # # def update(self, instance, validated_data):
#     # #     # Check if geometry-related fields have changed
#     # #     # geometry_fields_changed = False
#     # #     # if any(field in validated_data for field in ['part_length_formula', 'part_width_formula', 'shape_type', 'geometry_features', 'orientation']):
#     # #     #     geometry_fields_changed = True
#     # #     #
#     # #     # instance = super().update(instance, validated_data)
#     # #     #
#     # #     # if geometry_fields_changed:
#     # #     #     # instance._generate_3d_model() # Trigger async generation
#     # #     #     pass
#     # #     return instance

#     # You'll need to update the `update` method to handle the nested _destroy flag for required_hardware
#     # (refer to the ModuleSerializer update method I provided earlier)
#     # The create method for PartHardware should be fine as is since it doesn't use _destroy
#     def create(self, validated_data):
#         required_hardware_data = validated_data.pop('required_hardware', [])
#         part = Part.objects.create(**validated_data)
#         for hardware_data in required_hardware_data:
#             # Note: PartHardware serializer should also use `hardware` for writing, not `hardware_id` if that's how it's defined
#             # If WritablePartHardwareSerializer's `hardware` field is a PrimaryKeyRelatedField, it will take the ID directly.
#             PartHardware.objects.create(part=part, **hardware_data)
#         return part

#     def update(self, instance, validated_data):
#         required_hardware_data = validated_data.pop('required_hardware', None)

#         # Update Part instance fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Handle nested PartHardware (Create, Update, Delete)
#         if required_hardware_data is not None:
#             current_hardware_items = {obj.id: obj for obj in instance.required_hardware.all()}
#             incoming_hardware_ids = set()

#             for item_data in required_hardware_data:
#                 item_id = item_data.get('id')
#                 should_destroy = item_data.pop('_destroy', False) # Safely pop _destroy flag

#                 if item_id: # Existing hardware item
#                     incoming_hardware_ids.add(item_id)
#                     if should_destroy:
#                         if item_id in current_hardware_items:
#                             current_hardware_items[item_id].delete()
#                     else:
#                         if item_id in current_hardware_items:
#                             nested_obj = current_hardware_items[item_id]
#                             for attr, value in item_data.items():
#                                 setattr(nested_obj, attr, value)
#                             nested_obj.save()
#                         else:
#                             # This case means an ID was provided that doesn't exist for this parent.
#                             # Treat as a new item.
#                             PartHardware.objects.create(part=instance, **item_data)
#                 else: # New hardware item (no ID)
#                     if not should_destroy: # Only create if not marked for destruction
#                         PartHardware.objects.create(part=instance, **item_data)
            
#             # Finally, delete any existing items that were NOT sent in the incoming data
#             # AND were not explicitly marked for destruction earlier.
#             for existing_id, existing_obj in current_hardware_items.items():
#                 if existing_id not in incoming_hardware_ids:
#                     if PartHardware.objects.filter(id=existing_id, part=instance).exists():
#                          existing_obj.delete()

#         return instance

# # Writable ModulePart Serializer (if you want to manage parts directly when creating/updating Modules)
# class WritableModulePartSerializer(serializers.ModelSerializer):
#     part = serializers.PrimaryKeyRelatedField(queryset=Part.objects.all()) # Writable by ID
#     class Meta:
#         model = ModulePart
#         fields = ['id', 'part', 'quantity']
#         extra_kwargs = {'id': {'read_only': False, 'required': False}} # Allow ID for update/delete

# class ModulePartDisplaySerializer(serializers.ModelSerializer): # Renamed for clarity if both exist
#     part_name = serializers.CharField(source='part.name', read_only=True)
#     part_width_mm = serializers.DecimalField(source='part.width_mm', max_digits=10, decimal_places=2, read_only=True)
#     part_length_mm = serializers.DecimalField(source='part.length_mm', max_digits=10, decimal_places=2, read_only=True)
#     part_material_id = serializers.IntegerField(source='part.material.id', read_only=True)
#     part_material_type = serializers.CharField(source='part.material.type', read_only=True)
#     part_material_thickness_mm = serializers.DecimalField(source='part.material.thickness_mm', max_digits=10, decimal_places=2, read_only=True)

#     class Meta:
#         model = ModulePart
#         fields = ['id', 'part', 'quantity', 'part_name', 'part_width_mm', 'part_length_mm', 'part_material_id', 'part_material_type', 'part_material_thickness_mm']
#         read_only_fields = ['part_name', 'part_width_mm', 'part_length_mm', 'part_material_id', 'part_material_type', 'part_material_thickness_mm']


# class ModuleDetailSerializer(serializers.ModelSerializer):
#     # These declarations are correct and necessary.
#     detailed_cost_breakdown_blueprint = serializers.SerializerMethodField(read_only=True)
#     packing_analysis = serializers.SerializerMethodField(read_only=True)
#     cost_comparison_with_sheets = serializers.SerializerMethodField(read_only=True)
    
#     # Existing fields that are directly mapped to the model attributes
#     module_parts = WritableModulePartSerializer(many=True, required=False) 
#     calculated_purchase_cost_blueprint = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     calculated_selling_cost_blueprint = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


#     class Meta:
#         model = Module
#         fields = '__all__' 

#      # fields = [
#         #     'id', 'name', 'description', 'default_length_mm', 'default_width_mm',
#         #     'default_height_mm', 'default_depth_mm',
#         #     # 'default_model_3d_file',
#         #     # 'default_connection_points',
#         # ]
    
#     # --- REINSTATED and CORRECTED get_... methods ---

#     def get_detailed_cost_breakdown_blueprint(self, obj):
#         request = self.context.get('request')
#         blade_size_mm_str = request.query_params.get('blade_size_mm', '0.0')
#         try:
#             blade_size_mm = Decimal(blade_size_mm_str)
#         except (ValueError, TypeError, InvalidOperation):
#             blade_size_mm = Decimal('0.0')

#         # Get base detailed cost breakdown from the Module model
#         base_detailed_breakdown = obj.get_module_detailed_cost_breakdown(
#             modular_product_instance=None, 
#             live_constraints=None       
#         )

#         # Get comparison results to extract wastage
#         comparison_results = obj.get_module_cost_comparison_with_sheets(
#             modular_product_instance=None, 
#             live_constraints=None,       
#             rotation_allowed=True,       
#             blade_size_mm=float(blade_size_mm) # Model expects float here
#         )
        
#         # Add Wastage Costs to the Detailed Cost Breakdown Blueprint
#         purchase_breakdown_final = base_detailed_breakdown['purchase_breakdown'].copy() 
#         purchase_breakdown_final['wastage_cost_from_sheets'] = comparison_results['total_purchase_wastage']
#         purchase_breakdown_final['total_purchase_cost'] = (
#             purchase_breakdown_final['total_purchase_cost'] + comparison_results['total_purchase_wastage']
#         ).quantize(Decimal('0.01'))
        
#         selling_breakdown_final = base_detailed_breakdown['selling_breakdown'].copy() 
#         selling_breakdown_final['wastage_cost_from_sheets'] = comparison_results['total_selling_wastage']
#         selling_breakdown_final['total_selling_cost'] = (
#             selling_breakdown_final['total_selling_cost'] + comparison_results['total_selling_wastage']
#         ).quantize(Decimal('0.01'))

#         return {
#             "purchase_breakdown": purchase_breakdown_final,
#             "selling_breakdown": selling_breakdown_final
#         }


#     def get_packing_analysis(self, obj):
#         request = self.context.get('request')
#         blade_size_mm_str = request.query_params.get('blade_size_mm', '0.0')
#         try:
#             blade_size_mm = Decimal(blade_size_mm_str)
#         except (ValueError, TypeError, InvalidOperation):
#             blade_size_mm = Decimal('0.0')

#         return obj.get_module_packing_analysis(
#             modular_product_instance=None, 
#             live_constraints=None,       
#             rotation_allowed=True,       
#             blade_size_mm=float(blade_size_mm) 
#         )

#     def get_cost_comparison_with_sheets(self, obj):
#         request = self.context.get('request')
#         blade_size_mm_str = request.query_params.get('blade_size_mm', '0.0')
#         try:
#             blade_size_mm = Decimal(blade_size_mm_str)
#         except (ValueError, TypeError, InvalidOperation):
#             blade_size_mm = Decimal('0.0')
            
#         comparison_results = obj.get_module_cost_comparison_with_sheets(
#             modular_product_instance=None, 
#             live_constraints=None,       
#             rotation_allowed=True,       
#             blade_size_mm=float(blade_size_mm) 
#         )
        
#         return {
#             **comparison_results['comparison_breakdown_data'], 
#             "status": comparison_results.get('status', 'N/A'), 
#             "module_cost_blueprint": comparison_results['module_cost_blueprint_base_total'], 
#             "blade_size_used_mm": float(comparison_results['blade_size_used_mm']), 
#             "note": comparison_results['note'] 
#         }

#     # --- to_representation is now simpler, letting super().to_representation handle SerializerMethodFields ---
#     def to_representation(self, instance):
#         # This calls super().to_representation, which in turn will call all the get_... methods
#         # defined above for fields declared as SerializerMethodField.
#         representation = super().to_representation(instance)
        
#         # You can add any other *global* manipulations to the representation here
#         # that don't fit into a single get_ method.
        
#         print("DEBUG: ModuleDetailSerializer.to_representation is being called and finished!") 
#         return representation

#     # --- Create and Update methods (kept as they were provided) ---
#     def create(self, validated_data):
#         module_parts_data = validated_data.pop('module_parts', [])
#         module = Module.objects.create(**validated_data)
#         for part_data in module_parts_data:
#             if 'id' in part_data and part_data['id'] is not None:
#                 raise serializers.ValidationError("Cannot provide 'id' for new module parts during module creation.")
#             ModulePart.objects.create(module=module, **part_data)
#         return module

#     def update(self, instance, validated_data):
#         module_parts_data = validated_data.pop('module_parts', [])

#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Handle nested ModuleParts (Create, Update, Delete)
#         if module_parts_data is not None:
#             current_module_parts = {obj.id: obj for obj in instance.module_parts.all()}
#             incoming_module_part_ids = set()

#             for item_data in module_parts_data:
#                 item_id = item_data.get('id')
#                 should_destroy = item_data.pop('_destroy', False) 

#                 if item_id: # Existing module part
#                     incoming_module_part_ids.add(item_id)
#                     if should_destroy:
#                         if item_id in current_module_parts:
#                             current_module_parts[item_id].delete()
#                     else:
#                         if item_id in current_module_parts:
#                             nested_obj = current_module_parts[item_id]
#                             for attr, value in item_data.items():
#                                 setattr(nested_obj, attr, value)
#                             nested_obj.save()
#                         else:
#                             ModulePart.objects.create(module=instance, **item_data)
#                 else: # New module part (no ID)
#                     if not should_destroy: 
#                         ModulePart.objects.create(module=instance, **item_data)
            
#             for existing_id, existing_obj in current_module_parts.items():
#                 if existing_id not in incoming_module_part_ids:
#                     if ModulePart.objects.filter(id=existing_id, module=instance).exists():
#                             existing_obj.delete()

#         return instance

# class ModuleSerializer(serializers.ModelSerializer):
#     module_parts = WritableModulePartSerializer(many=True, required=False)
#     calculated_purchase_cost_blueprint = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True, source='calculate_module_total_purchase_cost', required=False)
#     calculated_selling_cost_blueprint = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True, source='calculate_module_total_selling_cost', required=False)
#     detailed_cost_breakdown_blueprint = serializers.SerializerMethodField()
#     packing_analysis = serializers.SerializerMethodField()

#     class Meta:
#         model = Module
#         fields = '__all__'

#     def create(self, validated_data):
#         module_parts_data = validated_data.pop('module_parts', [])
#         module = Module.objects.create(**validated_data)
#         for part_data in module_parts_data:
#             ModulePart.objects.create(module=module, **part_data)
#         return module

#     def update(self, instance, validated_data):
#         module_parts_data = validated_data.pop('module_parts', None)

#         # Update Module instance fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Handle nested ModuleParts (Create, Update, Delete)
#         if module_parts_data is not None:
#             current_module_parts = {obj.id: obj for obj in instance.module_parts.all()}
#             incoming_module_part_ids = set()

#             for item_data in module_parts_data:
#                 item_id = item_data.get('id')
#                 should_destroy = item_data.pop('_destroy', False) # Safely pop _destroy flag

#                 if item_id: # Existing module part
#                     incoming_module_part_ids.add(item_id)
#                     if should_destroy:
#                         if item_id in current_module_parts:
#                             current_module_parts[item_id].delete()
#                     else:
#                         if item_id in current_module_parts:
#                             nested_obj = current_module_parts[item_id]
#                             for attr, value in item_data.items():
#                                 setattr(nested_obj, attr, value)
#                             nested_obj.save()
#                         else:
#                             # This case means an ID was provided that doesn't exist for this parent.
#                             # Treat as a new item.
#                             ModulePart.objects.create(module=instance, **item_data)
#                 else: # New module part (no ID)
#                     if not should_destroy: # Only create if not marked for destruction
#                         ModulePart.objects.create(module=instance, **item_data)
            
#             # Finally, delete any existing items that were NOT sent in the incoming data
#             # AND were not explicitly marked for destruction earlier.
#             for existing_id, existing_obj in current_module_parts.items():
#                 if existing_id not in incoming_module_part_ids:
#                     # Double-check if the object still exists before trying to delete it
#                     if ModulePart.objects.filter(id=existing_id, module=instance).exists():
#                          existing_obj.delete()

#         return instance
#     def get_detailed_cost_breakdown_blueprint(self, obj):
#         #return obj.get_module_detailed_cost_breakdown()
#         pass

#     def get_total_material_area_sq_mm_blueprint(self, obj):
#         #return obj.get_module_total_material_area_sq_mm() # If you added this in the previous step
#         pass

#     # NEW METHOD FOR SERIALIZERMETHODFIELD
#     def get_packing_analysis(self, obj):
#         # You can add rotation_allowed as a context variable if needed
#         #rotation_allowed = self.context.get('rotation_allowed', True)
#         #return obj.get_module_packing_analysis(rotation_allowed=rotation_allowed)
#         pass

# # --- Product Subclass Serializers (No changes) ---
# class StandardProductImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StandardProductImage
#         fields = '__all__'

# class StandardProductSerializer(serializers.ModelSerializer):
#     # --- For Reading (Output) ---
#     category = ProductCategorySerializer(read_only=True)
#     type = TypeSerializer(read_only=True)
#     model = ModelSerializer(read_only=True)
#     brand = BrandMinimalSerializer(read_only=True) # For displaying nested Brand info
#     price_unit = UnitSerializer(read_only=True)
#     images = StandardProductImageSerializer(many=True, read_only=True) # For displaying nested images

#     # --- For Writing (Input) ---
#     # These fields accept IDs and map them to the corresponding ForeignKey
#     category_id = serializers.PrimaryKeyRelatedField(
#         queryset=ProductCategory.objects.all(), source='category', write_only=True
#     )
#     type_id = serializers.PrimaryKeyRelatedField(
#         queryset=Type.objects.all(), source='type', write_only=True
#     )
#     model_id = serializers.PrimaryKeyRelatedField(
#         queryset=Model.objects.all(), source='model', write_only=True
#     )
#     brand_id = serializers.PrimaryKeyRelatedField(
#         queryset=Brand.objects.all(), source='brand', write_only=True
#     )
#     price_unit_id = serializers.PrimaryKeyRelatedField(
#         queryset=Unit.objects.all(), source='price_unit', write_only=True,
#         allow_null=True, required=False # Add allow_null/required=False if your Unit FK is optional
#     )

#     # Other read-only properties/calculated fields
#     display_selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     formatted_break_even_status_standard = serializers.CharField(read_only=True)
#     formatted_profit_margin_standard = serializers.CharField(read_only=True)

#     class Meta:
#         model = StandardProduct
#         # Explicitly list ALL fields. This is safer when mixing read_only nested and write_only PK fields.
#         fields = [
#             'id', 'name', 'product_type', 
#             'category', 'category_id', # 'category' for read, 'category_id' for write
#             'type', 'type_id',         # 'type' for read, 'type_id' for write
#             'model', 'model_id',       # 'model' for read, 'model_id' for write
#             'brand', 'brand_id',       # 'brand' for read, 'brand_id' for write
#             'price_unit', 'price_unit_id', # 'price_unit' for read, 'price_unit_id' for write
#             'image', # The actual ImageField, not related to StandardProductImageSerializer
#             'created_at', 'updated_at',
#             'slug', 'meta_title', 'meta_description', 'keywords',
#             'section', 'material_description', 'color', 
#             'length_mm', 'width_mm', 'height_mm',
#             's_price', 'p_price', 'sl_price', # sl_price is read_only/calculated
#             'images', # Read-only nested images
#             'display_selling_price', 'formatted_break_even_status_standard',
#             'formatted_profit_margin_standard'
#         ]
# class CustomProductSerializer(serializers.ModelSerializer):
#     category = ProductCategorySerializer(read_only=True)
#     type = TypeSerializer(read_only=True)
#     model = ModelSerializer(read_only=True)
#     brand = BrandMinimalSerializer(read_only=True)
#     display_selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

#     class Meta:
#         model = CustomProduct
#         fields = '__all__'


# # --- Modular Product Serializers (Crucial updates for writable nested) ---

# # Writable Constraint Serializer
# class WritableConstraintSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Constraint
#         fields = ['id', 'abbreviation', 'value'] # Include ID for updates/deletes
#         extra_kwargs = {'id': {'read_only': False, 'required': False}}

# # Writable ModularProductModule Serializer
# class WritableModularProductModuleSerializer(serializers.ModelSerializer):
#     module = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all()) # Writable by ID
#     class Meta:
#         model = ModularProductModule
#         fields = ['id', 'module', 'quantity', 'position_x', 'position_y', 'position_z',
#                   'orientation_roll', 'orientation_pitch', 'orientation_yaw']
#         extra_kwargs = {'id': {'read_only': False, 'required': False}}

# # Writable ModularProductMaterialOverride Serializer
# class WritableModularProductMaterialOverrideSerializer(serializers.ModelSerializer):
#     wooden_material = serializers.PrimaryKeyRelatedField(queryset=WoodEn.objects.all()) # Writable by ID
#     class Meta:
#         model = ModularProductMaterialOverride
#         fields = ['id', 'wooden_material', 'is_default']
#         extra_kwargs = {'id': {'read_only': False, 'required': False}}

# # ModularProduct Serializer (Now handles writable nested objects)
# class ModularProductSerializer(serializers.ModelSerializer):
#     category = ProductCategorySerializer(read_only=True)
#     type = TypeSerializer(read_only=True)
#     model = ModelSerializer(read_only=True)
#     brand = BrandMinimalSerializer(read_only=True)

#     # Use the new Writable Serializers for nested fields
#     # `many=True` for lists, `required=False` if not strictly needed on create
#     modular_product_modules = WritableModularProductModuleSerializer(many=True, required=False)
#     constraints = WritableConstraintSerializer(many=True, required=False)
#     material_overrides = WritableModularProductMaterialOverrideSerializer(many=True, required=False)

#     # Calculated fields for display (read-only)
#     display_selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     # Using source for calculated methods in Model
#     calculated_total_purchase_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True, source='calculate_total_modular_product_purchase_cost', required=False)
#     calculated_total_selling_cost_derived = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True, source='calculate_total_modular_product_selling_cost_derived', required=False)
#     formatted_break_even_status = serializers.CharField(read_only=True)
#     formatted_profit_margin = serializers.CharField(read_only=True)

#     class Meta:
#         model = ModularProduct
#         fields = '__all__'

#     # --- Override create and update for nested object management ---
#     def create(self, validated_data):
#         # Pop nested data before creating the parent
#         modules_data = validated_data.pop('modular_product_modules', [])
#         constraints_data = validated_data.pop('constraints', [])
#         material_overrides_data = validated_data.pop('material_overrides', [])

#         modular_product = ModularProduct.objects.create(**validated_data)

#         # Create nested objects
#         for module_data in modules_data:
#             ModularProductModule.objects.create(modular_product=modular_product, **module_data)
#         for constraint_data in constraints_data:
#             Constraint.objects.create(modular_product=modular_product, **constraint_data)
#         for override_data in material_overrides_data:
#             ModularProductMaterialOverride.objects.create(modular_product=modular_product, **override_data)

#         return modular_product

#     def update(self, instance, validated_data):
#         # Handle modular_product_modules
#         modules_data = validated_data.pop('modular_product_modules', None)
#         if modules_data is not None: # Only update if the field is present in the request
#             self._update_nested_relationships(
#                 instance, modules_data, 'modular_product_modules', ModularProductModule
#             )

#         # Handle constraints
#         constraints_data = validated_data.pop('constraints', None)
#         if constraints_data is not None:
#             self._update_nested_relationships(
#                 instance, constraints_data, 'constraints', Constraint
#             )

#         # Handle material_overrides
#         material_overrides_data = validated_data.pop('material_overrides', None)
#         if material_overrides_data is not None:
#             self._update_nested_relationships(
#                 instance, material_overrides_data, 'material_overrides', ModularProductMaterialOverride
#             )

#         # Update parent ModularProduct fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         return instance

#     def _update_nested_relationships(self, parent_instance, nested_data, related_name, nested_model):
#         """
#         Helper method to manage nested many-to-one relationships (create, update, delete).
#         """
#         current_nested_ids = set(getattr(parent_instance, related_name).values_list('id', flat=True))
#         incoming_nested_ids = set()

#         for item_data in nested_data:
#             item_id = item_data.get('id')
#             if item_id: # Existing item
#                 incoming_nested_ids.add(item_id)
#                 try:
#                     nested_obj = nested_model.objects.get(id=item_id, **{f'modular_product': parent_instance}) # Ensure it belongs to this product
#                     item_data.pop('id') # Remove ID before updating
#                     for attr, value in item_data.items():
#                         setattr(nested_obj, attr, value)
#                     nested_obj.save()
#                 except nested_model.DoesNotExist:
#                     # If an ID is provided but it doesn't exist or doesn't belong to this parent,
#                     # treat as a new item. Adjust logic if you prefer strict error or ignore.
#                     nested_model.objects.create(**{f'modular_product': parent_instance}, **item_data)
#             else: # New item
#                 nested_model.objects.create(**{f'modular_product': parent_instance}, **item_data)

#         # Delete items not present in the incoming data
#         items_to_delete_ids = current_nested_ids - incoming_nested_ids
#         nested_model.objects.filter(id__in=items_to_delete_ids, **{f'modular_product': parent_instance}).delete()


# # fields = [
#         #     'id', 'name', 'description',
#         #     # 'assembled_model_3d_file',
#         #     # 'assembly_hash',
#         #     # 'get_assembled_3d_model_url',
#         # ]
#         # read_only_fields = ['assembled_model_3d_file', 'assembly_hash', 'get_assembled_3d_model_url']

#     # # Similar logic for triggering assembly model generation
#     # # def create(self, validated_data):
#     # #     instance = super().create(validated_data)
#     # #     # instance._generate_assembled_3d_model()
#     # #     return instance
#     #
#     # # def update(self, instance, validated_data):
#     # #     # Check for changes in related modules/parts/constraints that would invalidate the assembly hash
#     # #     # if assembly_related_fields_changed:
#     # #     #     # instance._generate_assembled_3d_model()
#     # #     #     pass
#     # #     return instance


# # --- New Serializers for Layout/Rooms (Commented for future use) ---
# # class BuildingSerializer(serializers.ModelSerializer):
# #     # floors = FloorSerializer(many=True, read_only=True) # Nested serializer for floors
# #     class Meta:
# #         model = Building
# #         fields = '__all__'
# #         # fields = [
# #         #     'id', 'name', 'description', # 'total_area_sqft', 'address', 'owner',
# #         #     # 'layout_2d_image', 'final_3d_model', 'floors'
# #         # ]
# #
# # class FloorSerializer(serializers.ModelSerializer):
# #     # rooms = RoomSerializer(many=True, read_only=True) # Nested serializer for rooms
# #     class Meta:
# #         model = Floor
# #         fields = '__all__'
# #         # fields = [
# #         #     'id', 'building', 'floor_number', 'height_mm', # 'rooms'
# #         # ]
# #
# # class RoomSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Room
# #         fields = '__all__'
# #         # fields = [
# #         #     'id', 'floor', 'name', 'room_module_type',
# #         #     'x_position_mm', 'y_position_mm', 'length_mm', 'width_mm', 'height_mm',
# #         #     # 'custom_constraints', 'associated_modular_product',
# #         # ]
# #
# #     # def create(self, validated_data):
# #     #     # When a room is created, also create an associated ModularProduct based on room_module_type
# #     #     # and link its dimensions (length_mm, width_mm, height_mm) as constraints.
# #     #     room = super().create(validated_data)
# #     #     # if room.room_module_type:
# #     #     #     # Logic to create ModularProduct and link it
# #     #     #     # and set initial constraints based on room dimensions
# #     #     #     pass
# #     #     return room
# #
# #     # def update(self, instance, validated_data):
# #     #     # If room dimensions change, update associated ModularProduct's constraints and trigger regeneration
# #     #     # room = super().update(instance, validated_data)
# #     #     # if 'length_mm' in validated_data or 'width_mm' in validated_data or 'height_mm' in validated_data:
# #     #     #     # Logic to update constraints on associated_modular_product
# #     #     #     # and trigger its _generate_assembled_3d_model()
# #     #     #     pass
# #     #     return instance

# # --- Polymorphic Product Serializer (for the base Product model, no change) ---
# class ProductSerializer(serializers.ModelSerializer):
#     # This serializer is used when querying the base Product model directly.
#     # It can show basic fields or, if PolymorphicSerializer was used, delegate.
#     # For now, it will act as a generic Product serializer.
#     category = ProductCategorySerializer(read_only=True)
#     type = TypeSerializer(read_only=True)
#     model = ModelSerializer(read_only=True)
#     brand = BrandMinimalSerializer(read_only=True)
#     product_type = serializers.CharField(source='get_product_type_display', read_only=True)

#     class Meta:
#         model = Product
#         fields = ['id', 'name', 'product_type', 'image', 'display_selling_price', 'slug',
#                   'category', 'type', 'model', 'brand', 'description', 'meta_title', 'meta_description',
#                   'created_at', 'updated_at']