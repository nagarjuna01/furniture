from rest_framework import viewsets
from partisoproduct.models import Part1
from partisoproduct.serializers.part_serializers import Part1Serializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class Part1ViewSet(viewsets.ModelViewSet):
    queryset = Part1.objects.select_related('modular_product').prefetch_related(
        'compatible_categories', 'compatible_types', 'compatible_models', 'compatible_woods'
    ).all()
    serializer_class = Part1Serializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['modular_product']  # Optional if using get_queryset
    search_fields = ['name']
    ordering_fields = ['name']

    def get_queryset(self):
        queryset = Part1.objects.all()
        product_id = self.request.query_params.get('modular_product')
        if product_id:
            queryset = queryset.filter(modular_product_id=product_id)
        return queryset
