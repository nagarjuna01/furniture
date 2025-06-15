# products/filters.py
import django_filters
from .models import Product, StandardProduct, CustomProduct, ModularProduct, Type, Model, Review, Part

class ProductFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['category', 'type', 'model', 'brand', 'product_type']

class StandardProductFilter(ProductFilter):
    section = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(ProductFilter.Meta):
        model = StandardProduct
        fields = ProductFilter.Meta.fields + ['section']

class CustomProductFilter(ProductFilter):
    class Meta(ProductFilter.Meta):
        model = CustomProduct

class ModularProductFilter(ProductFilter):
    class Meta(ProductFilter.Meta):
        model = ModularProduct

class TypeFilter(django_filters.FilterSet):
    class Meta:
        model = Type
        fields = ['category']

class ModelFilter(django_filters.FilterSet):
    class Meta:
        model = Model
        fields = ['type__category', 'type']

class ReviewFilter(django_filters.FilterSet):
    class Meta:
        model = Review
        fields = ['product', 'user', 'rating']

class PartFilter(django_filters.FilterSet):
    class Meta:
        model = Part
        fields = ['material', 'shape_type']
