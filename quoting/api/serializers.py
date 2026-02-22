from rest_framework import serializers

class ClientNestedSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    tax_id = serializers.CharField(required=False, allow_blank=True)

class ProjectInitSerializer(serializers.Serializer):
    name = serializers.CharField() # Contact Person
    email = serializers.EmailField()
    source = serializers.CharField()
    status = serializers.CharField()
    client = ClientNestedSerializer() # The Nested Object