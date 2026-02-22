import uuid
from rest_framework import serializers
from django.db import transaction
from .evaluation.validators import validate_boolean_expression
from .evaluation.context import ProductContext
# --- MODEL IMPORTS ---
from .models import (
    ModularProduct, ProductParameter, PartTemplate, 
    PartMaterialWhitelist, PartEdgeBandWhitelist, ProductHardwareRule, 
    PartHardwareRule,ModularProductCategory,ModularProductType,ModularProductModel
)
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware
from modular_calc.utils.expression_dependencies import *
from .evaluation.geometry_utils import generate_default_svg
from .utils.edgeband_resolver import resolve_edgebands_for_material


class FlexiblePrimaryKeyField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if isinstance(data, self.queryset.model):
            return data
        return super().to_internal_value(data)

class WoodEnMiniSerializer(serializers.ModelSerializer):
    thickness_mm = serializers.DecimalField(source='thickness_value', max_digits=5, decimal_places=2, read_only=True)
    category = serializers.CharField(source='material_grp.name', read_only=True)
    type = serializers.CharField(source='material_type.name', read_only=True)
    model = serializers.CharField(source='material_model.name', read_only=True)
    class Meta:
        model = WoodMaterial
        fields = ('id', 'name', 'thickness_mm', 'color','category', 'type', 'model')
        read_only_fields = ('id',)

class EdgeBandMiniSerializer(serializers.ModelSerializer):
    thickness_mm = serializers.DecimalField(source='e_thickness', max_digits=5, decimal_places=2, read_only=True)
    name = serializers.CharField(source='edgeband_name.name', read_only=True)
    class Meta:
        model = EdgeBand
        fields = ('id', 'name', 'thickness_mm')
        read_only_fields = ('id',)
        
class HardwareMiniSerializer(serializers.ModelSerializer):
    group = serializers.CharField(source='h_group.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    billing_unit_code = serializers.CharField(source="billing_unit.code", read_only=True)    
    class Meta:
        model = Hardware 
        fields = ('id', 'h_name','billing_unit','billing_unit_code','cost_price','sell_price','group','brand_name')
        read_only_fields = ('id', 'billing_unit_code')

class PartEdgeBandWhitelistSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    edgeband_details = EdgeBandMiniSerializer(source='edgeband', read_only=True)
    is_whitelisted = serializers.SerializerMethodField()
    edgeband = FlexiblePrimaryKeyField(queryset=EdgeBand.objects.none())

    class Meta:
        model = PartEdgeBandWhitelist
        fields = (
            'id',
            'tenant',
            'side',
            'edgeband',
            'edgeband_details',
            'is_default',
            'is_whitelisted'
        )
        read_only_fields = ('id', 'tenant')
        extra_kwargs = {'part_template': {'required': False}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        req = self.context.get("request")
        if req:
            # Only show active edgebands for the tenant
            self.fields["edgeband"].queryset = EdgeBand.objects.filter(
                tenant=req.user.tenant,
                is_active=True
            )

    def _is_compatible(self, material, edgeband) -> bool:
        """Helper to check if edgeband depth matches material thickness"""
        try:
            return material.thickness_value <= edgeband.depth <= material.thickness_value + 5
        except Exception:
            return False

    def validate(self, attrs):
        edgeband = attrs.get("edgeband")
        material = None

        # Update case
        if self.instance:
            material = getattr(self.instance.material_selection, "material", None)

        # Create case
        if not material:
            material_selection = attrs.get("material_selection")
            if material_selection:
                material = getattr(material_selection, "material", None)

        if material and edgeband and not self._is_compatible(material, edgeband):
            raise serializers.ValidationError(
                "Edgeband depth is not compatible with material thickness."
            )

        return attrs

    def validate_edgeband(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Selected edgeband is inactive."
            )
        return value

    def get_is_whitelisted(self, obj):
        """Informational flag: True if edgeband compatible with material"""
        material = getattr(getattr(obj, "material_selection", None), "material", None)
        if material and obj.edgeband:
            return self._is_compatible(material, obj.edgeband)
        return False


class PartMaterialWhitelistSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    is_default = serializers.BooleanField(required=False, default=False) 
    selected_sides = serializers.ListField(
        child=serializers.ChoiceField(choices=["top","bottom","left","right"]),
        write_only=True,
        required=False
    )
    edgeband_options = PartEdgeBandWhitelistSerializer(many=True, read_only=True)
    material = FlexiblePrimaryKeyField(queryset=WoodMaterial.objects.all())
    material_details = WoodEnMiniSerializer(source='material', read_only=True) 
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_code = serializers.CharField(source='material.code', read_only=True)
    class Meta:
        model = PartMaterialWhitelist
        fields = ('id', 'tenant', 'material', 'material_details', 'is_default', 
                  'material_name', 'material_code', 'selected_sides', 'edgeband_options')
        read_only_fields = ('id', 'tenant')
        extra_kwargs = {'part_template': {'required': False}} 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        req = self.context.get("request")
        if req:
            self.fields["material"].queryset = WoodMaterial.objects.filter(tenant=req.user.tenant,is_active= True)


class PartHardwareRuleSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    hardware = FlexiblePrimaryKeyField(queryset=Hardware.objects.all())
    hardware_details = HardwareMiniSerializer(source='hardware', read_only=True)
    class Meta:
        model = PartHardwareRule
        fields = ('id', 'tenant','hardware', 'hardware_details', 'quantity_equation', 'applicability_condition')
        read_only_fields =('id','tenant')
        extra_kwargs = {'part_template': {'required': False}}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        req = self.context.get("request")
        if req:
            self.fields["hardware"].queryset = Hardware.objects.filter(tenant=req.user.tenant)

class ProductParameterSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = ProductParameter
        fields = ('id', 'name', 'abbreviation','tenant', 'default_value', 'description')
        read_only_fields = ['product','tenant']
        extra_kwargs = {'product': {'required': False}}

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        req = self.context.get("request")
        if req:
            self.fields["hardware"].queryset = Hardware.objects.filter(tenant=req.user.tenant)

class PartTemplateSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    # Nested relations
    material_whitelist = PartMaterialWhitelistSerializer(many=True, required=False)
    hardware_rules = PartHardwareRuleSerializer(many=True, required=False)

    # SVG handling
    svg_data = serializers.CharField(write_only=True, required=False, allow_null=True)
    resolved_svg = serializers.SerializerMethodField()

    class Meta:
        model = PartTemplate
        fields = (
            "id", "tenant", "name", "shape_type",
            "part_length_equation", "part_width_equation", "part_qty_equation",
            "param1_eq", "param2_eq", "shape_wastage_multiplier",
            "material_whitelist", "hardware_rules",
            "resolved_svg", "svg_data",
        )
        read_only_fields = ("id", "tenant")

    def create(self, validated_data):
        tenant = self.context['request'].user.tenant
        material_data = validated_data.pop("material_whitelist", [])
        hardware_data = validated_data.pop("hardware_rules", [])
        validated_data.pop("svg_data", None)

        with transaction.atomic():
            part = PartTemplate.objects.create(tenant=tenant, **validated_data)

            # Sync materials and nested edgebands
            for mat_row in material_data:
                selected_sides = mat_row.pop("selected_sides", [])
                mat_obj = mat_row.pop('material')

                mat_link = PartMaterialWhitelist.objects.create(
                    part_template=part,
                    tenant=tenant,
                    material=mat_obj
                )

                # 🔥 backend decides edgebands
                whitelisted, default_eb = resolve_edgebands_for_material(mat_obj)

                for side in selected_sides:  # helper or stored flags
                    for eb in whitelisted:
                        PartEdgeBandWhitelist.objects.create(
                            material_selection=mat_link,
                            tenant=tenant,
                            side=side,
                            edgeband=eb,
                            is_default=(eb.id == default_eb.id)
                        )
            # Sync hardware
            for hw_row in hardware_data:
                hw_obj = hw_row.pop('hardware')
                PartHardwareRule.objects.create(
                    part_template=part, tenant=tenant, hardware=hw_obj, **hw_row
                )
            
            return part

    def update(self, instance, validated_data):
        tenant = self.context["request"].user.tenant

        material_data = validated_data.pop("material_whitelist", [])
        hardware_data = validated_data.pop("hardware_rules", [])
        validated_data.pop("svg_data", None)

        with transaction.atomic():

            # 1️⃣ Update core part fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # 2️⃣ Resolve selected sides ONCE
            selected_sides = instance.get_selected_edgeband_sides()
            # example return: ['top', 'right']

            # 3️⃣ Sync materials (EDGEBANDS ARE BACKEND-OWNED)
            incoming_mat_ids = set()

            for mat_row in material_data:
                mat_obj = mat_row.pop("material")
                mat_id = mat_obj.id if hasattr(mat_obj, "id") else mat_obj

                mat_link, _ = PartMaterialWhitelist.objects.update_or_create(
                    part_template=instance,
                    material_id=mat_id,
                    defaults={"tenant": tenant}
                )
                incoming_mat_ids.add(mat_link.id)

                # 🔥 FULL RESET of edgebands for this material
                mat_link.edgeband_options.all().delete()

                # 🔥 Backend computes valid edgebands
                whitelisted, default_eb = resolve_edgebands_for_material(mat_link.material)

                for side in selected_sides:
                    for eb in whitelisted:
                        PartEdgeBandWhitelist.objects.create(
                            material_selection=mat_link,
                            tenant=tenant,
                            side=side,
                            edgeband=eb,
                            is_default=(default_eb and eb.id == default_eb.id)
                        )

            # 4️⃣ Remove deleted materials
            instance.material_whitelist.exclude(id__in=incoming_mat_ids).delete()

            # 5️⃣ Sync hardware (unchanged)
            incoming_hw_ids = set()
            for hw_row in hardware_data:
                hw_obj = hw_row.pop("hardware")
                hw_id = hw_obj.id if hasattr(hw_obj, "id") else hw_obj

                hw_link, _ = PartHardwareRule.objects.update_or_create(
                    part_template=instance,
                    hardware_id=hw_id,
                    defaults={"tenant": tenant, **hw_row}
                )
                incoming_hw_ids.add(hw_link.id)

            instance.hardware_rules.exclude(id__in=incoming_hw_ids).delete()

            return instance


    def get_resolved_svg(self, obj):
        svg_val = getattr(obj, 'svg_data', None)
        if svg_val:
            return svg_val
        return generate_default_svg(obj.shape_type, obj.part_length_equation, obj.part_width_equation)

# ==============================================================================
#                      3. TOP-LEVEL NESTED SERIALIZER (ModularProductSerializer)
# ==============================================================================
from rest_framework import serializers
from django.db import transaction

class ModularProductSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=ModularProductCategory.objects.all())
    type = serializers.PrimaryKeyRelatedField(queryset=ModularProductType.objects.all(), required=False, allow_null=True)
    productmodel = serializers.PrimaryKeyRelatedField(queryset=ModularProductModel.objects.all(), required=False, allow_null=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    type_name = serializers.CharField(source="type.name", read_only=True)
    productmodel_name = serializers.CharField(source='productmodel.name', read_only=True)
    text = serializers.CharField(source='name', read_only=True)
    parameters = ProductParameterSerializer(many=True, required=False, allow_empty=True)
    hardware_rules = ProductHardwareRuleSerializer(many=True, required=False, allow_empty=True)
    part_templates = PartTemplateSerializer(many=True, required=False, allow_empty=True)

    class Meta:
        model = ModularProduct
        fields = (
            'id','tenant','name','text','category','category_name','type','type_name',
            'productmodel','productmodel_name','product_validation_expression',
            'three_d_asset','two_d_template_svg','parameters','hardware_rules','part_templates'
        )
        read_only_fields = ('id','tenant','created_at','updated_at')

    # --------------------------
    # Helper: create nested objects
    # --------------------------
    def _create_nested(self, product, tenant, parameters=None, hardware_rules=None, part_templates=None):
        parameters = parameters or []
        hardware_rules = hardware_rules or []
        part_templates = part_templates or []

        # Parameters
        for row in parameters:
            ProductParameter.objects.create(product=product, tenant=tenant, **row)

        # Hardware rules
        for row in hardware_rules:
            hw = row.pop('hardware')
            hw_id = hw.id if hasattr(hw, 'id') else hw
            ProductHardwareRule.objects.create(product=product, tenant=tenant, hardware_id=hw_id, **row)

        # Part templates
        for part_row in part_templates:
            serializer = PartTemplateSerializer(data=part_row, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save(product=product, tenant=tenant)

    # --------------------------
    # Create
    # --------------------------
    def create(self, validated_data):
        request = self.context.get("request")
        tenant = request.user.tenant        

        # 1. Pop nested lists ONLY
        parameters_data = validated_data.pop("parameters", [])
        hardware_rules_data = validated_data.pop("hardware_rules", [])
        part_templates_data = validated_data.pop("part_templates", [])
        validated_data.pop('tenant', None)
        try:
            with transaction.atomic():
                # 2. Create the main product
                product = ModularProduct.objects.create(
                    tenant=tenant,
                    **validated_data
                )

                # 3. Save Parameters (map fields correctly)
                for param in parameters_data:
                    ProductParameter.objects.create(
                        product=product,
                        tenant=tenant,
                        name=param.get("name", ""),
                        abbreviation=param.get("abbreviation", ""),  # if your model uses abbreviation
                        default_value=param.get("default_value", 0),
                        description=param.get("description", "")
                    )

                # 4. Save Hardware Rules
                for hw_rule in hardware_rules_data:
                    hw = hw_rule.pop("hardware")
                    hw_id = hw.id if hasattr(hw, "id") else hw
                    ProductHardwareRule.objects.create(
                        product=product,
                        tenant=tenant,
                        hardware_id=hw_id,
                        quantity_equation=hw_rule.get("quantity_equation", "1"),
                        applicability_condition=hw_rule.get("applicability_condition", "")
                    )

                # 5. Save Part Templates (with nested materials & hardware)
                for pt_data in part_templates_data:
                    materials = pt_data.pop("material_whitelist", [])
                    hardware_rules = pt_data.pop("hardware_rules", [])
                    product_hardware = pt_data.pop("product_hardware", [])

                    pt_serializer = PartTemplateSerializer(data=pt_data, context=self.context)
                    pt_serializer.is_valid(raise_exception=True)
                    pt_instance = pt_serializer.save(product=product)

                    # --- REPLACED: Save materials whitelist with Auto-Edgeband Resolution ---
                    for mat_item in materials:
                        material_val = mat_item.get("material")
                        if not material_val:
                            continue
                        
                        # Handle potential Object vs ID mismatch
                        actual_material_id = material_val.id if hasattr(material_val, 'id') else material_val
                        
                        # 1. Create the Whitelist entry for the material
                        whitelist_entry = PartMaterialWhitelist.objects.create(
                            part_template=pt_instance,
                            tenant=tenant,
                            material_id=actual_material_id,
                            is_default=mat_item.get("is_default", False)
                        )

                        # 2. GET INTELLIGENT DEFAULT EDGEBAND
                        # We fetch the object to get the thickness_value for your resolver
                        try:
                            mat_obj = WoodMaterial.objects.get(id=actual_material_id)
                            _, default_eb = resolve_edgebands_for_material(mat_obj)
                        except WoodMaterial.DoesNotExist:
                            default_eb = None

                        # 3. Save EdgeBand relations for each selected side
                        sides = mat_item.get("selected_sides", [])
                        for side_name in sides:
                            # Prioritize payload ID, fallback to Intelligent Default
                            eb_id_from_payload = mat_item.get("edgeband_id")
                            
                            target_eb = None
                            if eb_id_from_payload:
                                target_eb = eb_id_from_payload # Use provided
                            elif default_eb:
                                target_eb = default_eb # Use auto-resolved
                            
                            if target_eb:
                                # Ensure we have an ID for the foreign key
                                final_eb_id = target_eb.id if hasattr(target_eb, 'id') else target_eb
                                
                                PartEdgeBandWhitelist.objects.create(
                                    material_selection=whitelist_entry,
                                    tenant=tenant,
                                    side=side_name.lower(),
                                    edgeband_id=final_eb_id,
                                    is_default=True
                                )

                    # Save part hardware rules
                    for h in hardware_rules:
                        hw = h.get("hardware")
                        hw_id = hw.id if hasattr(hw, "id") else hw
                        
                        PartHardwareRule.objects.create( # Use PartHardwareRule here!
                            part_template=pt_instance,
                            tenant=tenant,
                            hardware_id=hw_id,
                            quantity_equation=h.get("quantity_equation", "1"),
                            applicability_condition=h.get("applicability_condition", "")
                        )

                    # Save product hardware linked to this part
                    for ph in product_hardware:
                        hw = ph.get("hardware")
                        hw_id = hw.id if hasattr(hw, "id") else hw
                        
                        ProductHardwareRule.objects.create( # This model does NOT have part_template
                            product=product,
                            tenant=tenant,
                            hardware_id=hw_id,
                            quantity_equation=ph.get("quantity_equation", "1"),
                            applicability_condition=ph.get("condition_expression", "")
                            # DO NOT pass part_template here
                        )

                return product

        except Exception as e:
            print(f"DATABASE ERROR: {str(e)}")
            raise serializers.ValidationError({"server_error": str(e)})

    # --------------------------
    # Update
    # --------------------------
    def update(self, instance, validated_data):
        request = self.context.get("request")
        tenant = request.user.tenant

        parameters_data = validated_data.pop("parameters", [])
        hardware_rules_data = validated_data.pop("hardware_rules", [])
        part_templates_data = validated_data.pop("part_templates", [])

        try:
            with transaction.atomic():
                # Update main fields
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                instance.save()

                # ----- Parameters -----
                existing_params = {p.id: p for p in instance.parameters.all()}
                incoming_param_ids = set()
                for row in parameters_data:
                    row_id = row.get("id")
                    if row_id and row_id in existing_params:
                        for k, v in row.items():
                            setattr(existing_params[row_id], k, v)
                        existing_params[row_id].save()
                        incoming_param_ids.add(row_id)
                    else:
                        ProductParameter.objects.create(product=instance, tenant=tenant, **row)
                ProductParameter.objects.filter(product=instance).exclude(id__in=incoming_param_ids).delete()

                # ----- Hardware Rules -----
                existing_hw = {h.id: h for h in instance.hardware_rules.all()}
                incoming_hw_ids = set()
                for row in hardware_rules_data:
                    row_id = row.get("id")
                    hw = row.pop("hardware")
                    hw_id = hw.id if hasattr(hw, 'id') else hw
                    row['hardware_id'] = hw_id

                    if row_id and row_id in existing_hw:
                        for k, v in row.items():
                            setattr(existing_hw[row_id], k, v)
                        existing_hw[row_id].save()
                        incoming_hw_ids.add(row_id)
                    else:
                        ProductHardwareRule.objects.create(product=instance, tenant=tenant, **row)
                ProductHardwareRule.objects.filter(product=instance).exclude(id__in=incoming_hw_ids).delete()

                # ----- Part Templates -----
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
                        serializer = PartTemplateSerializer(data=row, context=self.context)
                        serializer.is_valid(raise_exception=True)
                        serializer.save(product=instance, tenant=tenant)
                PartTemplate.objects.filter(product=instance).exclude(id__in=incoming_part_ids).delete()

                return instance
        except Exception as e:
            raise serializers.ValidationError({"server_error": str(e)})

    # --------------------------
    # Validation
    # --------------------------
    def validate(self, attrs):
        part_templates_data = attrs.get("part_templates", getattr(self.instance, "part_templates", []))
        part_instances = []

        for pt in part_templates_data:
            if isinstance(pt, dict) and "id" in pt:
                try:
                    part_instances.append(PartTemplate.objects.get(id=pt["id"]))
                except PartTemplate.DoesNotExist:
                    part_instances.append(PartTemplate(**pt))
            elif isinstance(pt, PartTemplate):
                part_instances.append(pt)

        graph = build_dependency_graph(part_instances)
        if has_circular_dependency(graph):
            raise serializers.ValidationError({
                "part_templates": "Circular dependency detected between part expressions. Remove the loop."
            })
        return attrs

    def validate_product_validation_expression(self, value):
        if not value:
            return value
        ctx = ProductContext({}).get_context()
        try:
            validate_boolean_expression(value, ctx)
        except ValueError as e:
            raise serializers.ValidationError(f"Logic Error: {str(e)}")
        return value


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

class DryRunSerializer(serializers.Serializer):
    product_dims = serializers.DictField()
    parameters = serializers.ListField(required=False)
    part_templates = serializers.ListField()

    def validate(self, attrs):
        if not attrs.get("part_templates"):
            raise serializers.ValidationError(
                {"part_templates": "At least one part is required for preview."}
            )
        return attrs

