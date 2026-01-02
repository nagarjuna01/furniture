# filters.py
import django_filters
from .models import Product, ProductVariant

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    product_type = django_filters.NumberFilter(field_name="product_type_id")
    product_series = django_filters.NumberFilter(field_name="product_series_id")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Product
        fields = []

class ProductVariantFilter(django_filters.FilterSet):
    sku = django_filters.CharFilter(lookup_expr="icontains")
    product = django_filters.NumberFilter(field_name="product_id")
    is_active = django_filters.BooleanFilter()
    min_price = django_filters.NumberFilter(
        field_name="selling_price", lookup_expr="gte"
    )
    max_price = django_filters.NumberFilter(
        field_name="selling_price", lookup_expr="lte"
    )

    class Meta:
        model = ProductVariant
        fields = []
