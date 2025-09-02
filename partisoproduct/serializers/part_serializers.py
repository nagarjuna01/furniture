from rest_framework import serializers
from partisoproduct.models import Part1
from material.models import EdgeBand, Category, CategoryTypes, CategoryModel, WoodEn

class Part1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Part1
        fields = '__all__'
