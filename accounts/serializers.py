from accounts.mixins import TenantSafeMixin
from rest_framework import serializers


class TenantSafeSerializerMixin(serializers.Serializer):
    tenant_field_map = {}

    def validate(self, data):
        tenant = self.context.get("tenant")
        if not tenant:
            return data

        for field, model in self.tenant_field_map.items():
            obj = data.get(field)
            if obj and getattr(obj, "tenant", None) != tenant:
                raise serializers.ValidationError({
                    field: "Invalid tenant reference"
                })
        return data


from .models import GlobalVariable

class GlobalVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalVariable
        fields = ['id', 'name', 'abbr', 'value', 'category']
        read_only_fields = ['id']

    def validate_abbr(self, value):
        if not value.startswith('@'):
            raise serializers.ValidationError("Abbreviations must start with '@' (e.g., @ST).")
        return value


