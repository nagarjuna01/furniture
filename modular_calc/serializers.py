import uuid
from rest_framework import serializers
from django.db import transaction

# --- MODEL IMPORTS ---
from .models import (
    ModularProduct, ProductParameter, PartTemplate, 
    PartMaterialWhitelist, PartEdgeBandWhitelist, ProductHardwareRule, 
    PartHardwareRule
)
# Assuming material.serializers contains the read-only serializers
# Note: Since material.models is imported, we will define the mini serializers here for completeness.
from material.models import WoodEn, EdgeBand, Hardware 


# ==============================================================================
#                      1. READ-ONLY MINI SERIALIZERS (For display in FK fields)
# ==============================================================================

# NOTE: These are used by the WRITE serializers to display details on read (GET)

class WoodEnMiniSerializer(serializers.ModelSerializer):
    """Used for Material Whitelist selection dropdowns and read details."""
    
    thickness_mm = serializers.DecimalField(source='thickness', max_digits=5, decimal_places=2, read_only=True)
    
    # NEW: Expose the related model names for hierarchical sorting and display
    category = serializers.CharField(source='material_grp.name', read_only=True)
    type = serializers.CharField(source='material_type.name', read_only=True)
    model = serializers.CharField(source='material_model.name', read_only=True)
    # If 'panel' is a field on the WoodEn model, use it; otherwise, check related fields.
    # Assuming 'panel' is not explicitly used, you can exclude it or map it if an equivalent exists.
    
    class Meta:
        model = WoodEn
        fields = (
            'id', 
            'name', 
            'thickness_mm', 
            'color',
            # Use the new calculated fields in the field list
            'category', 
            'type', 
            'model', 
            # You may need to replace 'panel' with a correct field or exclude it
        )


class EdgeBandMiniSerializer(serializers.ModelSerializer):
    """Used for PartTemplate edgeband dropdowns and read details."""
    thickness_mm = serializers.DecimalField(source='e_thickness', max_digits=5, decimal_places=2, read_only=True)
    name = serializers.CharField(source='edgeband_name.name', read_only=True)
    class Meta:
        model = EdgeBand
        fields = ('id', 'name', 'thickness_mm')
        
class HardwareMiniSerializer(serializers.ModelSerializer):
    """Used for Part Hardware Rule selection and display."""

    # 🎯 1. Expose Hardware Group name as 'group' (The Category)
    group = serializers.CharField(source='h_group.name', read_only=True)
    
    # 🎯 2. Expose Brand name
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    # The sl_price is defined as a @property on the model, so we can expose it directly
    sl_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True) 

    class Meta:
        model = Hardware 
        fields = (
            'id', 
            'h_name',       # The item name
            'unit',
            'p_price',
            's_price',
            'sl_price',
            # Include the semantic fields for sorting/display
            'group',        
            'brand_name',   
            # Note: We don't expose h_group or brand FK IDs, only the names
        )


# ==============================================================================
#                      2. DEEPLY NESTED WRITE/READ SERIALIZERS
# ==============================================================================

# --- Grandchildren (Level 3) ---

class PartMaterialWhitelistSerializer(serializers.ModelSerializer):
    # Use Mini serializer for read operations to display the WoodEn name/details
    material_details = WoodEnMiniSerializer(source='material', read_only=True) 
    class Meta:
        model = PartMaterialWhitelist
        # 'material' (PK) for write, 'material_details' for read
        fields = ('id', 'material', 'material_details', 'is_default')
        extra_kwargs = {'part_template': {'required': False}} # Parent FK is set later

class PartEdgeBandWhitelistSerializer(serializers.ModelSerializer):
    edgeband_details = EdgeBandMiniSerializer(source='edgeband', read_only=True)
    class Meta:
        model = PartEdgeBandWhitelist
        fields = ('id', 'edgeband', 'edgeband_details', 'is_default')
        extra_kwargs = {'part_template': {'required': False}}

class PartHardwareRuleSerializer(serializers.ModelSerializer):
    hardware_details = HardwareMiniSerializer(source='hardware', read_only=True)
    class Meta:
        model = PartHardwareRule
        fields = ('id', 'hardware', 'hardware_details', 'quantity_equation', 'applicability_condition')
        extra_kwargs = {'part_template': {'required': False}}


# --- Children (Level 2) ---

class ProductParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductParameter
        fields = ('id', 'name', 'abbreviation', 'default_value', 'description')
        extra_kwargs = {'product': {'required': False}}
        read_only_fields = ['product']

class ProductHardwareRuleSerializer(serializers.ModelSerializer):
    hardware_details = HardwareMiniSerializer(source='hardware', read_only=True)
    class Meta:
        model = ProductHardwareRule
        fields = ('id', 'hardware', 'hardware_details', 'quantity')
        extra_kwargs = {'product': {'required': False}}


class PartTemplateSerializer(serializers.ModelSerializer):
    # Use the nested serializers defined above (Level 3)
    material_whitelist = PartMaterialWhitelistSerializer(many=True, required=False)
    edgeband_whitelist = PartEdgeBandWhitelistSerializer(many=True, required=False)
    hardware_rules = PartHardwareRuleSerializer(many=True, required=False)

    # Read-only details for edgeband FKs (for display)
    edgeband_top_details = EdgeBandMiniSerializer(source='edgeband_top', read_only=True)
    edgeband_bottom_details = EdgeBandMiniSerializer(source='edgeband_bottom', read_only=True)
    edgeband_left_details = EdgeBandMiniSerializer(source='edgeband_left', read_only=True)
    edgeband_right_details = EdgeBandMiniSerializer(source='edgeband_right', read_only=True)

    class Meta:
        model = PartTemplate
        fields = (
            'id', 'name', 'part_length_equation', 'part_width_equation', 'part_qty_equation', 
            'part_thickness_mm', 'shape_wastage_multiplier',
            # Writable FKs (PK)
            'edgeband_top', 'edgeband_bottom', 'edgeband_left', 'edgeband_right',
            # Nested Lists
            'material_whitelist', 'edgeband_whitelist', 'hardware_rules',
            # Read-only details
            'edgeband_top_details', 'edgeband_bottom_details', 'edgeband_left_details', 'edgeband_right_details'
        )
        extra_kwargs = {'product': {'required': False}}


# ==============================================================================
#                      3. TOP-LEVEL NESTED SERIALIZER (ModularProductSerializer)
# ==============================================================================

class ModularProductSerializer(serializers.ModelSerializer):
    # Use the nested serializers defined above (Level 2)
    parameters = ProductParameterSerializer(many=True, required=False)
    hardware_rules = ProductHardwareRuleSerializer(many=True, required=False) 
    part_templates = PartTemplateSerializer(many=True, required=False)

    class Meta:
        model = ModularProduct
        fields = (
            'id', 'name', 'product_validation_expression', 'three_d_asset', 
            'two_d_template_svg', 
            'parameters', 'hardware_rules', 'part_templates' # Nested fields
        )
        read_only_fields = ('created_at', 'updated_at')
        
    # --------------------------------------------------
    # Reusable Helper Methods for Nested CUD
    # --------------------------------------------------

    # CUD Helper for single-level nesting (like parameters/product hardware)
    def _handle_nested_update(self, parent_obj, validated_data, related_name, SerializerClass, Model, fk_field_name):
        new_or_updated_items_data = validated_data.pop(related_name, [])
        current_items = getattr(parent_obj, related_name).all()
        current_item_ids = {item.id for item in current_items}
        incoming_ids = set()
        
        for item_data in new_or_updated_items_data:
            item_id = item_data.get('id')
            if item_id:
                try:
                    # UPDATE existing item
                    item_instance = current_items.get(id=item_id)
                    serializer = SerializerClass(instance=item_instance, data=item_data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(**{fk_field_name: parent_obj})
                    incoming_ids.add(item_id)
                except Model.DoesNotExist:
                    pass 
            else:
                # CREATE new item
                item_data[fk_field_name] = parent_obj
                serializer = SerializerClass(data=item_data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        # DELETE items removed from the list
        items_to_delete_ids = current_item_ids - incoming_ids
        Model.objects.filter(id__in=items_to_delete_ids).delete()

    # C Helper for single-level nesting on CREATE
    def _create_nested_items(self, parent_obj, data_list, Model, fk_field_name):
        for item_data in data_list:
            item_data[fk_field_name] = parent_obj
            Model.objects.create(**item_data)
            
    # Deeper CUD Helper for PartTemplates and their nested whitelists/rules
    def _create_part_templates(self, product, part_templates_data):
        for part_data in part_templates_data:
            # 1. Pop nested data
            whitelist_data = part_data.pop('material_whitelist', [])
            eb_whitelist_data = part_data.pop('edgeband_whitelist', [])
            hw_rules_data = part_data.pop('hardware_rules', [])
            
            # 2. Create PartTemplate
            part_data['product'] = product
            part = PartTemplate.objects.create(**part_data)
            
            # 3. Create Grandchildren
            self._create_nested_items(part, whitelist_data, PartMaterialWhitelist, 'part_template')
            self._create_nested_items(part, eb_whitelist_data, PartEdgeBandWhitelist, 'part_template')
            self._create_nested_items(part, hw_rules_data, PartHardwareRule, 'part_template')


    def _handle_part_template_update(self, product_instance, validated_data):
        part_templates_data = validated_data.pop('part_templates', [])
        current_parts = product_instance.part_templates.all()
        current_part_ids = {part.id for part in current_parts}
        incoming_ids = set()

        for part_data in part_templates_data:
            part_id = part_data.get('id')
            
            # 1. Pop nested data
            whitelist_data = part_data.pop('material_whitelist', [])
            eb_whitelist_data = part_data.pop('edgeband_whitelist', [])
            hw_rules_data = part_data.pop('hardware_rules', [])
            
            if part_id:
                # 2A. UPDATE PartTemplate
                try:
                    part_instance = current_parts.get(id=part_id)
                    serializer = PartTemplateSerializer(instance=part_instance, data=part_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(product=product_instance) 
                    incoming_ids.add(part_id)
                    
                    # 3A. Recurse: Handle Grandchildren CUD
                    self._handle_nested_update(part_instance, {'material_whitelist': whitelist_data}, 'material_whitelist', PartMaterialWhitelistSerializer, PartMaterialWhitelist, 'part_template')
                    self._handle_nested_update(part_instance, {'edgeband_whitelist': eb_whitelist_data}, 'edgeband_whitelist', PartEdgeBandWhitelistSerializer, PartEdgeBandWhitelist, 'part_template')
                    self._handle_nested_update(part_instance, {'hardware_rules': hw_rules_data}, 'hardware_rules', PartHardwareRuleSerializer, PartHardwareRule, 'part_template')
                    
                except PartTemplate.DoesNotExist: pass
            else:
                # 2B. CREATE PartTemplate (use helper)
                part_data['material_whitelist'] = whitelist_data 
                part_data['edgeband_whitelist'] = eb_whitelist_data
                part_data['hardware_rules'] = hw_rules_data
                self._create_part_templates(product_instance, [part_data])

        # 4. DELETE PartTemplates
        parts_to_delete_ids = current_part_ids - incoming_ids
        PartTemplate.objects.filter(id__in=parts_to_delete_ids).delete()

    # --------------------------------------------------
    # Overriding create/update
    # --------------------------------------------------

    def create(self, validated_data):
        with transaction.atomic():
            # 1. Extract nested data
            parameters_data = validated_data.pop('parameters', [])
            hardware_rules_data = validated_data.pop('hardware_rules', [])
            part_templates_data = validated_data.pop('part_templates', [])

            # 2. Create parent object
            product = ModularProduct.objects.create(**validated_data)

            # 3. Create nested objects
            self._create_nested_items(product, parameters_data, ProductParameter, 'product')
            self._create_nested_items(product, hardware_rules_data, ProductHardwareRule, 'product')
            self._create_part_templates(product, part_templates_data) 

            return product

    def update(self, instance, validated_data):
        with transaction.atomic():
            # 1. Update Top-Level Fields
            for attr, value in validated_data.items():
                if attr not in ('parameters', 'hardware_rules', 'part_templates'):
                    setattr(instance, attr, value)
            instance.save()
            
            # 2. Handle Nested CUD for Parameters & Product Hardware Rules
            self._handle_nested_update(instance, validated_data, 'parameters', ProductParameterSerializer, ProductParameter, 'product')
            self._handle_nested_update(instance, validated_data, 'hardware_rules', ProductHardwareRuleSerializer, ProductHardwareRule, 'product')

            # 3. Handle Part Templates (and their deep nesting)
            self._handle_part_template_update(instance, validated_data)

            return instance