import uuid
from rest_framework import serializers
from django.db import transaction

# --- MODEL IMPORTS ---
from .models import (
    ModularProduct, ProductParameter, PartTemplate, 
    PartMaterialWhitelist, PartEdgeBandWhitelist, ProductHardwareRule, 
    PartHardwareRule,ModularProductCategory,ModularProductType,ModularProductModel
)
# Assuming material.serializers contains the read-only serializers
# Note: Since material.models is imported, we will define the mini serializers here for completeness.
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware


class FlexiblePrimaryKeyField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        # If Django already turned this into an object, just return it!
        if isinstance(data, self.queryset.model):
            return data
        return super().to_internal_value(data)

# ==============================================================================
#                      1. READ-ONLY MINI SERIALIZERS (For display in FK fields)
# ==============================================================================

# NOTE: These are used by the WRITE serializers to display details on read (GET)

class WoodEnMiniSerializer(serializers.ModelSerializer):
    """Used for Material Whitelist selection dropdowns and read details."""
    
    thickness_mm = serializers.DecimalField(source='thickness_value', max_digits=5, decimal_places=2, read_only=True)
    
    # NEW: Expose the related model names for hierarchical sorting and display
    category = serializers.CharField(source='material_grp.name', read_only=True)
    type = serializers.CharField(source='material_type.name', read_only=True)
    model = serializers.CharField(source='material_model.name', read_only=True)
    # If 'panel' is a field on the WoodEn model, use it; otherwise, check related fields.
    # Assuming 'panel' is not explicitly used, you can exclude it or map it if an equivalent exists.
    
    class Meta:
        model = WoodMaterial
        fields = ('id', 'name', 'thickness_mm', 'color','category', 'type', 'model')
        read_only_fields = ('id',)


class EdgeBandMiniSerializer(serializers.ModelSerializer):
    """Used for PartTemplate edgeband dropdowns and read details."""
    thickness_mm = serializers.DecimalField(source='e_thickness', max_digits=5, decimal_places=2, read_only=True)
    name = serializers.CharField(source='edgeband_name.name', read_only=True)
    class Meta:
        model = EdgeBand
        fields = ('id', 'name', 'thickness_mm')
        read_only_fields = ('id',)
        
class HardwareMiniSerializer(serializers.ModelSerializer):
    group = serializers.CharField(source='h_group.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    billing_unit_code = serializers.CharField(
        source="billing_unit.code", 
        read_only=True
    )
    
    class Meta:
        model = Hardware 
        fields = (
            'id', 
            'h_name',           # Item Name
            'billing_unit',     # ForeignKey ID (for saving)
            'billing_unit_code',# Display code (e.g., "PCS", "SET")
            'cost_price',
            'sell_price',
            'group', 
            'brand_name',   
        )
        read_only_fields = ('id', 'billing_unit_code')


# ==============================================================================
#                      2. DEEPLY NESTED WRITE/READ SERIALIZERS
# ==============================================================================

# --- Grandchildren (Level 3) ---

class PartMaterialWhitelistSerializer(serializers.ModelSerializer):
    
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    # Use Mini serializer for read operations to display the WoodEn name/
    material = FlexiblePrimaryKeyField(queryset=WoodMaterial.objects.all())
    material_details = WoodEnMiniSerializer(source='material', read_only=True) 
    class Meta:
        model = PartMaterialWhitelist
        # 'material' (PK) for write, 'material_details' for read
        fields = ('id','tenant', 'material', 'material_details', 'is_default')
        read_only_fields = ('id','tenant')
        extra_kwargs = {'part_template': {'required': False}} # Parent FK is set later
    # def to_internal_value(self, data):
    #      # If the incoming data has an object instead of an ID, grab the ID
    #     if 'material' in data and hasattr(data['material'], 'id'):
    #         data['material'] = data['material'].id
    #     return super().to_internal_value(data)

class PartEdgeBandWhitelistSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    edgeband_details = EdgeBandMiniSerializer(source='edgeband', read_only=True)
    class Meta:
        model = PartEdgeBandWhitelist
        fields = ('id', 'tenant','side','edgeband', 'edgeband_details', 'is_default')
        read_only_fields =('id','tenant')
        extra_kwargs = {'part_template': {'required': False}}

class PartHardwareRuleSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    hardware = FlexiblePrimaryKeyField(queryset=Hardware.objects.all())
    hardware_details = HardwareMiniSerializer(source='hardware', read_only=True)
    class Meta:
        model = PartHardwareRule
        fields = ('id', 'tenant','hardware', 'hardware_details', 'quantity_equation', 'applicability_condition')
        read_only_fields =('id','tenant')
        extra_kwargs = {'part_template': {'required': False}}


# --- Children (Level 2) ---

class ProductParameterSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = ProductParameter
        fields = ('id', 'name', 'abbreviation','tenant', 'default_value', 'description')
        extra_kwargs = {'product': {'required': False}}
        read_only_fields = ['product','tenant']

class ProductHardwareRuleSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    hardware = FlexiblePrimaryKeyField(queryset=Hardware.objects.all())
    hardware_details = HardwareMiniSerializer(source='hardware', read_only=True)
    class Meta:
        model = ProductHardwareRule
        fields = ['id','tenant', 'hardware', 'hardware_details', "quantity_equation",
            "applicability_condition",]

        read_only_fields = ('id','tenant','hardware_details')
        extra_kwargs = {'product': {'required': False}}
    # def to_internal_value(self, data):
    #     if 'hardware' in data and hasattr(data['hardware'], 'id'):
    #         data = data.copy()
    #         data['hardware'] = data['hardware'].id
    #     return super().to_internal_value(data)

class PartTemplateSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    material_whitelist = PartMaterialWhitelistSerializer(many=True, required=False)
    hardware_rules = PartHardwareRuleSerializer(many=True, required=False)
    edgeband_top_details = EdgeBandMiniSerializer(source="edgeband_top", read_only=True)
    edgeband_bottom_details = EdgeBandMiniSerializer(source="edgeband_bottom", read_only=True)
    edgeband_left_details = EdgeBandMiniSerializer(source="edgeband_left", read_only=True)
    edgeband_right_details = EdgeBandMiniSerializer(source="edgeband_right", read_only=True)
    edgeband_whitelist = PartEdgeBandWhitelistSerializer(many=True, required=False)
    class Meta:
        model = PartTemplate
        fields = (
            "id",
            "tenant",
            "name",
            "part_length_equation",
            "part_width_equation",
            "part_qty_equation",
            "shape_wastage_multiplier",
            "edgeband_top",
            "edgeband_bottom",
            "edgeband_left",
            "edgeband_right",
            "material_whitelist",
            "hardware_rules",
            "edgeband_top_details",
            "edgeband_bottom_details",
            "edgeband_left_details",
            "edgeband_right_details",
        )
        read_only_fields = ("id", "tenant")
        extra_kwargs = {"product": {"required": False}}
    def _sync_edgebands(self, part, edgeband_map, tenant):
        """
        Syncs the PartEdgeBandWhitelist table based on the primary side selections.
        This ensures the 'edgeband_details' and whitelists stay in sync.
        """
        PartEdgeBandWhitelist.objects.filter(part_template=part).delete()
        
        for side, edgeband_id in edgeband_map.items():
            if not edgeband_id:
                continue
                
            # Extract ID if passed as object
            actual_id = edgeband_id.id if hasattr(edgeband_id, 'id') else edgeband_id
            
            PartEdgeBandWhitelist.objects.create(
                part_template=part,
                tenant=tenant,
                side=side,
                edgeband_id=actual_id,
                is_default=True
            )
            
            # Update flat field on PartTemplate instance
            side_field = f"edgeband_{side}"
            if hasattr(part, side_field):
                setattr(part, side_field, actual_id)
        
        part.save()

    def create(self, validated_data):
        tenant = self.context['request'].user.tenant
        
        material_data = validated_data.pop("material_whitelist", [])
        hardware_data = validated_data.pop("hardware_rules", [])

        # Extract edgebands for the map
        eb_top = validated_data.pop("edgeband_top", None)
        eb_bottom = validated_data.pop("edgeband_bottom", None)
        eb_left = validated_data.pop("edgeband_left", None)
        eb_right = validated_data.pop("edgeband_right", None)
        edgeband_map = {"top": eb_top, "bottom": eb_bottom, "left": eb_left, "right": eb_right}

        with transaction.atomic():
            part = PartTemplate.objects.create(
                tenant=tenant,
                edgeband_top=eb_top,
                edgeband_bottom=eb_bottom,
                edgeband_left=eb_left,
                edgeband_right=eb_right,
                **{k: v for k, v in validated_data.items() if k != 'tenant'}
            )

            self._sync_edgebands(part, edgeband_map, tenant)

            # --- Material Whitelist ---
            for row in material_data:
                mat = row.pop('material')
                mat_id = mat.id if hasattr(mat, 'id') else mat
                PartMaterialWhitelist.objects.create(
                    part_template=part, tenant=tenant, material_id=mat_id, **row 
                )

            # --- Part Hardware ---
            for row in hardware_data:
                hw = row.pop('hardware')
                hw_id = hw.id if hasattr(hw, 'id') else hw
                PartHardwareRule.objects.create(
                    part_template=part, tenant=tenant, hardware_id=hw_id, **row
                )

            return part

    def update(self, instance, validated_data):
        tenant = self.context.get("request").user.tenant

        material_data = validated_data.pop("material_whitelist", [])
        hardware_data = validated_data.pop("hardware_rules", [])

        edgeband_fields = ["edgeband_top", "edgeband_bottom", "edgeband_left", "edgeband_right"]
        edgeband_map = {}
        
        for field in edgeband_fields:
            val = validated_data.pop(field, getattr(instance, field))
            setattr(instance, field, val)
            edgeband_map[field.replace("edgeband_", "")] = val

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            self._sync_edgebands(instance, edgeband_map, tenant)

            # Sync Materials
            existing_mats = {m.id: m for m in instance.material_whitelist.all()}
            incoming_mat_ids = set()
            for row in material_data:
                row_id = row.get("id")
                mat = row.pop('material', None)
                mat_id = mat.id if hasattr(mat, 'id') else mat
                if row_id and row_id in existing_mats:
                    item = existing_mats[row_id]
                    for k, v in row.items(): setattr(item, k, v)
                    if mat_id: item.material_id = mat_id
                    item.save()
                    incoming_mat_ids.add(row_id)
                else:
                    new_item = PartMaterialWhitelist.objects.create(
                        part_template=instance, tenant=tenant, material_id=mat_id, **row
                    )
                    incoming_mat_ids.add(new_item.id)
            PartMaterialWhitelist.objects.filter(part_template=instance).exclude(id__in=incoming_mat_ids).delete()

            # Sync Hardware
            existing_hws = {h.id: h for h in instance.hardware_rules.all()}
            incoming_hw_ids = set()
            for row in hardware_data:
                row_id = row.get("id")
                hw = row.pop('hardware', None)
                hw_id = hw.id if hasattr(hw, 'id') else hw
                if row_id and row_id in existing_hws:
                    item = existing_hws[row_id]
                    for k, v in row.items(): setattr(item, k, v)
                    if hw_id: item.hardware_id = hw_id
                    item.save()
                    incoming_hw_ids.add(row_id)
                else:
                    new_item = PartHardwareRule.objects.create(
                        part_template=instance, tenant=tenant, hardware_id=hw_id, **row
                    )
                    incoming_hw_ids.add(new_item.id)
            PartHardwareRule.objects.filter(part_template=instance).exclude(id__in=incoming_hw_ids).delete()

            return instance
# ==============================================================================
#                      3. TOP-LEVEL NESTED SERIALIZER (ModularProductSerializer)
# ==============================================================================

class ModularProductSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    type_name = serializers.CharField(source="type.name", read_only=True)
    productmodel_name = serializers.CharField(source='productmodel.name', read_only=True)
    parameters = ProductParameterSerializer(many=True, required=False)
    hardware_rules = ProductHardwareRuleSerializer(many=True, required=False) 
    part_templates = PartTemplateSerializer(many=True, required=False)

    class Meta:
        model = ModularProduct
        fields = (
            'id','tenant', 'name', "category", "category_name","type", "type_name",'productmodel', 'productmodel_name','product_validation_expression', 'three_d_asset', 
            'two_d_template_svg', 
            'parameters', 'hardware_rules', 'part_templates') 
        
        read_only_fields = ('id','tenant','created_at', 'updated_at')
    def create(self, validated_data):
        request = self.context.get("request")
        tenant = request.user.tenant        

        parameters_data = validated_data.pop("parameters", [])
        hardware_rules_data = validated_data.pop("hardware_rules", [])
        part_templates_data = validated_data.pop("part_templates", [])

        with transaction.atomic():
            # Create product
            product = ModularProduct.objects.create(
                tenant=tenant,                
                **{k: v for k, v in validated_data.items() if k != 'tenant'}
            )

            # Parameters
            for row in parameters_data:
                ProductParameter.objects.create(product=product, tenant=tenant, **row)

            # 3️⃣ Product Hardware Rules - THE TERMINAL FIX
            for row in hardware_rules_data:
                hw = row.pop('hardware')
                hw_id = hw.id if hasattr(hw, 'id') else hw
                ProductHardwareRule.objects.create(
                    product=product,
                    tenant=tenant,
                    hardware_id=hw_id,
                    **row
                )

            # 4️⃣ Part templates - Delegate
            for part_row in part_templates_data:
                # Flatten edgebands before passing to child serializer
                for eb in ['edgeband_top', 'edgeband_bottom', 'edgeband_left', 'edgeband_right']:
                    if eb in part_row and hasattr(part_row[eb], 'id'):
                        part_row[eb] = part_row[eb].id

                serializer = PartTemplateSerializer(data=part_row, context=self.context)
                serializer.is_valid(raise_exception=True)
                serializer.save(product=product, tenant=tenant)

            return product

    # =====================================================
    # UPDATE
    # =====================================================
    def update(self, instance, validated_data):
        request = self.context.get("request")
        tenant = request.user.tenant    

        parameters_data = validated_data.pop("parameters", [])
        hardware_rules_data = validated_data.pop("hardware_rules", [])
        part_templates_data = validated_data.pop("part_templates", [])

        with transaction.atomic():
            # 1️⃣ Update product fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # -------------------------------------------------
            # PARAMETERS (ID-based safe update)
            # -------------------------------------------------
            existing = {p.id: p for p in instance.parameters.all()}
            incoming_ids = set()

            for row in parameters_data:
                row_id = row.get("id")
                if row_id and row_id in existing:
                    for k, v in row.items():
                        setattr(existing[row_id], k, v)
                    existing[row_id].save()
                    incoming_ids.add(row_id)
                else:
                    ProductParameter.objects.create(
                        product=instance,
                        tenant = tenant,
                        **row
                    )
                      
            ProductParameter.objects.filter(
                product=instance
            ).exclude(id__in=incoming_ids).delete()

            # -------------------------------------------------
            # PRODUCT HARDWARE RULES
            # -------------------------------------------------
            existing = {h.id: h for h in instance.hardware_rules.all()}
            incoming_ids = set()

            for row in hardware_rules_data:
                row_id = row.get("id")
                if row_id and row_id in existing:
                    for k, v in row.items():
                        setattr(existing[row_id], k, v)
                    existing[row_id].save()
                    incoming_ids.add(row_id)
                else:
                    ProductHardwareRule.objects.create(
                        product=instance,tenant=tenant,                       
                        **row )

            ProductHardwareRule.objects.filter(
                product=instance
            ).exclude(id__in=incoming_ids).delete()

            # -------------------------------------------------
            # PART TEMPLATES (delegate – NO whitelist logic here)
            # -------------------------------------------------
            existing_parts = {p.id: p for p in instance.part_templates.all()}
            incoming_part_ids = set()

            for row in part_templates_data:
                part_id = row.get("id")

                if part_id and part_id in existing_parts:
                    serializer = PartTemplateSerializer(
                        instance=existing_parts[part_id],
                        data=row,
                        partial=True,
                        context=self.context
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    incoming_part_ids.add(part_id)
                else:
                    serializer = PartTemplateSerializer(
                        data=row,
                        context=self.context
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save(
                        product=instance,tenant= tenant,                        
                    )

            PartTemplate.objects.filter(
                product=instance
            ).exclude(id__in=incoming_part_ids).delete()

            return instance

class ModularProductModelSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    products = ModularProductSerializer(source="modularproduct_set", many=True, read_only=True)
    class Meta:
        model = ModularProductModel
        fields = ['id', 'name', 'type', 'type_name','products']

    def get_type_name(self, obj):
        return obj.type.name if obj.type else None


class ModularProductTypeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    models = ModularProductModelSerializer(
        source='modularproductmodel_set', 
        many=True, 
        read_only=True
    )

    class Meta:
        model = ModularProductType
        fields = ['id', 'name', 'category', 'category_name', 'models']



class ModularProductCategorySerializer(serializers.ModelSerializer):
    """Serializes ProductCategory, including its nested Types."""
    types = ModularProductTypeSerializer(source='modularproducttype_set', many=True, read_only=True)

    class Meta:
        model = ModularProductCategory
        fields = ['id', 'name', 'types']

